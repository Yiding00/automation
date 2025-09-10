from data_utils.Ashare import *
import pandas as pd

# 以往数据测试
f = '30m' # '1m','5m','15m','30m','60m', 1d, 1w, 1M
timepoints = 10

A={}
A_scaled={}
A[1] = get_price('sz159934',frequency=f,count=timepoints) # 黄金
A[0] = get_price('sh511010',frequency=f,count=timepoints) # 债券
A[2] = get_price('sh513500',frequency=f,count=timepoints) # 标普500
A[3] = get_price('sh000300',frequency=f,count=timepoints) # 沪深300
A[4] = get_price('sz399006',frequency=f,count=timepoints) # 创业板
A[5] = get_price('sz164824',frequency=f,count=timepoints) # 印度指数

p = [0.4,0.2,0.1,0.1,0.1,0.1] # 资产比例

A_scaled[0] = A[0].div(A[0].iloc[0])
A_scaled[1] = A[1].div(A[1].iloc[0])
A_scaled[2] = A[2].div(A[2].iloc[0])
A_scaled[3] = A[3].div(A[3].iloc[0])
A_scaled[4] = A[4].div(A[4].iloc[0])
A_scaled[5] = A[5].div(A[5].iloc[0])

portfolio = sum(a * b for a, b in zip(A_scaled.values(), p))

# print(portfolio['close'])

asset_names = {
    0: "债券",
    1: "黄金",
    2: "标普500",
    3: "沪深300",
    4: "创业板",
    5: "印度指数"
}

# 提取每个资产的 close 列，并用中文名字重命名
close_dfs = [A[i]['close'].rename(asset_names[i]) for i in range(6)]
close_df = pd.concat(close_dfs, axis=1).round(6)

df = pd.read_csv("output.txt", sep="|")
last_row = df.tail(1)

# 今天日期（取 close_df 的最后一天作为基准）
now = close_df.index[-2]

# 检查是否已经有今天的数据
last_date = pd.to_datetime(last_row.iloc[0, 0])
if str(last_date) == str(now):
    print(f"✅ {now} 已经计算过，不再重复追加。")
else:
    # 取 close_df 最近两天
    prev_close = close_df.loc[last_date]
    today_close = close_df.loc[now]

    # 计算比例
    ratio = today_close / prev_close

    # 计算今天的资产（去掉第一列日期，只算资产部分）
    new_assets = last_row.iloc[0, 1:-1] * ratio.values

    # 拼接成新的 row
    new_row = pd.DataFrame([[now.strftime("%Y-%m-%d %H:%M:%S")] + new_assets.round(2).tolist() + [new_assets.sum().round(2)]],
                       columns=last_row.columns)

    filename = "output.txt"
    with open(filename, "a", encoding="utf-8") as f:
        # 写数据
        f.write("{:<19} | ".format(now.strftime("%Y-%m-%d %H:%M:%S")))
        for val in new_assets:
            f.write("{:<8} | ".format(val.round(2)))
        f.write("{:<8}\n".format(new_assets.sum().round(2)))


    print("✅ 已添加新的一行：")
    print(new_row)


import numpy as np
import tkinter as tk
from tkinter import messagebox

df = pd.read_csv("output.txt", sep="|")
last_row = df.tail(1)
# 今天日期（取 close_df 的最后一天作为基准）
now = close_df.index[-1]

# 检查是否已经有今天的数据
last_date = pd.to_datetime(last_row.iloc[0, 0])

# 取 close_df 最近两天
prev_close = close_df.loc[last_date]
today_close = close_df.loc[now]

# 计算比例
ratio = today_close / prev_close

# 计算今天的资产（去掉第一列日期，只算资产部分）
new_assets = last_row.iloc[0, 1:-1] * ratio.values

# 拼接成新的 row
new_row = pd.DataFrame([[now.strftime("%Y-%m-%d %H:%M:%S")] + new_assets.round(2).tolist() + [new_assets.sum().round(2)]],
                       columns=last_row.columns)

assets = new_row.to_numpy()[0, 1:-1]

ratio = assets / np.sum(assets)
# ratio = np.floor(ratio*1e4)/1e4

diff_ratio = (ratio - p) / p
diff_ratio = np.floor(diff_ratio*1e4)/1e4

print(now)

# 转换为百分比
diff_percentage = diff_ratio * 100

# 构建弹窗内容
message_lines = []
message_lines.append(str(now))

# 每个资产的差距百分比
for idx, diff in enumerate(diff_percentage):
    message_lines.append(f"{asset_names[idx]}: {diff:.2f}%")

# 差距超过20%的资产
exceed_idx = [idx for idx, diff in enumerate(diff_ratio) if np.abs(diff) > 0.2]
if exceed_idx:
    message_lines.append("\n差距超过20%的资产：")
    for idx in exceed_idx:
        current = assets[idx]
        target = np.sum(assets) * p[idx]
        message_lines.append(f"{asset_names[idx]} 当前值={current:.2f}, 目标值={target:.2f}, 差额={current - target:.2f}")
else:
    message_lines.append("\n✅ 所有资产均在合理范围内（偏差≤20%）")


root = tk.Tk()
root.withdraw()  # 隐藏主窗口
messagebox.showinfo("资产差距报告", "\n".join(message_lines))