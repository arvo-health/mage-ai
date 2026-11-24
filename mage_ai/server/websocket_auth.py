from typing import Optional

import jwt

from mage_ai.api.utils import authenticate_client_and_token, parse_cookie_header
from mage_ai.authentication.oauth2 import decode_token
from mage_ai.orchestration.db.models.oauth import Oauth2AccessToken, Oauth2Application
from mage_ai.server.api.constants import COOKIE_OAUTH_TOKEN
from mage_ai.settings import OAUTH2_APPLICATION_CLIENT_ID


def authenticate_websocket_request(request) -> Optional[Oauth2AccessToken]:
    """Return the valid access token, with a user, from the handshake's session cookie."""
    cookies = parse_cookie_header(request.headers.get('Cookie', ''))
    encoded_token = cookies.get(COOKIE_OAUTH_TOKEN)
    if not encoded_token:
        return None

    try:
        token = decode_token(encoded_token).get('token')
    except jwt.PyJWTError:
        return None
    if not token:
        return None

    oauth_client = Oauth2Application.query_client(OAUTH2_APPLICATION_CLIENT_ID)
    if not oauth_client:
        return None

    oauth_token, valid = authenticate_client_and_token(oauth_client.id, token)
    if not valid or not oauth_token or not oauth_token.user:
        return None

    return oauth_token
