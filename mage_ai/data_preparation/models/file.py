import errno
import os
import re
import shutil
import stat
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Iterator, List, Optional, Tuple

import aiofiles

from mage_ai.cache.dbt.constants import IGNORE_DIRECTORY_NAMES
from mage_ai.data_preparation.models.errors import (
    FileExistsError,
    FileNotInProjectError,
)
from mage_ai.data_preparation.models.project import Project
from mage_ai.data_preparation.models.project.constants import FeatureUUID
from mage_ai.settings.platform import project_platform_activated  # noqa: F401
from mage_ai.settings.repo import get_repo_path
from mage_ai.shared.environments import is_debug
from mage_ai.shared.files import exists_async, rename_async, write_async
from mage_ai.shared.path_fixer import remove_base_repo_path_or_name

FILE_VERSIONS_DIR = '.file_versions'
BLACKLISTED_DIRS = frozenset([
    'venv',
    'env',
    '.git',
    '.logs',
    '.variables',
    '.DS_Store',
    '__pycache__',
    FILE_VERSIONS_DIR,
])
INACCESSIBLE_DIRS = frozenset(['__pycache__'])
MAX_DEPTH = 30
MAX_NUMBER_OF_FILE_VERSIONS = int(os.getenv('MAX_NUMBER_OF_FILE_VERSIONS', 100) or 100)

PIPELINES_FOLDER_PREFIX = f'pipelines{os.sep}'


class File:
    def __init__(
        self,
        filename: str,
        dir_path: str,
        repo_path: str,
        project_bound: bool = False,
    ) -> None:
        self.filename = filename
        self.dir_path = dir_path
        self.repo_path = repo_path
        # When True, every filesystem access stays inside the root project directory.
        self.project_bound = project_bound
        self._identity = None

    @property
    def file_path(self) -> str:
        return os.path.join(self.repo_path, self.dir_path, self.filename)

    def bind_to_project(self) -> 'File':
        """Confine this file to the root project and record which file it currently is.

        Raises FileNotInProjectError if the path resolves outside the root project.
        Later reads refuse to return a different file than the one recorded here.
        """
        self.project_bound = True
        try:
            self._identity = _identity(stat_in_project(self.file_path))
        except (FileNotFoundError, NotADirectoryError):
            self._identity = None
        return self

    def _open_bound(self, flags: int) -> int:
        fd = open_in_project(self.file_path, flags)
        if self._identity is not None and _identity(os.fstat(fd)) != self._identity:
            os.close(fd)
            raise FileNotInProjectError(
                f'File at path: {self.file_path} changed after it was checked.',
            )
        return fd

    def _stat(self) -> Optional[os.stat_result]:
        try:
            if self.project_bound:
                return stat_in_project(self.file_path)
            return os.stat(self.file_path)
        except (FileNotFoundError, NotADirectoryError, FileNotInProjectError):
            return None

    @classmethod
    def file_exists(self, file_path: str) -> bool:
        return os.path.isfile(file_path)

    @classmethod
    def create_parent_directories(self, file_path: str, raise_exception: bool = False) -> bool:
        will_create = not self.file_exists(file_path)
        if will_create:
            try:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
            except FileExistsError as err:
                if raise_exception:
                    raise err
                print(f'[WARNING] File.create_parent_directories: {err}.')
        return will_create

    @classmethod
    def create(
        self,
        filename,
        dir_path,
        content: str = None,
        repo_path: str = None,
        create_directories_if_not_exist: bool = True,
        file_version_only: bool = False,
        overwrite: bool = True,
        project_bound: bool = False,
    ):
        repo_path = repo_path or get_repo_path(file_path=os.path.join(dir_path, filename))
        file = File(filename, dir_path, repo_path, project_bound=project_bound)

        self.write(
            repo_path,
            dir_path,
            filename,
            content,
            create_directories_if_not_exist=create_directories_if_not_exist,
            file_version_only=file_version_only,
            overwrite=overwrite,
            project_bound=project_bound,
        )

        return file

    @classmethod
    async def create_async(
        cls,
        filename,
        dir_path,
        content: Optional[str] = None,
        repo_path: Optional[str] = None,
        create_directories_if_not_exist: bool = True,
        file_version_only: bool = False,
        overwrite: Optional[bool] = True,
        project_bound: bool = False,
    ):
        repo_path = repo_path or get_repo_path(file_path=os.path.join(dir_path, filename))
        file = File(filename, dir_path, repo_path, project_bound=project_bound)

        await cls.write_async(
            repo_path,
            dir_path,
            filename,
            content,
            create_directories_if_not_exist=create_directories_if_not_exist,
            file_version_only=file_version_only,
            overwrite=overwrite,
            project_bound=project_bound,
        )

        return file

    @classmethod
    async def rename_async(
        cls, old_path: str, new_path: str, overwrite: Optional[bool] = None
    ) -> bool:
        result = await rename_async(old_path, new_path, overwrite=overwrite)

        old_filename = os.path.basename(old_path)
        old_dir_path = os.path.dirname(old_path)
        old_repo_path = get_repo_path(file_path=os.path.join(old_dir_path, old_filename))

        new_filename = os.path.basename(new_path)
        new_dir_path = os.path.dirname(new_path)
        new_repo_path = get_repo_path(file_path=os.path.join(new_dir_path, new_filename))

        old_file_path_versions_dir = cls.file_path_versions_dir(
            old_repo_path,
            old_dir_path,
            old_filename,
        )

        if await exists_async(old_file_path_versions_dir):
            new_file_path_versions_dir = cls.file_path_versions_dir(
                new_repo_path,
                new_dir_path,
                new_filename,
            )
            raise Exception(old_file_path_versions_dir, new_file_path_versions_dir)
            await write_async(new_file_path_versions_dir)

        return result

    @classmethod
    def from_path(self, file_path, repo_path: str = None):
        repo_path_alt = repo_path
        if repo_path_alt is None:
            repo_path_alt = get_repo_path(file_path=file_path)
        return File(
            os.path.basename(file_path or ''),
            os.path.dirname(file_path or ''),
            repo_path_alt or '',
        )

    @classmethod
    def get_all_files(
        self,
        repo_path,
        exclude_dir_pattern: str = None,
        exclude_pattern: str = None,
        pattern: str = None,
        check_file_path: bool = False,
        include_pipeline_count: bool = False,
    ):
        dir_selector = None
        file_selector = None

        if exclude_pattern is not None or pattern is not None:

            def __select(x: Dict, check_file_path=check_file_path, pattern=pattern):
                filename = x.get('path') if check_file_path else x.get('name')
                checks = []
                if exclude_pattern:
                    checks.append(not re.search(exclude_pattern, filename or ''))
                if pattern:
                    checks.append(re.search(pattern, filename or ''))
                return all(checks)

            file_selector = __select

        if exclude_dir_pattern is not None:

            def __select(x: Dict, pattern=pattern):
                filename = x.get('name')
                checks = []
                if exclude_dir_pattern:
                    checks.append(not re.search(exclude_dir_pattern, filename or ''))
                return all(checks)

            dir_selector = __select

        pipeline_count_mapping = None
        if include_pipeline_count:
            from mage_ai.cache.block import BlockCache

            pipeline_count_mapping = BlockCache().get_pipeline_count_mapping()

        return traverse(
            os.path.basename(repo_path),
            True,
            repo_path,
            dir_selector=dir_selector,
            file_selector=file_selector,
            include_pipeline_count=include_pipeline_count,
            pipeline_count_mapping=pipeline_count_mapping,
        )

    @classmethod
    def file_path_versions_dir(
        self,
        repo_path: str,
        dir_path: str,
        filename: str,
    ) -> str:
        return os.path.join(
            repo_path,
            FILE_VERSIONS_DIR,
            dir_path.replace(repo_path, os.path.join(repo_path, FILE_VERSIONS_DIR)),
            filename,
        )

    @classmethod
    def validate_content(self, dir_path, filename, content):
        if dir_path.startswith(PIPELINES_FOLDER_PREFIX) and filename == 'triggers.yaml':
            from mage_ai.data_preparation.models.triggers import load_trigger_configs

            pipeline_uuid = dir_path[len(PIPELINES_FOLDER_PREFIX) :]
            load_trigger_configs(content, pipeline_uuid=pipeline_uuid, raise_exception=True)

    @classmethod
    def write_preprocess(
        self,
        repo_path: str,
        dir_path: str,
        filename: str,
        content: str,
        create_directories_if_not_exist: bool = True,
        file_version_only: bool = False,
        overwrite: bool = True,
        project_bound: bool = False,
    ):
        file_path_main = os.path.join(repo_path, dir_path, filename)
        file_path_versions_dir = self.file_path_versions_dir(repo_path, dir_path, filename)
        file_path_versions = os.path.join(
            file_path_versions_dir,
            str(round(datetime.utcnow().timestamp())),
        )

        if project_bound:
            if not file_version_only:
                resolve_path_in_project(file_path_main)
            if MAX_NUMBER_OF_FILE_VERSIONS >= 1:
                resolve_path_in_project(file_path_versions)

        arr = []

        if not file_version_only:
            arr.append((file_path_main, overwrite, create_directories_if_not_exist))

        if MAX_NUMBER_OF_FILE_VERSIONS >= 1:
            arr.append((file_path_versions, True, True))

            file_versions = []
            step = 0
            for _, _, files in os.walk(file_path_versions_dir):
                if step >= 1:
                    continue
                file_versions += files
                step += 1
            number_of_file_versions = len(file_versions)

            if number_of_file_versions >= MAX_NUMBER_OF_FILE_VERSIONS:
                number_of_file_versions_to_delete = 1 + (
                    number_of_file_versions - MAX_NUMBER_OF_FILE_VERSIONS
                )
                for fn in sorted(file_versions)[:number_of_file_versions_to_delete]:
                    fn_path = os.path.join(file_path_versions_dir, fn)
                    if project_bound:
                        remove_file_in_project(fn_path)
                    else:
                        os.remove(fn_path)

        for tup in arr:
            file_path, should_overwrite, should_create_directories = tup
            write_type = 'wb' if content and type(content) is bytes else 'w'

            if project_bound:
                flags = os.O_WRONLY | os.O_CREAT | (os.O_TRUNC if should_overwrite else os.O_EXCL)
                if write_type == 'wb':
                    flags |= getattr(os, 'O_BINARY', 0)
                try:
                    fd = open_in_project(
                        file_path,
                        flags,
                        create_parents=should_create_directories,
                    )
                except OSError as err:
                    if err.errno == errno.EEXIST:
                        raise FileExistsError(f'File at {file_path} already exists.')
                    raise
                yield fd, write_type
                continue

            if self.file_exists(file_path) and not should_overwrite:
                raise FileExistsError(f'File at {file_path} already exists.')

            if should_create_directories:
                self.create_parent_directories(file_path)

            yield file_path, write_type

    @classmethod
    def write(
        self,
        repo_path: str,
        dir_path: str,
        filename: str,
        content: str,
        create_directories_if_not_exist: bool = True,
        file_version_only: bool = False,
        overwrite: bool = True,
        project_bound: bool = False,
    ) -> None:
        for file_path, write_type in self.write_preprocess(
            repo_path,
            dir_path,
            filename,
            content,
            create_directories_if_not_exist=create_directories_if_not_exist,
            file_version_only=file_version_only,
            overwrite=overwrite,
            project_bound=project_bound,
        ):
            kwargs = dict(
                mode=write_type,
            )
            if write_type != 'wb':
                kwargs['encoding'] = 'utf-8'
            with open(file_path, **kwargs) as f:
                if content:
                    f.write(content or '')
        self.validate_content(dir_path, filename, content)

        update_caches(repo_path, dir_path, filename)

        update_file_cache()

    @classmethod
    async def write_async(
        self,
        repo_path: str,
        dir_path: str,
        filename: str,
        content: str,
        create_directories_if_not_exist: bool = True,
        file_version_only: bool = False,
        overwrite: bool = True,
        project_bound: bool = False,
    ) -> None:
        for file_path, write_type in self.write_preprocess(
            repo_path,
            dir_path,
            filename,
            content,
            create_directories_if_not_exist=create_directories_if_not_exist,
            file_version_only=file_version_only,
            overwrite=overwrite,
            project_bound=project_bound,
        ):
            kwargs = dict(
                mode=write_type,
            )
            if write_type != 'wb':
                kwargs['encoding'] = 'utf-8'
            async with aiofiles.open(file_path, **kwargs) as fp:
                await fp.write(content or '')

        await update_caches_async(repo_path, dir_path, filename)

        update_file_cache()

    @property
    def size(self) -> int:
        if self.project_bound:
            return stat_in_project(self.file_path).st_size
        return os.path.getsize(self.file_path)

    @property
    def modified_timestamp(self) -> float:
        if self.project_bound:
            return stat_in_project(self.file_path).st_mtime
        return os.path.getmtime(self.file_path)

    def exists(self) -> bool:
        if self.project_bound:
            file_stat = self._stat()
            return file_stat is not None and stat.S_ISREG(file_stat.st_mode)
        return self.file_exists(self.file_path)

    def content(self):
        try:
            if self.project_bound:
                fp = open(self._open_bound(os.O_RDONLY), encoding='utf-8')
            else:
                fp = open(self.file_path, encoding='utf-8')
            with fp:
                file_content = fp.read()
            return file_content
        except FileNotFoundError as err:
            print(f'[ERROR] File.content: {err}')
            if is_debug():
                raise err
        return ''

    async def content_async(self):
        try:
            target = self._open_bound(os.O_RDONLY) if self.project_bound else self.file_path
            async with aiofiles.open(target, mode='r', encoding='utf-8') as fp:
                file_content = await fp.read()
            return file_content
        except Exception as err:
            print(f'[File.content_async] {err}')
        return ''

    def file_versions(self) -> List[str]:
        file_path_versions_dir = self.file_path_versions_dir(
            self.repo_path,
            self.dir_path,
            self.filename,
        )
        if self.project_bound:
            try:
                resolve_path_in_project(file_path_versions_dir)
            except FileNotInProjectError:
                return []

        file_versions = []
        step = 0
        for _, _, files in os.walk(file_path_versions_dir):
            if step >= 1:
                continue
            file_versions += files
            step += 1

        file_path_versions_dir_without_repo = file_path_versions_dir.replace(
            os.path.join(self.repo_path, ''),
            '',
        )
        return [
            File(
                v,
                file_path_versions_dir_without_repo,
                self.repo_path,
                project_bound=self.project_bound,
            )
            for v in sorted(file_versions, reverse=True)
        ]

    def update_content(self, content: str):
        self.write(
            self.repo_path,
            self.dir_path,
            self.filename,
            content,
            project_bound=self.project_bound,
        )

    async def update_content_async(self, content: str):
        await self.write_async(
            self.repo_path,
            self.dir_path,
            self.filename,
            content,
            project_bound=self.project_bound,
        )

    def delete(self):
        if self.project_bound:
            remove_file_in_project(self.file_path)
        else:
            os.remove(self.file_path)

        update_file_cache()

    def rename(self, dir_path: str, filename):
        full_path = os.path.join(self.repo_path, dir_path, filename)

        if self.project_bound:
            rename_in_project(self.file_path, full_path)
        else:
            self.create_parent_directories(full_path)
            os.rename(self.file_path, full_path)

        file_path_versions_dir = self.file_path_versions_dir(
            self.repo_path,
            self.dir_path,
            self.filename,
        )
        if os.path.exists(file_path_versions_dir):
            new_path = self.file_path_versions_dir(
                self.repo_path,
                dir_path,
                filename,
            )
            if self.project_bound:
                rename_in_project(file_path_versions_dir, new_path)
            else:
                os.makedirs(new_path, exist_ok=True)
                os.rename(
                    file_path_versions_dir,
                    new_path,
                )

        self.dir_path = dir_path
        self.filename = filename

        update_file_cache()

    def to_dict(self, include_content: bool = False, include_metadata: bool = False):
        file_exists = self.exists()
        data = dict(
            name=self.filename,
            path=os.path.join(self.dir_path, self.filename),
            size=None,
            modified_timestamp=None,
        )

        if include_content:
            data['content'] = self.content()

        if include_metadata and file_exists:
            data['size'] = self.size
            data['modified_timestamp'] = self.modified_timestamp

        return data

    async def to_dict_async(self, include_content=False):
        file_exists = self.exists()
        data = dict(
            name=self.filename,
            path=os.path.join(self.dir_path, self.filename),
            size=self.size if file_exists else None,
            modified_timestamp=self.modified_timestamp if file_exists else None,
        )
        if include_content:
            data['content'] = await self.content_async()

        return data


def project_root_real_path() -> str:
    return os.path.realpath(get_repo_path(root_project=True))


def resolve_path_in_project(
    path: str,
    follow_symlinks: bool = True,
    root: Optional[str] = None,
) -> str:
    """Return the real path of `path`, or raise FileNotInProjectError when it is outside
    `root` (default: the root project directory). This applies whether or not project
    platform is activated, because every project in the platform lives under the root
    project directory.

    With follow_symlinks=False, the last path component is kept as is (e.g. to delete or
    rename a symlink itself), while all of its parent directories are resolved.
    """
    try:
        name = os.path.basename(path)
        if follow_symlinks or name in ('', os.curdir, os.pardir):
            resolved = os.path.realpath(path)
        else:
            resolved = os.path.join(os.path.realpath(os.path.dirname(path) or os.curdir), name)
        root = os.path.realpath(root) if root else project_root_real_path()
        in_project = os.path.commonpath([resolved, root]) == root
    except (TypeError, ValueError):
        in_project = False

    if not in_project:
        raise FileNotInProjectError(f'File at path: {path} is not in the project directory.')

    return resolved


def ensure_file_is_in_project(file_path: str) -> None:
    resolve_path_in_project(file_path)


_DIR_FD_SUPPORTED = (
    hasattr(os, 'O_NOFOLLOW')
    and hasattr(os, 'O_DIRECTORY')
    and all(
        fn in os.supports_dir_fd
        for fn in (os.open, os.mkdir, os.rename, os.rmdir, os.stat, os.unlink)
    )
)


def _identity(file_stat: os.stat_result) -> Tuple[int, int]:
    return file_stat.st_dev, file_stat.st_ino


def _open_directory(name: str, dir_fd: Optional[int] = None) -> int:
    return os.open(
        name,
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, 'O_CLOEXEC', 0),
        dir_fd=dir_fd,
    )


def _is_symlink_error(err: OSError) -> bool:
    return err.errno in (errno.ELOOP, errno.EMLINK, errno.ENOTDIR)


@contextmanager
def _parent_directory_in_project(
    path: str,
    follow_symlinks: bool = True,
    create_parents: bool = False,
    root: Optional[str] = None,
) -> Iterator[Tuple[Optional[int], str]]:
    """Yield an open file descriptor of the parent directory of `path` and the name of
    `path` inside it.

    The descriptor is reached from the root project directory one component at a time
    without following symlinks, so a directory swapped for a symlink after the path was
    resolved is refused instead of followed out of the project.

    On platforms without dir_fd support, yields (None, resolved path).
    """
    resolved = resolve_path_in_project(path, follow_symlinks=follow_symlinks, root=root)
    root = os.path.realpath(root) if root else project_root_real_path()
    relative = os.path.relpath(resolved, root)
    if relative == os.curdir:
        raise FileNotInProjectError(f'Path: {path} is the project directory itself.')
    parts = relative.split(os.sep)

    if not _DIR_FD_SUPPORTED:
        if create_parents:
            os.makedirs(os.path.dirname(resolved), exist_ok=True)
        yield None, resolved
        return

    dir_fd = _open_directory(root)
    try:
        for part in parts[:-1]:
            if create_parents:
                try:
                    os.mkdir(part, dir_fd=dir_fd)
                except OSError as err:
                    if err.errno != errno.EEXIST:
                        raise
            try:
                next_dir_fd = _open_directory(part, dir_fd=dir_fd)
            except OSError as err:
                if _is_symlink_error(err):
                    raise FileNotInProjectError(
                        f'File at path: {path} is not in the project directory.',
                    ) from err
                raise
            os.close(dir_fd)
            dir_fd = next_dir_fd
        yield dir_fd, parts[-1]
    finally:
        os.close(dir_fd)


def open_in_project(
    path: str,
    flags: int,
    mode: int = 0o666,
    create_parents: bool = False,
    root: Optional[str] = None,
) -> int:
    """Open `path` and return its file descriptor, refusing anything outside `root` (default:
    the root project directory), including through symlinks or directories swapped while
    opening."""
    with _parent_directory_in_project(
        path,
        create_parents=create_parents,
        root=root,
    ) as (dir_fd, name):
        if dir_fd is None:
            return os.open(name, flags, mode)
        try:
            return os.open(
                name,
                flags | os.O_NOFOLLOW | getattr(os, 'O_CLOEXEC', 0),
                mode,
                dir_fd=dir_fd,
            )
        except OSError as err:
            if _is_symlink_error(err):
                raise FileNotInProjectError(
                    f'File at path: {path} is not in the project directory.',
                ) from err
            raise


def stat_in_project(path: str) -> os.stat_result:
    with _parent_directory_in_project(path) as (dir_fd, name):
        if dir_fd is None:
            return os.stat(name)
        return os.stat(name, dir_fd=dir_fd, follow_symlinks=False)


def remove_file_in_project(path: str) -> None:
    with _parent_directory_in_project(path, follow_symlinks=False) as (dir_fd, name):
        if dir_fd is None:
            os.remove(name)
        else:
            os.unlink(name, dir_fd=dir_fd)


def rename_in_project(old_path: str, new_path: str, create_parents: bool = True) -> None:
    with _parent_directory_in_project(old_path, follow_symlinks=False) as (old_dir_fd, old_name):
        with _parent_directory_in_project(
            new_path,
            follow_symlinks=False,
            create_parents=create_parents,
        ) as (new_dir_fd, new_name):
            if old_dir_fd is None:
                os.rename(old_name, new_name)
            else:
                os.rename(old_name, new_name, src_dir_fd=old_dir_fd, dst_dir_fd=new_dir_fd)


def make_directories_in_project(path: str, exist_ok: bool = False) -> None:
    with _parent_directory_in_project(
        path,
        follow_symlinks=False,
        create_parents=True,
    ) as (dir_fd, name):
        if dir_fd is None:
            os.makedirs(name, exist_ok=exist_ok)
            return
        try:
            os.mkdir(name, dir_fd=dir_fd)
        except OSError as err:
            if err.errno != errno.EEXIST or not exist_ok:
                raise
            if not stat.S_ISDIR(os.stat(name, dir_fd=dir_fd, follow_symlinks=False).st_mode):
                raise


def _remove_tree_at(dir_fd: int, name: str) -> None:
    child_fd = _open_directory(name, dir_fd=dir_fd)
    try:
        with os.scandir(child_fd) as entries:
            children = [(entry.name, entry.is_dir(follow_symlinks=False)) for entry in entries]
        for child_name, is_dir in children:
            if is_dir:
                _remove_tree_at(child_fd, child_name)
            else:
                os.unlink(child_name, dir_fd=child_fd)
    finally:
        os.close(child_fd)
    os.rmdir(name, dir_fd=dir_fd)


def remove_directory_in_project(path: str) -> None:
    with _parent_directory_in_project(path, follow_symlinks=False) as (dir_fd, name):
        if dir_fd is None:
            shutil.rmtree(name)
        else:
            _remove_tree_at(dir_fd, name)


def traverse(
    name: str,
    is_dir: bool,
    path: str,
    disabled=False,
    depth=1,
    dir_selector: Callable = None,
    file_selector: Callable = None,
    include_pipeline_count: bool = False,
    pipeline_count_mapping: Dict = None,
) -> Dict:
    tree_entry = dict(name=name)
    if not is_dir:
        tree_entry['disabled'] = disabled
        if include_pipeline_count:
            pipeline_count_mapping = pipeline_count_mapping or {}
            cache_key = remove_base_repo_path_or_name(path)
            pipeline_count = pipeline_count_mapping.get(cache_key)
            if pipeline_count is not None:
                tree_entry['pipeline_count'] = pipeline_count

        return tree_entry
    if depth >= MAX_DEPTH:
        return tree_entry
    can_access_children = name[0] == '.' or name in INACCESSIBLE_DIRS

    def __filter(
        entry,
        depth=depth,
        dir_selector=dir_selector,
        file_selector=file_selector,
    ) -> bool:
        if entry.name in BLACKLISTED_DIRS:
            return False

        if not file_selector:
            return True

        entry_path = entry.path
        if entry.is_dir(follow_symlinks=False) or os.path.isdir(entry_path):
            return (
                True
                if dir_selector is None
                else dir_selector(
                    dict(
                        depth=depth + 1,
                        name=str(entry.name),
                        path=entry.path,
                    )
                )
            )
        else:
            return file_selector(
                dict(
                    depth=depth + 1,
                    name=str(entry.name),
                    path=entry.path,
                )
            )

        return True

    tree_entry['children'] = list(
        traverse(
            entry.name,
            entry.is_dir(follow_symlinks=False),
            entry.path,
            can_access_children,
            depth + 1,
            dir_selector=dir_selector,
            file_selector=file_selector,
            include_pipeline_count=include_pipeline_count,
            pipeline_count_mapping=pipeline_count_mapping,
        )
        for entry in sorted(
            filter(__filter, os.scandir(path)),
            key=lambda entry: entry.name,
        )
    )

    return tree_entry


def __should_update_dbt_cache(dir_path: str, filename: str) -> bool:
    project_model = Project(root_project=True)
    if project_model and project_model.is_feature_enabled(FeatureUUID.DBT_V2) and dir_path:
        # If the file is a SQL or YAML file
        if filename.endswith('.sql') or filename.endswith('.yml') or filename.endswith('.yaml'):
            base_dir_path = Path(dir_path).parts[0].lower()
            # If the file doesn’t exist in a block’s folder (e.g. data_loaders/, pipelines/)
            if base_dir_path not in IGNORE_DIRECTORY_NAMES:
                # If project platform features isn’t enabled or the repo_path exists outside of
                # the registered projects.
                return True

    return False


async def update_caches_async(repo_path: str, dir_path: str, filename: str) -> None:
    if __should_update_dbt_cache(dir_path, filename):
        print(f'Updating dbt cache for {repo_path}.')

        try:
            from mage_ai.cache.dbt.cache import DBTCache

            dbt_cache = await DBTCache.initialize_cache_async(root_project=True)
            await dbt_cache.update_async(file_path=os.path.join(repo_path, dir_path, filename))
        except Exception as err:
            print(f'[ERROR] File update DBTCache for {repo_path}, {dir_path}, {filename}: {err}.')
            if is_debug():
                raise err


def update_caches(repo_path: str, dir_path: str, filename: str) -> None:
    if __should_update_dbt_cache(dir_path, filename):
        print(f'Updating dbt cache for {repo_path}.')

        try:
            from mage_ai.cache.dbt.cache import DBTCache

            dbt_cache = DBTCache.initialize_cache(root_project=True)
            dbt_cache.update(file_path=os.path.join(repo_path, dir_path, filename))
        except Exception as err:
            print(f'[ERROR] File update DBTCache for {repo_path}, {dir_path}, {filename}: {err}.')
            if is_debug():
                raise err


def update_file_cache() -> None:
    project_model = Project(root_project=True)
    if project_model and project_model.is_feature_enabled(FeatureUUID.COMMAND_CENTER):
        from mage_ai.cache.file import FileCache

        FileCache().invalidate()
