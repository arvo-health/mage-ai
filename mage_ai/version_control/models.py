import asyncio
import os
import re
import shlex
import shutil
import subprocess
import time
from asyncio.subprocess import PIPE, STDOUT
from dataclasses import dataclass, field
from typing import Any, Dict, List

from mage_ai.authentication.oauth.constants import ProviderName
from mage_ai.data_preparation.git.api import get_user
from mage_ai.data_preparation.git.utils import (
    execute_on_remote_branch,
    get_access_token,
    get_auth_type_from_url,
    get_oauth_access_token_for_user,
    get_provider_from_remote_url,
)
from mage_ai.data_preparation.preferences import Preferences, get_preferences
from mage_ai.data_preparation.sync import AuthType, GitConfig
from mage_ai.orchestration.db.models.oauth import User
from mage_ai.settings.platform import platform_settings, update_settings
from mage_ai.settings.utils import base_repo_path
from mage_ai.shared.array import find, unique_by
from mage_ai.shared.files import read_async
from mage_ai.shared.hash import merge_dict
from mage_ai.shared.models import BaseDataClass
from mage_ai.version_control.branch import utils as branch_utils

# Subcommands that can be run through the free-form git command field.
ALLOWED_GIT_SUBCOMMANDS = frozenset([
    'add',
    'blame',
    'branch',
    'checkout',
    'cherry-pick',
    'commit',
    'diff',
    'fetch',
    'log',
    'ls-files',
    'merge',
    'mv',
    'pull',
    'push',
    'rebase',
    'reflog',
    'remote',
    'reset',
    'restore',
    'revert',
    'rm',
    'shortlog',
    'show',
    'stash',
    'status',
    'switch',
    'tag',
])

# Options that make git run another program, write to an arbitrary path, or read a
# file from outside the repository. Git accepts unambiguous prefixes of long options,
# so these are matched by prefix.
BLOCKED_GIT_LONG_OPTIONS = (
    '--config',
    '--contents',
    '--exec',
    '--exec-path',
    '--ext-diff',
    '--file',
    '--git-dir',
    '--no-index',
    '--open-files-in-pager',
    '--output',
    '--output-directory',
    '--pathspec-from-file',
    '--receive-pack',
    '--template',
    '--textconv',
    '--upload-pack',
    '--work-tree',
)

BLOCKED_GIT_SHORT_OPTIONS = {
    'blame': frozenset('S'),
    'commit': frozenset('Ft'),
    'rebase': frozenset('x'),
    'tag': frozenset('F'),
}


def is_option_like(value: str) -> bool:
    return isinstance(value, str) and value.startswith('-')


def validate_git_command_args(args: List[str]) -> str:
    """Returns an error message if the arguments are not allowed, otherwise None."""
    if not args:
        return 'error: no git command was provided.'

    subcommand = args[0]
    if subcommand not in ALLOWED_GIT_SUBCOMMANDS:
        return f'error: git command "{subcommand}" is not allowed.'

    blocked_short = BLOCKED_GIT_SHORT_OPTIONS.get(subcommand, frozenset())
    for arg in args[1:]:
        if arg == '--':
            break

        if arg.startswith('--'):
            name = arg.split('=', 1)[0]
            if len(name) > 2 and any(opt.startswith(name) for opt in BLOCKED_GIT_LONG_OPTIONS):
                return f'error: git option "{name}" is not allowed.'
        elif arg.startswith('-') and blocked_short.intersection(arg[1:]):
            return f'error: git option "{arg}" is not allowed.'

    return None


def split_names(text: str) -> List[str]:
    try:
        return shlex.split(text)
    except ValueError:
        return text.split()


@dataclass
class BaseVersionControl(BaseDataClass):
    output: List[str] = None
    project: Any = None
    project_uuid: str = None

    @property
    def git(self):
        return self.repo.git

    @property
    def repo(self):
        import git
        return git.Repo(self.project.repo_path)

    def prepare_commands(self, args: List[str]) -> List[str]:
        if isinstance(args, str):
            raise TypeError('Git commands must be passed as a list of arguments.')

        args = [
            'git',
            '-C',
            self.repo_path,
        ] + [str(arg) for arg in args]

        print(f'[VersionControl] Run: {shlex.join(args)}')

        return args

    async def run_async(
        self,
        args: List[str],
        timeout: int = 12,
    ) -> List[str]:
        proc = await asyncio.wait_for(
            asyncio.create_subprocess_exec(
                *self.prepare_commands(args),
                stdin=PIPE,
                stdout=PIPE,
                stderr=STDOUT,
            ),
            timeout,
        )

        output = await proc.stdout.read()
        return self.add_outputs(output.decode().split('\n') if output else output)

    def run(self, args: List[str]) -> List[str]:
        proc = subprocess.run(
            self.prepare_commands(args),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

        return self.add_outputs(proc.stdout.decode().split('\n'))

    def run_with_inputs(self, args: List[str], message: str) -> List[str]:
        proc = subprocess.Popen(
            self.prepare_commands(args),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        time.sleep(3)
        proc.communicate(message.encode())

        return self.add_outputs(proc.stdout.decode().split('\n'))

    @property
    def repo_path(self) -> str:
        return self.project.repo_path if self.project else None

    def to_dict(self, **kwargs) -> Dict:
        return dict(
            output=self.output,
            project_uuid=self.project.uuid if self.project else None,
            repo_path=self.repo_path,
        )

    def add_outputs(self, lines: List[str]) -> List[str]:
        self.output = self.output or []
        if lines:
            if isinstance(lines, str):
                lines = lines.split('\n')
            self.output.extend(lines)
        return self.output


@dataclass
class Commit(BaseVersionControl):
    message: str = None
    sha: str = None


@dataclass
class Provider(BaseVersionControl):
    name: ProviderName = field(default_factory=lambda: ProviderName.GITHUB)

    @classmethod
    def load(self, name: ProviderName = None, url: str = None) -> 'Provider':
        return self(name=name or get_provider_from_remote_url(url) if url else ProviderName.GITHUB)


@dataclass
class Remote(BaseVersionControl):
    name: str = None
    provider: Provider = None
    url: str = None

    @classmethod
    def load_all(self, project: 'Project' = None) -> List['Remote']:
        lines = self(project=project).list()

        arr = []
        for remote in unique_by(
            [self.load_from_text(line) for line in lines if len(line) >= 1],
            lambda x: x.name,
        ):
            remote.project = project
            arr.append(remote)

        return arr

    @classmethod
    def load_from_text(self, line: str) -> Dict:
        name = ''
        url = ''
        parts = line.split('\t')
        if len(parts) >= 1:
            name = parts[0]
            if len(parts) >= 2:
                url = parts[1]
                url = url.split('(')[0].strip()

        return self.load(
            name=name.strip(),
            url=url.strip(),
        )

    def hydrate(self, name: str = None, project=None) -> BaseVersionControl:
        self.name = name or self.name
        self.project = project or self.project

        match = find(
            lambda x: x and x.name == self.name,
            [self.load_from_text(line) for line in self.list() if len(line.strip()) >= 1],
        )
        if match:
            self.url = match.url
        self.provider = Provider.load(url=self.url)

        return self

    def list(self) -> List[str]:
        return self.run(['remote', '-v'])

    def create(self) -> List[str]:
        return self.run(['remote', 'add', '--', self.name, self.url])

    def delete(self) -> List[str]:
        return self.run(['remote', 'rm', '--', self.name])

    def update(self, fetch: bool = False, set_url: bool = False) -> List[str]:
        if fetch:
            return self.run(['fetch', '--', self.name])
        elif set_url:
            return self.run(['remote', 'set-url', '--', self.name, self.url])

        return ['Nothing was done.']

    def to_dict(self, **kwargs) -> Dict:
        return merge_dict(super().to_dict(**kwargs), dict(
            name=self.name,
            url=self.url,
        ))


@dataclass
class Branch(BaseVersionControl):
    current: bool = None
    name: str = None
    remote: Remote = None

    @classmethod
    def clean(self, line: str) -> str:
        if line.startswith('*'):
            line = line[1:].strip()
        return line.strip()

    @classmethod
    def load_all(
        self,
        lines: List[str] = None,
        remote: Remote = None,
        project: 'Project' = None,
    ) -> List['Branch']:
        base = self(project=project)

        if not lines:
            lines = base.list(include_all=True)

        mapping = {}
        arr = []
        for line in lines:
            if len(line) == 0:
                continue

            current = line.startswith('*')
            name = self.clean(line)
            if name not in mapping:
                mapping[name] = True
                model = self.load(current=current, name=name)
                model.remote = remote
                model.project = project
                arr.append(model)

        if len([line for line in base.list() if line and line.strip()]) == 0:
            # Need to fake a local branch until user makes a commit.
            name = 'master'

            output = base.run(['reflog'])
            if output:
                parts = output[0].split("'")
                if len(parts) == 3:
                    name = parts[1]

            model = Branch.load(current=True, name=name)
            model.remote = remote
            model.project = project
            arr.append(model)

        return arr

    @property
    def auth_type(self) -> AuthType:
        return self.project.auth_type or get_auth_type_from_url(self.remote.url),

    def hydrate(self, remote=None, project=None, **kwargs) -> BaseVersionControl:
        self.remote = remote or self.remote
        self.project = project or self.project

        if kwargs:
            for k, v in kwargs.items():
                setattr(self, k, v)

        if self.name:
            model = find(
                lambda x, b=self: x.name == b.name,
                self.load_all(remote=self.remote, project=self.project),
            )
            if model:
                self.current = model.current

        return self

    def get_current_branch(self) -> 'Branch':
        return find(lambda x: x.current, self.load_all(
            lines=self.run(['branch']),
            project=self.project,
            remote=self.remote,
        ))

    def list(self, include_all: bool = False) -> List[str]:
        commands = ['branch']
        if include_all:
            commands.append('-a')

        return self.run(commands)

    def invalid_name_error(self) -> List[str]:
        names = [self.name]
        if self.remote and self.remote.name:
            names.append(self.remote.name)

        for name in names:
            if is_option_like(name):
                return self.add_outputs([f'error: invalid branch or remote name "{name}".'])

        return None

    def create(self) -> List[str]:
        error = self.invalid_name_error()
        if error:
            return error

        return self.run(['checkout', '-b', self.name])

    def detail(self, **kwargs) -> List[str]:
        return []

    def delete(self, name: str = None, force: bool = False) -> List[str]:
        flag = 'd'
        if force:
            flag = flag.upper()
        return self.run(['branch', f'-{flag}', '--', name or self.name])

    async def update_async(
        self,
        checkout: bool = False,
        clone: bool = False,
        merge: bool = False,
        pull: bool = False,
        push: bool = False,
        rebase: bool = False,
    ) -> List[str]:
        error = self.invalid_name_error()
        if error:
            return error

        commands = []

        if clone:
            commands.extend(['clone', '-b', self.name, '--'])
            if self.remote and self.remote.url:
                commands.append(self.remote.url)
        elif pull or rebase:
            commands.extend(['rebase' if rebase else 'pull', '--'])
            if self.remote and self.remote.name:
                commands.append(self.remote.name)
            commands.append(self.name)
        elif merge:
            commands.extend(['merge', '--', self.name])
        elif checkout:
            # The trailing "--" makes git treat the name as a branch, never as a path.
            commands.extend(['checkout', self.name, '--'])
        elif push:
            self.project.set_user_config()
            if AuthType.SSH == self.project.auth_type:
                return await execute_on_remote_branch(self.git.push, self)(
                    '--set-upstream',
                    '--',
                    self.remote.name,
                    self.name,
                )
            else:
                return await branch_utils.push(self)

        lines = await self.run_async(commands)
        self.hydrate()

        return lines

    def to_dict(self, **kwargs) -> Dict:
        return merge_dict(super().to_dict(**kwargs), dict(
            current=self.current,
            name=self.name,
            remote=self.remote.to_dict(**kwargs) if self.remote else None,
        ))


@dataclass
class File(BaseVersionControl):
    additions: int = None
    content: str = None
    deletions: int = None
    diff: List[str] = None
    file_path: str = None
    name: str = None
    staged: bool = False
    unstaged: bool = False
    untracked: bool = False

    @classmethod
    def load_all(self, project: 'Project' = None) -> List['File']:
        lines_staged = self(project=project).list(staged=True)
        lines_unstaged = self(project=project).list(unstaged=True)
        lines_untracked = self(project=project).list(untracked=True)

        mapping = {}
        for opts, arr in [
            (dict(staged=True), lines_staged),
            (dict(unstaged=True), lines_unstaged),
            (dict(untracked=True), lines_untracked),
        ]:
            for line in arr:
                if line and line.strip():
                    file = File.load(name=line.strip(), **opts)
                    file.project = project
                    file_path = file.get_file_path()

                    if file_path in mapping:
                        file_prev = mapping[file_path]
                        file.staged = file.staged and file_prev.staged
                        file.unstaged = file.unstaged or file_prev.unstaged
                        file.untracked = file.untracked or file_prev.untracked
                    mapping[file_path] = file

        return sorted(list(mapping.values()), key=lambda x: x.name)

    def diff_stats(self, include_all: bool = False) -> Dict:
        lines = []
        if include_all:
            lines.extend(self.run(['diff', '--stat']))
        else:
            lines.extend(self.run(['diff', '--stat', '--', self.name]))

        mapping = {}

        # Remove the last line
        # 5 files changed, 232 insertions(+), 28 deletions(-)
        for line in lines[:-1]:
            line = line.strip()
            parts = line.split('|')
            if len(parts) != 2:
                continue

            name, stats = parts
            name = name.strip()
            stats = stats.strip()

            match = re.search(r'^[\d]+[ ]*([+-]+)$', stats)
            if match:
                symbols = match.group(1)
                additions = symbols.count('+')
                deletions = symbols.count('-')

                mapping[name] = dict(
                    additions=additions,
                    deletions=deletions,
                )

        if mapping.get(self.name):
            stats = mapping[self.name]
            self.additions = stats.get('additions')
            self.deletions = stats.get('deletions')

        return mapping

    def list(
        self,
        staged: bool = False,     # Modified and git add already
        unstaged: bool = False,   # Modified but no git add yet
        untracked: bool = False,  # Modified but never checked in before
    ) -> str:
        # A file can belong to staged and unstaged because it has unstaged modifications.
        outputs = []
        if staged:
            outputs.extend(self.run(['diff', '--name-only', '--staged']))

        # Files with unstaged changes
        if unstaged:
            outputs.extend(self.run(['diff', '--name-only']))

        if untracked:
            outputs.extend(self.run(['ls-files', '--others', '--exclude-standard']))

        if not staged and not unstaged and not untracked:
            outputs.extend(self.run(['ls-files', '--other', '--modified', '--exclude-standard']))

        self.output = outputs

        return outputs

    def create(self) -> List[str]:
        return self.run(['add', '--', self.name])

    async def detail_async(self) -> List[str]:
        self.diff = await self.run_async(['diff', '--', self.name])
        return self.diff

    async def read_content_async(self) -> str:
        if os.path.exists(self.get_file_path()):
            self.content = await read_async(self.get_file_path())
            return self.content

    def detail(self) -> List[str]:
        self.diff = self.run(['diff', '--', self.name])
        return self.diff

    async def update_async(
        self,
        add: str = None,
        command: str = None,
        commit: str = None,
        reset: str = False,
    ) -> List[str]:
        if add:
            return await self.run_async(['add', '--'] + split_names(add))
        elif command:
            try:
                args = shlex.split(command)
            except ValueError as err:
                return self.add_outputs([f'error: {err}'])

            if args and args[0] == 'git':
                args = args[1:]

            error = validate_git_command_args(args)
            if error:
                return self.add_outputs([error])

            return await self.run_async(args)
        elif commit:
            return await self.run_async(['commit', '-m', commit])
        elif reset:
            return await self.run_async(['reset', '--'] + split_names(reset))

        return ['Nothing was done.']

    def delete(self) -> List[str]:
        return self.run(['checkout', '--', self.name])

    def get_file_path(self) -> str:
        return self.file_path or os.path.join(self.repo_path, self.name)

    def hydrate(self, project=None, **kwargs) -> BaseVersionControl:
        self.project = project or self.project
        return self

    def to_dict(self, **kwargs) -> Dict:
        return merge_dict(super().to_dict(**kwargs), dict(
            additions=self.additions,
            content=self.content,
            deletions=self.deletions,
            diff=self.diff,
            file_path=self.get_file_path(),
            name=self.name,
            staged=self.staged,
            unstaged=self.unstaged,
            untracked=self.untracked,
        ))


@dataclass
class ProjectUser(BaseVersionControl):
    email: str = None
    name: str = None
    remote: Remote = None
    user: User = None

    @property
    def access_token(self) -> str:
        if self.user and self.provider:
            access_token = get_oauth_access_token_for_user(self.user, provider=self.provider.name)
            if access_token:
                return access_token.token

    @property
    def provider(self):
        if self.project and self.project.remote:
            return self.project.remote.provider

    def hydrate(self, access_token: str = None, project=None, user: User = None) -> None:
        self.project = project or self.project
        self.user = user or self.user

        user_from_api = get_user(
            access_token or self.access_token,
            provider=self.provider.name if self.provider else None,
        )
        if user_from_api:
            self.email = user_from_api.get(
                'email',
                self.user.email if self.user else None,
            )
            self.name = user_from_api.get('username') or self.name
        else:
            user_email = self.run(['config', 'user.email'])
            if user_email:
                self.email = ' '.join(user_email).replace('"', '').strip()

            user_name = self.run(['config', 'user.name'])
            if user_name:
                self.name = ' '.join(user_name).replace('"', '').strip()

    def to_dict(self, **kwargs) -> Dict:
        return dict(
            email=self.email,
            name=self.name,
            provider=self.provider.to_dict() if self.provider else None,
        )


@dataclass
class Project(BaseVersionControl):
    branch: Branch = None
    file: File = None
    remote: Remote = None
    sync_config: Dict = None
    user: ProjectUser = None
    uuid: str = None

    def __post_init__(self):
        self.hydrate()

    @classmethod
    def load_all(self, user: User = None) -> List['Project']:
        settings = (platform_settings() or {}).get('version_control') or {}
        uuids = list(settings.keys() if settings else [])
        return [self.load(user=user, uuid=uuid) for uuid in uuids]

    @classmethod
    def create(sefl, uuid: str) -> 'Project':
        settings = platform_settings() or {}
        if not settings.get('version_control'):
            settings['version_control'] = {}

        if uuid not in settings['version_control']:
            settings['version_control'][uuid] = {}
            update_settings(settings)

        project = Project.load(uuid=uuid)
        project.initialize()

        return project

    @property
    def access_token(self) -> str:
        token = get_access_token(self.git_config, repo_path=self.repo_path)
        if not token and self.user:
            return self.user.access_token

    @property
    def auth_type(self) -> AuthType:
        return self.git_config.auth_type

    @property
    def preferences(self) -> Preferences:
        return get_preferences(self.repo_path)

    @property
    def git_config(self) -> GitConfig:
        config = {}
        if self.preferences and self.preferences.sync_config:
            config = self.preferences.sync_config
        return GitConfig.load(config=config)

    @property
    def repo_path(self) -> str:
        return os.path.join(base_repo_path(), self.uuid)

    @property
    def repo(self):
        import git
        return git.Repo(self.repo_path)

    def set_user_config(self) -> None:
        if self.access_token and self.user.provider:
            self.user.hydrate(access_token=self.access_token)

        if self.user:
            self.configure(self.user.email, self.user.name)

    def exists(self) -> bool:
        settings = platform_settings() or {}
        if 'version_control' not in settings:
            return False

        if self.uuid not in settings['version_control']:
            return False

        return True

    def initialize(self) -> List[str]:
        if not os.path.exists(self.preferences.preferences_file_path):
            os.makedirs(os.path.dirname(self.preferences.preferences_file_path), exist_ok=True)
            self.update(dict(
                sync_config=dict(
                    repo_path=self.repo_path,
                ),
            ))

        git_path = os.path.join(self.repo_path, '.git')
        if os.path.exists(git_path):
            return [f'.git already exists in {git_path}.']
        else:
            return self.run(['init'])

    def update(self, settings: Dict = None):
        self.preferences.update_preferences(settings)

    def hydrate(self, user: User = None) -> BaseVersionControl:
        self.remote = self.remote or Remote()
        self.remote.hydrate(project=self)

        self.branch = self.branch or Branch()
        self.branch.hydrate(project=self, remote=self.remote)

        self.file = self.file or File()
        self.file.hydrate(project=self)

        if isinstance(self.user, User):
            self.user = ProjectUser.load(user=self.user)
        elif self.user is None:
            self.user = ProjectUser()
        self.user.hydrate(project=self, user=user)

        return self

    def delete(self):
        git_path = os.path.join(self.repo_path, '.git')
        if os.path.exists(git_path):
            shutil.rmtree(git_path)

        if os.path.exists(self.preferences.preferences_file_path):
            os.remove(self.preferences.preferences_file_path)

        settings = platform_settings() or {}
        if 'version_control' in settings and self.uuid in settings.get('version_control'):
            settings['version_control'].pop(self.uuid, None)
        update_settings(settings)

    def configure(self, email: str = None, name: str = None) -> List[str]:
        if email:
            return self.run(['config', '--global', '--', 'user.email', email])
        if name:
            return self.run(['config', '--global', '--', 'user.name', name])

        return ['Nothing was done.']

    def to_dict(self, **kwargs) -> Dict:
        sync_config = merge_dict(
            self.preferences.to_dict().get('sync_config') or {},
            self.sync_config or {},
        )

        return dict(
            output=self.output,
            repo_path=self.repo_path,
            sync_config=sync_config,
            user=self.user.to_dict(**kwargs) if self.user else None,
            uuid=self.uuid,
        )
