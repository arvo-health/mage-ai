"""Spec for the startup owner created from built-in credentials.

These tests fail while that owner can be created and can sign in. They pass
when startup refuses to persist an owner, and refuses a session, unless the
operator set a password other than the value used when the variable is unset.

The password is never written here. It is the value
``mage_ai.settings.server.DEFAULT_OWNER_PASSWORD`` resolves to when
``DEFAULT_OWNER_PASSWORD`` is unset (see that assignment).

Not covered here:
- The LDAP branch of ``initialize_user_authentication`` does not hash a local
  password, so it does not share this fallback.
- Running a block on the kernel websocket uses the same owner token as the
  terminal socket and is not invoked separately.
- The image user in the Dockerfile is not started by these tests.
"""

import asyncio
import base64
import importlib
import json
import os
import urllib.parse
from unittest.mock import patch

from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado.netutil import bind_sockets
from tornado.websocket import websocket_connect

from mage_ai.authentication.passwords import verify_password
from mage_ai.data_preparation.repo_manager import ProjectType
from mage_ai.orchestration.db import db_connection
from mage_ai.orchestration.db.models.oauth import (
    Oauth2AccessToken,
    Oauth2Application,
    Permission,
    Role,
    RolePermission,
    User,
    UserRole,
)
from mage_ai.server.server import initialize_user_authentication, make_app
from mage_ai.settings import OAUTH2_APPLICATION_CLIENT_ID
from mage_ai.tests.base_test import AsyncDBTestCase

OWNER_ENV_KEYS = (
    'AUTHENTICATION_MODE',
    'DEFAULT_OWNER_EMAIL',
    'DEFAULT_OWNER_PASSWORD',
    'DEFAULT_OWNER_USERNAME',
    'REQUIRE_USER_AUTHENTICATION',
)
OPERATOR_EMAIL = 'operator-owner@example.com'
OPERATOR_PASSWORD = 'operator-supplied-password'
OPERATOR_USERNAME = 'operator-owner'
PLANTED_MARKER = 'operator-planted-data-source-marker'
REPLACED_MARKER = 'attacker-replaced-project-file'
TERMINAL_MARKER = 'operator-terminal-marker'


def _reload_owner_settings():
    import mage_ai.api.middleware as middleware
    import mage_ai.api.policies.BasePolicy as base_policy
    import mage_ai.api.resources.SessionResource as session_resource
    import mage_ai.api.utils as api_utils
    import mage_ai.server.server as server_module
    import mage_ai.server.terminal_server as terminal_server
    import mage_ai.settings as settings_pkg
    import mage_ai.settings.server as server_settings

    importlib.reload(server_settings)
    for name in (
        'AUTHENTICATION_MODE',
        'DEFAULT_OWNER_EMAIL',
        'DEFAULT_OWNER_PASSWORD',
        'DEFAULT_OWNER_USERNAME',
        'REQUIRE_USER_AUTHENTICATION',
    ):
        value = getattr(server_settings, name)
        setattr(server_module, name, value)
        setattr(settings_pkg, name, value)
    session_resource.AUTHENTICATION_MODE = server_settings.AUTHENTICATION_MODE
    middleware.REQUIRE_USER_AUTHENTICATION = server_settings.REQUIRE_USER_AUTHENTICATION
    base_policy.REQUIRE_USER_AUTHENTICATION = server_settings.REQUIRE_USER_AUTHENTICATION
    api_utils.REQUIRE_USER_AUTHENTICATION = server_settings.REQUIRE_USER_AUTHENTICATION
    terminal_server.REQUIRE_USER_AUTHENTICATION = server_settings.REQUIRE_USER_AUTHENTICATION
    return server_settings


def _fallback_owner():
    """Owner identity the process resolves when the owner env vars are unset."""
    saved = {key: os.environ.pop(key) for key in OWNER_ENV_KEYS if key in os.environ}
    try:
        server_settings = _reload_owner_settings()
        return {
            'authentication_mode': server_settings.AUTHENTICATION_MODE,
            'email': server_settings.DEFAULT_OWNER_EMAIL,
            'password': server_settings.DEFAULT_OWNER_PASSWORD,
            'require_user_authentication': server_settings.REQUIRE_USER_AUTHENTICATION,
            'username': server_settings.DEFAULT_OWNER_USERNAME,
        }
    finally:
        for key in OWNER_ENV_KEYS:
            os.environ.pop(key, None)
        os.environ.update(saved)
        _reload_owner_settings()


def _apply_owner_env(updates):
    saved = {key: os.environ.pop(key) for key in OWNER_ENV_KEYS if key in os.environ}
    for key in OWNER_ENV_KEYS:
        os.environ.pop(key, None)
    for key, value in updates.items():
        if value is not None:
            os.environ[key] = value
    server_settings = _reload_owner_settings()
    return saved, server_settings


def _restore_owner_env(saved):
    for key in OWNER_ENV_KEYS:
        os.environ.pop(key, None)
    os.environ.update(saved)
    _reload_owner_settings()


def _raw_token(session_body):
    """Match the frontend, which base64-decodes the session JWT payload."""
    encoded = (session_body.get('session') or {}).get('token')
    if not isinstance(encoded, str) or encoded.count('.') < 2:
        return None
    payload_b64 = encoded.split('.')[1]
    padding = '=' * (-len(payload_b64) % 4)
    try:
        payload = json.loads(base64.urlsafe_b64decode(payload_b64 + padding))
    except (ValueError, json.JSONDecodeError):
        return None
    raw = payload.get('token')
    if not isinstance(raw, str) or not raw:
        return None
    return raw


def _default_listen_is_wildcard():
    """Run Tornado's binder with the address ``main`` passes for the CLI default host."""
    for host in ('localhost', None):
        address = host if host != 'localhost' else None
        sockets = bind_sockets(0, address=address)
        try:
            if not any(sock.getsockname()[0] in ('0.0.0.0', '::') for sock in sockets):
                return False
        finally:
            for sock in sockets:
                sock.close()
    return True


class DefaultOwnerBuiltinPasswordTests(AsyncDBTestCase):
    def setUp(self):
        super().setUp()
        self._servers = []
        self._clear_auth_rows()

    def tearDown(self):
        for server in self._servers:
            server.stop()
        self._clear_auth_rows()
        super().tearDown()

    def _clear_auth_rows(self):
        Oauth2AccessToken.query.delete()
        Oauth2Application.query.delete()
        UserRole.query.delete()
        RolePermission.query.delete()
        Permission.query.delete()
        Role.query.delete()
        User.query.delete()
        db_connection.session.commit()

    def _password_matches_any_user(self, password):
        if not isinstance(password, str) or password == '':
            return False
        for user in User.query.all():
            if not user.password_hash:
                continue
            try:
                if verify_password(password, user.password_hash):
                    return True
            except Exception:
                continue
        return False

    async def _start_app(self):
        app = make_app()
        server = app.listen(0, address='127.0.0.1')
        self._servers.append(server)
        port = next(iter(server._sockets.values())).getsockname()[1]
        return port

    async def _fetch(self, port, method, path, body=None, token=None):
        headers = {}
        if body is not None:
            headers['Content-Type'] = 'application/json'
        if token:
            headers['Authorization'] = f'Bearer {token}'
        request = HTTPRequest(
            url=f'http://127.0.0.1:{port}{path}',
            method=method,
            headers=headers,
            body=body,
            request_timeout=30,
        )
        client = AsyncHTTPClient()
        response = await client.fetch(request, raise_error=False)
        try:
            parsed = json.loads(response.body.decode())
        except (UnicodeDecodeError, json.JSONDecodeError):
            parsed = {}
        return response.code, parsed

    async def _session_token(self, port, password, email=None, username=None):
        session = {'password': password}
        if email is not None:
            session['email'] = email
        if username is not None:
            session['username'] = username
        _, body = await self._fetch(
            port,
            'POST',
            '/api/sessions',
            body=json.dumps({
                'api_key': OAUTH2_APPLICATION_CLIENT_ID,
                'session': session,
            }),
        )
        return _raw_token(body)

    async def _exercise_owner_session(self, port, password, email, username, credentials_path, marker_path):
        token = await self._session_token(port, password, email=email)
        if token is None:
            token = await self._session_token(port, password, username=username)
        outcome = {
            'session_issued': token is not None,
            'project_file_read': False,
            'project_file_changed': False,
            'terminal_marker_written': False,
        }
        if token is None:
            return outcome

        quoted = urllib.parse.quote(credentials_path, safe='')
        api_key = urllib.parse.quote(OAUTH2_APPLICATION_CLIENT_ID, safe='')
        _, read_body = await self._fetch(
            port,
            'GET',
            f'/api/file_contents/{quoted}?api_key={api_key}',
            token=token,
        )
        content = ((read_body.get('file_content') or {}).get('content')) or ''
        outcome['project_file_read'] = PLANTED_MARKER in content

        await self._fetch(
            port,
            'PUT',
            f'/api/file_contents/{quoted}?api_key={api_key}',
            body=json.dumps({
                'api_key': OAUTH2_APPLICATION_CLIENT_ID,
                'file_content': {'content': REPLACED_MARKER + '\n'},
            }),
            token=token,
        )
        with open(credentials_path, 'r', encoding='utf-8') as handle:
            outcome['project_file_changed'] = REPLACED_MARKER in handle.read()

        connection = await websocket_connect(f'ws://127.0.0.1:{port}/websocket/terminal')
        try:
            await connection.write_message(json.dumps({
                'api_key': OAUTH2_APPLICATION_CLIENT_ID,
                'command': ['stdin', f"printf '%s\\n' {TERMINAL_MARKER} > '{marker_path}'\r"],
                'token': token,
            }))
            for _ in range(20):
                if os.path.exists(marker_path):
                    break
                await asyncio.sleep(0.1)
        finally:
            connection.close()
        if os.path.exists(marker_path):
            with open(marker_path, 'r', encoding='utf-8') as handle:
                outcome['terminal_marker_written'] = TERMINAL_MARKER in handle.read()
        return outcome

    async def _boot_and_attack(self, project_type, updates):
        credentials_path = os.path.join(self.repo_path, 'data_source_credentials.yaml')
        marker_path = os.path.join(self.repo_path, 'terminal_marker.txt')
        for path in (credentials_path, marker_path):
            if os.path.exists(path):
                os.remove(path)
        with open(credentials_path, 'w', encoding='utf-8') as handle:
            handle.write(f'connection: {PLANTED_MARKER}\n')

        saved, _server_settings = _apply_owner_env(updates)
        boot_error = None
        try:
            with patch('mage_ai.server.server.sleep', return_value=None):
                try:
                    initialize_user_authentication(project_type)
                except Exception as exc:
                    boot_error = type(exc).__name__
                    db_connection.session.rollback()
            import mage_ai.server.server as server_module
            password = server_module.DEFAULT_OWNER_PASSWORD
            email = server_module.DEFAULT_OWNER_EMAIL
            username = server_module.DEFAULT_OWNER_USERNAME
            port = await self._start_app()
            outcome = await self._exercise_owner_session(
                port,
                password,
                email,
                username,
                credentials_path,
                marker_path,
            )
        finally:
            _restore_owner_env(saved)

        outcome['boot_error'] = boot_error
        outcome['owner_with_builtin_password'] = self._password_matches_any_user(password)
        outcome['owner_row_created'] = User.query.count() > 0
        outcome['listens_on_all_interfaces'] = _default_listen_is_wildcard()
        return outcome

    def _assert_rejected(self, outcome):
        self.assertEqual(
            {
                'owner_row_created': False,
                'owner_with_builtin_password': False,
                'project_file_changed': False,
                'project_file_read': False,
                'session_issued': False,
                'terminal_marker_written': False,
            },
            {
                'owner_row_created': outcome['owner_row_created'],
                'owner_with_builtin_password': outcome['owner_with_builtin_password'],
                'project_file_changed': outcome['project_file_changed'],
                'project_file_read': outcome['project_file_read'],
                'session_issued': outcome['session_issued'],
                'terminal_marker_written': outcome['terminal_marker_written'],
            },
            outcome,
        )

    async def test_default_authentication_uses_local_owner_fallback(self):
        fallback = _fallback_owner()
        self.assertEqual('local', str(fallback['authentication_mode']).lower())
        self.assertTrue(fallback['require_user_authentication'])

    async def test_unset_owner_password_does_not_grant_standalone_owner(self):
        outcome = await self._boot_and_attack(ProjectType.STANDALONE, {})
        self._assert_rejected(outcome)

    async def test_owner_password_set_to_builtin_fallback_does_not_grant_owner(self):
        fallback = _fallback_owner()
        outcome = await self._boot_and_attack(
            ProjectType.STANDALONE,
            {
                'DEFAULT_OWNER_EMAIL': fallback['email'],
                'DEFAULT_OWNER_PASSWORD': fallback['password'],
                'DEFAULT_OWNER_USERNAME': fallback['username'],
            },
        )
        self._assert_rejected(outcome)

    async def test_unset_owner_password_does_not_grant_subproject_owner(self):
        outcome = await self._boot_and_attack(ProjectType.SUB, {})
        self._assert_rejected(outcome)

    async def test_operator_supplied_password_can_sign_in_and_edit(self):
        outcome = await self._boot_and_attack(
            ProjectType.STANDALONE,
            {
                'DEFAULT_OWNER_EMAIL': OPERATOR_EMAIL,
                'DEFAULT_OWNER_PASSWORD': OPERATOR_PASSWORD,
                'DEFAULT_OWNER_USERNAME': OPERATOR_USERNAME,
            },
        )
        self.assertFalse(outcome['boot_error'])
        self.assertTrue(outcome['owner_row_created'])
        self.assertTrue(outcome['owner_with_builtin_password'])
        self.assertTrue(outcome['session_issued'])
        self.assertTrue(outcome['project_file_read'])
        self.assertTrue(outcome['project_file_changed'])
        self.assertTrue(outcome['terminal_marker_written'])
