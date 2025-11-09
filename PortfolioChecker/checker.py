import pandas as pd
from data_utils.Ashare import *
from data_utils.utils import get_fund_price
from my_assets import assets_info, target_ratio, target_ratio_sub
from datetime import datetime

output_file = "output.txt"

# === 获取现有价值 ===
A = {}
for name, (code, _, source, units, _) in assets_info.items():
    if source == "fund":
        A[name] = get_fund_price(code, count=1)
    elif source == "etf":
        A[name] = get_price(code, frequency="5m", count=1)

current_values = {}
for name, (_, cname, source, units, _) in assets_info.items():
    if source == "cash":
        current_values[name] = units
    else:
        latest_price = A[name]["close"].iloc[-1]
        current_values[name] = units * latest_price

# === 转换成 DataFrame ===
df = pd.DataFrame.from_dict(assets_info, orient="index",
    columns=["代码", "渠道", "类型", "持有份额", "分类"])
df["现有价值"] = [current_values[k] for k in df.index]
df[["大类","小类"]] = df["分类"].str.split("-", expand=True)

# === 总资产 ===
total_value = df["现有价值"].sum()


# === 小类汇总 ===
sub_summary = df.groupby("分类")["现有价值"].sum()
sub_diff = {}
sub_diff_ratio = {}
for k, tar in target_ratio_sub.items():
    target_value = total_value * tar
    actual_value = sub_summary.get(k, 0)
    sub_diff[k] = actual_value - target_value
    sub_diff_ratio[k] = sub_diff[k]/target_value * 100

# === 大类汇总 ===
cls_summary = df.groupby("大类")["现有价值"].sum()
cls_diff = {}
cls_diff_ratio = {}
for k, tar in target_ratio.items():
    target_value = total_value * tar
    actual_value = cls_summary.get(k, 0)
    cls_diff[k] = actual_value - target_value
    cls_diff_ratio[k] = cls_diff[k]/target_value * 100


output_file = "portfolio.txt"

# 列宽
col1, col2, col3, col4 = 12, 25, 25, 25

with open(output_file, "w", encoding="utf-8") as f:
    now = datetime.now()
    f.write(str(now.strftime("%Y-%m-%d %H:%M:%S")))
    # === 各小类 ===
    f.write("\n— 各小类 —\n")
    f.write(f"{'分类':<{col1+4}}{'现有':<{col2-2}}{'目标':<{col3-2}}{'差额':<{col4-5}}\n")
    f.write("-" * (col1 + col2 + col3 + col4) + "\n")

    for k, v in sub_summary.items():
        tar_ratio = target_ratio_sub[k] * 100
        tar_value = total_value * target_ratio_sub[k]
        current_ratio = v / total_value * 100
        diff_val = sub_diff[k]
        diff_ratio = sub_diff_ratio[k]

        current_str = f"{v:.2f} ({current_ratio:.2f}%)"
        target_str  = f"{tar_value:.2f} ({tar_ratio:.2f}%)"
        if diff_ratio > 20 or diff_ratio < -20:
            diff_str    = f"{diff_val:.2f} [{diff_ratio:.2f}%]!!!!"
        elif diff_ratio > 15 or diff_ratio < -15:
            diff_str    = f"{diff_val:.2f} [{diff_ratio:.2f}%]!"
        else:
            diff_str    = f"{diff_val:.2f} ({diff_ratio:.2f}%)"


        f.write(f"{k:<{col1}}{current_str:<{col2}}{target_str:<{col3}}{diff_str:<{col4}}\n")

    # === 各大类 ===
    f.write("\n— 各大类 —\n")
    f.write(f"{'分类':<{col1}}{'现有':<{col2-2}}{'目标':<{col3-2}}{'差额':<{col4}}\n")
    f.write("-" * (col1 + col2 + col3 + col4) + "\n")

    for k, v in cls_summary.items():
        tar_ratio = target_ratio[k] * 100
        tar_value = total_value * target_ratio[k]
        current_ratio = v / total_value * 100
        diff_val = cls_diff[k]
        diff_ratio = cls_diff_ratio[k]

        current_str = f"{v:.2f} ({current_ratio:.2f}%)"
        target_str  = f"{tar_value:.2f} ({tar_ratio:.2f}%)"
        if diff_ratio > 15 or diff_ratio < -15:
            diff_str    = f"{diff_val:.2f} [{diff_ratio:.2f}%]"
        else:
            diff_str    = f"{diff_val:.2f} ({diff_ratio:.2f}%)"


        f.write(f"{k:<{col1}}{current_str:<{col2}}{target_str:<{col3}}{diff_str:<{col4}}\n")

    # === 总资产 ===
    f.write(f"\n投资组合总价值: {total_value:.2f}\n")

    # === 计算 ETF 调仓建议 ===
    adjust = {}

    f.write("\n— 每月固定投入400，奖金投入80% —\n")
    f.write("\n— 按大类差额进行调仓，若差距大于20%再主动调 —\n")

    for k, v in sub_summary.items():
        diff_ratio = sub_diff_ratio[k]
        if diff_ratio > 0:
            for name, (code, cname, source, units, cls) in assets_info.items():
                if source == "fund" and cls == k:
                # if cls == k:
                    latest_price = A[name]["close"].iloc[-1]
                    # 小类目标差额
                    diff_val = sub_diff.get(k, 0)
                    
                    # 计算需要买入/卖出份额
                    shares_to_adjust = -diff_val / latest_price

                    if shares_to_adjust != 0:
                        adjust[name] = {
                            "代码": code,
                            "现价": latest_price,
                            "持仓份额": units,
                            "目标调整份额": int(shares_to_adjust*100)/100,
                            "目标调整手数": int(shares_to_adjust*100)/100,
                            "调整金额": int(shares_to_adjust*100)/100 * latest_price,
                            "所属小类": k
                        }
                    break

        if diff_ratio < 0:
            for name, (code, cname, source, units, cls) in assets_info.items():
                if source == "etf" and cls == k:
                    latest_price = A[name]["close"].iloc[-1]
                    # 小类目标差额
                    diff_val = sub_diff.get(k, 0)
                    
                    # 计算需要买入/卖出份额
                    shares_to_adjust = -diff_val / latest_price
                    lots_to_adjust = int(shares_to_adjust / 100)  # 换算成手数，取整

                    if lots_to_adjust != 0:
                        adjust[name] = {
                            "代码": code,
                            "现价": latest_price,
                            "持仓份额": units,
                            "目标调整份额": int(lots_to_adjust * 100),
                            "目标调整手数": lots_to_adjust,
                            "调整金额": lots_to_adjust * 100 * latest_price,
                            "所属小类": k
                        }
                    break


    # === 写入输出文件 ===
    f.write("\n— 资产调仓建议 —\n")
    if not adjust:
        f.write("所有资产已满足目标比例，无需调整。\n")
    else:
        f.write(f"{'代码':<10}{'现价':<10}{'调整手数':<10}{'调整金额':<15}{'小类':<10}\n")
        f.write("-" * 70 + "\n")
        for name, info in adjust.items():
            f.write(f"{info['代码']:<12}{info['现价']:<12.2f}"
                    f"{info['目标调整手数']:<14}{info['调整金额']:<19.2f}{info['所属小类']:<10}\n")
