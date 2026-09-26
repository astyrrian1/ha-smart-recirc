"""Use installed library in development and bundled library in local releases."""

try:
    from leridian_smart_recirc.client import Client
    from leridian_smart_recirc.errors import RecircError, UnsupportedAuthentication
    from leridian_smart_recirc.framing import Frame
    from leridian_smart_recirc.identifiers import Identifier
    from leridian_smart_recirc.models import DeviceInfo, LiveState, parse_pair, text
    from leridian_smart_recirc.settings import (
        NUMBERS,
        SETTINGS,
        STATUS,
        SWITCHES,
        Schedule,
        parse_schedules,
    )
except ModuleNotFoundError as exc:
    if exc.name != "leridian_smart_recirc":
        raise
    from ._vendor.leridian_smart_recirc.client import Client
    from ._vendor.leridian_smart_recirc.errors import RecircError, UnsupportedAuthentication
    from ._vendor.leridian_smart_recirc.framing import Frame
    from ._vendor.leridian_smart_recirc.identifiers import Identifier
    from ._vendor.leridian_smart_recirc.models import DeviceInfo, LiveState, parse_pair, text
    from ._vendor.leridian_smart_recirc.settings import (
        NUMBERS,
        SETTINGS,
        STATUS,
        SWITCHES,
        Schedule,
        parse_schedules,
    )

__all__ = [
    "Frame",
    "Identifier",
    "SETTINGS",
    "parse_pair",
    "parse_schedules",
    "text",
    "NUMBERS",
    "SWITCHES",
    "STATUS",
    "Schedule",
    "Client",
    "DeviceInfo",
    "LiveState",
    "RecircError",
    "UnsupportedAuthentication",
]
