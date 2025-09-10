from utils import check_status
import tkinter as tk
from tkinter import messagebox

# 查询当前状态
status1 = check_status('NeuCom', stage='revision')

# 弹窗
message = f"{status1}\n{status1}"

root = tk.Tk()
root.withdraw()  # 隐藏主窗口
messagebox.showinfo("查询结果", message)