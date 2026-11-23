"""Bind-address tests for ``mage start``.

These tests fail while the web server drops the host ``localhost`` (and an
omitted host, which is logged as localhost) and listens on every interface.
They pass once that host is bound to loopback, and an explicit all-interfaces
host still listens on every interface.

``mage_ai/server/docs_server.py`` ``run_docs_server`` is not covered. It is a
different operation: it ignores the host and always constructs
``socketserver.TCPServer(('', 7789), ...)``, and only when the process is
started with ``--dbt-docs-instance 1``.
"""
import asyncio
import http.client
import logging
import os
import shutil
import socket
import struct
import tempfile
import threading
import time
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import fcntl

from mage_ai.cli.main import app as cli_app
from mage_ai.server import active_kernel
from mage_ai.server import server as server_module
from typer.main import get_command


_SIOCGIFADDR = 0x8915
_LOOPBACK_V4 = '127.'
_WILDCARD_V4 = '0.0.0.0'


def _free_port():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]
    finally:
        sock.close()


def _non_loopback_ipv4_addresses():
    addresses = []
    for name in os.listdir('/sys/class/net'):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            packed = fcntl.ioctl(
                sock.fileno(),
                _SIOCGIFADDR,
                struct.pack('256s', name.encode('utf-8')[:15]),
            )
        except OSError:
            continue
        finally:
            sock.close()
        address = socket.inet_ntoa(packed[20:24])
        if address.startswith(_LOOPBACK_V4):
            continue
        addresses.append(address)
    return addresses


def _parse_proc_address(hex_address):
    raw = bytes.fromhex(hex_address)
    if len(raw) == 4:
        return socket.inet_ntop(socket.AF_INET, raw[::-1])
    groups = [raw[index:index + 4][::-1] for index in range(0, 16, 4)]
    return socket.inet_ntop(socket.AF_INET6, b''.join(groups))


def _listening_addresses(port):
    found = []
    for path in ('/proc/net/tcp', '/proc/net/tcp6'):
        if not os.path.exists(path):
            continue
        with open(path) as handle:
            next(handle)
            for line in handle:
                parts = line.split()
                local, state = parts[1], parts[3]
                if state != '0A':
                    continue
                hex_address, hex_port = local.split(':')
                if int(hex_port, 16) != port:
                    continue
                found.append(_parse_proc_address(hex_address))
    return found


def _is_loopback(address):
    parsed = ipaddress_address(address)
    return parsed.is_loopback


def ipaddress_address(address):
    import ipaddress
    return ipaddress.ip_address(address)


def _http(ip, port, method, path, body=None):
    connection = http.client.HTTPConnection(ip, port, timeout=3)
    try:
        headers = {'Content-Type': 'application/json'} if body is not None else {}
        connection.request(method, path, body=body, headers=headers)
        response = connection.getresponse()
        payload = response.read(512)
        return response.status, payload
    finally:
        connection.close()


def _websocket_status(ip, port):
    sock = socket.create_connection((ip, port), timeout=3)
    try:
        request = (
            f'GET /websocket/terminal HTTP/1.1\r\n'
            f'Host: {ip}:{port}\r\n'
            'Upgrade: websocket\r\n'
            'Connection: Upgrade\r\n'
            'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n'
            'Sec-WebSocket-Version: 13\r\n'
            '\r\n'
        )
        sock.sendall(request.encode('ascii'))
        data = b''
        while b'\r\n' not in data:
            chunk = sock.recv(256)
            if not chunk:
                break
            data += chunk
        line = data.split(b'\r\n', 1)[0].decode('ascii', 'replace')
        parts = line.split()
        if len(parts) < 2 or not parts[1].isdigit():
            raise AssertionError(f'websocket response was {line!r}')
        return int(parts[1])
    finally:
        sock.close()


class _StopEvent:
    def __init__(self, flag):
        self._flag = flag

    async def wait(self):
        while not self._flag.is_set():
            await asyncio.sleep(0.05)


class _Server:
    def __init__(self, project, port, host=None, via_cli=False):
        self.project = project
        self.port = port
        self.host = host
        self.via_cli = via_cli
        self.stop_flag = threading.Event()
        self.thread_error = None
        self.startup_logs = []
        self._patches = []
        self._thread = None
        self._previous_repo_path = os.environ.get('MAGE_REPO_PATH')

    def _apply_patches(self):
        async def _no_impression(self, *args, **kwargs):
            return False

        self._patches = [
            patch.object(active_kernel, 'switch_active_kernel', lambda *args, **kwargs: None),
            patch.object(server_module, 'initialize_user_authentication', lambda *args, **kwargs: None),
            patch.object(server_module, 'DISABLE_AUTO_BROWSER_OPEN', True),
            patch.object(server_module.db_connection, 'start_session', lambda *args, **kwargs: None),
            patch.object(
                server_module,
                'get_preferences',
                lambda *args, **kwargs: MagicMock(sync_config=None),
            ),
            patch.object(server_module.BlockCache, 'initialize_cache', new=AsyncMock()),
            patch.object(server_module.TagCache, 'initialize_cache', new=AsyncMock()),
            patch.object(server_module.BlockActionObjectCache, 'initialize_cache', new=AsyncMock()),
            patch.object(server_module, 'get_messages', lambda *args, **kwargs: None),
            patch.object(server_module.Observer, 'start', lambda self: None),
            patch.object(server_module, 'update_settings_on_metadata_change', lambda *args, **kwargs: None),
            patch.object(server_module, 'check_scheduler_status', lambda *args, **kwargs: None),
            patch.object(
                server_module,
                'get_memory_manager_controller',
                lambda: MagicMock(events=None),
            ),
            patch.object(server_module.scheduler_manager, 'start_scheduler', lambda *args, **kwargs: None),
            patch.object(server_module.database_manager, 'run_migrations', lambda *args, **kwargs: None),
            patch.object(server_module.UsageStatisticLogger, 'project_impression', new=_no_impression),
            patch.object(server_module.asyncio, 'Event', lambda: _StopEvent(self.stop_flag)),
        ]
        for item in self._patches:
            item.start()

    def _record_logs(self):
        handler = logging.Handler()
        handler.emit = lambda record: self.startup_logs.append(record.getMessage())
        logger = logging.getLogger('mage_ai.server.server')
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        self._log_handler = handler
        self._logger = logger

    def _run_direct(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def _go():
            await server_module.main(
                host=self.host,
                port=str(self.port),
                project=self.project,
            )

        try:
            loop.run_until_complete(_go())
        finally:
            loop.close()

    def _run_cli(self):
        from typer.testing import CliRunner

        CliRunner().invoke(cli_app, ['start', self.project, '--port', str(self.port)])

    def _thread_main(self):
        try:
            self._apply_patches()
            if self.via_cli:
                self._run_cli()
            else:
                self._run_direct()
        except Exception as exc:
            self.thread_error = exc
        finally:
            for item in reversed(self._patches):
                item.stop()

    def __enter__(self):
        from mage_ai.settings.repo import set_repo_path

        os.makedirs(self.project, exist_ok=True)
        set_repo_path(self.project)
        self._record_logs()
        self._thread = threading.Thread(target=self._thread_main, daemon=True)
        self._thread.start()
        deadline = time.time() + 30
        while time.time() < deadline:
            if self.thread_error is not None:
                raise self.thread_error
            try:
                sock = socket.create_connection(('127.0.0.1', self.port), timeout=0.2)
            except OSError:
                time.sleep(0.05)
                continue
            else:
                sock.close()
                return self
        self.stop_flag.set()
        if self._thread is not None:
            self._thread.join(timeout=5)
        if self.thread_error is not None:
            raise self.thread_error
        raise RuntimeError(f'server did not accept loopback connections on {self.port}')

    def __exit__(self, exc_type, exc, tb):
        self.stop_flag.set()
        if self._thread is not None:
            self._thread.join(timeout=5)
        self._logger.removeHandler(self._log_handler)
        if self._previous_repo_path is None:
            os.environ.pop('MAGE_REPO_PATH', None)
        else:
            os.environ['MAGE_REPO_PATH'] = self._previous_repo_path
        return False

    def startup_message(self):
        for message in self.startup_logs:
            if message.startswith('Mage is running at '):
                return message
        return ''


class ListenAddressTests(unittest.TestCase):
    def setUp(self):
        self.project = tempfile.mkdtemp(prefix='mage-listen-')
        self.port = _free_port()
        self.off_host = _non_loopback_ipv4_addresses()
        if not self.off_host:
            self.fail('this host has no non-loopback IPv4 address to connect to')

    def tearDown(self):
        shutil.rmtree(self.project, ignore_errors=True)

    def _probe(self, ip):
        sign_in = _http(ip, self.port, 'GET', '/sign-in')
        events_get = _http(ip, self.port, 'GET', '/api/events')
        events_post = _http(ip, self.port, 'POST', '/api/events', body=b'{}')
        # Hyphens do not match the unauthenticated analyses route, which is
        # registered ahead of the generic OAuth API. "demo" matches that route.
        analyses = _http(
            ip,
            self.port,
            'GET',
            '/api/pipelines/demo/blocks/demo/analyses',
        )
        terminal = _websocket_status(ip, self.port)
        return {
            'sign_in': sign_in,
            'events_get': events_get,
            'events_post': events_post,
            'analyses': analyses,
            'terminal': terminal,
        }

    def _assert_service_answers(self, results):
        sign_in_status, sign_in_body = results['sign_in']
        self.assertEqual(sign_in_status, 200, results)
        self.assertIn(b'<!DOCTYPE html>', sign_in_body)
        # These handlers do not use the OAuth middleware. A response other than
        # an authentication failure shows the route ran with no credentials.
        for key in ('events_get', 'events_post', 'analyses'):
            status = results[key][0]
            self.assertNotIn(status, (401, 403), results)
        self.assertEqual(results['terminal'], 101, results)

    def _assert_loopback_service(self, server, logged_host):
        message = server.startup_message()
        self.assertIn(f'http://{logged_host}:{self.port}', message)
        loopback = self._probe('127.0.0.1')
        self._assert_service_answers(loopback)
        return message

    def test_cli_default_host_is_localhost(self):
        command = get_command(cli_app)
        host_param = next(param for param in command.commands['start'].params if param.name == 'host')
        self.assertEqual(host_param.default, 'localhost')

    def test_localhost_host_is_reachable_only_on_loopback(self):
        with _Server(self.project, self.port, host='localhost') as server:
            message = self._assert_loopback_service(server, 'localhost')
            self._assert_not_reachable_off_host(server, message)

    def test_omitted_host_is_reachable_only_on_loopback(self):
        # ``python mage_ai/server/server.py`` leaves --host unset. start_server
        # turns that into None, and the startup log still prints localhost.
        with _Server(self.project, self.port, host=None) as server:
            message = self._assert_loopback_service(server, 'localhost')
            self._assert_not_reachable_off_host(server, message)

    def test_mage_start_without_host_flag_is_reachable_only_on_loopback(self):
        with _Server(self.project, self.port, via_cli=True) as server:
            message = self._assert_loopback_service(server, 'localhost')
            self._assert_not_reachable_off_host(server, message)

    def test_explicit_all_interfaces_host_accepts_off_host_connections(self):
        with _Server(self.project, self.port, host='0.0.0.0') as server:
            message = self._assert_loopback_service(server, '0.0.0.0')
            addresses = _listening_addresses(self.port)
            self.assertIn(_WILDCARD_V4, addresses, addresses)
            off_host = self._probe(self.off_host[0])
            self._assert_service_answers(off_host)
            self.assertIn('Mage is running at http://0.0.0.0:', message)

    def _assert_not_reachable_off_host(self, server, message):
        addresses = _listening_addresses(self.port)
        self.assertTrue(addresses, 'server has no listening socket')
        off_host_results = {}
        for address in self.off_host:
            try:
                off_host_results[address] = self._probe(address)
            except OSError as exc:
                off_host_results[address] = exc
        reachable = {
            address: result
            for address, result in off_host_results.items()
            if not isinstance(result, OSError)
        }
        non_loopback_listeners = [
            address for address in addresses if not _is_loopback(address)
        ]
        self.assertFalse(
            non_loopback_listeners or reachable,
            (
                f'{message} listened on {addresses}. '
                f'Connections to non-loopback addresses returned {reachable or off_host_results}.'
            ),
        )


if __name__ == '__main__':
    unittest.main()
