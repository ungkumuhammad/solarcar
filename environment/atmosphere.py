def air_density(altitude_m: float = 0.0, temp_c: float = 25.0) -> float:
    """Air density using International Standard Atmosphere with temperature correction.

    Returns kg/m³. At sea level 25°C ≈ 1.184 kg/m³.
    """
    # ISA barometric formula for pressure
    pressure_ratio = (1 - 2.2558e-5 * altitude_m) ** 5.2559
    # Ideal gas: density ∝ P/T
    temp_k = temp_c + 273.15
    rho_stc = 1.225  # kg/m³ at 15°C sea level
    temp_k_stc = 288.15
    return rho_stc * pressure_ratio * (temp_k_stc / temp_k)
