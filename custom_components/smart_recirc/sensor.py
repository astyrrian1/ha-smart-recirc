"""Verified metadata and explicitly uncalibrated probe telemetry."""

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import UnitOfVolumeFlowRate
from homeassistant.helpers.entity import EntityCategory

from .const import CONF_FLOW_METER, FLOW_METER_UNKNOWN
from .entity import RecircEntity
from .flow import gallons_per_minute


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(
        RecircSensor(entry.runtime_data, key)
        for key in (
            "firmware",
            "probe_1",
            "probe_2",
            "last_read",
            "flow",
            "flow_rate",
            "temperature_difference",
        )
    )


class RecircSensor(RecircEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, key):
        super().__init__(coordinator, key)
        self.key = key
        self._attr_name = {
            "firmware": "Firmware",
            "probe_1": "Probe 1 raw value",
            "probe_2": "Probe 2 raw value",
            "last_read": "Last received update",
            "flow": "Flow pulse count",
            "flow_rate": "Flow rate",
            "temperature_difference": "Temperature difference",
        }[key]
        if key == "flow_rate":
            self._attr_entity_category = None
            self._attr_device_class = SensorDeviceClass.VOLUME_FLOW_RATE
            self._attr_state_class = SensorStateClass.MEASUREMENT
            self._attr_native_unit_of_measurement = UnitOfVolumeFlowRate.GALLONS_PER_MINUTE
        if key == "last_read":
            self._attr_device_class = SensorDeviceClass.TIMESTAMP
        if key in ("probe_1", "probe_2"):
            self._attr_name = "Low temperature" if key == "probe_1" else "High temperature"
            self._attr_device_class = SensorDeviceClass.TEMPERATURE
            self._attr_native_unit_of_measurement = "°F"
        if key == "temperature_difference":
            self._attr_native_unit_of_measurement = "°F"
            # No absolute-temperature device class: this is an interval.

    @property
    def native_value(self):
        data = self.coordinator.data
        if self.key == "firmware":
            return data.info.firmware
        if self.key == "last_read":
            return data.observed_at
        if self.key == "flow":
            return data.details["flow"]
        if self.key == "flow_rate":
            return gallons_per_minute(
                data.details.get("flow"),
                data.details.get("flow_delay"),
                self.coordinator.entry.options.get(CONF_FLOW_METER, FLOW_METER_UNKNOWN),
            )
        if self.key == "temperature_difference":
            return round(abs(data.state.probe_values[1] - data.state.probe_values[0]), 1)
        return data.state.probe_values[0 if self.key == "probe_1" else 1]
