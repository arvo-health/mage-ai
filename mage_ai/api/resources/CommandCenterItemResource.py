import re
from typing import Dict

from mage_ai.api.errors import ApiError
from mage_ai.api.resources.AsyncBaseResource import AsyncBaseResource
from mage_ai.command_center.models import CommandCenterSettings
from mage_ai.command_center.service import search_items
from mage_ai.orchestration.db.models.oauth import User
from mage_ai.shared.hash import dig

KEYBOARD_SHORTCUT_KEY_PATTERN = re.compile(r'[A-Za-z0-9_]{1,32}')


class CommandCenterItemResource(AsyncBaseResource):
    @classmethod
    async def create(self, payload: Dict, user: User, **kwargs) -> 'CommandCenterItemResource':
        items = []
        settings = None

        if payload.get('settings'):
            keys = dig(payload.get('settings'), ['interface', 'keyboard_shortcuts', 'main'])
            if keys is not None and not isinstance(keys, str):
                raise ApiError(dict(
                    ApiError.RESOURCE_INVALID,
                    message='Keyboard shortcut must be a comma separated string of key codes.',
                ))

            keys = [k.strip() for k in (keys or '').split(',')]
            keys = [k for k in keys if k]
            invalid_keys = [k for k in keys if not KEYBOARD_SHORTCUT_KEY_PATTERN.fullmatch(k)]
            if invalid_keys:
                raise ApiError(dict(
                    ApiError.RESOURCE_INVALID,
                    message='Keyboard shortcut keys must be key codes or key names.',
                ))

            settings = CommandCenterSettings.load(interface=dict(
                keyboard_shortcuts=dict(
                    main=keys,
                ),
            ))
            settings.save()
        else:
            state = payload.get('state') or {}
            timeline = payload.get('timeline') or {}
            items = await search_items(user=user, **state, **timeline)
            settings = CommandCenterSettings.load_from_file_path()

        return self(dict(items=items, settings=settings), user, **kwargs)
