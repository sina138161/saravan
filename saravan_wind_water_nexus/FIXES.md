# رفع مشکلات Infeasibility و AttributeError در بهینه‌سازی

## خلاصه مشکلات و راه‌حل‌ها

| مشکل | علت | راه‌حل | Commit |
|------|------|---------|--------|
| AttributeError: objective | API جدید PyPSA | try-except با hasattr | 65a92f5 |
| KeyError: Wind_HAWT | خطا در extract_results | بررسی status قبل از extraction | 9977b11 |
| Model status: Infeasible | تقاضای آب > ظرفیت چاه | افزایش capacity از 50→200 m³/h | a95634b |
| Unused buses warning | باس‌های غیرفعال | حذف natural_gas, wastewater_treated_primary | 65a92f5 |
| Wastewater discharge | Link با efficiency=0 | bus جدید + Store sink | 9977b11 |

## مشکلات اولیه (قبل از fixes)

هنگام اجرای کد، خطاهای زیر رخ می‌داد:

```
WARNING: The following buses have no attached components: {'wastewater_treated_primary', 'natural_gas'}
WARNING: Encountered nan's in static data for columns ['efficiency2'] of component 'Link'
Model status: Infeasible
AttributeError: 'Network' object has no attribute 'objective'
```

و سپس:
```
Model status: warning
Objective: $0.00
KeyError: 'Wind_HAWT'
```

## راه‌حل‌های اعمال شده

### 1. حذف باس‌های غیرضروری ✅
- باس `natural_gas` و `wastewater_treated_primary` که استفاده نمی‌شدند حذف شدند
- این کار warning اول را برطرف کرد

### 2. افزودن Wastewater Discharge Link ✅
**مشکل:** فاضلاب تولید شده ممکن بود بیش از ظرفیت تصفیه باشد و باعث infeasibility شود

**راه‌حل:** افزودن link تخلیه فاضلاب به عنوان slack variable:

```python
self.network.add(
    "Link",
    "Wastewater_Discharge",
    bus0="wastewater_municipal",
    bus1="electricity",  # Dummy sink
    p_nom=max_urban * wastewater_factor,
    efficiency=0,  # Wastewater is discharged, no output
    marginal_cost=5  # Small cost to prefer recycling over discharge
)
```

این link:
- به عنوان خروجی اضطراری برای فاضلاب عمل می‌کند
- هزینه جزئی دارد تا optimizer بازیافت را ترجیح دهد
- از infeasibility جلوگیری می‌کند

### 3. رفع مشکل AttributeError در objective ✅
**مشکل:** دسترسی مستقیم به `network.objective` در نسخه‌های جدید PyPSA خطا می‌داد

**راه‌حل:** استفاده از try-except و بررسی hasattr:

```python
objective = None
try:
    if hasattr(self.network, 'objective'):
        objective = float(self.network.objective)
    elif hasattr(self.network, 'objective_constant'):
        objective = float(self.network.objective_constant)
except (AttributeError, TypeError, ValueError):
    objective = None
```

### 4. افزودن Carrier Definitions ✅
**مشکل:** Warning درباره carriers تعریف نشده

**راه‌حل:** افزودن متد `_add_carriers()`:

```python
def _add_carriers(self):
    carriers = [
        ('electricity', 'Electricity'),
        ('wind', 'Wind energy'),
        ('natural_gas', 'Natural gas'),
        ('water', 'Water'),
    ]
    for carrier_name, nice_name in carriers:
        self.network.add("Carrier", carrier_name, nice_name=nice_name)
```

و تخصیص carrier به هر generator:
- Wind turbines: `carrier='wind'`
- Grid power: `carrier='natural_gas'`
- Emergency backup: `carrier='electricity'`

### 5. رفع KeyError در استخراج نتایج ✅
**مشکل:** وقتی optimization failed می‌شود، generators_t.p خالی است اما کد سعی می‌کند آن را بخواند

**راه‌حل:** بررسی status قبل از استخراج جزئیات:

```python
def _extract_results(self, status_str: str, objective: float, elapsed: float):
    # If failed, return minimal results
    if status_str != 'ok' or objective is None or objective == 0:
        print("⚠️  Optimization did not complete successfully")
        return results

    # Safe extraction with column check
    for gen in self.network.generators.index:
        if gen not in self.network.generators_t.p.columns:
            continue  # Skip if no data
        ...
```

### 6. افزایش ظرفیت چاه ✅
**مشکل:** تقاضای اوج آب (150-160 m³/h) بیش از ظرفیت چاه (50 m³/h) بود

**تحلیل تقاضا:**
- کشاورزی: 400,000 m³/سال
  - با factor تابستانی 2.0 → ~91 m³/h avg در تابستان
  - با peak روزانه 1.5 → ~137 m³/h در اوج
- شهری: 80,000 m³/سال
  - با factor تابستانی 1.4 → ~13 m³/h
  - با peak 1.5 → ~19 m³/h
- صنعتی: 20,000 m³/سال → ~2.3 m³/h

**تقاضای اوج کل:** ~158 m³/h

**راه‌حل:** افزایش `extraction_limit_m3_per_hour` از 50 به 200 m³/h

```python
'groundwater_well': {
    'extraction_limit_m3_per_hour': 200,  # Was 50
    'extraction_limit_annual_m3': 640000,  # Unchanged
}
```

همچنین افزودن `marginal_cost=0.5` به چاه تا optimizer ترجیح دهد از bازیافت فاضلاب استفاده کند.

### 7. افزودن Consistency Check ✅
**مشکل:** خطاها در network structure قبل از optimization شناسایی نمی‌شدند

**راه‌حل:** فراخوانی `network.consistency_check()` قبل از optimize:

```python
def optimize(self, solver='highs'):
    print("🔍 Checking network consistency...")
    self.network.consistency_check()

    status = self.network.optimize(solver_name=solver)
    ...
```

## نتیجه

با این تغییرات، مشکلات زیر برطرف شدند:
1. ✅ حذف warning باس‌های غیرفعال
2. ✅ رفع infeasibility با:
   - اضافه کردن wastewater discharge sink
   - افزایش ظرفیت چاه از 50 به 200 m³/h
3. ✅ رفع AttributeError در دسترسی به objective
4. ✅ رفع KeyError در استخراج نتایج
5. ✅ حذف warnings مربوط به carrier
6. ✅ افزودن consistency check

## اجرای کد

### پیش‌نیازها

```bash
pip install pypsa pandas numpy matplotlib
```

### اجرا

```bash
cd saravan_wind_water_nexus
python main.py
```

نتایج در پوشه `~/Desktop/saravan_wind_water_results/` ذخیره می‌شوند و شامل:
- نمودارهای ساعتی تولید و مصرف برق
- نمودارهای سیستم آب (تقاضا، تصفیه، بازیافت)
- نمودارهای انتشار CO2 و درآمد بازار کربن
- داده‌های خام CSV

## نکات مهم

1. **Wastewater Discharge**:
   - این sink فقط در صورت پر شدن ظرفیت تصفیه فعال می‌شود
   - هزینه $5/m³ دارد تا optimizer ترجیح دهد از recycling استفاده کند

2. **Groundwater Well**:
   - ظرفیت اوج: 200 m³/h
   - محدودیت سالانه: 640,000 m³/year
   - marginal_cost=0.5 تا recycling را ترجیح دهد

3. **Carrier Tracking**:
   - می‌توانید مصرف گاز طبیعی را از طریق `carrier='natural_gas'` پیگیری کنید
   - انتشار CO2 از grid power محاسبه می‌شود

4. **Objective Value**:
   - کد با نسخه‌های مختلف PyPSA سازگار است
   - status و objective به درستی بررسی می‌شوند

5. **Network Consistency**:
   - قبل از optimization، consistency check اجرا می‌شود
   - warnings و errors زودتر شناسایی می‌شوند

## تغییرات در فایل‌ها

- **network_builder_simple.py** (3 commits):
  - افزودن `_add_carriers()` و carrier assignments
  - افزودن `wastewater_discharge` bus و Store sink
  - بهبود `optimize()` و `_extract_results()` methods
  - افزودن consistency check
  - افزودن marginal cost به groundwater well

- **water_system_model.py** (1 commit):
  - افزایش `extraction_limit_m3_per_hour` از 50 به 200

## Commit History

```
a95634b - Increase groundwater well capacity to match peak demand
9977b11 - Fix optimization warning and KeyError issues
65a92f5 - Fix PyPSA optimization infeasibility and API compatibility issues
f1d5b21 - Add documentation explaining infeasibility fixes
```

## آزمایش و اعتبارسنجی

برای اطمینان از عملکرد صحیح:

1. اجرا با داده‌های 168 ساعته (1 هفته):
```bash
python network_builder_simple.py
```

2. بررسی نتایج:
   - Optimization status باید 'ok' باشد
   - Objective value باید مثبت باشد
   - همه charts باید بدون خطا تولید شوند

3. بررسی sustainability:
   - Total groundwater extraction < 640,000 m³/year
   - Wastewater recycling rate معقول باشد
   - Grid electricity usage کمینه شود
