import json
import os
import shutil
import tempfile
from datetime import datetime, timedelta
from unittest.mock import patch
from urllib.parse import urlencode, urlparse

import tornado.web
from tornado.httpclient import HTTPClientError, HTTPRequest
from tornado.testing import AsyncHTTPTestCase, gen_test
from tornado.websocket import websocket_connect

from mage_ai.api.utils import has_at_least_editor_role, has_at_least_viewer_role
from mage_ai.data_preparation.models.pipeline import Pipeline
from mage_ai.data_preparation.repo_manager import init_project_uuid
from mage_ai.orchestration.constants import Entity
from mage_ai.orchestration.db import TEST_DB, db_connection
from mage_ai.orchestration.db.database_manager import database_manager
from mage_ai.orchestration.db.models.oauth import (
    Oauth2AccessToken,
    Oauth2Application,
    Permission,
    Role,
    RolePermission,
    UserRole,
)
from mage_ai.server.kernel_output_parser import parse_output_message
from mage_ai.server.server import make_app
from mage_ai.server.subscriber import get_messages
from mage_ai.server.websocket_server import WebSocketServer, publish_pipeline_message
from mage_ai.settings.repo import set_repo_path
from mage_ai.tests.factory import create_user

# Obvious placeholders. These are not credentials for any deployment.
OAUTH_CLIENT_ID = 'placeholder-oauth-client'
TOKEN_VIEWER = 'placeholder-token-viewer'
TOKEN_OTHER = 'placeholder-token-other'
TOKEN_STRANGER = 'placeholder-token-stranger'
TOKEN_EDITOR = 'placeholder-token-editor'

STDOUT_MARKER = 'notebook-stdout-marker'
FRAME_MARKER = 'notebook-frame-marker'
TRACEBACK_MARKER = 'notebook-traceback-marker'
PIPELINE_MARKER = 'notebook-pipeline-marker'
RELAY_MARKER = 'notebook-relay-marker'
OTHER_PIPELINE_MARKER = 'notebook-other-pipeline-marker'


def _texts(messages):
    parts = []
    for message in messages:
        if isinstance(message, bytes):
            message = message.decode()
        parts.append(message)
    return '\n'.join(parts)


class NotebookWebsocketAuthorizationTest(AsyncHTTPTestCase):
    """
    Notebook output on /websocket/ is delivered only to a socket that
    authenticated during the handshake and whose user can view that pipeline.

    Credentials use the same names the notebook already sends, api_key and
    token, as query parameters on the handshake. api_key is the OAuth client
    id. A socket may receive a message only when has_at_least_viewer_role is
    true for that user, Entity.PIPELINE, and the pipeline_uuid on that
    message (execution_metadata or the kernel execution record). Authorizing
    one pipeline must not deliver a message for another pipeline. A handshake
    whose Origin host is not this server's Host is rejected.

    These assertions fail while every connected socket receives the broadcast.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.repo_path = tempfile.mkdtemp(prefix='mage-ws-auth-')
        set_repo_path(cls.repo_path)
        init_project_uuid()
        database_manager.run_migrations()
        db_connection.start_session(force=True)

        cls.allowed = Pipeline.create('pipeline_allowed', repo_path=cls.repo_path)
        cls.other = Pipeline.create('pipeline_other', repo_path=cls.repo_path)

        cls.oauth_client = Oauth2Application.create(
            client_id=OAUTH_CLIENT_ID,
            client_type=Oauth2Application.ClientType.PUBLIC,
            name='placeholder-frontend',
        )
        cls.viewer = cls._user_with_access(
            'viewer',
            TOKEN_VIEWER,
            Permission.Access.VIEWER,
            cls.allowed.uuid,
        )
        cls.editor = cls._user_with_access(
            'editor',
            TOKEN_EDITOR,
            Permission.Access.EDITOR,
            cls.allowed.uuid,
        )
        cls.other_editor = cls._user_with_access(
            'other',
            TOKEN_OTHER,
            Permission.Access.EDITOR,
            cls.other.uuid,
        )
        cls.stranger = create_user(username='stranger-user', email='stranger@example.com')
        Oauth2AccessToken.create(
            expires=datetime.utcnow() + timedelta(days=1),
            oauth2_application_id=cls.oauth_client.id,
            token=TOKEN_STRANGER,
            user_id=cls.stranger.id,
        )

        from jupyter_client import KernelManager

        cls.kernel = KernelManager()
        cls.kernel.start_kernel()
        cls.kernel_client = cls.kernel.client()
        cls.kernel_client.start_channels()
        cls.kernel_client.wait_for_ready(timeout=60)

    @classmethod
    def tearDownClass(cls):
        try:
            cls.kernel_client.stop_channels()
            cls.kernel.shutdown_kernel(now=True)
        except Exception:
            pass
        Oauth2AccessToken.query.delete()
        Oauth2Application.query.delete()
        RolePermission.query.delete()
        UserRole.query.delete()
        Permission.query.delete()
        Role.query.delete()
        db_connection.session.commit()
        if os.path.exists(cls.repo_path):
            shutil.rmtree(cls.repo_path)
        db_connection.close_session()
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        super().tearDownClass()

    @classmethod
    def _user_with_access(cls, name, token, access, pipeline_uuid):
        user = create_user(
            username='{}-user'.format(name),
            email='{}@example.com'.format(name),
        )
        permission = Permission.create(
            access=access,
            entity=Entity.PIPELINE,
            entity_id=pipeline_uuid,
        )
        role = Role.create(name='{}-role'.format(name))
        RolePermission.create(permission_id=permission.id, role_id=role.id)
        UserRole.create(user_id=user.id, role_id=role.id)
        Oauth2AccessToken.create(
            expires=datetime.utcnow() + timedelta(days=1),
            oauth2_application_id=cls.oauth_client.id,
            token=token,
            user_id=user.id,
        )
        db_connection.session.commit()
        db_connection.session.refresh(user)
        return user

    def setUp(self):
        WebSocketServer.clients.clear()
        WebSocketServer.running_executions_mapping.clear()
        self.connections = []
        super().setUp()
        self.assertTrue(
            has_at_least_viewer_role(self.viewer, Entity.PIPELINE, self.allowed.uuid)
        )
        self.assertTrue(
            has_at_least_editor_role(self.editor, Entity.PIPELINE, self.allowed.uuid)
        )
        self.assertFalse(
            has_at_least_viewer_role(self.viewer, Entity.PIPELINE, self.other.uuid)
        )
        self.assertFalse(
            has_at_least_viewer_role(self.other_editor, Entity.PIPELINE, self.allowed.uuid)
        )
        self.assertFalse(
            has_at_least_viewer_role(self.stranger, Entity.PIPELINE, self.allowed.uuid)
        )

    def tearDown(self):
        for connection, _messages in self.connections:
            connection.close()
        WebSocketServer.running_executions_mapping.clear()
        super().tearDown()

    def get_app(self):
        # Same route registration as mage_ai/server/server.py.
        return tornado.web.Application([(r'/websocket/', WebSocketServer)])

    def _origin(self):
        parsed = urlparse(self.get_url('/'))
        return '{}://{}'.format(parsed.scheme, parsed.netloc)

    async def _connect(self, token=None, origin=None):
        url = self.get_url('/websocket/').replace('http', 'ws', 1)
        headers = {}
        if origin is not None:
            headers['Origin'] = origin
        if token is not None:
            url = '{}?{}'.format(url, urlencode({
                'api_key': OAUTH_CLIENT_ID,
                'token': token,
            }))
        messages = []
        connection = await websocket_connect(
            HTTPRequest(url, headers=headers),
            on_message_callback=messages.append,
        )
        self.connections.append((connection, messages))
        return connection, messages

    def _deliver_iopub(self, code, execution):
        """
        Run code in a real kernel and push every IOPub message through the
        subscriber callback registered in mage_ai/server/server.py.
        """
        msg_id = self.kernel_client.execute(code)
        WebSocketServer.running_executions_mapping[msg_id] = execution
        original = self.kernel_client.get_iopub_msg
        state = {'stop': False, 'seen': 0}

        def get_iopub_msg(timeout=1):
            if state['stop']:
                raise KeyboardInterrupt
            message = original(timeout=timeout)
            state['seen'] += 1
            parent = (message.get('parent_header') or {}).get('msg_id')
            content = message.get('content') or {}
            if state['seen'] > 40 or (
                parent == msg_id and content.get('execution_state') == 'idle'
            ):
                state['stop'] = True
            return message

        self.kernel_client.get_iopub_msg = get_iopub_msg
        try:
            with patch(
                'mage_ai.server.subscriber.get_active_kernel_client',
                return_value=self.kernel_client,
            ):
                try:
                    get_messages(
                        lambda content: WebSocketServer.send_message(
                            parse_output_message(content),
                        ),
                    )
                except KeyboardInterrupt:
                    pass
        finally:
            self.kernel_client.get_iopub_msg = original
        return msg_id

    def test_make_app_mounts_notebook_websocket(self):
        app = make_app()
        mounted = [
            rule.matcher.regex.pattern
            for rule in app.wildcard_router.rules
            if rule.target is WebSocketServer
        ]
        self.assertEqual(['/websocket/$'], mounted)

    @gen_test(timeout=30)
    async def test_foreign_origin_handshake_is_rejected(self):
        with self.assertRaises(HTTPClientError) as caught:
            await self._connect(origin='https://attacker.example')
        self.assertEqual(403, caught.exception.code)
        self.assertEqual(set(), WebSocketServer.clients)

    @gen_test(timeout=60)
    async def test_kernel_output_is_limited_to_pipeline_viewers(self):
        _anonymous, anonymous_messages = await self._connect(origin=self._origin())
        _stranger, stranger_messages = await self._connect(
            token=TOKEN_STRANGER,
            origin=self._origin(),
        )
        _viewer, viewer_messages = await self._connect(
            token=TOKEN_VIEWER,
            origin=self._origin(),
        )
        _other, other_messages = await self._connect(
            token=TOKEN_OTHER,
            origin=self._origin(),
        )

        # Shape written by WebSocketServer.__execute_pipeline for the PySpark kernel.
        self._deliver_iopub(
            "print('{}')\n'{}'".format(STDOUT_MARKER, FRAME_MARKER),
            {'pipeline_uuid': self.allowed.uuid},
        )
        self._deliver_iopub(
            "raise RuntimeError('{}')".format(TRACEBACK_MARKER),
            {'pipeline_uuid': self.allowed.uuid},
        )
        await self._flush()

        viewer_text = _texts(viewer_messages)
        self.assertIn(STDOUT_MARKER, viewer_text)
        self.assertIn(FRAME_MARKER, viewer_text)
        self.assertIn(TRACEBACK_MARKER, viewer_text)
        for messages in (anonymous_messages, stranger_messages, other_messages):
            text = _texts(messages)
            self.assertNotIn(STDOUT_MARKER, text)
            self.assertNotIn(FRAME_MARKER, text)
            self.assertNotIn(TRACEBACK_MARKER, text)

        for bucket in (
            anonymous_messages,
            stranger_messages,
            viewer_messages,
            other_messages,
        ):
            bucket.clear()

        # The next message is for the other pipeline. Permission to view the
        # previous pipeline must not carry over.
        self._deliver_iopub(
            "print('{}')".format(OTHER_PIPELINE_MARKER),
            {'pipeline_uuid': self.other.uuid},
        )
        await self._flush()
        self.assertIn(OTHER_PIPELINE_MARKER, _texts(other_messages))
        self.assertNotIn(OTHER_PIPELINE_MARKER, _texts(viewer_messages))
        self.assertNotIn(OTHER_PIPELINE_MARKER, _texts(anonymous_messages))
        self.assertNotIn(OTHER_PIPELINE_MARKER, _texts(stranger_messages))

    @gen_test(timeout=60)
    async def test_block_execution_without_pipeline_is_not_broadcast(self):
        # Shape written by WebSocketServer.__execute_block. It has a block id
        # and no pipeline id. That record is still enough for send_message to
        # broadcast today.
        _anonymous, anonymous_messages = await self._connect(origin=self._origin())
        _stranger, stranger_messages = await self._connect(
            token=TOKEN_STRANGER,
            origin=self._origin(),
        )
        _viewer, viewer_messages = await self._connect(
            token=TOKEN_VIEWER,
            origin=self._origin(),
        )
        self._deliver_iopub(
            "print('{}')".format(STDOUT_MARKER),
            {
                'block_type': 'data_loader',
                'block_uuid': 'secret_block',
                'replicated_block': None,
            },
        )
        await self._flush()
        for messages in (anonymous_messages, stranger_messages, viewer_messages):
            self.assertNotIn(STDOUT_MARKER, _texts(messages))

    @gen_test(timeout=30)
    async def test_pipeline_execution_messages_follow_the_same_rule(self):
        _anonymous, anonymous_messages = await self._connect(origin=self._origin())
        _viewer, viewer_messages = await self._connect(
            token=TOKEN_VIEWER,
            origin=self._origin(),
        )
        _other, other_messages = await self._connect(
            token=TOKEN_OTHER,
            origin=self._origin(),
        )
        publish_pipeline_message(
            PIPELINE_MARKER,
            metadata={
                'block_uuid': 'secret_block',
                'pipeline_uuid': self.allowed.uuid,
            },
        )
        await self._flush()
        self.assertIn(PIPELINE_MARKER, _texts(viewer_messages))
        self.assertNotIn(PIPELINE_MARKER, _texts(anonymous_messages))
        self.assertNotIn(PIPELINE_MARKER, _texts(other_messages))

    @gen_test(timeout=30)
    async def test_relayed_output_uses_the_pipeline_on_the_payload(self):
        editor, editor_messages = await self._connect(
            token=TOKEN_EDITOR,
            origin=self._origin(),
        )
        _viewer, viewer_messages = await self._connect(
            token=TOKEN_VIEWER,
            origin=self._origin(),
        )
        _other, other_messages = await self._connect(
            token=TOKEN_OTHER,
            origin=self._origin(),
        )
        _anonymous, anonymous_messages = await self._connect(origin=self._origin())

        editor.write_message(json.dumps({
            'api_key': OAUTH_CLIENT_ID,
            'output': {
                'data': RELAY_MARKER,
                'execution_metadata': {
                    'block_uuid': 'secret_block',
                    'pipeline_uuid': self.allowed.uuid,
                },
                'msg_id': 'relay-allowed',
                'type': 'text/plain',
            },
            'pipeline_uuid': self.allowed.uuid,
            'token': TOKEN_EDITOR,
        }))
        await self._flush()
        self.assertIn(RELAY_MARKER, _texts(viewer_messages))
        self.assertIn(RELAY_MARKER, _texts(editor_messages))
        self.assertNotIn(RELAY_MARKER, _texts(other_messages))
        self.assertNotIn(RELAY_MARKER, _texts(anonymous_messages))

        for bucket in (editor_messages, viewer_messages, other_messages, anonymous_messages):
            bucket.clear()

        # The handshake and the message are authorized for pipeline_allowed.
        # The payload names pipeline_other. Viewers of pipeline_allowed must
        # not receive it.
        editor.write_message(json.dumps({
            'api_key': OAUTH_CLIENT_ID,
            'output': {
                'data': OTHER_PIPELINE_MARKER,
                'execution_metadata': {
                    'block_uuid': 'secret_block',
                    'pipeline_uuid': self.other.uuid,
                },
                'msg_id': 'relay-other',
                'type': 'text/plain',
            },
            'pipeline_uuid': self.allowed.uuid,
            'token': TOKEN_EDITOR,
        }))
        await self._flush()
        self.assertNotIn(OTHER_PIPELINE_MARKER, _texts(viewer_messages))
        self.assertNotIn(OTHER_PIPELINE_MARKER, _texts(editor_messages))
        self.assertNotIn(OTHER_PIPELINE_MARKER, _texts(anonymous_messages))

    async def _flush(self):
        from tornado import gen

        await gen.sleep(0.2)
