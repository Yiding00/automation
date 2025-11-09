from utils import check_status
import tkinter as tk
from tkinter import messagebox

# 查询当前状态
# stage:
#   init: 初次提交
#   revision: 返修

status2 = check_status('MedIA', stage='init')
status1 = check_status('NeuCom', stage='revision')

# 弹窗
message = f"{status1}\n{status2}"

root = tk.Tk()
root.withdraw()  # 隐藏主窗口
messagebox.showinfo("查询结果", message)