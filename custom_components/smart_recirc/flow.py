"""Manufacturer-published conversion of Live Data flow counts to US gal/min."""

from .const import FLOW_METER_1, FLOW_METER_3_4

# https://smartrecirculationcontrol.com/flow-rate-calculations/
# These divisors and offsets apply to a 75 cs counting window. The controller's
# Flow Meter Delay can change, so normalize the observed count to that window.
CALIBRATION = {
    FLOW_METER_3_4: (23.0, 0.163),
    FLOW_METER_1: (14.2, 0.159),
}
REFERENCE_DELAY_CS = 75


def gallons_per_minute(pulses: int | None, delay_cs: int | None, meter: str) -> float | None:
    """Estimate current flow, leaving uncalibrated or missing readings unknown."""
    if meter not in CALIBRATION or pulses is None or delay_cs is None or delay_cs <= 0:
        return None
    if pulses == 0:
        return 0.0
    divisor, offset = CALIBRATION[meter]
    return round(pulses * REFERENCE_DELAY_CS / delay_cs / divisor + offset, 2)
