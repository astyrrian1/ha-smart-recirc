"""Exercise real HA setup against a synthetic TCP controller."""

from unittest.mock import patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from leridian_smart_recirc.simulator import Simulator
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.smart_recirc.const import CONF_FLOW_METER, FLOW_METER_1, FLOW_METER_3_4
from custom_components.smart_recirc.flow import gallons_per_minute

DOMAIN = "smart_recirc"


@pytest.fixture
async def simulator(socket_enabled):
    sim = Simulator()
    await sim.start()
    yield sim
    await sim.close()


async def setup_entry(hass, simulator):
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="020000000001",
        title="Test controller",
        data={"host": "127.0.0.1", "port": simulator.port},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_setup_sensors_device_refresh_and_unload(hass, simulator):
    entry = await setup_entry(hass, simulator)
    assert entry.state is ConfigEntryState.LOADED
    assert entry.runtime_data.update_interval is None
    assert entry.runtime_data.client.connected
    registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(registry, entry.entry_id)
    assert len(entities) == 23
    assert len({e.device_id for e in entities}) == 1
    device = dr.async_get(hass).async_get(entities[0].device_id)
    assert device.sw_version == "6.2.2"
    probe = next(e for e in entities if e.unique_id.endswith("_probe_1"))
    assert float(hass.states.get(probe.entity_id).state) == pytest.approx((72.9 - 32) * 5 / 9)
    assert hass.states.get(probe.entity_id).attributes["unit_of_measurement"] == "°C"
    refresh = next(e for e in entities if e.domain == "button")
    simulator.values[next(k for k in simulator.values if k.name == "TEMPERATURE_PAIR")] = (
        b"73.1,75.0"
    )
    await hass.services.async_call(
        "button", "press", {"entity_id": refresh.entity_id}, blocking=True
    )
    await hass.async_block_till_done()
    assert float(hass.states.get(probe.entity_id).state) == pytest.approx((73.1 - 32) * 5 / 9)
    client = entry.runtime_data.client
    assert await hass.config_entries.async_unload(entry.entry_id)
    assert not client.connected


async def test_config_flow_acknowledgment_and_duplicates(hass, simulator):
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    data = {"host": "127.0.0.1", "port": simulator.port, "acknowledge_timer_effect": False}
    result = await hass.config_entries.flow.async_configure(result["flow_id"], data)
    assert result["errors"] == {"acknowledge_timer_effect": "acknowledgment_required"}
    assert not simulator.received
    data["acknowledge_timer_effect"] = True
    with patch("custom_components.smart_recirc.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], data)
        assert result["type"] is FlowResultType.CREATE_ENTRY
        await hass.async_block_till_done()
    second = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    second = await hass.config_entries.flow.async_configure(second["flow_id"], data)
    assert second["type"] is FlowResultType.ABORT
    assert second["reason"] == "already_configured"


@pytest.mark.parametrize(
    ("meter", "expected"),
    [(FLOW_METER_3_4, 2.71), (FLOW_METER_1, 4.28)],
)
def test_manufacturer_flow_calibration_accounts_for_delay(meter, expected):
    # 39 pulses over 50 cs equals 58.5 pulses over the vendor's 75 cs reference.
    assert gallons_per_minute(39, 50, meter) == expected
    assert gallons_per_minute(0, 50, meter) == 0
    assert gallons_per_minute(39, 0, meter) is None
    assert gallons_per_minute(39, 50, "unknown") is None


async def test_flow_rate_options_use_live_delay_without_reconnecting(hass, simulator):
    import asyncio

    from leridian_smart_recirc.identifiers import Identifier as I

    simulator.values[I.FLOW_DELAY] = b"\x32"  # 50 cs
    simulator.values[I.FLOW] = b"\x27"  # 39 pulses
    entry = await setup_entry(hass, simulator)
    entities = er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)
    raw = next(e for e in entities if e.unique_id.endswith("_flow"))
    rate = next(e for e in entities if e.unique_id.endswith("_flow_rate"))
    assert hass.states.get(raw.entity_id).state == "39"
    assert hass.states.get(rate.entity_id).state == "unknown"
    before_requests = len(simulator.received)
    flow = await hass.config_entries.options.async_init(entry.entry_id)
    assert flow["type"] is FlowResultType.FORM
    result = await hass.config_entries.options.async_configure(
        flow["flow_id"], {CONF_FLOW_METER: FLOW_METER_3_4}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    state = hass.states.get(rate.entity_id)
    assert float(state.state) == pytest.approx(2.71)
    assert state.attributes["unit_of_measurement"] == "gal/min"
    assert len(simulator.received) == before_requests
    assert entry.runtime_data.client.connections == 1
    await simulator.push(I.FLOW_DELAY, b"\x4b")  # 75 cs
    for _ in range(100):
        if entry.runtime_data.data.details["flow_delay"] == 75:
            break
        await asyncio.sleep(0.01)
    await hass.async_block_till_done()
    assert float(hass.states.get(rate.entity_id).state) == pytest.approx(1.86)
    assert hass.states.get(raw.entity_id).state == "39"
    await hass.config_entries.async_unload(entry.entry_id)


async def test_diagnostics_are_allowlisted(hass, simulator):
    entry = await setup_entry(hass, simulator)
    from custom_components.smart_recirc.diagnostics import async_get_config_entry_diagnostics

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)
    assert diagnostics["firmware"] == "6.2.2"
    assert all(
        secret not in str(diagnostics) for secret in ["127.0.0.1", "020000000001", "Simulated"]
    )
    await hass.config_entries.async_unload(entry.entry_id)


async def test_wrong_identity_is_not_loaded(hass, simulator):
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id="wrong", data={"host": "127.0.0.1", "port": simulator.port}
    )
    entry.add_to_hass(hass)
    assert not await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.SETUP_ERROR


async def test_refresh_failure_unavailable_and_recovery(hass, simulator):
    from homeassistant.exceptions import HomeAssistantError

    entry = await setup_entry(hass, simulator)
    entities = er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)
    refresh = next(e for e in entities if e.domain == "button")
    probe = next(e for e in entities if e.unique_id.endswith("_probe_1"))
    simulator.wrong_identifier = True
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            "button", "press", {"entity_id": refresh.entity_id}, blocking=True
        )
    assert hass.states.get(probe.entity_id).state == "unavailable"
    assert hass.states.get(refresh.entity_id).state != "unavailable"
    simulator.wrong_identifier = False
    # Ask coordinator directly to avoid the intentional refresh debouncer in this recovery test.
    await entry.runtime_data.async_refresh()
    assert float(hass.states.get(probe.entity_id).state) == pytest.approx((72.9 - 32) * 5 / 9)
    await hass.config_entries.async_unload(entry.entry_id)


async def test_controls_and_schedule_services(hass, simulator):
    from homeassistant.exceptions import HomeAssistantError
    from leridian_smart_recirc.identifiers import Identifier

    entry = await setup_entry(hass, simulator)
    entities = er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)
    sensitivity = next(e for e in entities if e.unique_id.endswith("_sensitivity"))
    await hass.services.async_call(
        "number", "set_value", {"entity_id": sensitivity.entity_id, "value": 8}, blocking=True
    )
    assert hass.states.get(sensitivity.entity_id).state == "8"
    enabled = next(e for e in entities if e.unique_id.endswith("_controller_enabled"))
    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": enabled.entity_id}, blocking=True
    )
    assert hass.states.get(enabled.entity_id).state == "on"
    base = {"config_entry_id": entry.entry_id}
    assert await hass.services.async_call(
        DOMAIN, "get_schedules", base, blocking=True, return_response=True
    ) == {"schedules": []}
    await hass.services.async_call(
        DOMAIN,
        "set_schedule",
        base
        | {
            "slot": 0,
            "start": "23:00",
            "end": "01:00",
            "weekdays": [False] * 7,
            "expected_schedules": [],
        },
        blocking=True,
    )
    schedules = await hass.services.async_call(
        DOMAIN, "get_schedules", base, blocking=True, return_response=True
    )
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            DOMAIN, "delete_schedule", base | {"slot": 0, "expected_schedules": []}, blocking=True
        )
    await hass.services.async_call(
        DOMAIN,
        "delete_schedule",
        base | {"slot": 0, "expected_schedules": schedules["schedules"]},
        blocking=True,
    )
    logs = await hass.services.async_call(
        DOMAIN, "get_logs", base, blocking=True, return_response=True
    )
    assert len(logs["records"]) == 1 and logs["complete"] is False
    assert logs["records"][0]["pump_on"] is True
    simulator.values[Identifier.TIMER_ACTIVE] = b"\x00"
    for suffix, expected in (("_trigger", b"\x01"), ("_stop", b"\x00")):
        button = next(e for e in entities if e.unique_id.endswith(suffix))
        await hass.services.async_call(
            "button", "press", {"entity_id": button.entity_id}, blocking=True
        )
        assert simulator.values[Identifier.PUMP_RUNNING] == expected
    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_push_updates_without_polling_and_ignores_old_poll_option(hass, simulator):
    import asyncio

    from leridian_smart_recirc.identifiers import Identifier as I

    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="020000000001",
        data={"host": "127.0.0.1", "port": simulator.port},
        options={"poll_interval": 30, "acknowledge_timer_effect": True},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    coordinator = entry.runtime_data
    before = len(simulator.received)
    entities = er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)
    probe = next(e for e in entities if e.unique_id.endswith("_probe_1"))
    pump = next(e for e in entities if e.unique_id.endswith("_pump_running"))
    old_time = coordinator.data.observed_at
    await simulator.push(I.TEMPERATURE_PAIR, b"80.0,85.0")
    await simulator.push(I.PUMP_RUNNING, b"\x01")
    await simulator.push(I.FLOW, b"\x04")
    await simulator.push(I.SENSITIVITY, b"\x07")
    await simulator.push(0xDEADBEEF, b"unknown extension")
    for _ in range(100):
        if coordinator.data.details["sensitivity"] == 7:
            break
        await asyncio.sleep(0.01)
    await hass.async_block_till_done()
    assert float(hass.states.get(probe.entity_id).state) == pytest.approx((80 - 32) * 5 / 9)
    assert hass.states.get(pump.entity_id).state == "on"
    assert coordinator.data.details["flow"] == 4
    assert coordinator.data.details["sensitivity"] == 7
    assert coordinator.data.observed_at > old_time
    assert coordinator.update_interval is None
    assert coordinator.client.connections == 1
    assert len(simulator.received) == before
    await hass.config_entries.async_unload(entry.entry_id)
    assert coordinator._session_task.done()
    assert coordinator.client._reader_task is None


async def test_push_disconnect_reconnect_and_malformed_frame(hass, simulator):
    import asyncio

    from leridian_smart_recirc.identifiers import Identifier as I

    entry = await setup_entry(hass, simulator)
    coordinator = entry.runtime_data
    simulator.values[I.TEMPERATURE_PAIR] = b"81.0,86.0"
    failed, recovered = asyncio.Event(), asyncio.Event()

    def changed():
        (recovered if coordinator.last_update_success else failed).set()

    unsubscribe = coordinator.async_add_listener(changed)
    await simulator.push(I.TEMPERATURE_PAIR, b"malformed")
    await asyncio.wait_for(failed.wait(), 2)
    await asyncio.wait_for(recovered.wait(), 4)
    assert coordinator.data.state.probe_values == (81, 86)
    assert coordinator.client.connections == 2
    failed.clear()
    await simulator.disconnect_clients()
    await asyncio.wait_for(failed.wait(), 2)
    unsubscribe()
    # Unloading during reconnect backoff cancels all future reconnects.
    await hass.config_entries.async_unload(entry.entry_id)
    count = coordinator.client.connections
    await asyncio.sleep(1.3)
    assert coordinator.client.connections == count
