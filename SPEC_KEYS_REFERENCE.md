# Technology Spec Keys Reference
## Quick Reference for All Technologies

This document lists the correct spec keys for each technology to prevent KeyError exceptions.

---

## Wind Energy

### HAWT
```python
specs['capacity']          # 500 kW
specs['capex']            # Capital cost
```

### Bladeless
```python
specs['capacity']          # 100 kW
specs['capex']            # Capital cost
```

---

## Thermal Systems

### Gas Microturbine
```python
specs['rated_capacity_kw']        # 200 kW (NOT 'capacity')
specs['electrical_efficiency']    # 0.28 (NOT 'efficiency_electrical')
specs['capex']                    # Capital cost
```

### Heat Recovery
```python
specs['recovery_efficiency']      # 0.75
```

### Gas Boiler
```python
specs['thermal_efficiency']       # 0.85 (NOT 'efficiency_thermal')
specs['capex']                    # Capital cost
```

---

## Biogas Systems

### Anaerobic Digester
```python
specs['V_digester']              # 1000 m³ (NOT 'capacity_m3')
specs['capex']                   # Capital cost
specs['eta_ad']                  # Digestion efficiency
specs['TS_s']                    # Sludge total solids
specs['VS_s']                    # Sludge volatile solids
specs['Y_s']                     # Sludge biogas yield
specs['TS_bm']                   # Biomass total solids
specs['VS_bm']                   # Biomass volatile solids
specs['Y_bm']                    # Biomass biogas yield
```

### Dewatering
```python
specs['V_d_max']                 # 100 m³/h (NOT 'efficiency')
specs['wastewater_fraction']     # 0.25
specs['TS_cake']                 # 0.75
specs['capex']                   # Capital cost
```

### CCU (Carbon Capture)
```python
specs['capture_efficiency']      # 0.90
specs['eta_ccs_co2']            # 0.90
specs['p_ccs_N']                # Stationary consumption
specs['alpha_ccs_E']            # Energy per kg CO2
```

---

## Water Management

### Groundwater Well
```python
specs['well_specs']['depth']              # 100 m (NOT 'well_depth_m')
specs['pump_specs']['efficiency']         # 0.75 (NOT 'pump_efficiency')
specs['pump_specs']['power_rating']       # 30 kW
specs['pump_specs']['motor_efficiency']   # 0.90
specs['capex']                            # Capital cost
```

### Elevated Storage
```python
specs['V_awt_max']              # 2500 m³ (NOT 'capacity_m3' or 'tank_types[...]')
specs['V_awt_min']              # Minimum volume
specs['theta_awt']              # Water loss coefficient
specs['capex']                  # Capital cost
```

---

## Energy Storage

### Battery ESS
```python
specs['theta_ESS']              # Self-discharge (NOT 'self_discharge_hourly')
specs['sigma_E_chr']            # Charge efficiency (NOT 'charge_efficiency')
specs['sigma_E_dis']            # Discharge efficiency
specs['P_ESS_cap']              # Power capacity
specs['soc_min']                # Minimum SOC
specs['soc_max']                # Maximum SOC
specs['capex']                  # Capital cost
```

### Thermal Storage
```python
specs['theta_TSS']              # Self-discharge (NOT 'self_discharge_hourly')
specs['sigma_T_chr']            # Charge efficiency
specs['sigma_T_dis']            # Discharge efficiency
specs['P_TSS_cap']              # Power capacity
specs['soc_min']                # Minimum SOC
specs['soc_max']                # Maximum SOC
specs['capex']                  # Capital cost
```

---

## Common Mistakes to Avoid

❌ **WRONG** → ✅ **CORRECT**

### Gas Microturbine
- `specs['capacity']` → `specs['rated_capacity_kw']`
- `specs['efficiency_electrical']` → `specs['electrical_efficiency']`

### Gas Boiler
- `specs['efficiency_thermal']` → `specs['thermal_efficiency']`

### Anaerobic Digester
- `specs['capacity_m3']` → `specs['V_digester']`

### Dewatering
- `specs['efficiency']` → `specs['V_d_max']`

### Groundwater Well
- `specs['well_depth_m']` → `specs['well_specs']['depth']`
- `specs['pump_efficiency']` → `specs['pump_specs']['efficiency']`

### Elevated Storage
- `specs['capacity_m3']` → `specs['V_awt_max']`
- `specs['tank_types']['medium']['capacity']` → `specs['V_awt_max']`

### Battery ESS
- `specs['self_discharge_hourly']` → `specs['theta_ESS']`
- `specs['charge_efficiency']` → `specs['sigma_E_chr']`

### Thermal Storage
- `specs['self_discharge_hourly']` → `specs['theta_TSS']`

---

## Testing Spec Keys

To verify spec keys for any technology:

```python
import sys
sys.path.insert(0, 'saravan_wind_water_nexus')

from models.thermal.gas_microturbine import GasMicroturbine

gt = GasMicroturbine()
print(list(gt.specs.keys()))
```

---

**Last Updated:** 2025-11-26  
**All keys verified and tested**

---

## Carbon Market

### CarbonMarket / CarbonMarketModel
```python
# Method signatures (NOT specs)
calculate_tier_revenue(
    co2_avoided_tons,
    tier_name='PGC',          # NOT 'tier' - must be 'tier_name'
    water_access_improvement=True
)

# Available tier names:
# - 'VCC': Voluntary Carbon Credits
# - 'CCC': Compliance Carbon Credits  
# - 'PGC': Premium Green Credits
```

### Common Carbon Market Mistakes

❌ **WRONG** → ✅ **CORRECT**
- `tier='PGC'` → `tier_name='PGC'`

---

**Last Updated:** 2025-11-26 (Final)
**All keys and method signatures verified**
