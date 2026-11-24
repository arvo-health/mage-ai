from __future__ import annotations

import asyncio
import errno
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import aiofiles

from mage_ai.data_preparation.models.constants import (
    FILE_EXTENSION_TO_BLOCK_LANGUAGE,
    BlockLanguage,
)
from mage_ai.data_preparation.models.errors import FileNotInProjectError
from mage_ai.data_preparation.models.file import (
    File,
    open_in_project,
    remove_file_in_project,
    rename_in_project,
    stat_in_project,
)
from mage_ai.shared.models import BaseDataClass
from mage_ai.shared.path_fixer import remove_base_repo_directory_name


@dataclass
class Item(BaseDataClass):
    path: str
    content: Optional[str] = None
    extension: Optional[str] = None
    language: Optional[BlockLanguage] = None
    modified_timestamp: Optional[int] = None
    name: Optional[str] = None
    relative_path: Optional[str] = None
    size: Optional[int] = None

    def __post_init__(self):
        if self.path is not None:
            self.name = os.path.basename(self.path)
            self.relative_path = remove_base_repo_directory_name(self.path)

            if os.path.exists(self.path):
                self.modified_timestamp = round(os.path.getmtime(self.path))
                self.size = os.path.getsize(self.path)

            self.extension = Path(self.path).suffix.lstrip('.')
            if self.language is None:
                self.language = (
                    FILE_EXTENSION_TO_BLOCK_LANGUAGE.get(self.extension, None)
                    if self.extension
                    else None
                )
            else:
                self.serialize_attribute_enum('language', BlockLanguage)

    async def get_content(self) -> Optional[str]:
        if self.content is None:
            fd = open_in_project(self.path, os.O_RDONLY)
            async with aiofiles.open(fd, mode='r') as file:
                self.content = await file.read()
        return self.content

    async def exists(self) -> bool:
        return await path_exists_in_project(self.path)

    async def create(self, overwrite: Optional[bool] = None) -> bool:
        return (
            True
            if await File.create_async(
                os.path.basename(self.path),
                os.path.dirname(self.path),
                content=self.content,
                overwrite=overwrite,
                project_bound=True,
            )
            else False
        )

    async def update(self) -> bool:
        return await self.create(overwrite=True)

    async def rename(self, new_path: str, overwrite: Optional[bool] = None) -> bool:
        if not overwrite and await path_exists_in_project(new_path):
            raise Exception(
                f'File already exists at {new_path}, cannot rename {self.path} to {new_path}.'
            )
        await asyncio.to_thread(rename_in_project, self.path, new_path)
        return True

    async def move(self, new_path: str, overwrite: Optional[bool] = None) -> bool:
        return await self.rename(new_path, overwrite=overwrite)

    async def delete(self, ignore_exists: Optional[bool] = None) -> bool:
        if not ignore_exists and not await self.exists():
            raise Exception(f'File does not exist at {self.path}, cannot delete non-existent file.')

        try:
            await asyncio.to_thread(remove_file_in_project, self.path)
            return True
        except FileNotInProjectError:
            raise
        except OSError:
            return False

    async def synchronize(self, item: Item) -> bool:
        new_content = item.content
        if self.content != new_content:
            self.content = new_content
            if not await self.update():
                raise Exception(f'Failed to update content for file at {self.path}')

        if os.path.dirname(self.path) != os.path.dirname(item.path):
            new_path = item.path
            if await self.move(new_path):
                self.path = new_path
            else:
                raise Exception(f'Failed to move file from {self.path} to {new_path}')
        elif item.name is not None and self.name != item.name:
            new_name = item.name
            if await self.rename(new_name):
                self.name = new_name
            else:
                raise Exception(f'Failed to rename file from {self.name} to {new_name}')

        return True


async def path_exists_in_project(path: str) -> bool:
    try:
        await asyncio.to_thread(stat_in_project, path)
        return True
    except FileNotInProjectError:
        raise
    except OSError as err:
        if err.errno in (errno.ENOENT, errno.ENOTDIR):
            return False
        raise
