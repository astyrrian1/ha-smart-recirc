"""Persistent push session with initial snapshots and bounded reconnect backoff."""

import asyncio
import logging
import random
from contextlib import suppress
from dataclasses import dataclass, replace
from datetime import datetime

from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import ConfigEntryError, HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import (
    SETTINGS,
    STATUS,
    Client,
    DeviceInfo,
    Frame,
    Identifier,
    LiveState,
    RecircError,
    UnsupportedAuthentication,
    parse_pair,
    parse_schedules,
    text,
)
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class Snapshot:
    info: DeviceInfo
    state: LiveState
    observed_at: datetime
    details: dict
    schedules: tuple


def apply_frame(snapshot: Snapshot, frame: Frame) -> Snapshot:
    """Merge only a verified field, preserving the rest of the current state."""
    identifier, payload = frame.identifier, frame.payload
    changes = {}
    details = snapshot.details
    if identifier == Identifier.TEMPERATURE_PAIR:
        changes["state"] = LiveState(parse_pair(payload))
    elif identifier == Identifier.NAME:
        changes["info"] = replace(snapshot.info, name=text(payload))
    elif identifier == Identifier.FIRMWARE:
        changes["info"] = replace(snapshot.info, firmware=text(payload, maximum=24))
    elif identifier == Identifier.SCHEDULES:
        changes["schedules"] = parse_schedules(payload)
    elif identifier == Identifier.FLOW:
        details = details | {"flow": payload[0]}
    elif identifier == Identifier.TEMPERATURE_DIFFERENCES:
        details = details | {"temperature_differences": tuple(payload)}
    else:
        for key, setting in SETTINGS.items():
            if identifier == setting.identifier:
                details = details | {key: payload[0]}
                break
        for key, status_id in STATUS.items():
            if identifier == status_id:
                details = details | {key: bool(payload[0])}
                break
    if not changes and details is snapshot.details:
        return snapshot
    return replace(snapshot, **changes, details=details, observed_at=dt_util.utcnow())


class RecircCoordinator(DataUpdateCoordinator[Snapshot]):
    def __init__(self, hass, entry, client: Client):
        super().__init__(hass, _LOGGER, config_entry=entry, name=DOMAIN, update_interval=None)
        self.operation_lock = asyncio.Lock()
        self.client = client
        self.entry = entry
        self._session_task = None
        self._reading_snapshot = False
        self._stopping = False
        self.client.on_frame = self._frame_received

    def _frame_received(self, frame):
        if (
            self.data is not None
            and frame.identifier == Identifier.IDENTITY
            and frame.payload.hex() != self.entry.unique_id
        ):
            # Raised into the reader to close a session with the wrong device.
            raise RecircError("Controller identity changed")
        if self.data is not None and not self._reading_snapshot and self.last_update_success:
            updated = apply_frame(self.data, frame)
            if updated is not self.data:
                self.async_set_updated_data(updated)

    def start(self):
        self._session_task = self.entry.async_create_background_task(
            self.hass, self._maintain_session(), "smart_recirc_session"
        )

    async def stop(self):
        self._stopping = True
        if self._session_task:
            self._session_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._session_task
        async with self.operation_lock:
            self.client.on_frame = None
            await self.client.close()

    async def _maintain_session(self):
        delay = 1.0
        while not self._stopping:
            await self.client.disconnected.wait()
            if self._stopping:
                return
            self.async_set_update_error(UpdateFailed("Controller disconnected"))
            await asyncio.sleep(delay * random.uniform(0.8, 1.2))
            async with self.operation_lock:
                if self.client.connected and self.last_update_success:
                    delay = 1.0
                    continue
                try:
                    snapshot = await self._read_snapshot()
                except (UpdateFailed, ConfigEntryError):
                    delay = min(delay * 2, 60)
                else:
                    self.async_set_updated_data(snapshot)
                    delay = 1.0

    async def _async_update_data(self) -> Snapshot:
        async with self.operation_lock:
            return await self._read_snapshot()

    async def _read_snapshot(self) -> Snapshot:
        if self._stopping:
            raise UpdateFailed("Integration is stopping")
        self._reading_snapshot = True
        try:
            info = await self.client.identify()
            if info.identity != self.entry.unique_id:
                raise ConfigEntryError("Controller identity changed; reconfigure the integration")
            state = await self.client.read_state()
            snapshot = Snapshot(
                info,
                state,
                dt_util.utcnow(),
                await self.client.read_details(),
                await self.client.get_schedules(),
            )
            # Notifications may interleave with startup reads. Apply each latest
            # frame so the completed snapshot cannot overwrite a newer update.
            for frame in self.client.latest.values():
                snapshot = apply_frame(snapshot, frame)
            return snapshot
        except ConfigEntryError:
            await self.client.close()
            raise
        except UnsupportedAuthentication as exc:
            await self.client.close()
            raise ConfigEntryError("Password-protected controllers are not yet supported") from exc
        except RecircError as exc:
            await self.client.close()
            raise UpdateFailed("Cannot read controller") from exc
        finally:
            self._reading_snapshot = False

    async def command(self, method, *args):
        async with self.operation_lock:
            if self._stopping:
                raise HomeAssistantError("Integration is stopping")
            try:
                info = await self.client.identify()
                if info.identity != self.entry.unique_id:
                    raise HomeAssistantError("Controller identity changed")
                result = await getattr(self.client, method)(*args)
                self.async_set_updated_data(await self._read_snapshot())
                return result
            except (RecircError, ValueError, KeyError, UpdateFailed) as exc:
                if not self.client.connected:
                    self.async_set_update_error(UpdateFailed("Controller disconnected"))
                raise HomeAssistantError(
                    "Controller command failed; refresh before retrying"
                ) from exc


type RecircConfigEntry = ConfigEntry[RecircCoordinator]
