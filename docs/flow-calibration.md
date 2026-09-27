# Flow pulse count and gallons per minute

Leridian's [Live Data conversion](https://smartrecirculationcontrol.com/flow-rate-calculations/) gives the following estimates at the controller's default **75 cs** (0.75 s) Flow Meter Delay:

| Installed meter | US gallons per minute from live count `Y` |
|---|---|
| 3/4-inch stainless steel | `Y / 23.0 + 0.163` |
| 1-inch brass | `Y / 14.2 + 0.159` |

Leridian rates these estimates to ±10%. The controller reports the number of pulses counted during its configurable Flow Meter Delay, not a cumulative pulse total. The integration reads the current delay from the same controller snapshot as the count and normalizes to the vendor's 75 cs reference: `Y = pulse_count × 75 / flow_delay_cs`. This scaling follows from the count-window setting; it is not a separate manufacturer calibration. A zero count reports 0 gal/min rather than the nonzero intercept of the vendor's fitted line.

Choose the physically installed meter in the integration's **Configure** options. Until it is chosen, the new **Flow rate** sensor remains unknown instead of assuming a meter size. The existing **Flow pulse count** diagnostic sensor and entity ID stay unchanged. The new sensor uses HA's `volume_flow_rate` device class, `measurement` state class, and `gal/min` unit. It updates from the persistent push stream as counts or delay settings change; changing the meter option recalculates locally without reconnecting to the controller.

This sensor is an **instantaneous rate estimate**, not gallons consumed. The count represents a rolling measurement window, and pushed observations can overlap or be missed. Summing these counts or integrating occasional rate samples would produce an unreliable consumption total. Flow below a meter's rated minimum may also be less accurate than Leridian's ±10% figure; the [3/4-inch meter](https://smartrecirculationcontrol.com/3-4-npt-hall-sensor-flow-meter/) is specified for 2–45 L/min (0.53–12 GPM).
