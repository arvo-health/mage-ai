import asyncio
import hashlib
import json
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

# The product chooses its database and its owner settings at import time.
# Clear operator overrides before those modules load so this exercises the
# defaults a fresh process uses.
os.environ['ENV'] = 'test_mage'
for _env_name in (
    'AUTHENTICATION_MODE',
    'DEFAULT_OWNER_EMAIL',
    'DEFAULT_OWNER_PASSWORD',
    'DEFAULT_OWNER_USERNAME',
    'DISABLE_TERMINAL',
    'REQUIRE_USER_AUTHENTICATION',
):
    os.environ.pop(_env_name, None)

import tornado.testing
import tornado.web
from tornado.websocket import websocket_connect

from mage_ai.authentication.oauth2 import decode_token
from mage_ai.data_preparation.repo_manager import ProjectType, init_project_uuid
from mage_ai.data_preparation.shared.secrets import create_secret
from mage_ai.orchestration.constants import Entity
from mage_ai.orchestration.db import TEST_DB, db_connection
from mage_ai.orchestration.db.database_manager import database_manager
from mage_ai.orchestration.db.models.oauth import (
    Oauth2AccessToken,
    Oauth2Application,
    Permission,
    Role,
    RolePermission,
    User,
    UserRole,
)
from mage_ai.orchestration.db.models.secrets import Secret
from mage_ai.server.server import initialize_user_authentication, main, make_app
from mage_ai.settings import (
    AUTHENTICATION_MODE,
    DEFAULT_OWNER_EMAIL,
    DEFAULT_OWNER_PASSWORD,
    DEFAULT_OWNER_USERNAME,
    OAUTH2_APPLICATION_CLIENT_ID,
    REQUIRE_USER_AUTHENTICATION,
)
from mage_ai.settings.repo import set_repo_path

SEEDED_SECRET_NAME = 'seeded-project-secret'
SEEDED_SECRET_VALUE = 'placeholder-secret-value'
ATTACKER_SECRET_NAME = 'attacker-created-secret'
ATTACKER_SECRET_VALUE = 'placeholder-created-secret-value'
PIPELINE_NAME = 'attacker-pipeline'
WRONG_PASSWORD = 'placeholder-not-the-owner-password'
UNAUTHORIZED = 'unauthorized_access'
LOOPBACK_HOSTS = ('127.0.0.1', '::1')


def _signature(root):
    found = []
    if not root or not os.path.exists(root):
        return tuple(found)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for name in sorted(filenames):
            path = os.path.join(dirpath, name)
            try:
                with open(path, 'rb') as handle:
                    digest = hashlib.sha256(handle.read()).hexdigest()
            except OSError:
                digest = 'unreadable'
            found.append((os.path.relpath(path, root), digest))
    return tuple(found)


def _listen_address(host, project):
    """Return the address argument main() passes to Application.listen."""
    captured = {}

    def capture(port, address=None, **kwargs):
        captured['address'] = address
        raise RuntimeError('listen-captured')

    with patch('tornado.web.Application.listen', side_effect=capture):
        try:
            asyncio.run(
                main(
                    host=host,
                    port='56789',
                    project=project,
                    project_type=ProjectType.STANDALONE,
                    status_only=True,
                )
            )
        except RuntimeError as err:
            if str(err) != 'listen-captured':
                raise
        else:
            raise AssertionError('server did not reach Application.listen')
    return captured['address']


def _bound_hosts(address):
    from tornado.netutil import bind_sockets

    sockets = bind_sockets(0, address=address)
    try:
        return [sock.getsockname()[0] for sock in sockets]
    finally:
        for sock in sockets:
            sock.close()


class DefaultOwnerCredentialTests(tornado.testing.AsyncHTTPTestCase):
    """A session from the built-in owner settings must not be able to act.

    LDAP bootstrap does not store DEFAULT_OWNER_PASSWORD, so it is not part
    of this sign-in path. Kernel update accepts the same owner token and is
    not called on its own; project, secret, pipeline, and terminal are.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.workspace = tempfile.mkdtemp(prefix='mage-default-owner-')
        cls.repo_path = os.path.join(cls.workspace, 'repo')
        os.makedirs(cls.repo_path)
        os.environ['MAGE_DATA_DIR'] = cls.workspace
        set_repo_path(cls.repo_path)
        init_project_uuid()
        database_manager.run_migrations(log_level='ERROR')
        db_connection.start_session(force=True)

    @classmethod
    def tearDownClass(cls):
        db_connection.close_session()
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        shutil.rmtree(cls.workspace, ignore_errors=True)
        super().tearDownClass()

    def get_app(self):
        return make_app()

    def setUp(self):
        self._reset_auth_tables()
        super().setUp()
        self.assertTrue(REQUIRE_USER_AUTHENTICATION)
        self.assertEqual(AUTHENTICATION_MODE, 'LOCAL')
        self.assertFalse(os.getenv('DEFAULT_OWNER_PASSWORD'))
        self.assertFalse(os.getenv('DEFAULT_OWNER_EMAIL'))
        self.assertFalse(os.getenv('DEFAULT_OWNER_USERNAME'))

    def tearDown(self):
        super().tearDown()
        self._reset_auth_tables()

    def _reset_auth_tables(self):
        Oauth2AccessToken.query.delete(synchronize_session=False)
        Oauth2Application.query.delete(synchronize_session=False)
        UserRole.query.delete(synchronize_session=False)
        RolePermission.query.delete(synchronize_session=False)
        Permission.query.delete(synchronize_session=False)
        Role.query.delete(synchronize_session=False)
        Secret.query.delete(synchronize_session=False)
        User.query.delete(synchronize_session=False)
        db_connection.session.commit()

    def _bootstrap(self, project_type):
        # The five-second pause waits for tables; it does not check credentials.
        with patch('mage_ai.server.server.sleep', return_value=None):
            try:
                initialize_user_authentication(project_type)
            except Exception:
                db_connection.session.rollback()

    def _seed_secret(self):
        create_secret(SEEDED_SECRET_NAME, SEEDED_SECRET_VALUE, entity=Entity.GLOBAL)

    def _snapshot(self):
        return (
            _signature(self.repo_path),
            _signature(os.path.join(self.workspace, 'secrets')),
            Secret.query.count(),
        )

    def _sign_in(self, password, email=None, username=None):
        session = {'password': password}
        if email is not None:
            session['email'] = email
        if username is not None:
            session['username'] = username
        response = self.fetch(
            '/api/sessions?api_key=' + OAUTH2_APPLICATION_CLIENT_ID,
            method='POST',
            body=json.dumps({
                'api_key': OAUTH2_APPLICATION_CLIENT_ID,
                'session': session,
            }),
            headers={'Content-Type': 'application/json'},
        )
        return json.loads(response.body.decode())

    def _raw_token(self, body):
        session = body.get('session') if isinstance(body, dict) else None
        if not isinstance(session, dict) or not session.get('token'):
            return None
        decoded = decode_token(session['token'])
        return decoded.get('token')

    def _authorized_fetch(self, path, token, method='GET', payload=None):
        separator = '&' if '?' in path else '?'
        url = path + separator + 'api_key=' + OAUTH2_APPLICATION_CLIENT_ID
        headers = {
            'Authorization': 'Bearer ' + token,
            'Content-Type': 'application/json',
        }
        kwargs = {'method': method, 'headers': headers}
        if payload is not None:
            body = dict(payload)
            body['api_key'] = OAUTH2_APPLICATION_CLIENT_ID
            kwargs['body'] = json.dumps(body)
        response = self.fetch(url, **kwargs)
        try:
            return json.loads(response.body.decode())
        except (UnicodeDecodeError, json.JSONDecodeError):
            return {}

    def _assert_unchanged(self, before, label):
        after = self._snapshot()
        if after != before:
            self.fail(label + ' changed project files or secrets')

    def _assert_rejected(self, body, label):
        error = body.get('error') if isinstance(body, dict) else None
        if not isinstance(error, dict) or error.get('type') != UNAUTHORIZED:
            self.fail(label + ' accepted a session from the built-in owner settings')

    def _assert_terminal_rejected(self, token):
        marker = os.path.join(self.workspace, 'terminal-side-effect')
        if os.path.exists(marker):
            os.remove(marker)

        async def exchange():
            connection = await websocket_connect(
                'ws://127.0.0.1:%s/websocket/terminal' % self.get_http_port(),
            )
            messages = []
            try:
                await connection.read_message()
                command = 'touch ' + marker
                for text in (command, '\r'):
                    await connection.write_message(json.dumps({
                        'api_key': OAUTH2_APPLICATION_CLIENT_ID,
                        'token': token,
                        'command': ['stdin', text],
                    }))
                while True:
                    try:
                        message = await asyncio.wait_for(connection.read_message(), timeout=1)
                    except asyncio.TimeoutError:
                        break
                    if message is None:
                        break
                    messages.append(message)
            finally:
                connection.close()
            return messages

        messages = self.io_loop.run_sync(exchange)
        if os.path.exists(marker):
            self.fail('terminal command ran for a built-in owner session')
        combined = '\n'.join(messages)
        if 'Unauthorized access to the terminal.' not in combined:
            self.fail('terminal accepted a session from the built-in owner settings')

    def _assert_owner_session_cannot_act(self, project_type):
        self._bootstrap(project_type)
        self._seed_secret()
        attempts = (
            ('email', {'email': DEFAULT_OWNER_EMAIL}),
            ('username', {'username': DEFAULT_OWNER_USERNAME}),
        )
        for login_as, fields in attempts:
            with self.subTest(project_type=str(project_type), login=login_as):
                before = self._snapshot()
                body = self._sign_in(DEFAULT_OWNER_PASSWORD, **fields)
                token = self._raw_token(body)
                if token is None:
                    error = body.get('error') if isinstance(body, dict) else None
                    self.assertIsInstance(error, dict)
                    self.assertIn(error.get('type'), ('record_not_found', UNAUTHORIZED))
                    self._assert_unchanged(before, 'rejected sign-in')
                    continue

                owner = User.query.filter(User.username == DEFAULT_OWNER_USERNAME).one()
                self.assertEqual(body['session']['user']['id'], owner.id)
                self.assertTrue(owner.owner)
                access_token = Oauth2AccessToken.query.filter(
                    Oauth2AccessToken.token == token,
                ).one()
                self.assertEqual(access_token.user_id, owner.id)

                calls = [
                    ('GET /api/secrets', self._authorized_fetch('/api/secrets', token)),
                    (
                        'POST /api/secrets',
                        self._authorized_fetch(
                            '/api/secrets',
                            token,
                            method='POST',
                            payload={
                                'secret': {
                                    'name': ATTACKER_SECRET_NAME,
                                    'value': ATTACKER_SECRET_VALUE,
                                },
                            },
                        ),
                    ),
                    ('GET /api/projects', self._authorized_fetch('/api/projects', token)),
                    (
                        'PUT /api/projects',
                        self._authorized_fetch(
                            '/api/projects/default',
                            token,
                            method='PUT',
                            payload={'project': {'help_improve_mage': False}},
                        ),
                    ),
                    (
                        'POST /api/pipelines',
                        self._authorized_fetch(
                            '/api/pipelines',
                            token,
                            method='POST',
                            payload={'pipeline': {'name': PIPELINE_NAME}},
                        ),
                    ),
                ]
                with self.subTest(check='files'):
                    self._assert_unchanged(before, 'owner APIs')
                for label, response in calls:
                    with self.subTest(operation=label):
                        self._assert_rejected(response, label)
                        if label == 'GET /api/secrets':
                            self.assertNotIn(
                                SEEDED_SECRET_NAME,
                                json.dumps(response.get('secrets', [])),
                            )
                        if label == 'GET /api/projects':
                            self.assertNotIn(
                                'repo_path',
                                json.dumps(response.get('projects', [])),
                            )
                with self.subTest(operation='terminal'):
                    self._assert_terminal_rejected(token)

    def test_standalone_builtin_owner_cannot_call_owner_apis(self):
        self._assert_owner_session_cannot_act(ProjectType.STANDALONE)

    def test_subproject_builtin_owner_cannot_call_owner_apis(self):
        self._assert_owner_session_cannot_act(ProjectType.SUB)

    def test_main_project_builtin_owner_cannot_call_owner_apis(self):
        # ProjectType.MAIN takes the same non-SUB branch as standalone.
        self._assert_owner_session_cannot_act(ProjectType.MAIN)

    def test_placeholder_password_is_rejected(self):
        self._bootstrap(ProjectType.STANDALONE)
        body = self._sign_in(WRONG_PASSWORD, email=DEFAULT_OWNER_EMAIL)
        self.assertIsNone(self._raw_token(body))
        error = body.get('error')
        self.assertIsInstance(error, dict)
        self.assertEqual(error.get('type'), 'record_not_found')


class DefaultListenAddressTests(unittest.TestCase):
    def test_default_host_arguments_do_not_listen_on_every_interface(self):
        workspace = tempfile.mkdtemp(prefix='mage-listen-')
        project = os.path.join(workspace, 'repo')
        os.makedirs(project)
        previous_repo = os.environ.get('MAGE_REPO_PATH')
        previous_data = os.environ.get('MAGE_DATA_DIR')
        os.environ['MAGE_DATA_DIR'] = workspace
        set_repo_path(project)
        try:
            # None is server.py's argparse default. localhost is the CLI default.
            # Both are handed to Application.listen, then Tornado's bind_sockets.
            for host in (None, 'localhost'):
                with self.subTest(host=repr(host)):
                    address = _listen_address(host, project)
                    for bound in _bound_hosts(address):
                        self.assertIn(bound, LOOPBACK_HOSTS)
        finally:
            if previous_repo is None:
                os.environ.pop('MAGE_REPO_PATH', None)
            else:
                os.environ['MAGE_REPO_PATH'] = previous_repo
            if previous_data is None:
                os.environ.pop('MAGE_DATA_DIR', None)
            else:
                os.environ['MAGE_DATA_DIR'] = previous_data
            shutil.rmtree(workspace, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
