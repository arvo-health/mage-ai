"""Security tests for the terminal websocket shared-name read path.

These tests describe the behavior required to close the unauthenticated
terminal attach. They fail while a client can join a named pty during
``TerminalWebsocketServer.open`` before the session is authenticated and
bound to that user.
"""
import json
import os
import shutil
import uuid
from datetime import timedelta
from urllib.parse import urlencode

import tornado.gen
import tornado.httpclient
import tornado.testing
import tornado.web
import tornado.websocket
from tornado.ioloop import IOLoop

# Select the unittest sqlite database before mage's db module is imported.
os.environ['ENV'] = 'test_mage'

from mage_ai.authentication.oauth2 import encode_token, generate_access_token
from mage_ai.data_preparation.repo_manager import init_project_uuid
from mage_ai.orchestration.db import db_connection, engine
from mage_ai.orchestration.db.models.base import Base
from mage_ai.orchestration.db.models.oauth import (
    Oauth2AccessToken,
    Oauth2Application,
    User,
)
from mage_ai.server.api.constants import COOKIE_OAUTH_TOKEN
from mage_ai.server.terminal_server import (
    DISABLE_TERMINAL,
    MageTermManager,
    MageUniqueTermManager,
    REQUIRE_USER_AUTHENTICATION,
    TerminalWebsocketServer,
)
from mage_ai.settings.repo import set_repo_path
from mage_ai.settings.server import OAUTH2_APPLICATION_CLIENT_ID


def _create_user(**kwargs):
    user = User(
        email=f'{uuid.uuid4().hex}@example.com',
        username=uuid.uuid4().hex,
        **kwargs,
    )
    user.save()
    return user

# Names the product actually uses. GitActions computes ``git_<user id>`` (or
# ``git`` when no id is present) but the websocket call does not send it, so
# that page and the pipeline editor both hit the server default. The command
# center terminal does send ``<user id>--PortalTerminal--Main Mage``.
DEFAULT_TERMINAL_NAME = 'tty'
GIT_TERMINAL_NAME_WITHOUT_USER = 'git'
PORTAL_TERMINAL_CONTROLLER = 'PortalTerminal'
PORTAL_TERMINAL_TAB = 'Main Mage'
TERMINAL_ROUTE = '/websocket/terminal'


def git_terminal_name(user_id):
    return f'git_{user_id}' if user_id else GIT_TERMINAL_NAME_WITHOUT_USER


def portal_terminal_name(user_id):
    return f'{user_id}--{PORTAL_TERMINAL_CONTROLLER}--{PORTAL_TERMINAL_TAB}'


def terminal_path(term_name=None):
    if term_name is None:
        return TERMINAL_ROUTE
    return f'{TERMINAL_ROUTE}?{urlencode({"term_name": term_name})}'


def command_message(raw_token, text, claimed_term_name=None):
    """Same JSON shape the terminal UI sends, plus an optional claimed name.

    A fix that authenticates the message and then opens whichever name it
    reads next — the query string, or this field — still fails the tests.
    """
    body = {
        'api_key': OAUTH2_APPLICATION_CLIENT_ID,
        'token': raw_token,
        'command': ['stdin', text],
    }
    if claimed_term_name is not None:
        body['term_name'] = claimed_term_name
    return json.dumps(body)


class TerminalWebsocketTestCase(tornado.testing.AsyncHTTPTestCase):
    manager_cls = MageTermManager

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.repo_path = os.path.join(os.getcwd(), 'test')
        os.makedirs(cls.repo_path, exist_ok=True)
        set_repo_path(cls.repo_path)
        init_project_uuid()
        # The oauth tables are the only ones this test writes. Creating them
        # from the mapped models avoids importing the scheduler migration
        # graph.
        Base.metadata.create_all(bind=engine)
        db_connection.start_session(force=True)

    @classmethod
    def tearDownClass(cls):
        db_connection.close_session()
        if os.path.isdir(cls.repo_path):
            shutil.rmtree(cls.repo_path, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self._sockets = []
        self.assertTrue(REQUIRE_USER_AUTHENTICATION)
        self.assertFalse(DISABLE_TERMINAL)
        self.oauth_client = Oauth2Application.create(
            client_id=OAUTH2_APPLICATION_CLIENT_ID,
            client_type=Oauth2Application.ClientType.PRIVATE,
            name='terminal-test',
        )
        self.owner = _create_user(_owner=True, roles=2)
        self.other_editor = _create_user(_owner=True, roles=2)
        self.viewer = _create_user(_owner=False, roles=4)
        self.owner_token = generate_access_token(self.owner, application=self.oauth_client)
        self.other_token = generate_access_token(
            self.other_editor,
            application=self.oauth_client,
        )
        self.viewer_token = generate_access_token(self.viewer, application=self.oauth_client)

    def tearDown(self):
        async def _shutdown():
            for ws in list(self._sockets):
                try:
                    ws.close()
                except Exception:
                    pass
            if getattr(self, 'term_manager', None) is not None:
                await self.term_manager.shutdown()

        try:
            self.io_loop.run_sync(_shutdown)
        except Exception:
            pass
        Oauth2AccessToken.query.delete()
        Oauth2Application.query.delete()
        User.query.delete()
        db_connection.session.commit()
        super().tearDown()

    def get_app(self):
        # Same manager selection and route as mage_ai.server.server.make_app.
        self.term_manager = self.manager_cls(shell_command=['bash'])
        return tornado.web.Application([
            (
                TERMINAL_ROUTE,
                TerminalWebsocketServer,
                {'term_manager': self.term_manager},
            ),
        ])

    def _cookie_for(self, access_token):
        encoded = encode_token(access_token.token, access_token.expires)
        return f'{COOKIE_OAUTH_TOKEN}={encoded}'

    async def _connect(self, path, access_token=None):
        port = self.get_http_port()
        url = f'ws://127.0.0.1:{port}{path}'
        headers = {
            'Origin': f'http://127.0.0.1:{port}',
        }
        if access_token is not None:
            headers['Cookie'] = self._cookie_for(access_token)
        request = tornado.httpclient.HTTPRequest(url, headers=headers)
        try:
            ws = await tornado.websocket.websocket_connect(request)
        except Exception:
            return None
        self._sockets.append(ws)
        return ws

    async def _read_stdout(self, ws, timeout):
        if ws is None:
            return ''
        text = ''
        deadline = IOLoop.current().time() + timeout
        while IOLoop.current().time() < deadline:
            remaining = deadline - IOLoop.current().time()
            try:
                message = await tornado.gen.with_timeout(
                    timedelta(seconds=remaining),
                    ws.read_message(),
                )
            except tornado.gen.TimeoutError:
                break
            if message is None:
                break
            try:
                payload = json.loads(message)
            except json.JSONDecodeError:
                text += message
                continue
            if isinstance(payload, list) and payload and payload[0] == 'stdout':
                text += payload[1]
            else:
                text += message
        return text

    async def _send_command(self, ws, access_token, text, claimed_term_name=None):
        await ws.write_message(command_message(
            access_token.token,
            text,
            claimed_term_name=claimed_term_name,
        ))
        await ws.write_message(command_message(
            access_token.token,
            '\r',
            claimed_term_name=claimed_term_name,
        ))

    def _terminal(self, term_name):
        return getattr(self.term_manager, 'terminals', {}).get(term_name)

    def _client_count(self, term_name):
        terminal = self._terminal(term_name)
        if terminal is None:
            return 0
        return len(terminal.clients)

    async def _owner_session(self, path, term_name):
        marker = f'MAGE_OWNER_MARKER_{uuid.uuid4().hex}'
        ws = await self._connect(path, access_token=self.owner_token)
        self.assertIsNotNone(ws)
        # open() runs after the 101 response, so wait until the shell is joined.
        await self._read_stdout(ws, 2)
        self.assertIsNotNone(
            self._terminal(term_name),
            f'owner session was not stored under {term_name}',
        )
        clients_before = self._client_count(term_name)
        await self._send_command(
            ws,
            self.owner_token,
            f"printf '%s\\n' {marker}",
            claimed_term_name=term_name,
        )
        output = await self._read_stdout(ws, 8)
        self.assertIn(marker, output)
        return ws, marker, clients_before

    async def _assert_reader_cannot_observe(
        self,
        path,
        term_name,
        reader_token,
        claimed_term_name,
    ):
        _owner_ws, marker, clients_before = await self._owner_session(path, term_name)
        reader = await self._connect(path, access_token=reader_token)
        reader_output = await self._read_stdout(reader, 2)
        follow_up = f'MAGE_FOLLOWUP_MARKER_{uuid.uuid4().hex}'
        await self._send_command(
            _owner_ws,
            self.owner_token,
            f"printf '%s\\n' {follow_up}",
            claimed_term_name=term_name,
        )
        reader_output += await self._read_stdout(reader, 2)
        problems = []
        if marker in reader_output or follow_up in reader_output:
            problems.append('received pty output from the owner session')
        if self._client_count(term_name) != clients_before:
            problems.append('was attached to the owner terminal')

        if reader is not None and reader_token is not None:
            intruder = f'MAGE_INTRUDER_MARKER_{uuid.uuid4().hex}'
            sent = True
            try:
                await self._send_command(
                    reader,
                    reader_token,
                    f"printf '%s\\n' {intruder}",
                    claimed_term_name=claimed_term_name,
                )
            except tornado.websocket.WebSocketClosedError:
                sent = False
            if sent:
                owner_after = await self._read_stdout(_owner_ws, 2)
                # A second lookup of the client-supplied name, from the query
                # string or from the command message, must not select the
                # owner's pty.
                if intruder in owner_after:
                    problems.append('wrote a command into the owner pty')
        if problems:
            self.fail(f'reader of {term_name!r} ' + '; '.join(problems))


class SharedTerminalNameTests(TerminalWebsocketTestCase):
    """Default make_app manager: one pty per client-supplied name."""

    @tornado.testing.gen_test(timeout=60)
    async def test_unauthenticated_open_does_not_create_a_terminal(self):
        names = [
            None,  # query omitted; server would otherwise use tty
            DEFAULT_TERMINAL_NAME,
            git_terminal_name(1),
            git_terminal_name(self.owner.id),
            GIT_TERMINAL_NAME_WITHOUT_USER,
            portal_terminal_name(self.owner.id),
            portal_terminal_name(1),
        ]
        for name in names:
            before = len(self.term_manager.ptys_by_fd)
            ws = await self._connect(terminal_path(name))
            await self._read_stdout(ws, 1)
            self.assertEqual(
                len(self.term_manager.ptys_by_fd),
                before,
                f'unauthenticated open created a pty for {name!r}',
            )
            if name is None:
                self.assertIsNone(self._terminal(DEFAULT_TERMINAL_NAME))
            else:
                self.assertIsNone(self._terminal(name))
            if ws is not None:
                ws.close()

    @tornado.testing.gen_test(timeout=60)
    async def test_unauthenticated_client_cannot_read_git_user_terminal(self):
        name = git_terminal_name(self.owner.id)
        await self._assert_reader_cannot_observe(
            terminal_path(name),
            name,
            reader_token=None,
            claimed_term_name=name,
        )

    @tornado.testing.gen_test(timeout=60)
    async def test_unauthenticated_client_cannot_read_git_fallback_terminal(self):
        await self._assert_reader_cannot_observe(
            terminal_path(GIT_TERMINAL_NAME_WITHOUT_USER),
            GIT_TERMINAL_NAME_WITHOUT_USER,
            reader_token=None,
            claimed_term_name=GIT_TERMINAL_NAME_WITHOUT_USER,
        )

    @tornado.testing.gen_test(timeout=60)
    async def test_unauthenticated_client_cannot_read_portal_terminal(self):
        name = portal_terminal_name(self.owner.id)
        await self._assert_reader_cannot_observe(
            terminal_path(name),
            name,
            reader_token=None,
            claimed_term_name=name,
        )

    @tornado.testing.gen_test(timeout=60)
    async def test_unauthenticated_client_cannot_read_default_terminal(self):
        # Owner joins the way GitActions and the pipeline editor do: no
        # term_name query. An attacker who omits the query, or who passes the
        # default name, must not observe that shell.
        await self._assert_reader_cannot_observe(
            terminal_path(None),
            DEFAULT_TERMINAL_NAME,
            reader_token=None,
            claimed_term_name=DEFAULT_TERMINAL_NAME,
        )

    @tornado.testing.gen_test(timeout=60)
    async def test_other_editor_cannot_attach_to_owner_terminal_by_name(self):
        # The other editor is authenticated, and both the query string and the
        # command message name the owner's git shell. Authorization for the
        # editor must not be reused for that shell.
        name = git_terminal_name(self.owner.id)
        await self._assert_reader_cannot_observe(
            terminal_path(name),
            name,
            reader_token=self.other_token,
            claimed_term_name=name,
        )

    @tornado.testing.gen_test(timeout=60)
    async def test_other_editor_cannot_attach_to_default_terminal(self):
        await self._assert_reader_cannot_observe(
            terminal_path(None),
            DEFAULT_TERMINAL_NAME,
            reader_token=self.other_token,
            claimed_term_name=git_terminal_name(self.owner.id),
        )

    @tornado.testing.gen_test(timeout=60)
    async def test_other_editor_cannot_attach_to_portal_terminal(self):
        name = portal_terminal_name(self.owner.id)
        await self._assert_reader_cannot_observe(
            terminal_path(name),
            name,
            reader_token=self.other_token,
            claimed_term_name=name,
        )

    @tornado.testing.gen_test(timeout=60)
    async def test_viewer_cannot_read_owner_terminal(self):
        name = git_terminal_name(self.owner.id)
        await self._assert_reader_cannot_observe(
            terminal_path(name),
            name,
            reader_token=self.viewer_token,
            claimed_term_name=name,
        )


class UniqueTerminalSpawnTests(TerminalWebsocketTestCase):
    """USE_UNIQUE_TERMINAL selects MageUniqueTermManager in make_app.

    Each socket gets its own pty, so names are not shared, but open() still
    spawns a shell before any authentication.
    """

    manager_cls = MageUniqueTermManager

    @tornado.testing.gen_test(timeout=30)
    async def test_unauthenticated_open_does_not_spawn_a_shell(self):
        before = len(self.term_manager.ptys_by_fd)
        peak = before
        for path in (
            terminal_path(None),
            terminal_path(git_terminal_name(self.owner.id)),
            terminal_path(portal_terminal_name(self.owner.id)),
        ):
            ws = await self._connect(path)
            await self._read_stdout(ws, 1)
            # Count while the socket is still open. UniqueTermManager reaps
            # the pty on disconnect, which would hide a shell that already spawned.
            peak = max(peak, len(self.term_manager.ptys_by_fd))
            if ws is not None:
                ws.close()
        self.assertEqual(peak, before)
