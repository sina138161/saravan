"""
BI-LEVEL Optimization Configuration
Economic and Technical Parameters for 30-Year Capacity Planning

این فایل شامل همه پارامترهای اقتصادی و فنی برای optimization دو سطحی است:
- Level 1: تصمیم‌گیری ظرفیت (30 سال)
- Level 2: بهینه‌سازی عملیاتی (سال 30ام، 8760 ساعت)
"""

from dataclasses import dataclass, field
from typing import Dict

@dataclass
class BiLevelConfig:
    """پیکربندی BI-LEVEL Optimization"""

    # ==================== TIME HORIZON ====================
    planning_horizon_years: int = 30
    """افق برنامه‌ریزی: 30 سال"""

    operational_year: int = 30
    """سال نماینده برای optimization عملیاتی (سال 30ام)"""

    discount_rate: float = 0.08
    """نرخ تنزیل (8%)"""

    # ==================== BUDGET CONSTRAINT ====================
    total_budget_usd: float = 1e9
    """محدودیت بودجه کل (1 میلیارد دلار - خیلی بزرگ برای عدم محدودیت)"""

    # ==================== WIND ENERGY ====================
    # HAWT (Horizontal Axis Wind Turbine)
    hawt_rated_power_kw: float = 30.0
    """توان اسمی HAWT: 30 kW"""

    hawt_capex_usd_per_kw: float = 1500.0
    """هزینه سرمایه‌گذاری HAWT: 1500 $/kW"""

    hawt_lifetime_years: int = 25
    """عمر مفید HAWT: 25 سال"""

    hawt_om_usd_per_kw_year: float = 30.0
    """هزینه نگهداری و تعمیرات HAWT: 30 $/kW/year (2% CAPEX)"""

    hawt_max_capacity_kw: float = 1000.0
    """حداکثر ظرفیت HAWT قابل نصب: 1 MW"""

    hawt_max_annual_expansion_kw: float = 100.0
    """حداکثر توسعه سالانه HAWT: 100 kW/year"""

    # Bladeless Wind Turbine
    bladeless_rated_power_kw: float = 3.0
    """توان اسمی Bladeless: 3 kW"""

    bladeless_capex_usd_per_kw: float = 2000.0
    """هزینه سرمایه‌گذاری Bladeless: 2000 $/kW"""

    bladeless_lifetime_years: int = 20
    """عمر مفید Bladeless: 20 سال"""

    bladeless_om_usd_per_kw_year: float = 40.0
    """هزینه نگهداری Bladeless: 40 $/kW/year (2% CAPEX)"""

    bladeless_max_capacity_kw: float = 500.0
    """حداکثر ظرفیت Bladeless: 500 kW"""

    bladeless_max_annual_expansion_kw: float = 50.0
    """حداکثر توسعه سالانه Bladeless: 50 kW/year"""

    # ==================== BATTERY STORAGE ====================
    battery_capex_usd_per_kwh: float = 500.0
    """هزینه سرمایه‌گذاری باتری: 500 $/kWh"""

    battery_lifetime_years: int = 15
    """عمر مفید باتری: 15 سال"""

    battery_om_usd_per_kwh_year: float = 10.0
    """هزینه نگهداری باتری: 10 $/kWh/year"""

    battery_max_capacity_kwh: float = 10000.0
    """حداکثر ظرفیت باتری: 10 MWh"""

    battery_efficiency: float = 0.90
    """بازده شارژ/دشارژ باتری: 90%"""

    battery_max_power_kw: float = 2000.0
    """حداکثر توان شارژ/دشارژ: 2 MW"""

    battery_max_annual_expansion_kwh: float = 500.0
    """حداکثر توسعه سالانه باتری: 500 kWh/year"""

    # ==================== GAS MICROTURBINE ====================
    gas_turbine_capex_usd_per_kw: float = 800.0
    """هزینه سرمایه‌گذاری میکروتوربین: 800 $/kW"""

    gas_turbine_lifetime_years: int = 20
    """عمر مفید میکروتوربین: 20 سال"""

    gas_turbine_om_usd_per_kwh: float = 0.015
    """هزینه نگهداری متغیر: 0.015 $/kWh"""

    gas_turbine_max_capacity_kw: float = 1000.0
    """حداکثر ظرفیت میکروتوربین: 1 MW"""

    gas_turbine_max_annual_expansion_kw: float = 100.0
    """حداکثر توسعه سالانه میکروتوربین: 100 kW/year"""

    gas_fuel_cost_usd_per_kwh: float = 0.05
    """قیمت سوخت گاز: 0.05 $/kWh (سال اول)"""

    gas_price_growth_rate: float = 0.05
    """نرخ رشد سالانه قیمت گاز: 5%/year"""

    gas_turbine_efficiency: float = 0.30
    """بازده الکتریکی میکروتوربین: 30%"""

    # ==================== GAS BOILER ====================
    gas_boiler_capex_usd_per_kw: float = 100.0
    """هزینه سرمایه‌گذاری بویلر: 100 $/kW"""

    gas_boiler_lifetime_years: int = 20
    """عمر مفید بویلر: 20 سال"""

    gas_boiler_om_usd_per_kwh: float = 0.005
    """هزینه نگهداری بویلر: 0.005 $/kWh"""

    gas_boiler_max_capacity_kw: float = 500.0
    """حداکثر ظرفیت بویلر: 500 kW"""

    gas_boiler_max_annual_expansion_kw: float = 50.0
    """حداکثر توسعه سالانه بویلر: 50 kW/year"""

    gas_boiler_efficiency: float = 0.85
    """بازده حرارتی بویلر: 85%"""

    # ==================== BIOGAS SYSTEM ====================
    biogas_digester_capex_usd_per_m3: float = 200.0
    """هزینه سرمایه‌گذاری دایجستر: 200 $/m³"""

    biogas_digester_lifetime_years: int = 20
    """عمر مفید دایجستر: 20 سال"""

    biogas_digester_om_usd_per_m3_year: float = 10.0
    """هزینه نگهداری دایجستر: 10 $/m³/year"""

    biogas_max_volume_m3: float = 1000.0
    """حداکثر حجم دایجستر: 1000 m³"""

    biogas_generator_capex_usd_per_kw: float = 1200.0
    """هزینه سرمایه‌گذاری ژنراتور بیوگاز: 1200 $/kW"""

    biogas_generator_lifetime_years: int = 15
    """عمر مفید ژنراتور بیوگاز: 15 سال"""

    biogas_generator_max_capacity_kw: float = 200.0
    """حداکثر ظرفیت ژنراتور: 200 kW"""

    # ==================== WATER SYSTEM ====================
    water_well_capex_usd: float = 50000.0
    """هزینه سرمایه‌گذاری چاه: 50,000 $"""

    water_well_lifetime_years: int = 30
    """عمر مفید چاه: 30 سال"""

    water_well_om_usd_per_year: float = 2000.0
    """هزینه نگهداری سالانه چاه: 2000 $/year"""

    water_pump_capex_usd_per_kw: float = 300.0
    """هزینه سرمایه‌گذاری پمپ: 300 $/kW"""

    water_pump_max_power_kw: float = 100.0
    """حداکثر توان پمپ: 100 kW"""

    water_tank_capex_usd_per_m3: float = 150.0
    """هزینه سرمایه‌گذاری مخزن: 150 $/m³"""

    water_tank_lifetime_years: int = 30
    """عمر مفید مخزن: 30 سال"""

    water_tank_max_volume_m3: float = 500.0
    """حداکثر حجم مخزن: 500 m³"""

    # ==================== THERMAL STORAGE ====================
    thermal_storage_capex_usd_per_kwh: float = 30.0
    """هزینه سرمایه‌گذاری ذخیره‌ساز حرارتی: 30 $/kWh"""

    thermal_storage_lifetime_years: int = 25
    """عمر مفید ذخیره‌ساز حرارتی: 25 سال"""

    thermal_storage_max_capacity_kwh: float = 5000.0
    """حداکثر ظرفیت ذخیره‌ساز: 5 MWh"""

    # ==================== GRID CONNECTION ====================
    grid_connection_capex_usd: float = 100000.0
    """هزینه اتصال به شبکه: 100,000 $"""

    grid_import_price_usd_per_kwh: float = 0.10
    """قیمت خرید از شبکه: 0.10 $/kWh (سال اول)"""

    grid_import_price_growth_rate: float = 0.03
    """نرخ رشد سالانه قیمت خرید برق: 3%/year"""

    grid_export_price_renewable_usd_per_kwh: float = 0.12
    """قیمت فروش برق تجدیدپذیر به شبکه: 0.12 $/kWh (سال اول - بالاتر از فسیلی)"""

    grid_export_price_fossil_usd_per_kwh: float = 0.08
    """قیمت فروش برق فسیلی به شبکه: 0.08 $/kWh (سال اول)"""

    grid_export_price_growth_rate: float = 0.04
    """نرخ رشد سالانه قیمت فروش برق: 4%/year"""

    grid_max_import_kw: float = 500.0
    """حداکثر توان import از شبکه: 500 kW"""

    grid_max_export_kw: float = 300.0
    """حداکثر توان export به شبکه: 300 kW"""

    # ==================== EMISSIONS ====================
    co2_price_usd_per_ton: float = 0.0
    """قیمت کربن (پایه): 0 $/ton (در سناریوها تغییر می‌کند)"""

    gas_co2_intensity_ton_per_mwh: float = 0.20
    """شدت انتشار گاز طبیعی: 0.20 ton CO2/MWh"""

    grid_co2_intensity_ton_per_mwh: float = 0.60
    """شدت انتشار شبکه برق: 0.60 ton CO2/MWh (فرض: غالباً fossil)"""

    mazut_co2_intensity_ton_per_mwh: float = 0.28
    """شدت انتشار مازوت: 0.28 ton CO2/MWh"""

    carbon_budget_ton_per_year: float = 1000.0
    """بودجه کربن سالانه: 1000 ton CO2/year (حداکثر مجاز انتشارات)"""

    # ==================== WATER TREATMENT ====================
    water_treatment_primary_capex_usd_per_m3h: float = 500.0
    """هزینه سرمایه‌گذاری تصفیه اولیه: 500 $/(m³/h)"""

    water_treatment_primary_om_usd_per_m3: float = 0.05
    """هزینه نگهداری تصفیه اولیه: 0.05 $/m³"""

    water_treatment_primary_power_kwh_per_m3: float = 0.3
    """مصرف برق تصفیه اولیه: 0.3 kWh/m³"""

    water_treatment_secondary_capex_usd_per_m3h: float = 800.0
    """هزینه سرمایه‌گذاری تصفیه ثانویه: 800 $/(m³/h)"""

    water_treatment_secondary_om_usd_per_m3: float = 0.10
    """هزینه نگهداری تصفیه ثانویه: 0.10 $/m³"""

    water_treatment_secondary_power_kwh_per_m3: float = 0.5
    """مصرف برق تصفیه ثانویه: 0.5 kWh/m³"""

    wastewater_treatment_primary_capex_usd_per_m3h: float = 600.0
    """هزینه سرمایه‌گذاری تصفیه فاضلاب اولیه: 600 $/(m³/h)"""

    wastewater_treatment_primary_om_usd_per_m3: float = 0.08
    """هزینه نگهداری تصفیه فاضلاب اولیه: 0.08 $/m³"""

    wastewater_treatment_primary_power_kwh_per_m3: float = 0.4
    """مصرف برق تصفیه فاضلاب اولیه: 0.4 kWh/m³"""

    wastewater_treatment_secondary_capex_usd_per_m3h: float = 1000.0
    """هزینه سرمایه‌گذاری تصفیه فاضلاب ثانویه: 1000 $/(m³/h)"""

    wastewater_treatment_secondary_om_usd_per_m3: float = 0.15
    """هزینه نگهداری تصفیه فاضلاب ثانویه: 0.15 $/m³"""

    wastewater_treatment_secondary_power_kwh_per_m3: float = 0.7
    """مصرف برق تصفیه فاضلاب ثانویه: 0.7 kWh/m³"""

    water_treatment_lifetime_years: int = 25
    """عمر مفید سیستم‌های تصفیه آب: 25 سال"""

    # ==================== METHODS ====================

    def calculate_annualized_capex(self, capex_total: float, lifetime_years: int) -> float:
        """
        محاسبه CAPEX سالانه با استفاده از Capital Recovery Factor

        CRF = r(1+r)^n / ((1+r)^n - 1)

        Args:
            capex_total: کل سرمایه‌گذاری اولیه ($)
            lifetime_years: عمر مفید (سال)

        Returns:
            CAPEX سالانه ($/year)
        """
        r = self.discount_rate
        n = lifetime_years

        if r == 0:
            crf = 1.0 / n
        else:
            crf = r * (1 + r)**n / ((1 + r)**n - 1)

        return capex_total * crf

    def calculate_npv_opex(self, annual_opex: float, years: int = None) -> float:
        """
        محاسبه NPV هزینه‌های عملیاتی

        NPV = Σ(OPEX / (1+r)^year) for year=1..years

        Args:
            annual_opex: هزینه عملیاتی سالانه ($/year)
            years: تعداد سال (پیش‌فرض: planning_horizon_years)

        Returns:
            NPV کل هزینه‌های عملیاتی ($)
        """
        if years is None:
            years = self.planning_horizon_years

        r = self.discount_rate

        if r == 0:
            return annual_opex * years
        else:
            # Formula: OPEX × [(1 - (1+r)^-n) / r]
            npv = annual_opex * (1 - (1 + r)**(-years)) / r
            return npv

    def get_technology_capex_per_unit(self, tech_name: str) -> float:
        """
        دریافت CAPEX واحد برای یک تکنولوژی

        Args:
            tech_name: نام تکنولوژی

        Returns:
            CAPEX per unit ($/kW or $/kWh or $/m³)
        """
        capex_map = {
            'hawt': self.hawt_capex_usd_per_kw,
            'bladeless': self.bladeless_capex_usd_per_kw,
            'battery': self.battery_capex_usd_per_kwh,
            'gas_turbine': self.gas_turbine_capex_usd_per_kw,
            'gas_boiler': self.gas_boiler_capex_usd_per_kw,
            'biogas_generator': self.biogas_generator_capex_usd_per_kw,
            'water_tank': self.water_tank_capex_usd_per_m3,
        }
        return capex_map.get(tech_name, 0.0)

    def get_technology_lifetime(self, tech_name: str) -> int:
        """
        دریافت عمر مفید یک تکنولوژی

        Args:
            tech_name: نام تکنولوژی

        Returns:
            عمر مفید (سال)
        """
        lifetime_map = {
            'hawt': self.hawt_lifetime_years,
            'bladeless': self.bladeless_lifetime_years,
            'battery': self.battery_lifetime_years,
            'gas_turbine': self.gas_turbine_lifetime_years,
            'gas_boiler': self.gas_boiler_lifetime_years,
            'biogas_generator': self.biogas_generator_lifetime_years,
            'water_tank': self.water_tank_lifetime_years,
        }
        return lifetime_map.get(tech_name, 20)  # default: 20 years


# Global instance
BI_LEVEL_CONFIG = BiLevelConfig()


if __name__ == "__main__":
    """تست پارامترها"""

    config = BI_LEVEL_CONFIG

    print("="*70)
    print("BI-LEVEL OPTIMIZATION CONFIGURATION")
    print("="*70)

    print(f"\n📅 Time Horizon: {config.planning_horizon_years} years")
    print(f"💰 Discount Rate: {config.discount_rate*100}%")
    print(f"💵 Total Budget: ${config.total_budget_usd:,.0f}")

    print("\n🌬️ WIND ENERGY:")
    print(f"  HAWT: ${config.hawt_capex_usd_per_kw}/kW, Max: {config.hawt_max_capacity_kw} kW")
    print(f"  Bladeless: ${config.bladeless_capex_usd_per_kw}/kW, Max: {config.bladeless_max_capacity_kw} kW")

    print("\n🔋 BATTERY STORAGE:")
    print(f"  CAPEX: ${config.battery_capex_usd_per_kwh}/kWh, Max: {config.battery_max_capacity_kwh} kWh")
    print(f"  Efficiency: {config.battery_efficiency*100}%")

    print("\n⚡ GAS TURBINE:")
    print(f"  CAPEX: ${config.gas_turbine_capex_usd_per_kw}/kW, Max: {config.gas_turbine_max_capacity_kw} kW")
    print(f"  Fuel: ${config.gas_fuel_cost_usd_per_kwh}/kWh, Efficiency: {config.gas_turbine_efficiency*100}%")

    print("\n💧 WATER SYSTEM:")
    print(f"  Tank: ${config.water_tank_capex_usd_per_m3}/m³, Max: {config.water_tank_max_volume_m3} m³")

    print("\n🔁 Example Calculations:")

    # Test annualization
    hawt_capex_total = 100 * config.hawt_capex_usd_per_kw  # 100 kW system
    hawt_annualized = config.calculate_annualized_capex(hawt_capex_total, config.hawt_lifetime_years)
    print(f"\n  100 kW HAWT:")
    print(f"    Total CAPEX: ${hawt_capex_total:,.0f}")
    print(f"    Annualized: ${hawt_annualized:,.0f}/year")

    # Test NPV
    annual_opex = 10000  # $10k/year
    npv_opex = config.calculate_npv_opex(annual_opex, 30)
    print(f"\n  OPEX Calculation:")
    print(f"    Annual OPEX: ${annual_opex:,.0f}/year")
    print(f"    30-year NPV: ${npv_opex:,.0f}")

    print("\n" + "="*70)
