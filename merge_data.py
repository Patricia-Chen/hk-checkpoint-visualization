import pandas as pd
import numpy as np
from datetime import datetime
import os

# 设定工作目录
work_dir = r'd:\SYSU\Data Visualization\Group Project\hk-checkpoint-visualization'
os.chdir(work_dir)

print("=" * 80)
print("合并港口岸人员流量2019-2021到日常旅客入出境统计")
print("=" * 80)

# 1. 读取港口岸人员流量数据
df_port = pd.read_csv('港口岸人员流量.csv')
print("\n港口岸数据形状:", df_port.shape)
print("\n港口岸数据示例:")
print(df_port.head(10))

# 过滤2019-2021年
df_port['年'] = df_port['年月'].astype(str).str[:4].astype(int)
df_port_filtered = df_port[(df_port['年'] >= 2019) & (df_port['年'] <= 2021)]
print("\n过滤后2019-2021数据形状:", df_port_filtered.shape)

# 关口代码映射到中文
crossing_mapping = {
    'AIR': '机场',
    'CFT': '中国客运码头',
    'HARB': '港口管制',
    'MFT': '港澳客轮码头',
    'TMFT': '屯门客运码头',
    'STK': '沙头角',  # 启德邮轮码头? 但STK是沙头角，日常有沙头角
    'MKT': '文锦渡',
    'LMC': '落马洲',
    'LWT': '落马洲支线',
    'SZB': '深圳湾',
    'HHS': '红磡',
    'RTT': '罗湖',
    'LMCSL': '落马洲支线'
}

# 映射关口
df_port_filtered['管制站'] = df_port_filtered['关口'].map(crossing_mapping)

# 过滤掉未映射的
df_port_filtered = df_port_filtered.dropna(subset=['管制站'])

# 映射方向
direction_mapping = {
    'AV': '入境',
    'DB': '出境'
}
df_port_filtered['入境 / 出境'] = df_port_filtered['抵港或离港'].map(direction_mapping)

# 创建年月格式 YYYY-MM
df_port_filtered['年月'] = df_port_filtered['年月'].astype(str).str[:4] + '-' + df_port_filtered['年月'].astype(str).str[4:]

# 重命名人次为总计
df_port_filtered = df_port_filtered.rename(columns={'人次': '总计'})

# 添加缺失列，设为0
df_port_filtered['香港居民'] = 0
df_port_filtered['内地访客'] = 0
df_port_filtered['其他访客'] = 0

# 选择需要的列
df_port_processed = df_port_filtered[['年月', '管制站', '入境 / 出境', '香港居民', '内地访客', '其他访客', '总计']]

print("\n处理后的港口岸数据示例:")
print(df_port_processed.head(10))

# 2. 读取日常旅客入出境统计月度数据
if os.path.exists('日常旅客入出境统计_月度.csv'):
    df_daily_monthly = pd.read_csv('日常旅客入出境统计_月度.csv')
    print("\n读取现有月度数据形状:", df_daily_monthly.shape)
else:
    # 如果不存在，生成
    df_daily = pd.read_csv('日常旅客入出境统计.csv')
    df_daily['日期'] = pd.to_datetime(df_daily['日期'], format='%d-%m-%Y')
    df_daily['年月'] = df_daily['日期'].dt.strftime('%Y-%m')
    df_daily_monthly = df_daily.groupby(['年月', '管制站', '入境 / 出境']).agg({
        '香港居民': 'sum',
        '内地访客': 'sum',
        '其他访客': 'sum',
        '总计': 'sum'
    }).reset_index()
    print("\n生成月度数据形状:", df_daily_monthly.shape)

print("\n日常月度数据示例:")
print(df_daily_monthly.head(10))

# 3. 合并数据
# 对于2019-2021，使用港口岸数据替换日常数据（如果有冲突）
# 首先，过滤日常数据排除2019-2021
df_daily_other = df_daily_monthly[~((df_daily_monthly['年月'].str[:4].astype(int) >= 2019) & (df_daily_monthly['年月'].str[:4].astype(int) <= 2021))]

# 合并
df_merged = pd.concat([df_daily_other, df_port_processed], ignore_index=True)

# 排序
df_merged = df_merged.sort_values(['年月', '管制站', '入境 / 出境'])

print("\n合并后数据形状:", df_merged.shape)
print("\n合并后数据示例:")
print(df_merged.head(20))

# 4. 保存副本文件
output_file = '日常旅客出入境统计_合并副本.csv'
df_merged.to_csv(output_file, index=False, encoding='utf-8-sig')
print(f"\n✓ 已保存副本文件：{output_file}")