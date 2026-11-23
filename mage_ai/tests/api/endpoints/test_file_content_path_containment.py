import json
import logging
import os
import shutil
import tempfile
import urllib.parse
from unittest.mock import patch

import aiofiles.threadpool
import tornado.web
from tornado.escape import to_unicode
from tornado.httputil import HTTPServerRequest

from mage_ai.api.operations.base import BaseOperation
from mage_ai.api.operations.constants import CREATE, DELETE, DETAIL, UPDATE
from mage_ai.orchestration.db.models.oauth import User
from mage_ai.server.api.base import BaseApiHandler
from mage_ai.server.terminal_server import MageTermManager, TerminalWebsocketServer
from mage_ai.settings.platform.constants import (
    set_project_platform_activated_flag,
)
from mage_ai.settings.platform.constants import (
    project_platform_activated as platform_flag,
)
from mage_ai.settings.repo import get_repo_path
from mage_ai.tests.base_test import AsyncDBTestCase

# Same order as mage_ai/server/server.py so Tornado picks the same handler
# and the same captured pk the running server would.
_API_ROUTES = [
    (r'/api/(?P<resource>file_contents)/(?P<pk>.+)', object),
    (
        r'/api/(?P<resource>pipelines)/(?P<pk>[\w\-\%2f\.]+)'
        r'/(?P<child>blocks)/(?P<child_pk>.+)',
        object,
    ),
    (
        r'/api/(?P<resource>files)/(?P<pk>.+)/(?P<child>file_versions)',
        object,
    ),
    (r'/api/(?P<resource>page_block_layouts)/(?P<pk>.+)', object),
    (r'/api/(?P<resource>block_outputs)/(?P<pk>.+)', object),
    (r'/api/(?P<resource>git_custom_branches)/(?P<pk>.+)', object),
    (
        r'/api/(?P<resource>\w+)/(?P<pk>[\w\-\%2f\.]+)'
        r'/(?P<child>\w+)/(?P<child_pk>[\w\-\%2f\.]+)',
        object,
    ),
    (
        r'/api/(?P<resource>\w+)/(?P<pk>[\w\-\%2f\.]+)/(?P<child>\w+)',
        object,
    ),
    (r'/api/(?P<resource>\w+)/(?P<pk>[\w\-\%2f\.]+)', object),
    (r'/api/(?P<resource>\w+)', object),
    (r'/api/(?P<resource>\w+)/(?P<pk>.+)', object),
]


class _RouteHandler(tornado.web.RequestHandler):
    def get(self, resource, pk=None, child=None, child_pk=None):
        pass

    post = put = delete = get


def _routes():
    return [(pattern, _RouteHandler) for pattern, _handler in _API_ROUTES]


class FileContentPathContainmentTest(AsyncDBTestCase):
    """Outside-project paths must be refused while platform mode is on.

    These tests fail while file reads and writes follow a path that escaped
    the project. They pass once every requested path is resolved and kept
    inside the project, including when the platform settings file is present.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.application = tornado.web.Application(_routes())

    def setUp(self):
        super().setUp()
        self.outside_root = tempfile.mkdtemp(prefix='mage-containment-')
        self.addCleanup(self._remove_outside_root)
        self._enable_platform_mode()
        self.viewer = User.create(
            username=self.faker.unique.user_name(),
            email=self.faker.unique.email(),
            roles=4,
        )
        self.editor = User.create(
            username=self.faker.unique.user_name(),
            email=self.faker.unique.email(),
            roles=2,
        )

    def tearDown(self):
        self._disable_platform_mode()
        super().tearDown()

    def _remove_outside_root(self):
        if os.path.isdir(self.outside_root):
            shutil.rmtree(self.outside_root)

    def _enable_platform_mode(self):
        settings_path = os.path.join(get_repo_path(root_project=True), 'settings.yaml')
        with open(settings_path, 'w', encoding='utf-8') as settings_file:
            settings_file.write('projects: {}\n')
        set_project_platform_activated_flag()
        self.assertTrue(platform_flag())

    def _disable_platform_mode(self):
        settings_path = os.path.join(get_repo_path(root_project=True), 'settings.yaml')
        if os.path.isfile(settings_path):
            os.remove(settings_path)
        set_project_platform_activated_flag()

    def _write(self, path, text):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as handle:
            handle.write(text)

    def _snapshot(self, root):
        found = []
        for dirpath, dirnames, filenames in os.walk(root):
            for name in dirnames + filenames:
                found.append(os.path.join(dirpath, name))
        return sorted(found)

    def _routed_pk(self, method, uri):
        """Return the pk Tornado would pass through, or None if the request stops."""
        request = HTTPServerRequest(method=method, uri=uri)
        decoded_path = urllib.parse.unquote(request.path)
        filter_handler = object.__new__(BaseApiHandler)
        if not filter_handler.is_safe_path(decoded_path):
            return None
        delegate = self.application.find_handler(request)
        if delegate.handler_class is tornado.web.ErrorHandler:
            return None
        pk = delegate.path_kwargs.get('pk')
        if pk is None:
            return None
        return to_unicode(pk)

    def _uri(self, resource, file_path, double_encode=False):
        encoded = urllib.parse.quote(file_path, safe='')
        if double_encode:
            encoded = urllib.parse.quote(encoded, safe='')
        return f'/api/{resource}/{encoded}'

    async def _execute(self, action, resource, user, pk=None, payload=None):
        operation = BaseOperation(
            action=action,
            payload=payload or {},
            pk=pk,
            resource=resource,
            user=user,
        )
        try:
            return await operation.execute()
        except Exception as exc:
            return {
                'error': {
                    'message': str(exc),
                    'type': type(exc).__name__,
                },
            }

    def _assert_refused(self, response, marker):
        blob = json.dumps(response, default=str)
        self.assertNotIn(marker, blob, response)
        self.assertIn('error', response, response)

    def _notebook_locked(self):
        return patch.multiple(
            'mage_ai.settings.server',
            DISABLE_NOTEBOOK_EDIT_ACCESS=1,
        )

    def _notebook_unlocked(self):
        return patch.multiple(
            'mage_ai.settings.server',
            DISABLE_NOTEBOOK_EDIT_ACCESS=0,
        )

    async def _assert_detail_refused(self, resource, file_path, marker, user, double_encode=False):
        method = 'GET' if resource == 'file_contents' else 'DELETE'
        uri = self._uri(resource, file_path, double_encode=double_encode)
        pk = self._routed_pk(method, uri)
        if pk is None:
            return
        action = DETAIL if resource == 'file_contents' else DELETE
        response = await self._execute(action, resource, user, pk=pk)
        self._assert_refused(response, marker)

    async def test_platform_mode_follows_the_settings_file(self):
        self.assertTrue(platform_flag())
        self._disable_platform_mode()
        self.assertFalse(platform_flag())

    async def test_viewer_cannot_read_outside_file_when_platform_mode_is_on(self):
        repo = get_repo_path(root_project=True)
        inside_marker = 'project-file-marker'
        outside_marker = 'outside-file-marker'
        inside_path = os.path.join(repo, 'notes', 'inside.txt')
        outside_path = os.path.join(self.outside_root, 'secret.txt')
        self._write(inside_path, inside_marker)
        self._write(outside_path, outside_marker)
        before = self._snapshot(self.outside_root)

        with self._notebook_locked():
            inside_pk = self._routed_pk('GET', self._uri('file_contents', 'notes/inside.txt'))
            self.assertIsNotNone(inside_pk)
            inside_response = await self._execute(
                DETAIL,
                'file_contents',
                self.viewer,
                pk=inside_pk,
            )
            self.assertNotIn('error', inside_response, inside_response)
            self.assertEqual(inside_response['file_content']['content'], inside_marker)

            with self.subTest('absolute path'):
                await self._assert_detail_refused(
                    'file_contents',
                    outside_path,
                    outside_marker,
                    self.viewer,
                )
            relative_escape = os.path.relpath(outside_path, repo)
            self.assertIn('..', relative_escape)
            with self.subTest('double-encoded relative path'):
                await self._assert_detail_refused(
                    'file_contents',
                    relative_escape,
                    outside_marker,
                    self.viewer,
                    double_encode=True,
                )

        self.assertEqual(self._snapshot(self.outside_root), before)
        with open(outside_path, encoding='utf-8') as handle:
            self.assertEqual(handle.read(), outside_marker)

    async def test_locked_editor_cannot_read_outside_file_when_platform_mode_is_on(self):
        outside_marker = 'outside-file-marker-editor'
        outside_path = os.path.join(self.outside_root, 'editor-secret.txt')
        self._write(outside_path, outside_marker)
        before = self._snapshot(self.outside_root)

        with self._notebook_locked():
            await self._assert_detail_refused(
                'file_contents',
                outside_path,
                outside_marker,
                self.editor,
            )

        self.assertEqual(self._snapshot(self.outside_root), before)

    async def test_symlink_outside_the_project_is_not_readable(self):
        repo = get_repo_path(root_project=True)
        outside_marker = 'symlink-outside-marker'
        nested = os.path.join(repo, self.faker.unique.pystr(min_chars=8, max_chars=12))
        os.makedirs(nested, exist_ok=True)
        outside_path = os.path.join(self.outside_root, 'target.txt')
        link_path = os.path.join(nested, 'alias.txt')
        self._write(outside_path, outside_marker)
        os.symlink(outside_path, link_path)

        with self._notebook_locked():
            await self._assert_detail_refused(
                'file_contents',
                os.path.join(os.path.basename(nested), 'alias.txt'),
                outside_marker,
                self.viewer,
            )

    async def test_read_uses_the_path_that_was_checked(self):
        """A check that passes, then opens the request path again, must not
        observe a symlink retargeted in between.
        """
        repo = get_repo_path(root_project=True)
        inside_marker = 'checked-file-marker'
        swapped_marker = 'swapped-file-marker'
        nested = os.path.join(repo, self.faker.unique.pystr(min_chars=8, max_chars=12))
        os.makedirs(nested, exist_ok=True)
        inside_path = os.path.join(nested, 'real.txt')
        link_path = os.path.join(nested, 'alias.txt')
        outside_path = os.path.join(self.outside_root, 'swapped.txt')
        self._write(inside_path, inside_marker)
        self._write(outside_path, swapped_marker)
        os.symlink(inside_path, link_path)
        retargeted = {'done': False}
        # aiofiles 22.1.0 binds the builtin at import as sync_open and calls that
        # from the worker, so patch the function content_async actually runs.
        real_open = aiofiles.threadpool.sync_open

        def open_and_retarget(file, *args, **kwargs):
            if not retargeted['done'] and isinstance(file, (str, bytes, os.PathLike)):
                if os.path.abspath(os.fspath(file)) == os.path.abspath(link_path):
                    retargeted['done'] = True
                    os.remove(link_path)
                    os.symlink(outside_path, link_path)
            return real_open(file, *args, **kwargs)

        with self._notebook_locked(), patch(
            'aiofiles.threadpool.sync_open',
            open_and_retarget,
        ):
            pk = self._routed_pk(
                'GET',
                self._uri(
                    'file_contents',
                    os.path.join(os.path.basename(nested), 'alias.txt'),
                ),
            )
            self.assertIsNotNone(pk)
            response = await self._execute(DETAIL, 'file_contents', self.viewer, pk=pk)

        blob = json.dumps(response, default=str)
        self.assertNotIn(swapped_marker, blob, response)
        if 'error' not in response:
            self.assertEqual(response['file_content']['content'], inside_marker)

    async def test_absolute_read_is_refused_when_platform_mode_is_off(self):
        outside_marker = 'outside-file-marker-disabled'
        outside_path = os.path.join(self.outside_root, 'disabled.txt')
        self._write(outside_path, outside_marker)
        self._disable_platform_mode()
        self.assertFalse(platform_flag())
        await self._assert_detail_refused(
            'file_contents',
            outside_path,
            outside_marker,
            self.viewer,
        )

    async def test_editor_cannot_write_outside_file_when_platform_mode_is_on(self):
        repo = get_repo_path(root_project=True)
        source_marker = 'project-source-marker'
        written_marker = 'outside-write-marker'
        source_path = os.path.join(repo, 'notes', 'source.txt')
        self._write(source_path, source_marker)
        created_name = 'created.txt'

        with self._notebook_unlocked():
            with self.subTest('create'):
                create_response = await self._execute(
                    CREATE,
                    'files',
                    self.editor,
                    payload={
                        'file': {
                            'dir_path': self.outside_root,
                            'name': created_name,
                        },
                    },
                )
                self.assertIn('error', create_response, create_response)
                self.assertFalse(os.path.exists(os.path.join(self.outside_root, created_name)))

            with self.subTest('update file content'):
                outside_content = os.path.join(self.outside_root, 'updated.txt')
                self._write(outside_content, source_marker)
                update_pk = self._routed_pk('PUT', self._uri('file_contents', outside_content))
                self.assertIsNotNone(update_pk)
                update_response = await self._execute(
                    UPDATE,
                    'file_contents',
                    self.editor,
                    pk=update_pk,
                    payload={'file_content': {'content': written_marker}},
                )
                self._assert_refused(update_response, written_marker)
                with open(outside_content, encoding='utf-8') as handle:
                    self.assertEqual(handle.read(), source_marker)

            with self.subTest('rename'):
                rename_response = await self._execute(
                    UPDATE,
                    'files',
                    self.editor,
                    pk=self._routed_pk('PUT', self._uri('files', 'notes/source.txt')),
                    payload={
                        'file': {
                            'dir_path': self.outside_root,
                            'name': 'renamed.txt',
                        },
                    },
                )
                self._assert_refused(rename_response, source_marker)
                self.assertFalse(os.path.exists(os.path.join(self.outside_root, 'renamed.txt')))
                self.assertTrue(os.path.isfile(source_path))

        self.assertEqual(
            [path for path in self._snapshot(self.outside_root) if path.endswith('updated.txt')],
            [os.path.join(self.outside_root, 'updated.txt')],
        )
        self.assertFalse(os.path.exists(os.path.join(self.outside_root, created_name)))
        self.assertFalse(os.path.exists(os.path.join(self.outside_root, 'renamed.txt')))

    async def test_locked_editor_cannot_create_outside_file(self):
        written_marker = 'locked-write-marker'
        before = self._snapshot(self.outside_root)
        with self._notebook_locked():
            response = await self._execute(
                CREATE,
                'files',
                self.editor,
                payload={
                    'file': {
                        'dir_path': self.outside_root,
                        'name': 'locked.txt',
                    },
                },
            )
        self.assertIn('error', response, response)
        self.assertNotIn(written_marker, json.dumps(response, default=str))
        self.assertEqual(self._snapshot(self.outside_root), before)

    async def test_editor_cannot_delete_or_move_outside_paths(self):
        outside_marker = 'outside-delete-marker'
        outside_file = os.path.join(self.outside_root, 'do-not-delete.txt')
        outside_dir = os.path.join(self.outside_root, 'do-not-remove')
        nested_file = os.path.join(outside_dir, 'keep.txt')
        self._write(outside_file, outside_marker)
        self._write(nested_file, outside_marker)
        before = self._snapshot(self.outside_root)
        repo = get_repo_path(root_project=True)
        project_dir = os.path.join(repo, 'notes', 'movable')
        os.makedirs(project_dir, exist_ok=True)

        with self._notebook_unlocked():
            with self.subTest('delete file'):
                file_pk = self._routed_pk('DELETE', self._uri('files', outside_file))
                self.assertIsNotNone(file_pk)
                file_response = await self._execute(DELETE, 'files', self.editor, pk=file_pk)
                self.assertIn('error', file_response, file_response)
                self.assertTrue(os.path.isfile(outside_file))

            with self.subTest('delete folder'):
                folder_pk = self._routed_pk('DELETE', self._uri('folders', outside_dir))
                self.assertIsNotNone(folder_pk)
                folder_response = await self._execute(
                    DELETE,
                    'folders',
                    self.editor,
                    pk=folder_pk,
                )
                self.assertIn('error', folder_response, folder_response)
                self.assertTrue(os.path.isdir(outside_dir))
                self.assertTrue(os.path.isfile(nested_file))

            with self.subTest('create folder'):
                create_response = await self._execute(
                    CREATE,
                    'folders',
                    self.editor,
                    payload={
                        'folder': {
                            'path': self.outside_root,
                            'name': 'created-folder',
                        },
                    },
                )
                self.assertIn('error', create_response, create_response)
                self.assertFalse(
                    os.path.exists(os.path.join(self.outside_root, 'created-folder')),
                )

            with self.subTest('move folder'):
                move_pk = self._routed_pk('PUT', self._uri('folders', 'notes/movable'))
                self.assertIsNotNone(move_pk)
                move_response = await self._execute(
                    UPDATE,
                    'folders',
                    self.editor,
                    pk=move_pk,
                    payload={
                        'folder': {
                            'path': self.outside_root,
                            'name': 'moved-folder',
                        },
                    },
                )
                self.assertIn('error', move_response, move_response)
                self.assertFalse(
                    os.path.exists(os.path.join(self.outside_root, 'moved-folder')),
                )
                self.assertTrue(os.path.isdir(project_dir))

        self.assertEqual(self._snapshot(self.outside_root), before)
        self.assertTrue(os.path.isdir(project_dir))

    async def test_terminal_cwd_stays_inside_the_project(self):
        self.assertTrue(platform_flag())
        socket = TerminalWebsocketServer.__new__(TerminalWebsocketServer)
        socket.term_manager = MageTermManager(shell_command=['bash'])
        socket._logger = logging.getLogger('mage-terminal-containment-test')
        socket.terminal = None
        socket.get_argument = (
            lambda name, default=None, strip=True: self.outside_root if name == 'cwd' else default
        )
        socket.send_json_message = lambda content: None
        socket.on_pty_read = lambda text: None
        socket.on_pty_died = lambda: None
        try:
            socket.open()
            pid = socket.terminal.ptyproc.pid
            terminal_cwd = os.path.realpath(os.readlink(f'/proc/{pid}/cwd'))
        finally:
            terminal = getattr(socket, 'terminal', None)
            if terminal is not None:
                terminal.kill()
            socket.term_manager.blocking_io_executor.shutdown(wait=False, cancel_futures=True)

        self.assertNotEqual(terminal_cwd, os.path.realpath(self.outside_root))
