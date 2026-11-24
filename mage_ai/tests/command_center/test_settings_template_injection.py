import json
import logging
import os
import tempfile
import unittest
import uuid
from types import SimpleNamespace

from mage_ai.api.views import execute_operation
from mage_ai.cache.file import FileCache
from mage_ai.command_center.constants import SETTINGS_FILENAME
from mage_ai.data_preparation.repo_manager import init_project_uuid
from mage_ai.orchestration.db import TEST_DB, db_connection
from mage_ai.orchestration.db.database_manager import database_manager
from mage_ai.orchestration.db.models.oauth import User
from mage_ai.settings.repo import get_variables_dir, set_repo_path


def _command_expression(marker_path):
    # No commas: CommandCenterItemResource splits this string on commas before saving.
    # Double quotes survive yaml.dump's single-quoted scalar, so the expression still parses.
    return '{{ lipsum.__globals__.os.system("touch %s") }}' % marker_path


class _Request(SimpleNamespace):
    def __init__(self, body, user):
        super().__init__(
            body=body,
            body_arguments={},
            current_user=user,
            error=None,
            files={},
            headers={},
            method='POST',
            oauth_client=None,
            oauth_token=None,
            query_arguments={},
        )


class _Handler:
    def __init__(self, body, user):
        self.request = _Request(body, user)
        self.written = None
        self.status = None

    def write(self, payload):
        self.written = payload

    def set_status(self, status):
        self.status = status


class CommandCenterSettingsTemplateInjectionTest(unittest.IsolatedAsyncioTestCase):
    """Settings saved through the Command Center item API must not be executed.

    These tests fail while keyboard-shortcut values are written into the project
    settings file and that file is later rendered with an unsandboxed Jinja template.
    """

    @classmethod
    def setUpClass(cls):
        cls._tmpdir = tempfile.TemporaryDirectory()
        cls.repo_path = os.path.join(cls._tmpdir.name, 'repo')
        os.makedirs(cls.repo_path)
        os.environ['MAGE_DATA_DIR'] = os.path.join(cls._tmpdir.name, 'data')
        set_repo_path(cls.repo_path)
        init_project_uuid(root_project=True)
        database_manager.run_migrations(log_level=logging.ERROR)
        db_connection.start_session(force=True)

    @classmethod
    def tearDownClass(cls):
        db_connection.close_session()
        cls._tmpdir.cleanup()
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        super().tearDownClass()

    def setUp(self):
        self.marker = os.path.join(self._tmpdir.name, 'marker-%s' % uuid.uuid4().hex)
        settings_path = self._settings_path()
        if os.path.exists(settings_path):
            os.remove(settings_path)
        if os.path.exists(self.marker):
            os.remove(self.marker)

    def tearDown(self):
        if os.path.exists(self.marker):
            os.remove(self.marker)

    def _settings_path(self):
        return os.path.join(get_variables_dir(root_project=True), SETTINGS_FILENAME)

    def _user(self, roles):
        suffix = uuid.uuid4().hex
        user = User(
            email='user-%s@example.com' % suffix,
            username='user-%s' % suffix,
            roles=roles,
            _owner=False,
        )
        user.save()
        return user

    async def _post(self, user, command_center_item):
        body = json.dumps({'command_center_item': command_center_item}).encode()
        handler = _Handler(body, user)
        await execute_operation(handler, 'command_center_items')
        written = handler.written
        if isinstance(written, (bytes, bytearray)):
            written = written.decode()
        parsed = json.loads(written) if isinstance(written, str) else written
        return handler, parsed

    def _assert_command_did_not_run(self):
        self.assertFalse(
            os.path.exists(self.marker),
            'A keyboard shortcut stored through the Command Center API was rendered '
            'as a template and ran a command',
        )

    async def _save_expression(self, user):
        expression = _command_expression(self.marker)
        self.assertNotIn(',', expression)
        try:
            await self._post(
                user,
                {
                    'settings': {
                        'interface': {
                            'keyboard_shortcuts': {
                                'main': expression,
                            },
                        },
                    },
                },
            )
        except Exception:
            # A fix may reject the value. The command still must not have run,
            # including when the settings file was written before the rejection.
            pass
        self._assert_command_did_not_run()

    async def _reload(self, user, command_center_item):
        parsed = None
        try:
            _handler, parsed = await self._post(user, command_center_item)
        except Exception:
            parsed = None
        self._assert_command_did_not_run()
        return parsed

    def _shortcut(self, parsed):
        if not isinstance(parsed, dict) or parsed.get('error'):
            return None
        return (
            ((parsed.get('command_center_item') or {}).get('settings') or {})
            .get('interface', {})
            .get('keyboard_shortcuts', {})
            .get('main')
        )

    async def test_viewer_shortcut_is_not_executed_when_command_center_reloads(self):
        user = self._user(roles=4)
        await self._save_expression(user)

        parsed = await self._reload(user, {})
        # os.system's return code is what the template writes back into the shortcut.
        self.assertNotEqual(['0'], self._shortcut(parsed))

    async def test_user_without_a_role_cannot_execute_shortcut_template(self):
        user = self._user(roles=0)
        await self._save_expression(user)
        await self._reload(user, {})

    async def test_file_cache_initialization_does_not_execute_saved_shortcut(self):
        user = self._user(roles=4)
        await self._save_expression(user)

        try:
            FileCache.initialize_cache_with_settings(replace=True)
        except Exception:
            pass
        self._assert_command_did_not_run()

    async def test_opening_command_center_with_a_search_does_not_execute_shortcut(self):
        user = self._user(roles=4)
        await self._save_expression(user)
        await self._reload(user, {'state': {'search': 'pipeline'}})

    async def test_plain_keyboard_shortcut_round_trips(self):
        user = self._user(roles=4)
        _handler, _parsed = await self._post(
            user,
            {
                'settings': {
                    'interface': {
                        'keyboard_shortcuts': {
                            'main': 'metaKey, 13',
                        },
                    },
                },
            },
        )
        _handler, parsed = await self._post(user, {})
        shortcut = (
            ((parsed.get('command_center_item') or {}).get('settings') or {})
            .get('interface', {})
            .get('keyboard_shortcuts', {})
            .get('main')
        )
        self.assertEqual(['metaKey', '13'], shortcut)


if __name__ == '__main__':
    unittest.main()
