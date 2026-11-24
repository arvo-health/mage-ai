from tornado.websocket import WebSocketHandler

from mage_ai.settings import WEBSOCKET_ALLOWED_ORIGINS


def is_allowed_websocket_origin(handler: WebSocketHandler, origin: str) -> bool:
    # Tornado's default check only accepts an Origin whose host matches the Host header.
    if WebSocketHandler.check_origin(handler, origin):
        return True
    return (origin or '').strip().rstrip('/').lower() in WEBSOCKET_ALLOWED_ORIGINS
