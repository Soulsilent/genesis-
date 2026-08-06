import os
from datetime import datetime

import win32gui

from PyQt5.QtWidgets import (QWidget, QVBoxLayout,
                             QTreeWidget, QTreeWidgetItem, QPushButton, QLabel, QHBoxLayout,
                             QStatusBar, QTabWidget)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWinExtras import QtWin


class ToolButton(QPushButton):
    """顶部工具栏按钮 - 图标在上，文字在下"""

    def __init__(self, icon_text, label_text):
        super().__init__()
        self.setFixedHeight(50)
        self.setFixedWidth(36)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(1)

        icon_label = QLabel(icon_text)
        icon_label.setFont(QFont("SimSun", 14))
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)

        text_label = QLabel(label_text)
        text_label.setFont(QFont("SimSun", 8))
        text_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(text_label)

        self.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #D6E8FF;
                border-radius: 2px;
            }
            QPushButton:pressed {
                background-color: #B8D4F0;
            }
        """)


def get_exe_icon(exe_path, size=(32, 32)):
    """从exe文件提取内置图标，返回QIcon对象
    
    Args:
        exe_path: exe文件绝对路径
        size: 目标图标尺寸 (width, height)，默认32x32
    
    Returns:
        QIcon对象，失败返回None
    """
    try:
        if not os.path.isfile(exe_path):
            return None

        # 提取大图标句柄 (index=0 为第一个图标组)
        large_icons, _ = win32gui.ExtractIconEx(exe_path, 0)
        if not large_icons:
            return None

        hicon = large_icons[0]
        # HICON -> QPixmap（QtWin自动处理32位含Alpha通道的图标）
        pixmap = QtWin.fromHICON(hicon)
        # 缩放到目标尺寸，保持宽高比，平滑变换
        pixmap = pixmap.scaled(
            size[0], size[1],
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        # 释放Windows图标资源
        win32gui.DestroyIcon(hicon)

        return QIcon(pixmap)
    except Exception:
        return None


class Ui_CAMGuideWindow(object):
    """CAM Guide UI 类"""

    def setupUi(self, MainWindow):
        """设置 UI"""
        MainWindow.setWindowTitle("深圳市天翼通电子-CAM Guide")
        MainWindow.resize(323, 700)

        # --- 主容器 ---
        self.centralWidget = QWidget(MainWindow)
        self.mainLayout = QVBoxLayout(self.centralWidget)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setSpacing(0)

        # --- 顶部工具栏 ---
        self.topBar = QWidget()
        self.topBar.setStyleSheet("background-color: #F0F0F0; border-bottom: 1px solid #CCCCCC;")
        self.topLayout = QHBoxLayout(self.topBar)
        self.topLayout.setContentsMargins(2, 2, 2, 2)
        self.topLayout.setSpacing(1)

        tools = [
            ("🔍", "搜索"), ("🖥", "AI"), ("☰", "工具"),("翻", "翻译"),
            ("📷", "截图"), ("📦️", "SAVE"), ("↔", "mini"), ("↻", "Exit")
        ]
        for icon, txt in tools:
            btn = ToolButton(icon, txt)
            self.topLayout.addWidget(btn)

        self.topLayout.addStretch()

        self.logo = QLabel("G")
        self.logo.setFont(QFont("SimSun", 16, QFont.Bold))
        self.logo.setStyleSheet("color: #CC0000; border: 2px solid #CC0000; border-radius: 8px; padding: 2px 6px;")
        self.topLayout.addWidget(self.logo)

        # --- JOB/STEP 信息栏 ---
        self.infoBar = QWidget()
        self.infoBar.setStyleSheet("background-color: #E8F4FF; border-bottom: 1px solid #CCCCCC;")
        self.infoLayout = QHBoxLayout(self.infoBar)
        self.infoLayout.setContentsMargins(8, 2, 8, 2)

        self.jobLabel = QLabel("JOB  r2n12771v1")
        self.jobLabel.setFont(QFont("SimSun", 9, QFont.Bold))
        self.jobLabel.setStyleSheet("color: #0000FF;")
        self.infoLayout.addWidget(self.jobLabel)

        self.infoLayout.addStretch()

        self.stepLabel = QLabel("STEP : orig")
        self.stepLabel.setFont(QFont("SimSun", 9, QFont.Bold))
        self.stepLabel.setStyleSheet("color: #0000FF;")
        self.infoLayout.addWidget(self.stepLabel)

        # --- Tab 栏 ---
        self.tabWidget = QTabWidget()
        self.tabWidget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                border-top: 1px solid #999999;
                background-color: #FFFFFF;
            }
            QTabBar::tab {
                background-color: #E8E8E8;
                color: #000000;
                border: 1px solid #999999;
                border-bottom: none;
                padding: 3px 15px;
                margin-right: 2px;
                font-family: "SimSun";
                font-size: 9pt;
                min-width: 60px;
            }
            QTabBar::tab:selected {
                background-color: #FFFFFF;
                color: #0000FF;
                border-bottom: 1px solid #FFFFFF;
                margin-bottom: -1px;
            }
            QTabBar::tab:hover {
                background-color: #F0F0F0;
            }
        """)

        # 创建4个Tab页面
        self.trees = []
        tab_names = ["脚本", "SYMBOL", "快捷键", "CAD快捷键"]
        for tab_name in tab_names:
            tab_page = QWidget()
            tab_layout = QVBoxLayout(tab_page)
            tab_layout.setContentsMargins(0, 0, 0, 0)
            tab_layout.setSpacing(0)

            tree = QTreeWidget()
            tree.setHeaderHidden(True)
            tree.setIconSize(QSize(20, 20))
            tree.setIndentation(20)
            tree.setRootIsDecorated(True)
            tree.setItemsExpandable(True)
            tree.setAnimated(True)
            tree.setStyleSheet("""
                QTreeWidget {
                    background-color: #F5F7FA;
                    border: none;
                    outline: none;
                    font-family: "SimSun";
                    font-size: 9pt;
                }
                QTreeWidget::item {
                    height: 34px;
                    padding: 2px 8px;
                    color: #333333;
                    border: none;
                }
                QTreeWidget::item:hover,
                QTreeWidget::item:selected {
                    background-color: #E6F7FF;
                    border-left: 3px solid #1890FF;
                    margin: 2px 8px;
                    border-radius: 8px;
                }
                QTreeWidget::branch {
                    background: transparent;
                }
            """)

            tab_layout.addWidget(tree)
            self.tabWidget.addTab(tab_page, tab_name)
            self.trees.append(tree)

        # --- 底部状态栏 ---
        self.statusBar = QStatusBar(MainWindow)
        self.statusBar.setStyleSheet(
            "background-color: #F0F0F0; border-top: 1px solid #CCCCCC; color: #333333; font-size: 9pt;")
        
        # 启动时间刷新定时器
        self.startTimeTimer()

        # --- 整合布局 ---
        self.mainLayout.addWidget(self.topBar)
        self.mainLayout.addWidget(self.infoBar)
        self.mainLayout.addWidget(self.tabWidget)

        MainWindow.setCentralWidget(self.centralWidget)
        MainWindow.setStatusBar(self.statusBar)

        # 注：不再在 setupUi 中填充菜单数据，
        # “脚本”树由 gtw.py 从 scripts.xml 加载后调用 populateScriptTree() 填充

    def startTimeTimer(self):
        """启动时间刷新定时器"""
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.updateTime)
        self.time_timer.start(1000)  # 每秒刷新一次
        self.updateTime()  # 立即执行一次
    
    def updateTime(self):
        """更新状态栏时间显示"""
        now = datetime.now()
        
        # 格式化日期
        date_str = now.strftime("%Y年%m月%d日")
        
        # 计算周数
        week_num = now.isocalendar()[1]
        week_str = f"第{week_num}周"
        
        # 农历（简化版，使用农历库或固定算法）
        lunar_str = self.getLunarDate(now)
        
        # 更新状态栏
        self.statusBar.showMessage(f"{date_str}  {week_str}  {lunar_str}")
    
    def getLunarDate(self, dt):
        """获取农历日期（简化版）"""
        # 这里使用简化的农历转换，实际项目建议使用 lunardate 库
        # 为了示例，这里返回固定格式
        # 实际使用时需要安装：pip install lunardate
        try:
            from lunardate import LunarDate
            lunar = LunarDate.fromSolarDate(dt.year, dt.month, dt.day)
            return f"农历{lunar.year}年{lunar.month}月{lunar.day}"
        except ImportError:
            # 如果没有安装 lunardate 库，返回简化格式
            return f"农历{dt.year}年{dt.month}月{dt.day}日"

    def populateScriptTree(self, groups):
        """根据脚本配置（scripts.xml）填充“脚本”Tab 树

        Args:
            groups: [{'name': 分组名, 'scripts': [{'label','path',...}]}]
                    由 gtw.py 的 load_script_config() 解析得到
        """
        tree = self.trees[0]
        tree.clear()

        for group in groups:
            item = QTreeWidgetItem(tree)
            item.setText(0, group['name'])
            item.setFont(0, QFont("SimSun", 9))
            item.setExpanded(False)

            for script in group['scripts']:
                child = QTreeWidgetItem(item)
                child.setText(0, script['label'])
                child.setFont(0, QFont("SimSun", 9))
                # 存入 exe 绝对路径，双击时由 gtw.py 据此后台运行
                child.setData(0, Qt.UserRole, script['path'])
                # 自动提取 exe 内置图标
                icon = get_exe_icon(script['path'], size=(16, 16))
                if icon is not None:
                    child.setIcon(0, icon)
