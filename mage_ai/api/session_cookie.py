from datetime import datetime, timezone
from typing import Optional

from mage_ai.api.utils import parse_cookie_header
from mage_ai.authentication.oauth2 import decode_token
from mage_ai.server.api.constants import COOKIE_OAUTH_TOKEN
from mage_ai.settings import REQUESTS_BASE_PATH


def session_cookie_path() -> str:
    base_path = (REQUESTS_BASE_PATH or '').strip('/')
    return f'/{base_path}' if base_path else '/'


def __is_secure_request(request) -> bool:
    forwarded_proto = request.headers.get('X-Forwarded-Proto', '') or ''
    return request.protocol == 'https' or \
        forwarded_proto.split(',')[0].strip().lower() == 'https'


def set_session_cookie(handler, encoded_token: str) -> None:
    """
    Store the session token in an HttpOnly cookie so that scripts running in the page can't
    read it. The frontend never needs the raw token: API requests and websocket connections
    are authenticated with this cookie.
    """
    try:
        token_data = decode_token(encoded_token)
    except Exception:
        return

    expires = token_data.get('expires')
    handler.set_cookie(
        COOKIE_OAUTH_TOKEN,
        encoded_token,
        expires=datetime.fromtimestamp(expires, tz=timezone.utc) if expires else None,
        httponly=True,
        path=session_cookie_path(),
        samesite='Strict',
        secure=__is_secure_request(handler.request),
    )


def clear_session_cookie(handler) -> None:
    handler.clear_cookie(
        COOKIE_OAUTH_TOKEN,
        httponly=True,
        path=session_cookie_path(),
        samesite='Strict',
        secure=__is_secure_request(handler.request),
    )


def token_from_session_cookie(request) -> Optional[str]:
    cookies = parse_cookie_header(request.headers.get('Cookie', ''))
    encoded_token = cookies.get(COOKIE_OAUTH_TOKEN)
    if not encoded_token:
        return None

    try:
        return decode_token(encoded_token).get('token')
    except Exception:
        return None
