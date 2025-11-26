#!/usr/bin/env python3
"""
مثال سیستم یکپارچه انرژی با فرمول‌های دقیق
این مثال نشون میده چطور تمام تکنولوژی‌ها با هم کار میکنن
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'saravan_wind_water_nexus'))

print("\n" + "="*80)
print("سیستم یکپارچه انرژی ساروان - نمونه کامل با فرمول‌های Exact")
print("="*80)

# وارد کردن تمام مدل‌های مورد نیاز
from saravan_wind_water_nexus.models import (
    GasMicroturbine, HeatRecovery, GasBoiler,
    AnaerobicDigester, Dewatering, CCU,
    GroundwaterWell, ElevatedStorage,
    BatteryESS, ThermalStorage
)

print("\n📋 سناریو: یک روز کاری معمولی در سیستم انرژی ساروان")
print("="*80)

# =====================================================================================
# مرحله 1: تولید انرژی با میکروتوربین و بازیابی حرارت
# =====================================================================================
print("\n1️⃣ تولید انرژی الکتریکی و حرارتی")
print("-" * 80)

gt = GasMicroturbine()
hr = HeatRecovery()

# میکروتوربین: 500 kWh گاز طبیعی مصرف میکنه
gt_output = gt.calculate_outputs(
    fuel_input_kwh=500,
    fuel_type='natural_gas',
    load_fraction=1.0
)

print(f"\nمیکروتوربین:")
print(f"  ورودی: {gt_output['fuel_input_kwh']} kWh گاز")
print(f"  برق تولیدی: {gt_output['electricity_kwh']:.1f} kWh")
print(f"  حرارت اگزوز: {gt_output['exhaust_heat_kwh']:.1f} kWh")
print(f"  CO2: {gt_output['co2_emissions_kg']:.1f} kg")

# بازیابی حرارت از اگزوز
heat_recovered = hr.calculate_heat_recovery_from_gt(
    p_gt=gt_output['p_gt'],
    eta_gt=gt_output['eta_gt']
)

print(f"\nبازیابی حرارت:")
print(f"  حرارت بازیافتی: {heat_recovered['p_whb_kwh']:.1f} kWh")

total_electricity = gt_output['electricity_kwh']
total_heat = heat_recovered['p_whb_kwh']

# =====================================================================================
# مرحله 2: مدیریت لجن و تولید بیوگاز
# =====================================================================================
print("\n2️⃣ تولید بیوگاز از لجن و زیست‌توده")
print("-" * 80)

digester = AnaerobicDigester()

# هاضم: 5 تن لجن + 2 تن زیست‌توده در روز
biogas_output = digester.calculate_biogas_production_exact(
    m_s_ton_h=5.0 / 24,      # 5 ton/day = 0.208 ton/h
    m_bm_ton_h=2.0 / 24,     # 2 ton/day = 0.083 ton/h
    season='winter',
    available_biomass_ton_h=5.0 / 24
)

print(f"\nهاضم بی‌هوازی:")
print(f"  ورودی لجن: {biogas_output['m_s_ton_h']:.3f} ton/h")
print(f"  ورودی زیست‌توده: {biogas_output['m_bm_ton_h']:.3f} ton/h")
print(f"  بیوگاز: {biogas_output['q_ad_bg_m3_h']:.2f} m³/h")
print(f"  انرژی بیوگاز: {biogas_output['biogas_energy_kwh_h']:.2f} kWh/h")
print(f"  آب مصرفی: {biogas_output['v_ad_fw_m3_h']:.2f} m³/h")
print(f"  حرارت مورد نیاز: {biogas_output['h_ad_kwh_h']:.2f} kWh/h")
print(f"  محدودیت‌ها: {'✓ برآورده' if biogas_output['all_constraints_met'] else '✗ نقض'}")

# =====================================================================================
# مرحله 3: سوزاندن بیوگاز در بویلر
# =====================================================================================
print("\n3️⃣ تبدیل بیوگاز به حرارت")
print("-" * 80)

boiler = GasBoiler()

# بویلر: تمام بیوگاز تولیدی رو مصرف میکنه
biogas_energy_daily = biogas_output['biogas_energy_kwh_h'] * 24
boiler_output = boiler.calculate_heat_output(
    fuel_input_kwh=biogas_energy_daily,
    fuel_type='biogas'
)

print(f"\nبویلر گازی:")
print(f"  ورودی بیوگاز: {boiler_output['fuel_input_kwh']:.1f} kWh")
print(f"  حرارت تولیدی: {boiler_output['p_gb_kwh']:.1f} kWh")
print(f"  CO2: {boiler_output['co2_emissions_kg']:.1f} kg (بیوژنیک)")

total_heat += boiler_output['p_gb_kwh']

# =====================================================================================
# مرحله 4: آبزدایی و بازیافت آب
# =====================================================================================
print("\n4️⃣ جداسازی جامدات و بازیافت آب")
print("-" * 80)

dewater = Dewatering()

dewater_output = dewater.calculate_dewatering_outputs_exact(
    m_ad_d_ton_h=biogas_output['m_ad_d_ton_h'],
    v_ad_fw_m3_h=biogas_output['v_ad_fw_m3_h'],
    TS_digestate=0.08
)

print(f"\nآبزدایی:")
print(f"  ورودی دایجست: {dewater_output['m_ad_d_ton_h']:.2f} ton/h")
print(f"  جامد خروجی: {dewater_output['m_d_solid_ton_h']:.3f} ton/h")
print(f"  آب بازیافتی: {dewater_output['v_ad_rw_m3_h']:.2f} m³/h")
print(f"  فاضلاب: {dewater_output['v_ad_ww_m3_h']:.2f} m³/h")

# =====================================================================================
# مرحله 5: ذخیره‌سازی کربن
# =====================================================================================
print("\n5️⃣ جذب و ذخیره‌سازی کربن")
print("-" * 80)

ccu = CCU()

ccs_output = ccu.calculate_ccs_exact(
    technologies_emissions={
        'gas_microturbine': {
            'ef': 0.20,  # emission factor
            'p': gt_output['electricity_kwh']
        }
    }
)

print(f"\nسیستم CCS:")
print(f"  CO2 جذب شده: {ccs_output['m_ccs_kg']:.2f} kg")
print(f"  CO2 آزاد شده: {ccs_output['o_ccs_kg']:.2f} kg")
print(f"  برق مصرفی: {ccs_output['p_ccs_kwh']:.2f} kWh")

# =====================================================================================
# مرحله 6: پمپاژ آب زیرزمینی
# =====================================================================================
print("\n6️⃣ تامین آب کشاورزی")
print("-" * 80)

well = GroundwaterWell()

# نیاز آبی = آب مصرفی هاضم - آب بازیافتی
water_needed_m3_h = max(0, biogas_output['v_ad_fw_m3_h'] - dewater_output['v_ad_rw_m3_h'])

pump_output = well.calculate_pumping_power_exact(
    v_ps_m3_h=water_needed_m3_h,
    H_m=100,  # عمق چاه
    v_ps_prev_m3_h=water_needed_m3_h * 0.9
)

print(f"\nپمپاژ آب زیرزمینی:")
print(f"  دبی: {pump_output['v_ps_m3_h']:.2f} m³/h")
print(f"  عمق: {pump_output['H_m']} متر")
print(f"  توان مصرفی: {pump_output['p_ps_kw']:.2f} kW")

# =====================================================================================
# مرحله 7: ذخیره‌سازی انرژی
# =====================================================================================
print("\n7️⃣ ذخیره‌سازی انرژی الکتریکی و حرارتی")
print("-" * 80)

# باتری
battery = BatteryESS(capacity_kwh=1000, battery_type='lithium_ion')

# فرض: برق اضافی رو ذخیره میکنیم
excess_electricity = max(0, total_electricity - pump_output['p_ps_kw'] - ccs_output['p_ccs_kwh'])

battery_charge = battery.calculate_soc_charging(
    p_ESS_prev=0.5,  # 50% شارژ قبلی
    p_E_chr=min(excess_electricity, 100),  # حداکثر 100 kW شارژ
    delta_t=1
)

print(f"\nباتری:")
print(f"  ظرفیت: {battery.capacity_kwh} kWh")
print(f"  شارژ: {battery_charge['p_ESS_soc']*100:.1f}%")
print(f"  انرژی ذخیره شده: {battery_charge['energy_stored_kwh']:.1f} kWh")

# مخزن حرارتی
thermal_storage = ThermalStorage(capacity_kwh=500, storage_type='hot_water_tank')

# فرض: حرارت اضافی رو ذخیره میکنیم
excess_heat = max(0, total_heat - biogas_output['h_ad_kwh_h'])

thermal_charge = thermal_storage.calculate_soc_charging(
    p_TSS_prev=0.3,
    p_T_chr=min(excess_heat, 50),
    delta_t=1
)

print(f"\nمخزن حرارتی:")
print(f"  ظرفیت: {thermal_storage.capacity_kwh} kWh")
print(f"  شارژ: {thermal_charge['p_TSS_soc']*100:.1f}%")

# =====================================================================================
# خلاصه کل سیستم
# =====================================================================================
print("\n" + "="*80)
print("📊 خلاصه عملکرد روزانه سیستم")
print("="*80)

print(f"\nتولید انرژی:")
print(f"  ⚡ برق کل: {total_electricity:.1f} kWh")
print(f"  🔥 حرارت کل: {total_heat:.1f} kWh")
print(f"  💨 بیوگاز: {biogas_output['q_ad_bg_m3_h'] * 24:.1f} m³/روز")

print(f"\nمصرف انرژی:")
print(f"  پمپاژ آب: {pump_output['p_ps_kw']:.1f} kW")
print(f"  سیستم CCS: {ccs_output['p_ccs_kwh']:.1f} kWh")
print(f"  گرمایش هاضم: {biogas_output['h_ad_kwh_h']:.1f} kWh/h")

print(f"\nمدیریت آب:")
print(f"  آب مصرفی کل: {biogas_output['v_ad_fw_m3_h']:.2f} m³/h")
print(f"  آب بازیافتی: {dewater_output['v_ad_rw_m3_h']:.2f} m³/h")
print(f"  آب پمپاژ شده: {pump_output['v_ps_m3_h']:.2f} m³/h")

print(f"\nانتشارات کربن:")
print(f"  CO2 تولید شده: {gt_output['co2_emissions_kg']:.1f} kg")
print(f"  CO2 جذب شده: {ccs_output['m_ccs_kg']:.1f} kg")
print(f"  CO2 خالص: {gt_output['co2_emissions_kg'] - ccs_output['m_ccs_kg']:.1f} kg")

print(f"\nذخیره‌سازی:")
print(f"  شارژ باتری: {battery_charge['p_ESS_soc']*100:.1f}%")
print(f"  شارژ مخزن حرارتی: {thermal_charge['p_TSS_soc']*100:.1f}%")

print("\n" + "="*80)
print("✅ سیستم با موفقیت شبیه‌سازی شد!")
print("="*80)

print("\n💡 نکات مهم:")
print("  • همه محاسبات با فرمول‌های exact ریاضی انجام شده")
print("  • محدودیت‌های عملیاتی چک شده‌اند")
print("  • مدل آماده ادغام در بهینه‌ساز PyPSA است")
print("  • هر تکنولوژی مستقلاً قابل استفاده در شبکه است")
print("\n")
