import pandas as pd
import numpy as np
from datetime import datetime
import os

# 设定工作目录
work_dir = r'd:\SYSU\Data Visualization\Group Project'
os.chdir(work_dir)

print("=" * 80)
print("任务1：处理日常旅客入出境统计，按月加和")
print("=" * 80)

# 1. 读取日常旅客入出境统计
df_passengers = pd.read_csv('日常旅客入出境统计.csv')
print("\n原始旅客数据形状:", df_passengers.shape)
print("\n原始数据示例:")
print(df_passengers.head(10))

# 转换日期格式
df_passengers['日期'] = pd.to_datetime(df_passengers['日期'], format='%d-%m-%Y')

# 按月、管制站、入境/出境进行加和
df_passengers['年月'] = df_passengers['日期'].dt.strftime('%Y-%m')

df_passengers_monthly = df_passengers.groupby(['年月', '管制站', '入境 / 出境']).agg({
    '香港居民': 'sum',
    '内地访客': 'sum',
    '其他访客': 'sum',
    '总计': 'sum'
}).reset_index()

print("\n按月聚合后的旅客数据形状:", df_passengers_monthly.shape)
print("\n聚合后数据示例:")
print(df_passengers_monthly.head(20))

# 保存按月聚合的旅客数据
df_passengers_monthly.to_csv('日常旅客入出境统计_月度.csv', index=False, encoding='utf-8-sig')
print("\n✓ 已保存：日常旅客入出境统计_月度.csv")

print("\n" + "=" * 80)
print("任务2：处理车辆流量数据，创建综合文件")
print("=" * 80)

# 2. 读取所有车辆流量数据
vehicle_files = {
    'table81a_sc.csv': 'MKT',  # 文锦渡
    'table81b_sc.csv': 'STK',  # 沙头角
    'table81e_sc.csv': 'HKZMB', # 港珠澳大桥
    'table81f_sc.csv': 'HYW',   # 香园围
    '深圳湾口岸车辆流量.csv': 'SZB',  # 深圳湾
    '落马洲口岸车辆流量.csv': 'LMC'   # 落马洲
}

# 定义口岸名称映射
crossing_names = {
    'MKT': '文锦渡',
    'STK': '沙头角',
    'LMC': '落马洲',
    'SZB': '深圳湾',
    'HKZMB': '港珠澳大桥',
    'HYW': '香园围'
}

# 定义行驶方向映射
direction_mapping = {
    'IB': '入境',
    'OB': '出境'
}

# 定义车辆种类名称
vehicle_types = {
    '1': '私家车',
    '23': '旅游巴士',
    '25': '跨境穿梭巴士',
    '36': '货车及货柜车'
}

# 读取和整合所有车辆流量数据
all_vehicle_data = []

for file, crossing_code in vehicle_files.items():
    if os.path.exists(file):
        df_vehicle = pd.read_csv(file)
        print(f"\n读取 {file}...")
        print(f"  数据形状: {df_vehicle.shape}")
        print(f"  关卡代码: {crossing_code}")
        
        # 添加关卡中文名称
        df_vehicle['关卡_中文'] = crossing_code
        all_vehicle_data.append(df_vehicle)
    else:
        print(f"\n警告：{file} 不存在")

# 合并所有车辆数据
df_all_vehicles = pd.concat(all_vehicle_data, ignore_index=True)
print(f"\n合并后的车辆数据形状: {df_all_vehicles.shape}")

# 转换年月格式为 YYYY-MM
df_all_vehicles['年月_formatted'] = df_all_vehicles['年月'].astype(str)
df_all_vehicles['年月_formatted'] = df_all_vehicles['年月_formatted'].str[:4] + '-' + df_all_vehicles['年月_formatted'].str[4:6]

print("\n车辆数据示例:")
print(df_all_vehicles.head(20))

print("\n" + "=" * 80)
print("任务3：创建综合数据表")
print("=" * 80)

# 3. 创建综合数据表
# 首先准备时间范围（从2021年1月开始）
date_range = pd.date_range(start='2021-01', end='2025-12', freq='M')
date_range_str = date_range.strftime('%Y-%m').tolist()

# 创建综合表的框架
# 每个月份、口岸、行驶方向的组合
combined_data = []

# 获取所有口岸列表（从2021年1月开始的数据）
valid_crossings = ['MKT', 'STK', 'LMC', 'SZB', 'HKZMB', 'HYW']

for year_month in date_range_str:
    for crossing in valid_crossings:
        for direction in ['入境', '出境']:
            row = {
                '日期': year_month,
                '口岸': crossing_names.get(crossing, crossing),
                '口岸代码': crossing,
                '出入境': direction,
            }
            
            # 添加旅客数据
            passenger_mask = (
                (df_passengers_monthly['年月'] == year_month) &
                (df_passengers_monthly['管制站'].isin([crossing_names.get(crossing, crossing)]))
            )
            
            # 对于旅客数据，需要按出入境方向过滤
            direction_mapping_reverse = {'入境': '入境', '出境': '出境'}
            passenger_mask = passenger_mask & (df_passengers_monthly['入境 / 出境'] == direction_mapping_reverse[direction])
            
            if passenger_mask.any():
                passenger_rows = df_passengers_monthly[passenger_mask]
                row['香港居民'] = passenger_rows['香港居民'].sum()
                row['内地访客'] = passenger_rows['内地访客'].sum()
                row['其他访客'] = passenger_rows['其他访客'].sum()
                row['旅客总和'] = passenger_rows['总计'].sum()
            else:
                row['香港居民'] = 0
                row['内地访客'] = 0
                row['其他访客'] = 0
                row['旅客总和'] = 0
            
            # 添加车辆数据
            vehicle_direction = '出境' if direction == '出境' else '入境'
            vehicle_mask = (
                (df_all_vehicles['年月_formatted'] == year_month) &
                (df_all_vehicles['关卡_中文'] == crossing) &
                (df_all_vehicles['行驶方向'] == ('OB' if direction == '出境' else 'IB'))
            )
            
            if vehicle_mask.any():
                vehicle_rows = df_all_vehicles[vehicle_mask]
                for vehicle_code, vehicle_name in vehicle_types.items():
                    vehicle_specific = vehicle_rows[vehicle_rows['车辆种类'] == int(vehicle_code)]
                    row[vehicle_name] = vehicle_specific['车流量'].sum() if not vehicle_specific.empty else 0
            else:
                for vehicle_name in vehicle_types.values():
                    row[vehicle_name] = 0
            
            combined_data.append(row)

# 创建综合数据框
df_combined = pd.DataFrame(combined_data)

# 重新排序列
column_order = [
    '日期', '口岸', '口岸代码', '出入境',
    '香港居民', '内地访客', '其他访客', '旅客总和',
    '私家车', '旅游巴士', '跨境穿梭巴士', '货车及货柜车'
]

df_combined = df_combined[column_order]

print("\n综合数据表形状:", df_combined.shape)
print("\n综合数据表示例:")
print(df_combined.head(20))

# 保存综合数据表
output_file = '综合旅客流量与车辆数据.csv'
df_combined.to_csv(output_file, index=False, encoding='utf-8-sig')
print(f"\n✓ 已保存：{output_file}")

# 显示统计信息
print("\n" + "=" * 80)
print("数据统计信息")
print("=" * 80)
print(f"\n综合表包含的时间范围：{df_combined['日期'].min()} 至 {df_combined['日期'].max()}")
print(f"包含的口岸数：{df_combined['口岸'].nunique()}")
print(f"包含的口岸列表：{', '.join(df_combined['口岸'].unique())}")
print(f"\n旅客总数（完整数据）：{df_combined['旅客总和'].sum():,.0f}")
print(f"车辆总数（完整数据）：{df_combined[['私家车', '旅游巴士', '跨境穿梭巴士', '货车及货柜车']].sum().sum():,.0f}")

# 按口岸统计
print("\n按口岸的旅客统计:")
station_summary = df_combined.groupby('口岸')[['香港居民', '内地访客', '其他访客', '旅客总和']].sum()
print(station_summary)

print("\n按口岸的车辆统计:")
vehicle_summary = df_combined.groupby('口岸')[['私家车', '旅游巴士', '跨境穿梭巴士', '货车及货柜车']].sum()
print(vehicle_summary)

print("\n" + "=" * 80)
print("处理完成！")
print("=" * 80)
import pandas as pd
import numpy as np
from datetime import datetime
import os
import glob

# 设置工作目录
work_dir = r"d:\SYSU\Data Visualization\Group Project"
os.chdir(work_dir)

# ============================================================================
# 任务1：处理日常旅客入出境统计，按月汇总
# ============================================================================

print("=" * 80)
print("任务1：处理日常旅客入出境统计，按月汇总")
print("=" * 80)

# 读取原始旅客数据
passenger_df = pd.read_csv('日常旅客入出境统计.csv')
print("\n原始旅客数据样本：")
print(passenger_df.head())
print(f"原始数据行数：{len(passenger_df)}")

# 转换日期格式
passenger_df['日期'] = pd.to_datetime(passenger_df['日期'], format='%d-%m-%Y')

# 提取年月
passenger_df['年月'] = passenger_df['日期'].dt.strftime('%Y-%m')

# 按年月、管制站、入境/出境进行分组汇总
monthly_passenger = passenger_df.groupby(['年月', '管制站', '入境 / 出境'])[
    ['香港居民', '内地访客', '其他访客', '总计']
].sum().reset_index()

monthly_passenger.columns = ['年月', '口岸', '流向', '香港居民', '内地访客', '其他访客', '总和']

print("\n按月汇总后的旅客数据样本：")
print(monthly_passenger.head(10))
print(f"汇总后数据行数：{len(monthly_passenger)}")

# 保存第一个任务的结果
monthly_passenger.to_csv('日常旅客入出境统计_月度汇总.csv', index=False, encoding='utf-8-sig')
print("\n✓ 已保存：日常旅客入出境统计_月度汇总.csv")

# ============================================================================
# 任务2：合并车流量数据
# ============================================================================

print("\n" + "=" * 80)
print("任务2：合并车流量数据")
print("=" * 80)

# 读取所有车流量数据
vehicle_files = [
    'table81a_sc.csv',
    'table81b_sc.csv', 
    'table81e_sc.csv',
    'table81f_sc.csv',
    '深圳湾口岸车辆流量.csv',
    '落马洲口岸车辆流量.csv'
]

vehicle_dfs = []
for file in vehicle_files:
    if os.path.exists(file):
        df = pd.read_csv(file)
        vehicle_dfs.append(df)
        print(f"✓ 已读取：{file} ({len(df)} 行)")

# 合并所有车流数据
vehicle_combined = pd.concat(vehicle_dfs, ignore_index=True)
print(f"\n合并后车流数据行数：{len(vehicle_combined)}")
print("\n车流数据结构：")
print(vehicle_combined.head())

# 数据清理：移除可能的引号
vehicle_combined.columns = vehicle_combined.columns.str.strip().str.strip('"')
for col in vehicle_combined.columns:
    if vehicle_combined[col].dtype == 'object':
        vehicle_combined[col] = vehicle_combined[col].str.strip().str.strip('"')

# 标准化列名
vehicle_combined.columns = ['关卡', '年月', '行驶方向', '车辆种类', '车流量']

print("\n清理后的车流数据样本：")
print(vehicle_combined.head())

# ============================================================================
# 任务3：创建合并表
# ============================================================================

print("\n" + "=" * 80)
print("任务3：创建合并表")
print("=" * 80)

# 口岸映射关系（从车流数据的关卡代码到旅客统计的口岸名称）
# 旅客统计中的口岸：机场、港珠澳大桥、罗湖、高铁西九龙、红磡等
# 车流数据中的关卡：MKT(文锦渡)、STK(沙头角)、LMC(落马洲)、SZB(深圳湾)、HKZMB(港珠澳大桥)、HYW(香园围)

gateway_mapping = {
    'MKT': '文锦渡',
    'STK': '沙头角',
    'LMC': '落马洲',
    'SZB': '深圳湾',
    'HKZMB': '港珠澳大桥',
    'HYW': '香园围'
}

# 转换关卡名称
vehicle_combined['关卡'] = vehicle_combined['关卡'].astype(str).str.strip()
vehicle_combined['口岸'] = vehicle_combined['关卡'].map(gateway_mapping)

# 转换行驶方向
vehicle_combined['流向'] = vehicle_combined['行驶方向'].map({
    'IB': '入境',
    'OB': '出境'
})

# 转换年月格式（从YYYYMM到YYYY-MM）
vehicle_combined['年月'] = pd.to_datetime(
    vehicle_combined['年月'].astype(str), 
    format='%Y%m'
).dt.strftime('%Y-%m')

# 车辆种类映射
vehicle_type_mapping = {
    '1': '私家车',
    '23': '旅游巴士',
    '25': '跨境穿梭巴士',
    '36': '货车及货柜车'
}

vehicle_combined['车辆种类'] = vehicle_combined['车辆种类'].astype(str).str.strip().map(vehicle_type_mapping)
vehicle_combined['车流量'] = pd.to_numeric(vehicle_combined['车流量'], errors='coerce')

print("\n转换后的车流数据样本：")
print(vehicle_combined.head(10))

# 创建透视表将车流量按车辆种类列组
vehicle_pivot = vehicle_combined.pivot_table(
    index=['年月', '口岸', '流向'],
    columns='车辆种类',
    values='车流量',
    aggfunc='sum'
).reset_index()

vehicle_pivot.columns.name = None
print("\n车流数据透视表样本：")
print(vehicle_pivot.head())

# 填充缺失值为0
for col in ['私家车', '旅游巴士', '跨境穿梭巴士', '货车及货柜车']:
    if col in vehicle_pivot.columns:
        vehicle_pivot[col] = vehicle_pivot[col].fillna(0).astype(int)

# ============================================================================
# 创建最终综合表
# ============================================================================

print("\n" + "=" * 80)
print("创建最终综合表")
print("=" * 80)

# 首先筛选出从2021年1月开始的数据
min_date = '2021-01'
vehicle_pivot = vehicle_pivot[vehicle_pivot['年月'] >= min_date]

# 与旅客数据合并
# 但要注意：旅客数据和车流数据的口岸不完全对应
# 先创建仅包含车流数据的表

final_table = vehicle_pivot.copy()
final_table = final_table.sort_values(['年月', '口岸', '流向']).reset_index(drop=True)

# 添加旅客数据（基于相同的年月和流向）
# 注意：旅客数据的管制站和车流数据的口岸不完全一致
# 需要创建一个映射关系

# 旅客统计中的口岸
print("\n旅客统计数据中的口岸：")
print(passenger_df['管制站'].unique())

print("\n车流数据中的关卡（映射后）：")
print(vehicle_combined['口岸'].unique())

# 为了创建完整的综合表，我们需要考虑两个数据源的所有信息
# 策略：创建一个包含所有关键字段的表

# 首先获取旅客数据中的所有口岸
all_gateways_passenger = passenger_df['管制站'].unique()
final_structure = []

# 遍历所有可能的年月范围（2021年1月到最后一个数据点）
date_range = pd.date_range(start='2021-01', periods=len(pd.period_range(start='2021-01', freq='M')), freq='M')

# 获取数据范围
min_passenger_date = passenger_df['年月'].min()
max_passenger_date = passenger_df['年月'].max()
min_vehicle_date = vehicle_pivot['年月'].min() if len(vehicle_pivot) > 0 else None
max_vehicle_date = vehicle_pivot['年月'].max() if len(vehicle_pivot) > 0 else None

print(f"\n旅客数据时间范围：{min_passenger_date} 至 {max_passenger_date}")
print(f"车流数据时间范围：{min_vehicle_date} 至 {max_vehicle_date}")

# 创建综合表：左表是旅客数据，右表通过join添加车流数据
# 此外，我们需要为没有旅客数据对应的车流口岸单独列出

# 首先处理旅客数据
combined_result = monthly_passenger.copy()
combined_result = combined_result[combined_result['年月'] >= '2021-01']

# 标准化列名以便合并
combined_result.columns = ['年月', '口岸', '流向', '香港居民', '内地访客', '其他访客', '旅客总和']

# 然后处理车流数据
# 由于口岸名称不对应，我们创建两部分表

# 第一部分：有对应关系的数据（基于口岸名称匹配）
# 第二部分：纯车流数据（不需要与旅客数据对应）

# 简化方案：创建一个包含所有可用信息的综合表
# 对于旅客数据的口岸，添加车流信息（如果有的话）
# 对于纯车流数据的口岸，单独列出

# 创建旅客数据的基础表
result_with_passenger = combined_result.copy()

# 尝试与车流数据通过口岸名称合并
result_merged = result_with_passenger.merge(
    vehicle_pivot,
    on=['年月', '口岸', '流向'],
    how='left'
)

# 填充缺失值
for col in ['私家车', '旅游巴士', '跨境穿梭巴士', '货车及货柜车']:
    if col in result_merged.columns:
        result_merged[col] = result_merged[col].fillna(0).astype(int)

# 添加纯车流数据（只有车流，没有旅客数据的记录）
vehicle_only = vehicle_pivot[
    ~vehicle_pivot[['年月', '口岸', '流向']].apply(tuple, axis=1).isin(
        result_merged[['年月', '口岸', '流向']].apply(tuple, axis=1)
    )
].copy()

if len(vehicle_only) > 0:
    vehicle_only_expanded = vehicle_only.copy()
    vehicle_only_expanded['香港居民'] = 0
    vehicle_only_expanded['内地访客'] = 0
    vehicle_only_expanded['其他访客'] = 0
    vehicle_only_expanded['旅客总和'] = 0
    
    # 重新排列列序
    vehicle_only_expanded = vehicle_only_expanded[[
        '年月', '口岸', '流向', '香港居民', '内地访客', '其他访客', '旅客总和',
        '私家车', '旅游巴士', '跨境穿梭巴士', '货车及货柜车'
    ]]
    
    result_merged = pd.concat([result_merged, vehicle_only_expanded], ignore_index=True)

# 填充缺失的车流列
for col in ['私家车', '旅游巴士', '跨境穿梭巴士', '货车及货柜车']:
    if col not in result_merged.columns:
        result_merged[col] = 0
    else:
        result_merged[col] = result_merged[col].fillna(0).astype(int)

# 排序
result_merged = result_merged.sort_values(['年月', '口岸', '流向']).reset_index(drop=True)

# 重新命名列
final_columns = ['年月', '口岸', '流向', '香港居民', '内地访客', '其他访客', '旅客总和',
                 '私家车', '旅游巴士', '跨境穿梭巴士', '货车及货柜车']

result_merged = result_merged[[col for col in final_columns if col in result_merged.columns]]

print("\n最终综合表样本：")
print(result_merged.head(20))
print(f"\n最终综合表行数：{len(result_merged)}")
print(f"时间范围：{result_merged['年月'].min()} 至 {result_merged['年月'].max()}")
print(f"口岸数量：{result_merged['口岸'].nunique()}")
print(result_merged['口岸'].unique())

# 保存最终表
result_merged.to_csv('香港入出境及车流综合统计_月度_2021起.csv', index=False, encoding='utf-8-sig')
print("\n✓ 已保存：香港入出境及车流综合统计_月度_2021起.csv")

print("\n" + "=" * 80)
print("处理完成！生成了两个新文件：")
print("1. 日常旅客入出境统计_月度汇总.csv - 旅客月度汇总数据")
print("2. 香港入出境及车流综合统计_月度_2021起.csv - 旅客+车流综合数据")
print("=" * 80)
