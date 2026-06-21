"""Solar panel model: irradiance → harvested power.

Includes temperature derating and MPPT efficiency.
P_panel = area × η_panel × G × f_temp × η_mppt
"""


def temperature_derating(
    temp_coeff: float,
    panel_temp_c: float,
    stc_temp_c: float = 25.0,
) -> float:
    """Return temperature derating factor (≤1 for c-Si above 25°C)."""
    return 1.0 + temp_coeff * (panel_temp_c - stc_temp_c)


def solar_panel_power(
    irradiance_w_m2: float,
    panel_area: float,
    panel_efficiency: float,
    panel_temp_coeff: float = -0.0038,
    panel_temp_operating: float = 55.0,
    panel_temp_stc: float = 25.0,
    mppt_efficiency: float = 0.98,
) -> float:
    """Return net solar power harvested in watts (after temp derate and MPPT loss)."""
    if irradiance_w_m2 <= 0:
        return 0.0
    f_temp = temperature_derating(panel_temp_coeff, panel_temp_operating, panel_temp_stc)
    P_stc = panel_area * panel_efficiency * irradiance_w_m2
    return P_stc * f_temp * mppt_efficiency


def mppt_loss_power(
    panel_gross_power_w: float,
    mppt_efficiency: float = 0.98,
) -> float:
    """Return MPPT conversion loss in watts."""
    return panel_gross_power_w * (1.0 - mppt_efficiency)
