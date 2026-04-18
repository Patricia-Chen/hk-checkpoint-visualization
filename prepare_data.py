import pandas as pd
import numpy as np
import json
import os

os.chdir(r'd:\hkust\DV\Group Project\Group Project')

output = {}

# ============================================================
# Chart 1: Monthly passenger flow by source type
# ============================================================
df = pd.read_csv('日常旅客入出境统计_月度.csv')
monthly = df.groupby('年月').agg({
    '香港居民': 'sum', '内地访客': 'sum', '其他访客': 'sum', '总计': 'sum'
}).reset_index().sort_values('年月')

output['chart1'] = {
    'months': monthly['年月'].tolist(),
    'hk_residents': monthly['香港居民'].astype(int).tolist(),
    'mainland': monthly['内地访客'].astype(int).tolist(),
    'other': monthly['其他访客'].astype(int).tolist(),
    'total': monthly['总计'].astype(int).tolist(),
}

# ============================================================
# Chart 2: Heatmap – checkpoint x month
# ============================================================
heatmap = df.groupby(['年月', '管制站'])['总计'].sum().reset_index()
checkpoints = sorted(heatmap['管制站'].unique().tolist())
months_all = sorted(heatmap['年月'].unique().tolist())

heat_data = []
for _, row in heatmap.iterrows():
    ci = checkpoints.index(row['管制站'])
    mi = months_all.index(row['年月'])
    heat_data.append([mi, ci, int(row['总计'])])

output['chart2'] = {
    'months': months_all,
    'checkpoints': checkpoints,
    'data': heat_data,
}

# ============================================================
# Chart 3: Holiday vs normal day comparison
# ============================================================
df_holiday = pd.read_csv('节假日旅客入出境统计.csv')
df_daily = pd.read_csv('日常旅客入出境统计.csv')

holiday_map = {
    '二': '春节',
    '三': '复活节',
    '四': '清明节',
    '五': '劳动节',
    '六': '佛诞',
    '七': '端午/回归日',
    '八': '暑假',
    '九': '中秋节',
    '十+十一': '国庆黄金周',
    '十二+一': '圣诞/元旦',
    '五+六': '劳动节/佛诞',
    '九+十': '中秋/国庆',
    '十一': '11月假期',
    '十二': '圣诞节',
}

df_holiday['假期名称'] = df_holiday['假期'].map(lambda x: holiday_map.get(str(x).strip(), str(x).strip()))

holiday_agg = df_holiday.groupby('假期名称').agg(
    days=('日期', 'nunique'),
    total=('总计', 'sum'),
    hk=('香港居民', 'sum'),
    mainland=('内地访客', 'sum'),
    other=('其他访客', 'sum'),
).reset_index()
holiday_agg['daily_avg'] = (holiday_agg['total'] / holiday_agg['days']).astype(int)
holiday_agg = holiday_agg.sort_values('daily_avg', ascending=False)

total_days_in_data = df_daily['日期'].nunique()
holiday_dates = df_holiday['日期'].unique()
normal_total = df_daily[~df_daily['日期'].isin(holiday_dates)]['总计'].sum()
normal_days = df_daily[~df_daily['日期'].isin(holiday_dates)]['日期'].nunique()
normal_daily_avg = int(normal_total / normal_days) if normal_days > 0 else 0

output['chart3'] = {
    'holidays': holiday_agg['假期名称'].tolist(),
    'holiday_daily_avg': holiday_agg['daily_avg'].tolist(),
    'normal_daily_avg': normal_daily_avg,
    'holiday_hk_pct': (holiday_agg['hk'] / holiday_agg['total'] * 100).round(1).tolist(),
    'holiday_mainland_pct': (holiday_agg['mainland'] / holiday_agg['total'] * 100).round(1).tolist(),
    'holiday_other_pct': (holiday_agg['other'] / holiday_agg['total'] * 100).round(1).tolist(),
}

# ============================================================
# Chart 4: Economic ripple – passenger vs hotel vs restaurant vs retail
# ============================================================
# Passenger monthly total
passenger_monthly = df.groupby('年月')['总计'].sum().reset_index()
passenger_monthly.columns = ['年月', '旅客总量']

# Hotel occupancy
df_hotel = pd.read_csv('酒店房间月度入住率.csv')
df_hotel.columns = [c.strip().strip('"') for c in df_hotel.columns]
df_hotel['年月'] = df_hotel['年月'].astype(str).str.strip('"')
df_hotel['年月_fmt'] = df_hotel['年月'].str[:4] + '-' + df_hotel['年月'].str[4:6]
df_hotel['入住率'] = pd.to_numeric(df_hotel['酒店房间入住率(%)'].astype(str).str.strip('"'), errors='coerce')

# Hotel by category
df_hotel_cat = pd.read_csv('酒店房间入住率按类别.csv')
df_hotel_cat.columns = [c.strip().strip('"') for c in df_hotel_cat.columns]
df_hotel_cat['年月'] = df_hotel_cat['年月'].astype(str).str.strip('"')
df_hotel_cat['年月_fmt'] = df_hotel_cat['年月'].str[:4] + '-' + df_hotel_cat['年月'].str[4:6]
for c in df_hotel_cat.columns:
    if '入住率' in c:
        df_hotel_cat[c] = pd.to_numeric(df_hotel_cat[c].astype(str).str.strip('"'), errors='coerce')

# Restaurant revenue (monthly)
df_rest = pd.read_csv('食肆收益购货统计按月.csv', header=None, skiprows=5)
df_rest = df_rest.iloc[:, :3]
df_rest.columns = ['年', '月', '食肆收益']
df_rest = df_rest[df_rest['月'].notna() & (df_rest['月'] != '')]
df_rest['年'] = pd.to_numeric(df_rest['年'], errors='coerce')
df_rest['月'] = pd.to_numeric(df_rest['月'], errors='coerce')
df_rest = df_rest.dropna(subset=['年', '月'])
df_rest['年月_fmt'] = df_rest['年'].astype(int).astype(str) + '-' + df_rest['月'].astype(int).astype(str).str.zfill(2)
df_rest['食肆收益'] = pd.to_numeric(df_rest['食肆收益'], errors='coerce')

# Retail – extract total row (first data row = 衣物)
# The wide table is very complex; use yearly totals from the data
# We'll manually parse row 8 (衣物...) for the yearly totals, but better to get ALL categories' yearly total
# Actually, let's get the yearly totals for top-level categories from the wide table
df_retail_raw = pd.read_csv('零售业销货价值指数.csv', header=None)
# Row index 7 (0-based) = 衣物; row 10 = 珠宝
# The yearly total values are at columns 1,3,5,7,9 (value) for years 2021-2025
# Let's extract just the yearly retail total by summing main categories
retail_yearly = {}
years_retail = [2021, 2022, 2023, 2024, 2025]
# Main categories are rows 7, 10 in the CSV (0-indexed)
# But we need total retail, which is the sum. Let's just use the value columns for main categories.
# Actually, let's get clothing + jewelry yearly values as a proxy for retail health
row_clothing = df_retail_raw.iloc[7]  # 衣物
row_jewelry = df_retail_raw.iloc[10]  # 珠宝

# Yearly values are at positions 1, 3, 5, 7, 9
clothing_yearly = [pd.to_numeric(row_clothing.iloc[i], errors='coerce') for i in [1, 3, 5, 7, 9]]
jewelry_yearly = [pd.to_numeric(row_jewelry.iloc[i], errors='coerce') for i in [1, 3, 5, 7, 9]]

# Also extract monthly clothing values for finer granularity
# Monthly values start at column 11 (2021-Jan value), step by 2
clothing_monthly_vals = []
for i in range(11, 11 + 60*2, 2):  # 60 months (2021-2025)
    if i < len(row_clothing):
        clothing_monthly_vals.append(pd.to_numeric(row_clothing.iloc[i], errors='coerce'))
    else:
        clothing_monthly_vals.append(np.nan)

jewelry_monthly_vals = []
for i in range(11, 11 + 60*2, 2):
    if i < len(row_jewelry):
        jewelry_monthly_vals.append(pd.to_numeric(row_jewelry.iloc[i], errors='coerce'))
    else:
        jewelry_monthly_vals.append(np.nan)

retail_months = []
for y in range(2021, 2026):
    for m in range(1, 13):
        retail_months.append(f'{y}-{m:02d}')

# After 2025-12, add 2026 months if available
# Check if we have 2026 data in the CSV (columns 131, 133)
extra_months_count = 0
if 131 < len(row_clothing):
    val = pd.to_numeric(row_clothing.iloc[131], errors='coerce')
    if not pd.isna(val):
        clothing_monthly_vals.append(val)
        jewelry_monthly_vals.append(pd.to_numeric(row_jewelry.iloc[131], errors='coerce'))
        retail_months.append('2026-01')
        extra_months_count += 1
if 133 < len(row_clothing):
    val = pd.to_numeric(row_clothing.iloc[133], errors='coerce')
    if not pd.isna(val):
        clothing_monthly_vals.append(val)
        jewelry_monthly_vals.append(pd.to_numeric(row_jewelry.iloc[133], errors='coerce'))
        retail_months.append('2026-02')
        extra_months_count += 1

total_retail_monthly = [
    (c if not pd.isna(c) else 0) + (j if not pd.isna(j) else 0)
    for c, j in zip(clothing_monthly_vals, jewelry_monthly_vals)
]

# Service industry (quarterly)
df_svc = pd.read_csv('服务业收益指数.csv', header=None, skiprows=7)
df_svc = df_svc.iloc[:, :5]
df_svc.columns = ['年', '季', '零售', '住宿', '膳食']
df_svc = df_svc[df_svc['季'].notna() & (df_svc['季'] != '') & (df_svc['季'].astype(str).str.strip() != '')]
df_svc['年'] = pd.to_numeric(df_svc['年'].astype(str).str.replace(' p', '').str.strip(), errors='coerce')
df_svc['季'] = pd.to_numeric(df_svc['季'].astype(str).str.replace(' p', '').str.strip(), errors='coerce')
df_svc = df_svc.dropna(subset=['年', '季'])

quarter_month_map = {1: '02', 2: '05', 3: '08', 4: '11'}
df_svc['年月_fmt'] = df_svc['年'].astype(int).astype(str) + '-' + df_svc['季'].astype(int).map(quarter_month_map)

for c in ['零售', '住宿', '膳食']:
    df_svc[c] = pd.to_numeric(df_svc[c].astype(str).str.replace(' p', '').str.strip(), errors='coerce')

# Build aligned data
common_months = sorted(passenger_monthly['年月'].tolist())

hotel_dict = dict(zip(df_hotel['年月_fmt'], df_hotel['入住率']))
rest_dict = dict(zip(df_rest['年月_fmt'], df_rest['食肆收益']))
retail_dict = dict(zip(retail_months[:len(total_retail_monthly)], total_retail_monthly))

chart4_months = []
chart4_passengers = []
chart4_hotel = []
chart4_restaurant = []
chart4_retail = []

for m in common_months:
    chart4_months.append(m)
    chart4_passengers.append(int(passenger_monthly[passenger_monthly['年月'] == m]['旅客总量'].values[0]))
    chart4_hotel.append(float(hotel_dict.get(m, 'null')) if m in hotel_dict else None)
    chart4_restaurant.append(int(rest_dict[m]) if m in rest_dict else None)
    chart4_retail.append(int(retail_dict[m]) if m in retail_dict and not pd.isna(retail_dict[m]) else None)

# Hotel by category
hotel_cat_months = df_hotel_cat['年月_fmt'].tolist()
hotel_a = df_hotel_cat['甲级高价酒店房间入住率(%)'].tolist()
hotel_b = df_hotel_cat['乙级高价酒店房间入住率(%)'].tolist()
hotel_mid = df_hotel_cat['中价酒店房间入住率(%)'].tolist()

output['chart4'] = {
    'months': chart4_months,
    'passengers': chart4_passengers,
    'hotel_occupancy': chart4_hotel,
    'restaurant_revenue': chart4_restaurant,
    'retail_sales': chart4_retail,
    'hotel_cat_months': hotel_cat_months,
    'hotel_a': [float(x) if pd.notna(x) else None for x in hotel_a],
    'hotel_b': [float(x) if pd.notna(x) else None for x in hotel_b],
    'hotel_mid': [float(x) if pd.notna(x) else None for x in hotel_mid],
    'svc_months': df_svc['年月_fmt'].tolist(),
    'svc_retail': [float(x) if pd.notna(x) else None for x in df_svc['零售'].tolist()],
    'svc_accommodation': [float(x) if pd.notna(x) else None for x in df_svc['住宿'].tolist()],
    'svc_food': [float(x) if pd.notna(x) else None for x in df_svc['膳食'].tolist()],
}

# ============================================================
# Chart 5: Exchange rate vs mainland visitors
# ============================================================
df_fx = pd.read_csv('HKD_CNY历史数据.csv')
df_fx.columns = [c.strip().strip('"') for c in df_fx.columns]
for c in df_fx.columns:
    df_fx[c] = df_fx[c].astype(str).str.strip('"')

df_fx['收盘'] = pd.to_numeric(df_fx['收盘'], errors='coerce')
df_fx['涨跌幅_num'] = df_fx['涨跌幅'].str.replace('%', '').astype(float)

# Parse date and create YYYY-MM
df_fx['date_parsed'] = pd.to_datetime(df_fx['日期'], format='mixed')
df_fx['年月'] = df_fx['date_parsed'].dt.strftime('%Y-%m')
df_fx = df_fx.sort_values('年月')

# Mainland visitors monthly
mainland_monthly = df.groupby('年月')['内地访客'].sum().reset_index()
mainland_monthly.columns = ['年月', '内地访客']
mainland_monthly = mainland_monthly.sort_values('年月')

# Merge
fx_months = df_fx['年月'].tolist()
fx_close = df_fx['收盘'].tolist()

mainland_dict = dict(zip(mainland_monthly['年月'], mainland_monthly['内地访客']))

chart5_months = []
chart5_fx = []
chart5_mainland = []
for m, fx in zip(fx_months, fx_close):
    if m in mainland_dict:
        chart5_months.append(m)
        chart5_fx.append(float(fx))
        chart5_mainland.append(int(mainland_dict[m]))

# For scatter: compute YoY changes
mainland_yoy = {}
for i, m in enumerate(sorted(mainland_monthly['年月'])):
    prev_m = f'{int(m[:4])-1}{m[4:]}'
    if prev_m in mainland_dict and mainland_dict[prev_m] > 0:
        change = (mainland_dict[m] - mainland_dict[prev_m]) / mainland_dict[prev_m] * 100
        mainland_yoy[m] = round(change, 1)

fx_dict = dict(zip(df_fx['年月'], df_fx['涨跌幅_num']))

scatter_data = []
for m in mainland_yoy:
    if m in fx_dict:
        scatter_data.append({
            'month': m,
            'fx_change': round(fx_dict[m], 2),
            'mainland_change': mainland_yoy[m]
        })

output['chart5'] = {
    'months': chart5_months,
    'fx_rate': chart5_fx,
    'mainland_visitors': chart5_mainland,
    'scatter': scatter_data,
}

# ============================================================
# Chart 6: Checkpoint transport profile
# ============================================================
df_enhanced = pd.read_csv('passenger_vehicle_integrated_enhanced_cn.csv')

checkpoint_profile = df_enhanced.groupby('口岸').agg({
    '旅客总和': 'sum',
    '内地访客': 'sum',
    '私家车': 'sum',
    '旅游巴士': 'sum',
    '跨境穿梭巴士': 'sum',
    '货车及货柜车': 'sum',
}).reset_index()

checkpoint_profile = checkpoint_profile.sort_values('旅客总和', ascending=False)

# Time series for key checkpoints with vehicle data
has_vehicle = df_enhanced[df_enhanced['有车流数据'] == '是'] if '是' in df_enhanced['有车流数据'].values else df_enhanced[df_enhanced['私家车'] > 0]
vehicle_checkpoints = has_vehicle.groupby('口岸')['私家车'].sum()
vehicle_checkpoints = vehicle_checkpoints[vehicle_checkpoints > 0].index.tolist()

vehicle_ts = {}
for cp in vehicle_checkpoints:
    cp_data = df_enhanced[df_enhanced['口岸'] == cp].groupby(['年份', '月份']).agg({
        '私家车': 'sum', '旅游巴士': 'sum', '跨境穿梭巴士': 'sum', '货车及货柜车': 'sum'
    }).reset_index()
    cp_data['年月'] = cp_data['年份'].astype(str) + '-' + cp_data['月份'].astype(str).str.zfill(2)
    cp_data = cp_data.sort_values('年月')
    vehicle_ts[cp] = {
        'months': cp_data['年月'].tolist(),
        'private_cars': cp_data['私家车'].astype(int).tolist(),
        'tour_buses': cp_data['旅游巴士'].astype(int).tolist(),
        'shuttle_buses': cp_data['跨境穿梭巴士'].astype(int).tolist(),
        'trucks': cp_data['货车及货柜车'].astype(int).tolist(),
    }

output['chart6'] = {
    'checkpoints': checkpoint_profile['口岸'].tolist(),
    'passengers': checkpoint_profile['旅客总和'].astype(int).tolist(),
    'mainland': checkpoint_profile['内地访客'].astype(int).tolist(),
    'private_cars': checkpoint_profile['私家车'].astype(int).tolist(),
    'tour_buses': checkpoint_profile['旅游巴士'].astype(int).tolist(),
    'shuttle_buses': checkpoint_profile['跨境穿梭巴士'].astype(int).tolist(),
    'trucks': checkpoint_profile['货车及货柜车'].astype(int).tolist(),
    'vehicle_ts': vehicle_ts,
}

# ============================================================
# Chart 0 (Map): Checkpoint geo-located passenger pulse
# ============================================================
CP_CN_TO_EN = {
    '机场':         'Airport',
    '港珠澳大桥':   'HK-Zhuhai-Macao Bridge',
    '高铁西九龙':   'XRL West Kowloon',
    '红磡':         'Hung Hom',
    '罗湖':         'Lo Wu',
    '落马洲支线':   'Lok Ma Chau Spur Line',
    '落马洲':       'Lok Ma Chau',
    '文锦渡':       'Man Kam To',
    '沙头角':       'Sha Tau Kok',
    '深圳湾':       'Shenzhen Bay',
    '香园围':       'Heung Yuen Wai',
    '港澳客轮码头': 'HK-Macau Ferry Terminal',
    '中国客运码头': 'China Ferry Terminal',
    '屯门客运码头': 'Tuen Mun Ferry Terminal',
    '启德邮轮码头': 'Kai Tak Cruise Terminal',
    '港口管制':     'Harbour Control',
}

TYPE_CN_TO_EN = {
    '航空':       'Aviation',
    '港珠澳大桥': 'HK-Zhuhai-Macao Bridge',
    '高铁西九龙': 'XRL West Kowloon',
    '陆路':       'Land',
    '海路':       'Sea',
}

checkpoint_coords = {
    '机场':         [113.9185, 22.3080],
    '港珠澳大桥':   [113.9516, 22.3180],
    '高铁西九龙':   [114.1649, 22.3043],
    '红磡':         [114.1821, 22.3030],
    '罗湖':         [114.1136, 22.5297],
    '落马洲支线':   [114.0667, 22.5154],
    '落马洲':       [114.0745, 22.5096],
    '文锦渡':       [114.1318, 22.5362],
    '沙头角':       [114.2212, 22.5455],
    '深圳湾':       [113.9445, 22.4900],
    '香园围':       [114.1539, 22.5528],
    '港澳客轮码头': [114.1522, 22.2896],
    '中国客运码头': [114.1678, 22.3008],
    '屯门客运码头': [113.9662, 22.3721],
    '启德邮轮码头': [114.2128, 22.3069],
    '港口管制':     [114.1556, 22.2887],
}

checkpoint_types = {
    '机场':         '航空',
    '港珠澳大桥':   '港珠澳大桥',
    '高铁西九龙':   '高铁西九龙',
    '红磡':         '陆路',
    '罗湖':         '陆路',
    '落马洲支线':   '陆路',
    '落马洲':       '陆路',
    '文锦渡':       '陆路',
    '沙头角':       '陆路',
    '深圳湾':       '陆路',
    '香园围':       '陆路',
    '港澳客轮码头': '海路',
    '中国客运码头': '海路',
    '屯门客运码头': '海路',
    '启德邮轮码头': '海路',
    '港口管制':     '海路',
}

# Use the merged file that includes 2019-2020 data
df_map = pd.read_csv('日常旅客出入境统计_合并副本.csv')
map_months = sorted(df_map['年月'].unique().tolist())

map_data = {}
for m in map_months:
    month_df = df_map[df_map['年月'] == m]
    cp_agg = month_df.groupby('管制站').agg({
        '香港居民': 'sum', '内地访客': 'sum', '其他访客': 'sum', '总计': 'sum'
    }).reset_index()
    entries = []
    for _, row in cp_agg.iterrows():
        cp = row['管制站']
        if cp in checkpoint_coords:
            en_name = CP_CN_TO_EN.get(cp, cp)
            en_type = TYPE_CN_TO_EN.get(checkpoint_types.get(cp, ''), 'Other')
            entries.append({
                'name': en_name,
                'coord': checkpoint_coords[cp],
                'type': en_type,
                'total': int(row['总计']),
                'hk': int(row['香港居民']),
                'mainland': int(row['内地访客']),
                'other': int(row['其他访客']),
            })
    map_data[m] = entries

# Load detail data for map popup
# Source 1: passenger breakdown from merged file (covers 2019+)
df_pax = df_map
# Source 2: vehicle + growth rates (only covers 2021+)
df_detail = pd.read_csv('passenger_vehicle_integrated_enhanced_cn.csv', encoding='utf-8-sig')
df_detail['年月'] = df_detail['年份'].astype(str) + '-' + df_detail['月份'].astype(str).str.zfill(2)

def safe_val(v):
    if pd.isna(v):
        return None
    return round(float(v), 2) if isinstance(v, (float, np.floating)) else int(v)

map_detail = {}
for m in map_months:
    pax_m = df_pax[df_pax['年月'] == m]
    enh_m = df_detail[df_detail['年月'] == m]
    month_detail = {}
    for cp in checkpoint_coords:
        en_name = CP_CN_TO_EN.get(cp, cp)
        pax_cp = pax_m[pax_m['管制站'] == cp]
        pax_in = pax_cp[pax_cp['入境 / 出境'] == '入境']
        pax_out = pax_cp[pax_cp['入境 / 出境'] == '出境']
        enh_cp = enh_m[enh_m['口岸'] == cp]
        enh_in = enh_cp[enh_cp['出入境'] == '入境']
        enh_out = enh_cp[enh_cp['出入境'] == '出境']

        pi = pax_in.iloc[0] if not pax_in.empty else None
        po = pax_out.iloc[0] if not pax_out.empty else None
        ei = enh_in.iloc[0] if not enh_in.empty else None
        eo = enh_out.iloc[0] if not enh_out.empty else None

        if pi is None and po is None and ei is None and eo is None:
            continue

        entry = {
            'in_total': safe_val(pi['总计']) if pi is not None else None,
            'out_total': safe_val(po['总计']) if po is not None else None,
            'in_hk': safe_val(pi['香港居民']) if pi is not None else None,
            'out_hk': safe_val(po['香港居民']) if po is not None else None,
            'in_mainland': safe_val(pi['内地访客']) if pi is not None else None,
            'out_mainland': safe_val(po['内地访客']) if po is not None else None,
            'in_other': safe_val(pi['其他访客']) if pi is not None else None,
            'out_other': safe_val(po['其他访客']) if po is not None else None,
            'mainland_mom': safe_val(ei['内地访客环比增长%']) if ei is not None else None,
            'mainland_yoy': safe_val(ei['内地访客同比增长%']) if ei is not None else None,
            'total_mom': safe_val(ei['旅客总和环比增长%']) if ei is not None else None,
            'total_yoy': safe_val(ei['旅客总和同比增长%']) if ei is not None else None,
        }

        has_vehicle = ei is not None and str(ei['有车流数据']) == '是'
        if has_vehicle:
            v_in = {
                'car': safe_val(ei['私家车']) or 0,
                'tour': safe_val(ei['旅游巴士']) or 0,
                'shuttle': safe_val(ei['跨境穿梭巴士']) or 0,
                'freight': safe_val(ei['货车及货柜车']) or 0,
            }
            v_out = {
                'car': safe_val(eo['私家车']) if eo is not None else 0,
                'tour': safe_val(eo['旅游巴士']) if eo is not None else 0,
                'shuttle': safe_val(eo['跨境穿梭巴士']) if eo is not None else 0,
                'freight': safe_val(eo['货车及货柜车']) if eo is not None else 0,
            }
            entry['has_vehicle'] = True
            entry['private_cars'] = (v_in['car'] or 0) + (v_out['car'] or 0)
            entry['tour_coaches'] = (v_in['tour'] or 0) + (v_out['tour'] or 0)
            entry['shuttle_buses'] = (v_in['shuttle'] or 0) + (v_out['shuttle'] or 0)
            entry['freight_vehicles'] = (v_in['freight'] or 0) + (v_out['freight'] or 0)
            total_v = entry['private_cars'] + entry['tour_coaches'] + entry['shuttle_buses'] + entry['freight_vehicles']

            prev_m_str = (pd.Timestamp(m + '-01') - pd.DateOffset(months=1)).strftime('%Y-%m')
            prev_y_str = (pd.Timestamp(m + '-01') - pd.DateOffset(years=1)).strftime('%Y-%m')
            def _veh_total(ym):
                d2 = df_detail[(df_detail['年月'] == ym) & (df_detail['口岸'] == cp)]
                if d2.empty:
                    return None
                return int(d2[['私家车', '旅游巴士', '跨境穿梭巴士', '货车及货柜车']].sum().sum())
            prev_m_v = _veh_total(prev_m_str)
            prev_y_v = _veh_total(prev_y_str)
            entry['vehicle_mom'] = round((total_v - prev_m_v) / prev_m_v * 100, 2) if prev_m_v and prev_m_v > 0 else None
            entry['vehicle_yoy'] = round((total_v - prev_y_v) / prev_y_v * 100, 2) if prev_y_v and prev_y_v > 0 else None

        month_detail[en_name] = entry
    map_detail[m] = month_detail

# Build coords dict with English keys
coords_en = {CP_CN_TO_EN.get(k, k): v for k, v in checkpoint_coords.items()}

fx_sorted = df_fx[['年月', '收盘']].dropna().sort_values('年月')
fx_months = fx_sorted['年月'].tolist()
fx_rates = fx_sorted['收盘'].tolist()

flow_data = {}
for m in map_months:
    mdf = df_map[df_map['年月'] == m]
    dir_agg = mdf.groupby('入境 / 出境')['总计'].sum()
    inb = int(dir_agg.get('入境', 0))
    outb = int(dir_agg.get('出境', 0))
    flow_data[m] = {'inbound': inb, 'outbound': outb, 'total': inb + outb}

output['chart_map'] = {
    'months': map_months,
    'coords': coords_en,
    'data': map_data,
    'detail': map_detail,
    'fx': { 'months': fx_months, 'rates': fx_rates },
    'flow': flow_data,
}

# Write JSON
with open('viz_data.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print("Done! viz_data.json created.")
print(f"Chart1 months: {len(output['chart1']['months'])}")
print(f"Chart2 heatmap points: {len(output['chart2']['data'])}")
print(f"Chart3 holidays: {output['chart3']['holidays']}")
print(f"Chart4 months: {len(output['chart4']['months'])}")
print(f"Chart5 months: {len(output['chart5']['months'])}")
print(f"Chart6 checkpoints: {output['chart6']['checkpoints']}")
print(f"Map months: {len(output['chart_map']['months'])}, checkpoints: {len(checkpoint_coords)}")
