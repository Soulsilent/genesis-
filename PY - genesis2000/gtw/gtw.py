import subprocess
import sys
import os
import xml.etree.ElementTree as ET
from functools import wraps

from PyQt5.QtGui import QIcon, QCursor
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QDesktopWidget, QLabel, QSystemTrayIcon, QMenu, \
    QAction, QFileDialog, QInputDialog
from PyQt5.QtCore import QTimer, Qt, QEvent, QThread, pyqtSignal
from GenesisAddress import get_address
from genesis_gateway import GenesisGateway
from gtw_ui import Ui_CAMGuideWindow

def prevent_repeat_click(func):
    """防止按钮重复点击/积压队列的装饰器"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        flag_name = f"_is_running_{func.__name__}"
        
        if getattr(self, flag_name, False):
            QMessageBox.warning(self, "提示", "程序正在运行中，请勿重复点击！")
            return
        
        setattr(self, flag_name, True)
        
        QApplication.processEvents()
        
        try:
            result = func(self, *args, **kwargs)
            return result
        except Exception as e:
            raise
        finally:
            QApplication.processEvents()
            
            setattr(self, flag_name, False)
            
    return wrapper

def load_script_config(config_path, script_dir):
    """读取 scripts.xml 脚本配置

    Args:
        config_path: 配置文件绝对路径
        script_dir:  脚本 exe 所在文件夹（src）

    Returns:
        (groups, scripts_by_name)
        groups:         [{'name': 分组名, 'scripts': [{'name','exe','label','path'}]}]
        scripts_by_name: {脚本name: 脚本条目}，供代码按名引用
    """
    groups = []
    scripts_by_name = {}
    try:
        root = ET.parse(config_path).getroot()
    except Exception as e:
        print(f"读取脚本配置失败: {e}，将使用空配置")
        return groups, scripts_by_name

    for group_el in root.findall('group'):
        group_name = group_el.get('name', '未命名分组')
        scripts = []
        for script_el in group_el.findall('script'):
            exe = (script_el.get('exe') or '').strip()
            if not exe:
                continue
            label = script_el.get('label') or exe
            name = script_el.get('name') or label
            entry = {
                'name': name,
                'exe': exe,
                'label': label,
                'path': os.path.join(script_dir, exe),
            }
            scripts.append(entry)
            scripts_by_name[name] = entry
        groups.append({'name': group_name, 'scripts': scripts})

    print(f"已加载脚本配置: {len(scripts_by_name)} 个脚本, {len(groups)} 个分组")
    return groups, scripts_by_name

# GENESIS_VER 环境变量值 -> Genesis 版本号映射（按需扩充）
# 例：e97 对应 Genesis 目录 e97，版本为 9.07b
GENESIS_VER_MAP = {
    '97': '9.07b',
    '105': '10.05',
    '140': '14.0',
}

DEFAULT_JOB_VER = 'JOB_14.0'
DEFAULT_STEP_VER = 'STEP_14.0'


def _match_version(raw_input, job_address, step_address):
    """把版本号（如 10.05 / 105 / e97）在 GenesisAddress 库中匹配

    Returns:
        (job_ver, step_ver) 匹配成功；否则 None
    """
    s = (raw_input or '').strip().lower().lstrip('e')
    if not s:
        return None
    # 依次尝试：直接按版本号（10.05）、GENESIS_VER 映射（105 -> 10.05）
    for ver in (s, GENESIS_VER_MAP.get(s)):
        if not ver:
            continue
        job_ver, step_ver = f'JOB_{ver}', f'STEP_{ver}'
        if job_ver in job_address and step_ver in step_address:
            return job_ver, step_ver
    return None


def _ask_user_version(parent, job_address, step_address):
    """弹窗让用户选择/输入 Genesis 版本，再从库中匹配；取消则回退默认版本"""
    versions = sorted({k[len('JOB_'):] for k in job_address if k.startswith('JOB_')})
    while True:
        text, ok = QInputDialog.getItem(
            parent, "选择 Genesis 版本",
            "无法自动匹配 Genesis 版本，请选择或输入版本号（如 14.0 / 10.05 / 9.07b）：",
            versions, 0, True)  # 可编辑，允许直接输入
        if not ok:
            print("用户取消版本选择，回退默认版本")
            return DEFAULT_JOB_VER, DEFAULT_STEP_VER

        matched = _match_version(text, job_address, step_address)
        if matched:
            print(f"用户输入版本 {text} -> 匹配 {matched[0]}/{matched[1]}")
            return matched
        QMessageBox.warning(parent, "提示", f"版本 {text} 在 GenesisAddress 库中不存在，请重新输入")


def get_job_step_ver(parent=None):
    """从环境变量 GENESIS_VER 解析 JOB/STEP 版本号，并在 GenesisAddress.py 中匹配

    匹配规则：
        GENESIS_VER=105  -> JOB_10.05 / STEP_10.05
        GENESIS_VER=140  -> JOB_14.0  / STEP_14.0
        GENESIS_VER=e97  -> JOB_9.07b / STEP_9.07b

    无法匹配（未设置环境变量、值不在映射表、库中无对应地址）时，
    弹窗让用户输入 Genesis 版本后再从库中匹配；用户取消则回退默认 14.0。

    Returns:
        (job_ver, step_ver)
    """
    job_address, step_address = get_address()

    raw = (os.getenv('GENESIS_VER') or '').strip().lower().lstrip('e')
    if raw:
        matched = _match_version(raw, job_address, step_address)
        if matched:
            print(f"GENESIS_VER={raw} -> 匹配 {matched[0]}/{matched[1]}")
            return matched
        print(f"警告: GENESIS_VER={raw} 未匹配到 GenesisAddress 中的版本，转人工选择")
    else:
        print("未设置 GENESIS_VER，转人工选择")

    return _ask_user_version(parent, job_address, step_address)

class CAMGuideWindow(QMainWindow):
    """主窗口类 - 负责业务逻辑与窗口行为"""
    
    # ==========================================
    # 区域 1: 常量与初始化
    # ==========================================
    # 吸附阈值（像素）
    SNAP_DISTANCE = 5
    # 隐藏后露出的边距（像素）
    HIDE_MARGIN = 2
    # 隐藏后鼠标触发显示的 Y 轴有效范围（仅顶部，避免整条边误触）
    HIDE_TRIGGER_HEIGHT = 40
    # 鼠标触发显示的阈值（像素）
    SHOW_THRESHOLD = 10
    # 失去焦点后延迟隐藏的时间（毫秒）
    HIDE_DELAY_MS = 2000
    
    # 脚本路径配置（脚本列表已外置到 scripts.xml，增删脚本只需改配置，不用动代码）
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    SCRIPT_DIR = os.path.join(BASE_DIR, 'src')          # src 存放所有脚本 exe
    CONFIG_FILE = os.path.join(BASE_DIR, 'scripts.xml') # 脚本列表配置文件

    def __init__(self):
        super().__init__()

        # PyQt5 隐藏到托盘必须：禁止"末窗口关闭时退出"
        QApplication.setQuitOnLastWindowClosed(False)

        # 状态变量
        self.is_hidden = False
        self.snap_direction = ""  # "left", "right", "up"
        self._snap_target = None  # 吸附目标坐标 (x, y)，消除 frameGeometry 抖动

        # 创建 Genesis 网关实例（版本号从环境变量 GENESIS_VER 读取，无法匹配时弹窗人工选择）
        job_ver, step_ver = get_job_step_ver(self)
        self.g = GenesisGateway(job_ver=job_ver, step_ver=step_ver)

        # 后台任务线程追踪（防止内存泄漏）
        self.active_workers = []

        # 初始化 UI
        self.ui = Ui_CAMGuideWindow()
        self.ui.setupUi(self)

        # 从 scripts.xml 加载脚本配置并填充“脚本”树
        self.script_groups, self.scripts_by_name = load_script_config(self.CONFIG_FILE, self.SCRIPT_DIR)
        self.ui.populateScriptTree(self.script_groups)

        # 禁止最大化（去掉最大化按钮 + 拦截快捷键/Aero Snap）
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, False)

        # 初始居中显示
        self.centerOnScreen()

        # 启动边缘检测定时器
        self.edge_timer = QTimer(self)
        self.edge_timer.timeout.connect(self.monitorLogic)
        self.edge_timer.start(50)

        # 启动 JOB/STEP 信息刷新定时器
        self.startRefreshTimer()

        # 绑定菜单与工具栏事件
        self.bindMenuEvents()
        self.bindToolbarEvents()

        # 创建隐藏延迟定时器
        self.hide_delay_timer = QTimer(self)
        self.hide_delay_timer.setSingleShot(True)
        self.hide_delay_timer.timeout.connect(self.hideToEdge)

        # 安装事件过滤器，监听窗口焦点变化
        self.installEventFilter(self)

        # 初始化系统托盘
        self.setupTrayIcon()

    # ==========================================
    # 区域 2: 系统托盘与关闭逻辑
    # ==========================================
    def setupTrayIcon(self):
        """设置系统托盘图标（幂等：重复调用不会重复创建，避免 Win10 出现多个图标）"""
        if hasattr(self, 'tray_icon') and self.tray_icon is not None:
            return  # 已创建过，防止重复注册托盘图标

        self.tray_icon = QSystemTrayIcon(self)
        base_dir = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_dir, 'ICO', 'xd.ico')
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
            self.setWindowIcon(QIcon(icon_path))  # 同步设置应用图标，确保托盘正常显示
        else:
            self.tray_icon.setIcon(self.windowIcon())
        
        tray_menu = QMenu()
        show_action = QAction("显示窗口", self)
        show_action.triggered.connect(self.showNormal)
        tray_menu.addAction(show_action)
        
        tray_menu.addSeparator()
        
        exit_action = QAction("退出程序", self)
        exit_action.triggered.connect(QApplication.quit)
        tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)

        # Win10 托盘多图标问题处理：
        # 1) 延迟到事件循环启动、托盘就绪后再 show（singleShot(0) 有时仍过早）
        # 2) 用 isVisible 守卫，保证整个生命周期只 show 一次，绝不 hide/show 反复切换
        # 3) 启动提示气泡放在图标注册完成之后再弹，避免与 show 竞争
        QTimer.singleShot(1000, self._showTrayIconOnce)

    def _showTrayIconOnce(self):
        """只显示一次托盘图标，防止重复注册产生多个图标"""
        if self.tray_icon and not self.tray_icon.isVisible():
            self.tray_icon.show()

        QTimer.singleShot(1000, lambda: self.tray_icon.showMessage(
            "CAM Guide", "程序已最小化到托盘，双击图标恢复窗口",
            QSystemTrayIcon.Information, 2000))

    def on_tray_activated(self, reason):
        """托盘图标激活事件 - 带防重复触发"""
        if reason == QSystemTrayIcon.DoubleClick:
            # 如果窗口可见，点击托盘则隐藏（开关效果）
            if self.isVisible():
                self.hide()
                self.is_hidden = True
                return

            # 延迟恢复，给系统时间处理窗口句柄就绪
            QTimer.singleShot(100, self.restoreWindowFromTray)

    def restoreWindowFromTray(self):
        """从托盘恢复窗口（居中 + 置顶）"""
        try:
            self.is_hidden = False
            self.setWindowState(self.windowState() & ~Qt.WindowMinimized)
            self.centerOnScreen()  # 居中显示
            self.show()
            self.raise_()
            self.activateWindow()
            # 短暂置顶确保窗口在最前，使用安全 API 避免 HWND 重建
            self._setTopHint(True)
            QTimer.singleShot(500, self._removeTopHint)
        except Exception as e:
            print(f"恢复窗口失败: {e}")

    def closeEvent(self, event):
        """重写关闭事件：点击 X 按钮时隐藏到托盘而不是退出"""
        event.ignore()
        self.hide()
        self.is_hidden = True  # 确保状态变量同步

        if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            self.tray_icon.showMessage("提示", "程序已在后台运行", QSystemTrayIcon.Information, 1500)

    def changeEvent(self, event):
        """拦截窗口状态变化，阻止最大化（Aero Snap / Win+↑ / 双击标题栏）"""
        if event.type() == QEvent.WindowStateChange:
            if self.isMaximized():
                self.showNormal()
                return
        super().changeEvent(event)

    # ==========================================
    # 区域 3: 窗口吸附与边缘检测逻辑
    # ==========================================
    def eventFilter(self, obj, event):
        """核心：失去焦点延迟隐藏，获得焦点取消隐藏"""
        if obj is self:
            if event.type() == QEvent.WindowDeactivate:
                # 延迟隐藏是为了防止误触：比如弹出一个子对话框导致短暂失焦
                if self.snap_direction and not self.is_hidden:
                    self.hide_delay_timer.start(self.HIDE_DELAY_MS)
            elif event.type() == QEvent.WindowActivate:
                self.hide_delay_timer.stop()
        return super().eventFilter(obj, event)

    def focusOutEvent(self, event):
        """双保险：焦点离开窗口时触发隐藏（弥补 WindowDeactivate 在 HWND 重建后不可靠的问题）"""
        super().focusOutEvent(event)
        if self.snap_direction and not self.is_hidden:
            # 使用 QTimer.singleShot 延迟检查，避免子控件间焦点转移误触发
            QTimer.singleShot(100, self._checkRealFocusLoss)

    def _checkRealFocusLoss(self):
        """确认窗口确实失去了焦点（而非子控件间转移）"""
        if not self.isActiveWindow() and self.snap_direction and not self.is_hidden:
            self.hideToEdge()

    def centerOnScreen(self):
        """将窗口居中显示"""
        desktop = QDesktopWidget()
        screen_rect = desktop.availableGeometry(self)
        size = self.geometry()
        self.move(int((screen_rect.width() - size.width()) / 2),
                  int((screen_rect.height() - size.height()) / 2))

    def monitorLogic(self):
        """统一管理吸附、显示和鼠标离开隐藏逻辑（含防抖处理）"""
        if not self.isVisible() or self.isMinimized() or self.isMaximized():
            return

        cursor_pos = QCursor.pos()
        win_rect = self.frameGeometry()
        screen_rect = QDesktopWidget().availableGeometry(self)

        if not self.is_hidden:
            left_gap = win_rect.left() - screen_rect.left()
            right_gap = screen_rect.right() - win_rect.right()
            top_gap = win_rect.top() - screen_rect.top()

            # 1. 计算目标吸附方向与目标坐标
            new_direction = ""
            target_x, target_y = win_rect.x(), win_rect.y()

            if abs(left_gap) <= self.SNAP_DISTANCE:
                new_direction = "left"
                target_x = screen_rect.left()
                target_y = win_rect.top()
            elif abs(right_gap) <= self.SNAP_DISTANCE:
                new_direction = "right"
                target_x = screen_rect.right() - win_rect.width()
                target_y = win_rect.top()
            elif abs(top_gap) <= self.SNAP_DISTANCE:
                new_direction = "up"
                target_x = win_rect.left()
                target_y = screen_rect.top()

            # 2. 状态同步 + 吸附位置锁定
            if new_direction != self.snap_direction:
                # 方向改变：更新方向，缓存新目标
                self.snap_direction = new_direction
                if new_direction:
                    self._snap_target = (target_x, target_y)
                    self.move(target_x, target_y)
                else:
                    self._snap_target = None
                    self.hide_delay_timer.stop()
            elif self._snap_target is not None:
                # 方向未变且已吸附：直接用缓存坐标，避免 frameGeometry 抖动
                sx, sy = self._snap_target
                if abs(sx - win_rect.x()) > 1 or abs(sy - win_rect.y()) > 1:
                    self.move(sx, sy)

            # 吸附状态下，鼠标离开窗口区域则启动隐藏倒计时
            if self.snap_direction:
                if not win_rect.contains(cursor_pos):
                    if not self.hide_delay_timer.isActive():
                        self.hide_delay_timer.start(self.HIDE_DELAY_MS)
                else:
                    self.hide_delay_timer.stop()
        else:
            need_show = False
            hidden_rect = self.frameGeometry()  # 获取隐藏窗口的实际逻辑坐标与宽度
            if self.snap_direction == "left" and cursor_pos.x() <= screen_rect.left() + self.SHOW_THRESHOLD \
                    and hidden_rect.top() <= cursor_pos.y() <= hidden_rect.top() + self.HIDE_TRIGGER_HEIGHT: need_show = True
            elif self.snap_direction == "right" and cursor_pos.x() >= screen_rect.right() - self.SHOW_THRESHOLD \
                    and hidden_rect.top() <= cursor_pos.y() <= hidden_rect.top() + self.HIDE_TRIGGER_HEIGHT: need_show = True
            elif self.snap_direction == "up" and cursor_pos.y() <= screen_rect.top() + self.SHOW_THRESHOLD \
                    and hidden_rect.left() <= cursor_pos.x() <= hidden_rect.right(): need_show = True

            if need_show:
                self.showFromEdge(screen_rect)

    def hideToEdge(self):
        """隐藏到屏幕边缘"""
        screen_rect = QDesktopWidget().availableGeometry(self)
        win_rect = self.frameGeometry()

        # 使用 windowHandle().setFlag 替代 setWindowFlags，避免重建原生 HWND
        self._setTopHint(False)

        if self.snap_direction == "left": self.move(screen_rect.left() - win_rect.width() + self.HIDE_MARGIN, win_rect.top())
        elif self.snap_direction == "right": self.move(screen_rect.right() - self.HIDE_MARGIN, win_rect.top())
        elif self.snap_direction == "up": self.move(win_rect.left(), screen_rect.top() - win_rect.height() + self.HIDE_MARGIN)

        self.is_hidden = True

    def showFromEdge(self, screen_rect):
        """从屏幕边缘滑出"""
        win_rect = self.frameGeometry()

        if self.snap_direction == "left": self.move(screen_rect.left(), win_rect.top())
        elif self.snap_direction == "right": self.move(screen_rect.right() - win_rect.width(), win_rect.top())
        elif self.snap_direction == "up": self.move(win_rect.left(), screen_rect.top())

        self.is_hidden = False
        # 短暂置顶用于视觉呈现，不抢焦点
        self.show()
        self.raise_()
        self._setTopHint(True)
        QTimer.singleShot(300, self._removeTopHint)

    def _setTopHint(self, on: bool):
        """安全切换置顶标志，不破坏原生窗口句柄"""
        handle = self.windowHandle()
        if handle:
            handle.setFlag(Qt.WindowStaysOnTopHint, on)

    def _removeTopHint(self):
        """移除置顶属性"""
        self._setTopHint(False)

    # ==========================================
    # 区域 4: 工具栏按钮与事件绑定
    # ==========================================
    def _safe_connect(self, signal, slot):
        """等价于 Qt::UniqueConnection：先断开再连接，防止重复绑定导致回调重复执行"""
        try:
            signal.disconnect(slot)
        except TypeError:
            pass  # 从未连接过该槽时 disconnect 会抛 TypeError，忽略即可
        signal.connect(slot)

    def bindToolbarEvents(self):
        """绑定顶部工具栏按钮事件（幂等：重复调用不会重复绑定）"""
        if not hasattr(self, '_toolbar_handlers'):
            self._toolbar_handlers = {}  # widget -> 已绑定的 lambda，用于精确断开

        for i in range(self.ui.topLayout.count()):
            widget = self.ui.topLayout.itemAt(i).widget()
            if widget is not None and hasattr(widget, 'clicked'):
                labels = widget.findChildren(QLabel)
                if len(labels) >= 2:
                    btn_text = labels[1].text()
                    # 先断开旧 handler（lambda 每次创建都是新对象，需按存储的引用精确断开）
                    old_handler = self._toolbar_handlers.get(widget)
                    if old_handler is not None:
                        try:
                            widget.clicked.disconnect(old_handler)
                        except TypeError:
                            pass
                    # 再绑定新 handler 并缓存引用
                    handler = lambda checked=False, txt=btn_text: self.on_toolbar_clicked(txt)
                    self._toolbar_handlers[widget] = handler
                    widget.clicked.connect(handler)
    
    def on_toolbar_clicked(self, btn_text):
        """工具栏按钮点击事件处理"""
        print(f"点击了工具栏按钮: {btn_text}")
        if btn_text == "搜索": self.on_search()
        elif btn_text == "AI": self.on_ai()
        elif btn_text == "工具": self.on_tools()
        elif btn_text == "SAVE": self.on_save_job()
        elif btn_text == "截图": self.on_screenshot()
        elif btn_text == "翻译": self.on_translate()
        elif btn_text == "mini": self.on_mini()
        elif btn_text == "Exit": self.on_exit()
    
    def on_search(self):
        """搜索：输入/选择 scripts.xml 中的脚本名，回车后展开对应分组并定位"""
        labels = [s['label'] for g in self.script_groups for s in g['scripts']]
        if not labels:
            QMessageBox.information(self, "搜索", "scripts.xml 中暂无脚本")
            return

        text, ok = QInputDialog.getItem(
            self, "搜索脚本", "输入或选择脚本名，按回车定位：", labels, 0, True)
        if not ok or not text.strip():
            return

        keyword = text.strip()
        tree = self.ui.trees[0]
        target = None
        parent_item = None

        # 1) 先精确匹配 label；2) 找不到再按“包含”模糊匹配
        for i in range(tree.topLevelItemCount()):
            group = tree.topLevelItem(i)
            for j in range(group.childCount()):
                child = group.child(j)
                if child.text(0) == keyword:
                    target, parent_item = child, group
                    break
            if target:
                break
        if target is None:
            keyword_lower = keyword.lower()
            for i in range(tree.topLevelItemCount()):
                group = tree.topLevelItem(i)
                for j in range(group.childCount()):
                    child = group.child(j)
                    if keyword_lower in child.text(0).lower():
                        target, parent_item = child, group
                        break
                if target:
                    break

        if target is None:
            QMessageBox.information(self, "搜索", f"未找到脚本: {keyword}")
            return

        parent_item.setExpanded(True)      # 展开对应分组
        tree.setCurrentItem(target)        # 选中脚本项
        tree.scrollToItem(target)          # 滚动到可见位置
        print(f"搜索定位: {parent_item.text(0)} -> {target.text(0)}")
    
    def on_ai(self):
        print("执行: AI")
        QMessageBox.information(self, "AI", "AI功能开发中...")
    
    def on_tools(self):
        """工具：启动 Hot-Key.exe（若已在运行则不重复启动）"""
        entry = self.scripts_by_name.get('Hot-Key')
        if not entry:
            QMessageBox.warning(self, "提示", "scripts.xml 配置中未找到 Hot-Key 脚本")
            return

        exe_path = entry['path']
        process_name = os.path.basename(exe_path)
        if self._is_process_running(process_name):
            print(f"{process_name} 已在运行，不重复启动")
            return

        print(f"启动: {exe_path}")
        subprocess.Popen(exe_path)

    @staticmethod
    def _is_process_running(process_name):
        """检查进程是否已在运行（Windows tasklist，失败时按未运行处理）"""
        try:
            result = subprocess.run(
                ['tasklist', '/FI', f'IMAGENAME eq {process_name}', '/NH'],
                capture_output=True, text=True, errors='ignore',
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
                timeout=5,
            )
            return process_name.lower() in (result.stdout or '').lower()
        except Exception:
            return False

    # ... (前面的代码保持不变)

    @prevent_repeat_click
    def on_save_job(self):
        """带防重复点击和异常安全的保存与导出逻辑"""
        print("开始执行保存与导出流程...")
        try:
            # 1. 获取Genesis进程PID
            pid = self.g.get_genesis_PID()
            if not pid:
                QMessageBox.warning(self, "警告", "未找到Genesis进程，请确认软件已启动！")
                return

            # 2. 获取当前作业名
            job = self.g.get_JobsStepName(pid, 'job')
            if not job:
                QMessageBox.warning(self, "警告", "无法获取作业名，请检查内存地址配置！")
                return

            # ================== 第一步：先执行 SAVE (保存作业) ==================
            save_cmd = f'COM save_job,job={job},override=no'
            print(f"正在执行保存命令: {save_cmd}")
            result_code, result_output = self.g.script_run(myScript=save_cmd, mode='COM')

            if result_code != 0:
                # 如果保存失败，直接弹窗报错并终止
                error_msg = f"保存作业失败，错误码: {result_code}\n输出: {result_output}"
                print(error_msg)
                QMessageBox.critical(self, "保存失败", error_msg)
                return
            print(f"作业 {job} 保存成功，准备开始导出...")

            # ================== 第二步：检查并执行 EXPORT (导出作业) ==================
            # 查询作业的默认导出路径
            check_cmd = f'COM get_job_info,job={job},property=export_path'
            result_code, result_output = self.g.script_run(myScript=check_cmd, mode='COM')

            export_path = ""
            # 解析结果并判断
            if result_code == 0 and result_output:
                lines = result_output.split('\n')
                for line in lines:
                    if 'export_path=' in line:
                        # 提取等号后面的内容，并去除引号和空格
                        export_path = line.split('export_path=')[-1].strip().strip('"')
                        break

            # ================== 核心逻辑：路径校验与料号文件夹追加 ==================
            final_export_path = ""

            # 检查获取到的路径是否有效（存在且不为空）
            if export_path and os.path.exists(os.path.dirname(export_path)):
                # 获取路径的最后一个文件夹名称
                last_folder_name = os.path.basename(os.path.normpath(export_path))
                # 如果最后一个文件夹的名字不等于当前的 JOB 名字（忽略大小写比较）
                if last_folder_name.upper() != job.upper():
                    final_export_path = os.path.join(export_path, job.upper())
                else:
                    final_export_path = export_path
            else:
                # 路径不存在或无效，提示用户选择路径
                default_path = os.path.join(os.path.expanduser('~'), 'Desktop')
                path = QFileDialog.getExistingDirectory(self, "选择导出路径", default_path)
                if not path:
                    QMessageBox.information(self, "提示", "作业已保存，但您取消了导出操作")
                    return
                # 如果用户选择的末级目录名已是料号名，不再重复追加
                last_folder = os.path.basename(os.path.normpath(path))
                if last_folder.upper() == job.upper():
                    final_export_path = path
                else:
                    final_export_path = os.path.join(path, job.upper())

            # --- 【关键修复】路径处理与文件夹创建 ---
            # 1. 强制将所有反斜杠转为正斜杠（Genesis 通用格式）
            final_export_path = final_export_path.replace('\\', '/')

            # 2. 自动创建目标文件夹（如果不存在）
            # exist_ok=True 表示如果文件夹已存在也不报错
            os.makedirs(final_export_path, exist_ok=True)

            # --- 【关键修复】生成导出命令 ---
            # 3. 移除了 'analyze_surfaces=no' 参数，防止旧版本报错
            # 注意：path 值加了双引号转义，防止路径含空格出错
            export_cmd = f'COM export_job,job={job},path=\"{final_export_path}\",mode=tar_gzip,submode=full,overwrite=yes'

            print(f"正在执行导出命令: {export_cmd}")
            result_code, result_output = self.g.script_run(myScript=export_cmd, mode='COM')

            if result_code == 0:
                # ✅ 成功：使用信息弹窗
                QMessageBox.information(self, "操作完成", f"{job} 已保存并自动导出到:\n{final_export_path}")
            else:
                # ❌ 失败：使用错误弹窗
                error_msg = f"导出作业失败，错误码: {result_code}\n输出: {result_output}"
                print(error_msg)
                QMessageBox.critical(self, "导出失败", error_msg)

        except Exception as e:
            # ⚠️ 捕获所有异常，确保锁能释放，并给用户提示
            error_msg = f"发生未预期的异常: {str(e)}"
            print(error_msg)
            QMessageBox.critical(self, "程序错误", error_msg)
        finally:
            # 确保无论如何都会释放锁（虽然装饰器会处理，这里双重保险）
            flag_name = f"_is_running_{sys._getframe().f_code.co_name}"
            if hasattr(self, flag_name):
                setattr(self, flag_name, False)
    def on_screenshot(self):
        try:
            self.hide()  # 先隐藏主窗口，避免挡截图
            subprocess.Popen('start ms-screenclip:', shell=True)
            # 延迟恢复窗口，给截图工具启动时间
            QTimer.singleShot(800, self._restoreAfterScreenshot)
        except Exception as e:
            self.show()
            QMessageBox.critical(None, "调用失败", f"无法启动系统截图工具。\n错误信息：{e}")

    def _restoreAfterScreenshot(self):
        """截图后恢复窗口显示"""
        self.show()
        self.raise_()
    
    def on_translate(self):
        print("执行: 翻译")
        QMessageBox.information(self, "翻译", "翻译功能开发中...")
    
    def on_mini(self):
        print("执行: Mini")
        self.showMinimized()
    
    def on_exit(self):
        print("执行: 退出")
        reply = QMessageBox.question(self, "退出", "确定要退出程序吗？", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes: QApplication.quit()

    # ==========================================
    # 区域 5: 树形菜单与业务功能逻辑
    # ==========================================
    def startRefreshTimer(self):
        """启动 JOB/STEP 信息刷新定时器（幂等：重复调用不会重复绑定/重复刷新）"""
        # 防止旧定时器仍在运行导致 updateJobStepInfo 被重复调用
        if hasattr(self, 'refresh_timer') and self.refresh_timer is not None:
            self.refresh_timer.stop()
            self.refresh_timer.deleteLater()
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.updateJobStepInfo)
        self.refresh_timer.start(500)
        self.updateJobStepInfo()

    def updateJobStepInfo(self):
        """更新 JOB 和 STEP 信息"""
        try:
            myPid = self.g.get_genesis_PID()
            if myPid:
                job_name = self.g.get_JobsStepName(myPid, getval='job')
                step_name = self.g.get_JobsStepName(myPid, getval='step')
                if job_name: self.ui.jobLabel.setText(f"JOB  {job_name}")
                if step_name: self.ui.stepLabel.setText(f"STEP : {step_name}")
        except Exception:
            pass

    def bindMenuEvents(self):
        """绑定菜单项的事件（幂等：重复调用不会重复绑定）"""
        tree = self.ui.trees[0]
        self._safe_connect(tree.itemExpanded, self.on_item_expanded)
        self._safe_connect(tree.itemCollapsed, self.on_item_collapsed)
        self._safe_connect(tree.itemDoubleClicked, self.on_item_clicked)

    def on_item_expanded(self, item):
        """展开时更新箭头"""
        text = item.text(0)
        if text.startswith("> "): item.setText(0, "V " + text[2:])

    def on_item_collapsed(self, item):
        """折叠时更新箭头"""
        text = item.text(0)
        if text.startswith("V "): item.setText(0, "> " + text[2:])

    def on_item_clicked(self, item, column):
        """菜单项点击事件：脚本项直接后台运行对应 exe（路径存于 UserRole）"""
        if item.childCount() == 0:
            exe_path = item.data(0, Qt.UserRole)
            if exe_path:
                print(f"运行脚本: {item.text(0)} -> {exe_path}")
                self._run_exe(exe_path)

    # ==========================================
    # 区域 N: 后台任务执行器（内部类 + 通用方法）
    # ==========================================
    class TaskExecutor(QThread):
        """后台执行 EXE 的工作线程，通过 Qt 信号跨线程通信"""
        # 信号：(是否成功, 消息内容)
        task_done = pyqtSignal(bool, str)

        def __init__(self, exe_path, gateway, parent=None):
            super().__init__(parent)
            self.exe_path = exe_path
            self.gateway = gateway

        def run(self):
            """子线程入口：通过 gateway 执行 exe，结果通过信号发回主线程"""
            try:
                code, output = self.gateway.script_run(self.exe_path, mode='script')
                if code == 0:
                    self.task_done.emit(True, "")
                else:
                    err = (output or "").strip()[:200]
                    msg = f"返回码: {code}\n{err}" if err else f"返回码: {code}"
                    self.task_done.emit(False, msg)
            except Exception as e:
                self.task_done.emit(False, f"异常: {str(e)}")

    def _run_exe(self, exe_path):
        """通用方法：后台执行 EXE，仅做异步化，自动解析路径"""
        # 解析路径：绝对路径直接用，否则相对于 SCRIPT_DIR 拼接
        if not os.path.isabs(exe_path):
            exe_path = os.path.join(self.SCRIPT_DIR, exe_path)

        if not os.path.exists(exe_path):
            QMessageBox.critical(self, "错误", f"程序不存在: {exe_path}")
            return

        worker = self.TaskExecutor(exe_path, self.g)
        worker.task_done.connect(lambda ok, msg: self._on_task_done(ok, msg))
        worker.finished.connect(lambda w=worker: self._cleanup_worker(w))
        self.active_workers.append(worker)
        worker.start()

        print(f"后台任务已启动: {exe_path}")

    def _on_task_done(self, success, message):
        """主线程回调：执行失败时显示错误弹窗"""
        if not success:
            QMessageBox.critical(self, "执行失败", message)

    def _cleanup_worker(self, worker):
        """清理已完成的工作线程，防止内存泄漏"""
        if worker in self.active_workers:
            self.active_workers.remove(worker)
        worker.deleteLater()

    # 未来新增脚本：只需在 scripts.xml 的对应 <group> 内添加 <script> 条目，无需新增代码

if __name__ == '__main__':
    app = QApplication(sys.argv)
    base_dir = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(base_dir, 'ICO', 'xd.ico')
    if os.path.exists(icon_path):
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)
        window = CAMGuideWindow()
        window.setWindowIcon(app_icon)
    else:
        print(f"警告：图标文件不存在 {icon_path}，将使用默认图标")
        window = CAMGuideWindow()

    window.show()
    sys.exit(app.exec_())
