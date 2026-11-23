import json
from unittest.mock import patch

from tornado.httpclient import AsyncHTTPClient
from tornado.ioloop import IOLoop

from mage_ai.authentication.oauth2 import decode_token
from mage_ai.authentication.providers.google import GoogleProvider
from mage_ai.data_preparation.repo_manager import ProjectType
from mage_ai.orchestration.db import db_connection
from mage_ai.orchestration.db.models.oauth import (
    Oauth2AccessToken,
    Oauth2Application,
    Permission,
    Role,
    User,
    UserRole,
)
from mage_ai.server.api.constants import COOKIE_OAUTH_TOKEN, HEADER_API_KEY
from mage_ai.server.server import initialize_user_authentication, make_app
from mage_ai.settings import OAUTH2_APPLICATION_CLIENT_ID, REQUIRE_USER_AUTHENTICATION
from mage_ai.settings.server import DEFAULT_OWNER_EMAIL
from mage_ai.tests.api.operations.test_base import BaseApiTestCase
from mage_ai.tests.factory import create_user

PLACEHOLDER_TOKEN = 'placeholder-token'
PLACEHOLDER_PASSWORD = 'placeholder-password'


class UnknownOauthProviderSessionTests(BaseApiTestCase):
    """Session creation must not treat an unknown provider as a successful OAuth login.

    These tests fail while a non-empty token and a provider name that is not a configured
    identity provider still issue an access token for the email in the request body.
    Run:

        ENV=test_mage python3 -m unittest \\
            mage_ai.tests.api.operations.test_session_unknown_oauth_provider
    """

    def setUp(self):
        super().setUp()
        self.assertTrue(REQUIRE_USER_AUTHENTICATION)
        with patch('mage_ai.server.server.sleep', lambda _seconds: None):
            initialize_user_authentication(ProjectType.STANDALONE)
        self.owner = User.query.filter(User.email == DEFAULT_OWNER_EMAIL).one()
        self.oauth_client = Oauth2Application.query.filter(
            Oauth2Application.client_id == OAUTH2_APPLICATION_CLIENT_ID,
        ).one()
        self.http_server = make_app().listen(0, address='127.0.0.1')
        socket = next(iter(self.http_server._sockets.values()))
        self.port = socket.getsockname()[1]
        self.client = AsyncHTTPClient()

    def tearDown(self):
        IOLoop.current().run_sync(self._stop_http)
        Oauth2AccessToken.query.delete()
        Oauth2Application.query.delete()
        Permission.query.delete()
        UserRole.query.delete()
        Role.query.delete()
        User.query.delete()
        db_connection.session.commit()
        super().tearDown()

    async def _stop_http(self):
        self.http_server.stop()
        await self.http_server.close_all_connections()
        self.client.close()

    def _url(self, path):
        return f'http://127.0.0.1:{self.port}{path}'

    async def _fetch(
        self,
        path,
        method='GET',
        payload=None,
        headers=None,
        cookie=None,
        include_api_key=True,
    ):
        request_headers = {}
        if include_api_key:
            request_headers[HEADER_API_KEY] = OAUTH2_APPLICATION_CLIENT_ID
        if headers:
            request_headers.update(headers)
        if cookie:
            request_headers['Cookie'] = f'{COOKIE_OAUTH_TOKEN}={cookie}'
        body = None
        if payload is not None:
            body = json.dumps(payload).encode()
            request_headers.setdefault('Content-Type', 'application/json')
        response = await self.client.fetch(
            self._url(path),
            method=method,
            headers=request_headers,
            body=body,
            raise_error=False,
        )
        text = response.body.decode()
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = {'raw': text}
        return response.code, parsed

    async def _post_session(self, session, api_key_in_body=False):
        payload = {'session': session}
        headers = {}
        include_api_key = True
        if api_key_in_body:
            payload['api_key'] = OAUTH2_APPLICATION_CLIENT_ID
            include_api_key = False
        return await self._fetch(
            '/api/sessions',
            method='POST',
            payload=payload,
            headers=headers,
            include_api_key=include_api_key,
        )

    def _refresh(self):
        db_connection.session.expire_all()

    def _tokens_for(self, user_id):
        self._refresh()
        return Oauth2AccessToken.query.filter(Oauth2AccessToken.user_id == user_id).all()

    def _assert_no_issued_session(self, body, user_ids):
        session = body.get('session') if isinstance(body, dict) else None
        issued = isinstance(session, dict) and bool(session.get('token'))
        self.assertFalse(issued)
        self._refresh()
        for user_id in user_ids:
            self.assertEqual(len(self._tokens_for(user_id)), 0)
        self.assertEqual(Oauth2AccessToken.query.count(), 0)

    async def test_password_login_still_requires_password_and_cookie_authenticates(self):
        owner_role = Role.get_role(Role.DefaultRole.OWNER)
        user = create_user(password=PLACEHOLDER_PASSWORD, roles_new=[owner_role])
        status, body = await self._post_session(
            {
                'email': user.email,
                'password': PLACEHOLDER_PASSWORD,
            }
        )
        self.assertEqual(status, 200)
        self.assertNotIn('error', body)
        encoded = body['session']['token']
        self.assertEqual(body['session']['user']['id'], user.id)
        self.assertEqual(len(self._tokens_for(user.id)), 1)

        _status, denied = await self._fetch('/api/secrets')
        self.assertIsNotNone(denied.get('error'))
        self.assertNotIn('secrets', denied)

        status, allowed = await self._fetch('/api/secrets', cookie=encoded)
        self.assertEqual(status, 200)
        self.assertNotIn('error', allowed)
        self.assertIn('secrets', allowed)

        wrong_status, wrong = await self._post_session(
            {
                'email': user.email,
                'password': 'placeholder-wrong-password',
            }
        )
        self.assertIsNotNone(wrong.get('error'))
        self.assertEqual(len(self._tokens_for(user.id)), 1)
        self.assertEqual(wrong_status, 200)

    async def test_unknown_provider_does_not_issue_session_for_existing_owner(self):
        providers = (
            'github',
            'GITHUB',
            'Google',
            'not-a-configured-provider',
        )
        for provider in providers:
            with self.subTest(provider=provider):
                user_count = User.query.count()
                status, body = await self._post_session(
                    {
                        'email': self.owner.email,
                        'provider': provider,
                        'token': PLACEHOLDER_TOKEN,
                    }
                )
                self._assert_no_issued_session(body, [self.owner.id])
                self._refresh()
                self.assertEqual(User.query.count(), user_count)
                self.assertIsNotNone(body.get('error'))
                self.assertNotEqual(status, 500)

    async def test_unknown_provider_with_api_key_in_body_does_not_issue_session(self):
        user_count = User.query.count()
        status, body = await self._post_session(
            {
                'email': self.owner.email,
                'provider': 'github',
                'token': PLACEHOLDER_TOKEN,
            },
            api_key_in_body=True,
        )
        self._assert_no_issued_session(body, [self.owner.id])
        self._refresh()
        self.assertEqual(User.query.count(), user_count)
        self.assertIsNotNone(body.get('error'))
        self.assertNotEqual(status, 500)

    async def test_unknown_provider_does_not_create_user_for_unknown_email(self):
        email = self.faker.unique.email()
        user_count = User.query.count()
        status, body = await self._post_session(
            {
                'email': email,
                'provider': 'github',
                'token': PLACEHOLDER_TOKEN,
                'username': 'placeholder-username',
            }
        )
        self._refresh()
        self.assertIsNone(User.query.filter(User.email == email).one_or_none())
        self.assertEqual(User.query.count(), user_count)
        self._assert_no_issued_session(body, [self.owner.id])
        self.assertIsNotNone(body.get('error'))
        self.assertNotEqual(status, 500)

    async def test_configured_provider_uses_user_info_email_not_request_email(self):
        provider_user = create_user()

        async def user_info(self, access_token=None, **kwargs):
            return {
                'email': provider_user.email,
                'username': provider_user.username,
            }

        with patch.dict(
            'os.environ',
            {
                'GOOGLE_CLIENT_ID': 'placeholder-client-id',
                'GOOGLE_CLIENT_SECRET': 'placeholder-client-secret',
            },
        ):
            with patch.object(GoogleProvider, 'get_user_info', user_info):
                status, body = await self._post_session(
                    {
                        'email': self.owner.email,
                        'provider': 'google',
                        'token': PLACEHOLDER_TOKEN,
                    }
                )

        self._refresh()
        self.assertEqual(len(self._tokens_for(self.owner.id)), 0)
        provider_tokens = self._tokens_for(provider_user.id)
        self.assertEqual(len(provider_tokens), 1)
        self.assertEqual(provider_tokens[0].oauth2_application_id, self.oauth_client.id)
        self.assertEqual(status, 200)
        self.assertNotIn('error', body)
        self.assertEqual(body['session']['user']['id'], provider_user.id)

        encoded = body['session']['token']
        inner = decode_token(encoded)['token']
        self.assertEqual(inner, provider_tokens[0].token)

        # The identity-provider user has no project role. The request email belongs to
        # the owner, who can read secrets. A session for the request email would succeed.
        status, secrets = await self._fetch('/api/secrets', cookie=encoded)
        self.assertEqual(status, 200)
        self.assertIsNotNone(secrets.get('error'))
        self.assertNotIn('secrets', secrets)

    async def test_configured_provider_without_email_does_not_use_request_email(self):
        async def user_info(self, access_token=None, **kwargs):
            return {'username': 'placeholder-username'}

        user_count = User.query.count()
        with patch.dict(
            'os.environ',
            {
                'GOOGLE_CLIENT_ID': 'placeholder-client-id',
                'GOOGLE_CLIENT_SECRET': 'placeholder-client-secret',
            },
        ):
            with patch.object(GoogleProvider, 'get_user_info', user_info):
                status, body = await self._post_session(
                    {
                        'email': self.owner.email,
                        'provider': 'google',
                        'token': PLACEHOLDER_TOKEN,
                    }
                )

        self._assert_no_issued_session(body, [self.owner.id])
        self._refresh()
        self.assertEqual(User.query.count(), user_count)
        self.assertIsNotNone(body.get('error'))
        self.assertNotEqual(status, 500)

    async def test_configured_provider_user_info_failure_does_not_use_request_email(self):
        async def user_info(self, access_token=None, **kwargs):
            raise RuntimeError('provider rejected the token')

        user_count = User.query.count()
        with patch.dict(
            'os.environ',
            {
                'GOOGLE_CLIENT_ID': 'placeholder-client-id',
                'GOOGLE_CLIENT_SECRET': 'placeholder-client-secret',
            },
        ):
            with patch.object(GoogleProvider, 'get_user_info', user_info):
                _status, body = await self._post_session(
                    {
                        'email': self.owner.email,
                        'provider': 'google',
                        'token': PLACEHOLDER_TOKEN,
                    }
                )

        self._refresh()
        self.assertEqual(len(self._tokens_for(self.owner.id)), 0)
        self.assertEqual(Oauth2AccessToken.query.count(), 0)
        self.assertEqual(User.query.count(), user_count)
        session = body.get('session') if isinstance(body, dict) else None
        issued = isinstance(session, dict) and bool(session.get('token'))
        self.assertFalse(issued)

    async def test_blank_token_does_not_take_oauth_path(self):
        user_count = User.query.count()
        _status, body = await self._post_session(
            {
                'email': self.owner.email,
                'provider': 'github',
                'token': '',
            }
        )
        self._assert_no_issued_session(body, [self.owner.id])
        self._refresh()
        self.assertEqual(User.query.count(), user_count)
        self.assertIsNotNone(body.get('error'))
