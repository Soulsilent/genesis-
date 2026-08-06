import tkinter as tk
from tkinter import ttk


class UIHelper:
    """UI助手类 - 提供常用的弹窗功能"""
    
    @staticmethod
    def selectOption(title="选择", label="请选择:", options=None):
        """
        下拉选择弹窗
        
        :param title: 窗口标题
        :param label: 提示文本
        :param options: 选项列表
        :return: 选中的字符串，取消返回None
        调用方法例子
        choice = genesis_ui.UIHelper.selectOption(
                title="颜色选择",
                label="选择颜色:",
                options=["红色", "绿色", "蓝色", "黄色"]
                )
        if choice:
            print(f"你选择了: {choice}")
        """
        if options is None:
            options = ["选项1", "选项2", "选项3"]
        
        result = [None]
        
        def confirm():
            result[0] = combo.get()
            root.destroy()
        
        root = tk.Tk()
        root.title(title)
        root.geometry("280x120")
        root.resizable(False, False)
        
        tk.Label(root, text=label, font=("微软雅黑", 10)).pack(pady=(15, 5))
        
        combo = ttk.Combobox(root, values=options, state="readonly", width=28)
        combo.pack(pady=5)
        combo.current(0)
        
        tk.Button(root, text="确定", command=confirm, width=10, bg="#4CAF50", fg="white").pack(pady=10)
        
        root.bind('<Return>', lambda e: confirm())
        root.mainloop()
        
        return result[0]
