#!/usr/bin/env python
# coding:utf-8
import GenesisPy3
import genClasses
from genesisGeometry import *
from genesisGeometry import Point
import sys
import math
import os
import json
import time
import re
from PyQt5.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout,
                             QLabel, QCheckBox, QPushButton, QScrollArea, QWidget, QMessageBox, QDoubleSpinBox,
                             QGroupBox, QGraphicsView, QGraphicsScene, QGraphicsRectItem, QListWidget, QListWidgetItem,
                             QComboBox, QRadioButton, QButtonGroup, QLineEdit)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPen, QBrush, QColor, QPainter, QDrag
import ezdxf

# ==================== Genesis环境初始化 ====================
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)

g = GenesisPy3.Genesis()
top = genClasses.Top()

if not top.currentJob or top.currentJob not in top.jobs:
    QMessageBox.warning(None, "警告", "当前未加载任何任务(Job)")
    sys.exit(0)

job = top.jobs[top.currentJob]

if top.currentStep not in job.steps:
    QMessageBox.warning(None, "警告", "当前未加载任何步骤(Step)")
    sys.exit(0)

step = job.steps[top.currentStep]

# ==================== 板子尺寸识别与自动方向判断 ====================
Xmin = step.profileLimits.xMin
Xmax = step.profileLimits.xMax
Ymin = step.profileLimits.yMin
Ymax = step.profileLimits.yMax

board_width = Xmax - Xmin
board_height = Ymax - Ymin

if board_height > 0.01 and board_width > 0.01:
    aspect_ratio = max(board_width, board_height) / min(board_width, board_height)
    max_dimension = max(board_width, board_height)
    is_long_strip = max_dimension > 100 and aspect_ratio > 2
else:
    is_long_strip = False

if is_long_strip:
    if board_width > board_height:
        auto_primary_axis = 'Y'
        auto_long_side = board_width
        auto_short_side = board_height
    else:
        auto_primary_axis = 'X'
        auto_long_side = board_height
        auto_short_side = board_width
else:
    auto_primary_axis = 'X'
    auto_long_side = board_width
    auto_short_side = board_height

all_layers = g.get_layers()

if not all_layers:
    QMessageBox.warning(None, "警告", "没有找到任何图层")
    sys.exit(0)

import random
test_layer = random.choice(all_layers)
try:
    step.displayLayer(layerName=test_layer, number=1, display='yes')
    step.displayLayer(layerName=test_layer, number=1, display='no')
except:
    pass

# ==================== 配置路径与文件读写 ====================
def get_genesis_scripts_dir():
    try:
        import winreg
        genesis_home = os.environ.get('GENESIS_HOME') or os.environ.get('GENE_EDIR')
        if genesis_home and os.path.exists(genesis_home):
            scripts_dir = os.path.join(genesis_home, "sys", "scripts")
            if os.path.exists(scripts_dir):
                return scripts_dir
        registry_paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Genesis"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Genesis"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Genesis"),
        ]
        for hkey, key_path in registry_paths:
            try:
                key = winreg.OpenKey(hkey, key_path)
                try:
                    genesis_path, _ = winreg.QueryValueEx(key, "InstallPath")
                    winreg.CloseKey(key)
                    if genesis_path and os.path.exists(genesis_path):
                        scripts_dir = os.path.join(genesis_path, "sys", "scripts")
                        if os.path.exists(scripts_dir):
                            return scripts_dir
                except (FileNotFoundError, OSError):
                    winreg.CloseKey(key)
                    continue
            except (FileNotFoundError, OSError):
                continue
        default_path = r"C:\genesis\sys\scripts"
        return default_path
    except Exception as e:
        QMessageBox.warning(None, "配置错误", f"获取 Genesis 安装目录失败: {e}")
        return r"C:\genesis\sys\scripts"

GENESIS_SCRIPTS_DIR = get_genesis_scripts_dir()
COMBINED_CONFIG_FILE = os.path.join(GENESIS_SCRIPTS_DIR, "AUTO_MI_config.json")
# 保留旧文件路径用于向后兼容迁移
OLD_CONFIG_FILE = os.path.join(GENESIS_SCRIPTS_DIR, "layer_config.json")
OLD_MIRROR_CONFIG_FILE = os.path.join(GENESIS_SCRIPTS_DIR, "mirror_config.json")

if not os.path.exists(GENESIS_SCRIPTS_DIR):
    try:
        os.makedirs(GENESIS_SCRIPTS_DIR, exist_ok=True)
    except Exception as e:
        QMessageBox.warning(None, "警告", f"无法创建配置目录 {GENESIS_SCRIPTS_DIR}: {e}")

def _load_json_file(path):
    """按多种编码尝试读取 JSON 文件，成功返回数据，失败返回 None。
    依次尝试 utf-8-sig / utf-8 / gbk，兼容不同编辑器保存的编码（含 BOM、ANSI/GBK）。
    """
    if not path or not os.path.exists(path):
        return None
    last_err = None
    for enc in ('utf-8-sig', 'utf-8', 'gbk'):
        try:
            with open(path, 'r', encoding=enc) as f:
                return json.load(f)
        except UnicodeDecodeError as e:
            last_err = e          # 编码不匹配，换下一种编码再试
            continue
        except Exception as e:
            last_err = e          # 能解码但 JSON 内容非法，再换编码无意义
            break
    return None


def loadCombinedConfig():
    """加载合并的 AUTO_MI_config.json，不存在时返回空 dict"""
    try:
        data = _load_json_file(COMBINED_CONFIG_FILE)
        if data is not None:
            return data
        if os.path.exists(COMBINED_CONFIG_FILE):
            QMessageBox.warning(None, "配置错误",
                                f"读取合并配置文件失败，请检查文件编码或格式:\n{COMBINED_CONFIG_FILE}")
    except Exception as e:
        QMessageBox.warning(None, "配置错误", f"读取合并配置文件失败: {e}")
    return {}


def saveCombinedConfig(data):
    """保存完整数据到合并的 AUTO_MI_config.json"""
    try:
        with open(COMBINED_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        QMessageBox.warning(None, "配置错误", f"保存合并配置文件失败: {e}")
        return False


def migrateOldConfigs():
    """从旧的独立配置文件 (layer_config.json / mirror_config.json) 迁移到合并文件"""
    combined = loadCombinedConfig()
    migrated = False

    try:
        if os.path.exists(OLD_CONFIG_FILE) and 'layer_config' not in combined:
            old = _load_json_file(OLD_CONFIG_FILE)
            if old and 'default_layers' in old:
                combined['layer_config'] = {'default_layers': old['default_layers']}
                migrated = True
    except Exception:
        pass

    try:
        if os.path.exists(OLD_MIRROR_CONFIG_FILE) and 'mirror_config' not in combined:
            old = _load_json_file(OLD_MIRROR_CONFIG_FILE)
            if old and 'mirror_layers' in old:
                combined['mirror_config'] = {'mirror_layers': old['mirror_layers']}
                migrated = True
    except Exception:
        pass

    if migrated:
        saveCombinedConfig(combined)
        QMessageBox.information(None, "迁移完成", "已将旧版独立配置文件迁移到 AUTO_MI_config.json")

    return combined


def load_default_layers():
    """从合并配置文件的 layer_config 命名空间加载默认图层列表"""
    combined = loadCombinedConfig()
    if 'layer_config' in combined and 'default_layers' in combined['layer_config']:
        return combined['layer_config']['default_layers']
    combined = migrateOldConfigs()
    if 'layer_config' in combined and 'default_layers' in combined['layer_config']:
        return combined['layer_config']['default_layers']
    return []

def save_default_layers(layers):
    """保存默认图层列表到合并配置文件的 layer_config 命名空间"""
    combined = loadCombinedConfig()
    if 'layer_config' not in combined:
        combined['layer_config'] = {}
    combined['layer_config']['default_layers'] = layers
    return saveCombinedConfig(combined)

def load_mirror_config():
    """从合并配置文件的 mirror_config 命名空间加载镜像配置"""
    combined = loadCombinedConfig()
    if 'mirror_config' in combined and 'mirror_layers' in combined['mirror_config']:
        return combined['mirror_config']['mirror_layers']
    combined = migrateOldConfigs()
    if 'mirror_config' in combined and 'mirror_layers' in combined['mirror_config']:
        return combined['mirror_config']['mirror_layers']
    return {}

def save_mirror_config(mirror_dict):
    """保存镜像配置到合并配置文件的 mirror_config 命名空间"""
    combined = loadCombinedConfig()
    if 'mirror_config' not in combined:
        combined['mirror_config'] = {}
    combined['mirror_config']['mirror_layers'] = mirror_dict
    return saveCombinedConfig(combined)


def load_layer_naming():
    """从合并配置文件的 layer_naming 命名空间加载图纸层映射列表
    返回格式: [{"source": "gtl", "target": "正面线路"}, ...]
    """
    combined = loadCombinedConfig()
    if 'layer_naming' in combined and isinstance(combined['layer_naming'], list):
        # 兼容旧格式（纯字符串列表）→ 升级为 dict 格式
        raw = combined['layer_naming']
        if raw and isinstance(raw[0], str):
            upgraded = [{"source": "", "target": item} for item in raw]
            combined['layer_naming'] = upgraded
            saveCombinedConfig(combined)
            return upgraded
        return raw
    return []


def save_layer_naming(naming_list):
    """保存图纸层映射列表到合并配置文件的 layer_naming 命名空间，不影响其他空间
    接收格式: [{"source": "gtl", "target": "正面线路"}, ...]
    """
    combined = loadCombinedConfig()
    combined['layer_naming'] = naming_list
    return saveCombinedConfig(combined)


# ==================== 全局设置 ====================
DEFAULT_SETTINGS = {
    'rout_width': 3.0,
    'min_gap': 10.0,
    'outline_mode': 'default',
    'outline_layer': '',
    # DXF 导出参数
    'dxf_surface_mode': 'Fill',
    'dxf_pad_as_circle': 'yes',
    'dxf_draft': 'no',
    'dxf_contour_to_hatch': 'no',
    'dxf_output_files': 'multiple',
    'dxf_output_tz': True,
    # 是否添加层名标注（Genesis addText + DXF 文字替换）
    'dxf_annotate_enabled': True,
    # 日志输出
    'dxf_log_enabled': True,
}


def loadSettings():
    """从合并配置文件的 settings 命名空间加载全局设置"""
    combined = loadCombinedConfig()
    if 'settings' in combined:
        s = combined['settings']
        result = {}
        for k, default in DEFAULT_SETTINGS.items():
            result[k] = s.get(k, default)
        return result
    return dict(DEFAULT_SETTINGS)


def saveSettings(settings_dict):
    """保存全局设置到合并配置文件的 settings 命名空间"""
    combined = loadCombinedConfig()
    combined['settings'] = {}
    for k in DEFAULT_SETTINGS:
        combined['settings'][k] = settings_dict.get(k, DEFAULT_SETTINGS[k])
    return saveCombinedConfig(combined)


# 加载全局设置
SETTINGS = loadSettings()


# ==================== 齿轮设置对话框 ====================
class SettingsDialog(QDialog):
    """全局设置对话框 - 齿轮图标打开"""
    # key 不在当前图层列表（或未指定）时下拉框显示的占位符
    NONE_PLACEHOLDER = "None"

    def __init__(self, parent=None):
        super().__init__(parent)
        # 每次打开设置对话框都重新从 AUTO_MI_config.json 读取设置，
        # 确保对话框显示的是配置文件中的最新参数（而不是脚本启动时的快照）
        global SETTINGS
        SETTINGS = loadSettings()
        self.setWindowTitle("全局设置")
        self.resize(420, 560)
        self.setWindowModality(Qt.ApplicationModal)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # 全部设置分组放入滚动区域：窗口高度固定较小，内容超出时滚动查看
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(10)

        form_group = QGroupBox("处理参数")
        form_layout = QVBoxLayout(form_group)
        form_layout.setSpacing(8)
        form_layout.setContentsMargins(10, 10, 10, 10)

        # 轮廓线宽
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("轮廓线宽 (ProfileToRout):"))
        self.spin_rout = QDoubleSpinBox()
        self.spin_rout.setRange(0.5, 50)
        self.spin_rout.setDecimals(1)
        self.spin_rout.setSuffix(" mm")
        self.spin_rout.setValue(SETTINGS['rout_width'])
        row1.addWidget(self.spin_rout)
        form_layout.addLayout(row1)

        # 最小间距
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("最小间距 (Min Gap):"))
        self.spin_gap = QDoubleSpinBox()
        self.spin_gap.setRange(1, 100)
        self.spin_gap.setDecimals(1)
        self.spin_gap.setSuffix(" mm")
        self.spin_gap.setValue(SETTINGS['min_gap'])
        row2.addWidget(self.spin_gap)
        form_layout.addLayout(row2)

        scroll_layout.addWidget(form_group)

        # ==================== 轮廓设置 ====================
        outline_group = QGroupBox("轮廓设置")
        outline_layout = QVBoxLayout(outline_group)
        outline_layout.setSpacing(6)
        outline_layout.setContentsMargins(10, 10, 10, 10)

        self.radio_default = QRadioButton("使用默认 (ProfileToRout)")
        self.radio_custom = QRadioButton("自定义图层 (Layer To Rout)")
        self.radio_grp = QButtonGroup(self)
        self.radio_grp.addButton(self.radio_default, 1)
        self.radio_grp.addButton(self.radio_custom, 2)
        outline_layout.addWidget(self.radio_default)
        outline_layout.addWidget(self.radio_custom)

        # 自定义图层选择行
        self.custom_layer_row = QHBoxLayout()
        self.custom_layer_row.setSpacing(5)
        self.custom_layer_row.addWidget(QLabel("目标图层:"))
        self.combo_outline_layer = QComboBox()
        self.combo_outline_layer.setEditable(True)
        self.combo_outline_layer.setInsertPolicy(QComboBox.NoInsert)
        # 用主对话框的 all_layers 填充列表（在 openSettings 中动态传入）
        outline_layout.addLayout(self.custom_layer_row)
        self.custom_layer_row.addWidget(self.combo_outline_layer)

        # 初始状态
        if SETTINGS['outline_mode'] == 'custom':
            self.radio_custom.setChecked(True)
        else:
            self.radio_default.setChecked(True)
        self._update_outline_ui()

        self.radio_default.toggled.connect(self._update_outline_ui)
        self.radio_custom.toggled.connect(self._update_outline_ui)

        scroll_layout.addWidget(outline_group)

        # ==================== 图纸输出参数设置 ====================
        dxf_group = QGroupBox("图纸输出参数设置")
        dxf_layout = QVBoxLayout(dxf_group)
        dxf_layout.setSpacing(6)
        dxf_layout.setContentsMargins(10, 10, 10, 10)

        # 是否输出 tz 层（开关在最顶部）
        self.chk_output_tz = QCheckBox("是否输出 tz 层")
        self.chk_output_tz.setChecked(SETTINGS.get('dxf_output_tz', True))
        dxf_layout.addWidget(self.chk_output_tz)
        dxf_layout.addSpacing(4)

        # 是否标注层（控制层名标注：Genesis addText 标注 + DXF 文字替换）
        self.chk_annotate = QCheckBox("是否标注层")
        self.chk_annotate.setChecked(SETTINGS.get('dxf_annotate_enabled', True))
        self.chk_annotate.setToolTip("关闭后不再向各层添加层名标注文字，DXF 中也不做文字替换")
        dxf_layout.addWidget(self.chk_annotate)
        dxf_layout.addSpacing(4)

        def make_dxf_row(label, combo_items, setting_key):
            row = QHBoxLayout()
            row.setSpacing(5)
            row.addWidget(QLabel(label))
            combo = QComboBox()
            combo.addItems(combo_items)
            saved_val = SETTINGS.get(setting_key, DEFAULT_SETTINGS[setting_key])
            idx = combo.findText(saved_val)
            if idx >= 0:
                combo.setCurrentIndex(idx)
            row.addWidget(combo)
            row.addStretch()
            dxf_layout.addLayout(row)
            return combo

        self.cbo_surface_mode = make_dxf_row(
            "表面模式 (surface_mode):", ['Fill', 'Contour'], 'dxf_surface_mode')
        self.cbo_pad_as_circle = make_dxf_row(
            "焊盘转圆 (Pad_as_Circle):", ['yes', 'no'], 'dxf_pad_as_circle')
        self.cbo_draft = make_dxf_row(
            "草稿模式 (draft):", ['no', 'yes', 'all'], 'dxf_draft')
        self.cbo_contour_to_hatch = make_dxf_row(
            "轮廓转填充 (contour_to_hatch):", ['yes', 'no'], 'dxf_contour_to_hatch')
        self.cbo_output_files = make_dxf_row(
            "文件模式 (output_files):", ['multiple', 'single'], 'dxf_output_files')

        scroll_layout.addWidget(dxf_group)

        # ==================== 日志输出设置 ====================
        log_group = QGroupBox("日志输出")
        log_layout = QVBoxLayout(log_group)
        log_layout.setSpacing(6)
        log_layout.setContentsMargins(10, 10, 10, 10)

        self.chk_log_enabled = QCheckBox("输出日志 (DXF 标注调试日志 cad_debug.log)")
        self.chk_log_enabled.setChecked(SETTINGS.get('dxf_log_enabled', True))
        log_layout.addWidget(self.chk_log_enabled)

        log_hint = QLabel("关闭后将不再生成/写入 *_cad_debug.log，也不打印标注日志")
        log_hint.setStyleSheet("color: #888888; font-size: 10px;")
        log_hint.setWordWrap(True)
        log_layout.addWidget(log_hint)

        scroll_layout.addWidget(log_group)

        # ==================== 图纸层命名分组（映射编辑器） ====================
        naming_group = QGroupBox("图纸层命名分组")
        naming_layout = QVBoxLayout(naming_group)
        naming_layout.setSpacing(4)
        naming_layout.setContentsMargins(8, 8, 8, 8)

        # 操作按钮行
        naming_btn_layout = QHBoxLayout()
        naming_btn_layout.setSpacing(6)
        btn_add_row = QPushButton("+ 添加映射")
        btn_add_row.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 4px 14px; border-radius: 3px; font-size: 11px; }"
            "QPushButton:hover { background-color: #388E3C; }"
        )
        btn_up_row = QPushButton("▲ 上移")
        btn_up_row.setStyleSheet(
            "QPushButton { background-color: #2196F3; color: white; font-weight: bold; padding: 4px 10px; border-radius: 3px; font-size: 11px; }"
            "QPushButton:hover { background-color: #1976D2; }"
        )
        btn_down_row = QPushButton("▼ 下移")
        btn_down_row.setStyleSheet(
            "QPushButton { background-color: #FF9800; color: white; font-weight: bold; padding: 4px 10px; border-radius: 3px; font-size: 11px; }"
            "QPushButton:hover { background-color: #F57C00; }"
        )
        naming_btn_layout.addWidget(btn_add_row)
        naming_btn_layout.addWidget(btn_up_row)
        naming_btn_layout.addWidget(btn_down_row)
        naming_btn_layout.addStretch()
        naming_layout.addLayout(naming_btn_layout)

        # 映射行容器（QScrollArea 内的 widget）
        self.naming_scroll_content = QWidget()
        self.naming_scroll_layout = QVBoxLayout(self.naming_scroll_content)
        self.naming_scroll_layout.setContentsMargins(2, 2, 2, 2)
        self.naming_scroll_layout.setSpacing(4)
        self.naming_scroll_layout.addStretch()

        self.naming_scroll = QScrollArea()
        self.naming_scroll.setWidgetResizable(True)
        self.naming_scroll.setMinimumHeight(100)
        self.naming_scroll.setMaximumHeight(200)
        self.naming_scroll.setWidget(self.naming_scroll_content)
        self.naming_scroll.setStyleSheet(
            "QScrollArea { border: 1px solid #CCC; border-radius: 3px; background: white; }"
        )
        naming_layout.addWidget(self.naming_scroll)

        # 加载已保存的映射数据
        self._naming_rows = []  # 存储每行控件引用: [{"combo": ..., "edit": ...}, ...]
        self._available_layers = []
        saved_naming = load_layer_naming()
        for mapping in saved_naming:
            if isinstance(mapping, dict):
                self._add_mapping_row(mapping.get("source", ""), mapping.get("target", ""))

        scroll_layout.addWidget(naming_group)

        # 滚动区域挂到主布局，保存/取消按钮固定在底部
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(scroll_content)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        layout.addWidget(scroll, 1)

        # 信号连接
        btn_add_row.clicked.connect(self._on_naming_add)
        btn_up_row.clicked.connect(self._on_naming_up)
        btn_down_row.clicked.connect(self._on_naming_down)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btn_save = QPushButton("保存并关闭")
        self.btn_save.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 8px 25px; border-radius: 4px; font-size: 13px; }"
            "QPushButton:hover { background-color: #388E3C; }"
        )
        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.setStyleSheet(
            "QPushButton { background-color: #9E9E9E; color: white; font-weight: bold; padding: 8px 20px; border-radius: 4px; font-size: 13px; }"
            "QPushButton:hover { background-color: #757575; }"
        )
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

        self.btn_save.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

    def _update_outline_ui(self):
        """根据单选按钮状态显示/隐藏自定义图层行"""
        is_custom = self.radio_custom.isChecked()
        for i in range(self.custom_layer_row.count()):
            item = self.custom_layer_row.itemAt(i)
            if item and item.widget():
                item.widget().setVisible(is_custom)
        if is_custom and hasattr(self, 'layers'):
            self.combo_outline_layer.clear()
            self.combo_outline_layer.addItems(self.layers)
            saved = SETTINGS.get('outline_layer', '')
            if saved and saved in self.layers:
                self.combo_outline_layer.setCurrentText(saved)

    def set_layers(self, layers):
        """从外部传入可用图层列表"""
        self.layers = layers
        self.combo_outline_layer.clear()
        self.combo_outline_layer.addItems(layers)
        saved = SETTINGS.get('outline_layer', '')
        if saved and saved in layers:
            self.combo_outline_layer.setCurrentText(saved)
        self._update_outline_ui()

    def update_layer_list(self, layer_names):
        """更新所有原始图层下拉列表的选项"""
        self._available_layers = list(layer_names)
        for row in self._naming_rows:
            combo = row["combo"]
            current = combo.currentText()
            combo.blockSignals(True)
            combo.clear()
            combo.addItems(self._available_layers)
            if (current and current != self.NONE_PLACEHOLDER
                    and current in self._available_layers):
                combo.setCurrentText(current)
            else:
                fb = row.get("fallback_source", "")
                if (fb and fb != self.NONE_PLACEHOLDER
                        and fb in self._available_layers):
                    # 原 key 存在于当前列表中，恢复显示原 key
                    combo.setCurrentText(fb)
                else:
                    # 原 key 不在当前列表（或未指定）：显示 None 占位，
                    # 直到用户重新指定新 key；JSON 中仍保留原 key
                    self._show_none_placeholder(combo)
            combo.blockSignals(False)

    def _show_none_placeholder(self, combo):
        """在下拉框中显示 None 占位（key 不在列表中或尚未指定时）"""
        idx = combo.findText(self.NONE_PLACEHOLDER)
        if idx < 0:
            combo.insertItem(0, self.NONE_PLACEHOLDER)
            idx = 0
        combo.setCurrentIndex(idx)

    def _add_mapping_row(self, source="", target=""):
        """添加一行映射: [QComboBox (source)] → [QLineEdit (target)] [X]"""
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(4)

        combo = QComboBox()
        combo.setEditable(False)
        combo.setMinimumWidth(100)
        if self._available_layers:
            combo.addItems(self._available_layers)
        if source and source in self._available_layers:
            combo.setCurrentText(source)
        elif source:
            # key 不在当前资料图层列表中：显示 None 占位，直到用户重新指定新 key；
            # 保存时仍保留原 key（fallback_source），确保 json 不变
            self._show_none_placeholder(combo)
        else:
            # 新加的空行：默认显示 None 占位，由用户选择图层
            self._show_none_placeholder(combo)
        row_layout.addWidget(combo)

        arrow = QLabel("  →  ")
        arrow.setStyleSheet("color: #666; font-weight: bold;")
        row_layout.addWidget(arrow)

        edit = QLineEdit()
        edit.setPlaceholderText("自定义导出名")
        edit.setText(target)
        edit.setMinimumWidth(120)
        row_layout.addWidget(edit)

        btn_del = QPushButton("✕")
        btn_del.setFixedSize(22, 22)
        btn_del.setStyleSheet(
            "QPushButton { background-color: #F44336; color: white; font-weight: bold; font-size: 10px; border-radius: 3px; }"
            "QPushButton:hover { background-color: #D32F2F; }"
        )
        row_layout.addWidget(btn_del)

        # 保存引用（fallback_source 保留原始 key，防止图层不在当前资料中时被覆盖为空；
        # last_source 记录当前选中值，用于重复 key 时的还原）
        row_data = {"combo": combo, "edit": edit, "widget": row_widget,
                    "del_btn": btn_del, "fallback_source": source,
                    "last_source": combo.currentText()}
        self._naming_rows.append(row_data)

        # 插入到 stretch 之前
        idx = self.naming_scroll_layout.count() - 1  # stretch 是最后一项
        self.naming_scroll_layout.insertWidget(idx, row_widget)

        # 删除按钮信号
        btn_del.clicked.connect(lambda checked, r=row_data: self._remove_mapping_row(r))
        # 选择变化时检查 key 是否重复（target 值允许重复，source key 不允许）
        combo.currentTextChanged.connect(self._on_naming_source_changed)

    def _on_naming_source_changed(self, text):
        """阻止同一个 source key 被多行重复使用。
        目标名称(target)允许重复，但每个图层(source)只能映射一次。
        """
        combo = self.sender()
        if not combo or not text:
            return
        # 找到当前行
        current_row = None
        for row in self._naming_rows:
            if row["combo"] is combo:
                current_row = row
                break
        if current_row is None:
            return
        # 检查其他行是否已使用该 key（显示 None 占位的行不参与冲突判断）
        if text != self.NONE_PLACEHOLDER:
            for row in self._naming_rows:
                if row is current_row:
                    continue
                if (row["combo"].currentText() != self.NONE_PLACEHOLDER
                        and row["combo"].currentText() == text):
                    prev = current_row.get("last_source", "")
                    combo.blockSignals(True)
                    if (prev and prev != text
                            and prev != self.NONE_PLACEHOLDER):
                        idx = combo.findText(prev)
                        if idx >= 0:
                            combo.setCurrentIndex(idx)
                    else:
                        self._show_none_placeholder(combo)
                    combo.blockSignals(False)
                    QMessageBox.warning(self, "重复图层",
                                        f"图层 [{text}] 已在列表中，每个图层只能映射一次。\n\n"
                                        f"（目标名称可以重复，但图层 key 不能重复）")
                    return
        # 无冲突，记录当前选择作为下次还原依据
        current_row["last_source"] = text

    def _remove_mapping_row(self, row_data):
        """删除指定行"""
        if row_data in self._naming_rows:
            self._naming_rows.remove(row_data)
            self.naming_scroll_layout.removeWidget(row_data["widget"])
            row_data["widget"].deleteLater()

    def get_naming_list(self):
        """返回当前图纸层映射列表
        格式: [{"source": "gtl", "target": "正面线路"}, ...]
        保证: source (key) 不重复，target 值允许重复（如 gto/gto1 都映射为"正面字符"）
        """
        result = []
        seen_sources = set()
        for row in self._naming_rows:
            source = row["combo"].currentText().strip()
            target = row["edit"].text().strip()
            if not source or source == self.NONE_PLACEHOLDER:
                # None 占位（key 不在列表中或未指定）→ 回退到原始 key，
                # 确保 json 中已有的映射不被覆盖为空/丢失
                source = row.get("fallback_source", "").strip()
            if not source or source in seen_sources:
                # 跳过空 key 与重复 key（保留先出现的映射）
                continue
            seen_sources.add(source)
            result.append({"source": source, "target": target if target else source})
        return result

    def _on_naming_add(self):
        """添加一行空白映射"""
        self._add_mapping_row()

    def _on_naming_up(self):
        """上移选中的行暂未实现焦点选择，使用整体上移最后添加的行"""
        # 简单实现：交换最后两行
        rows = self._naming_rows
        if len(rows) >= 2:
            r1 = rows[-2]
            r2 = rows[-1]
            # 交换位置
            idx1 = self.naming_scroll_layout.indexOf(r1["widget"])
            idx2 = self.naming_scroll_layout.indexOf(r2["widget"])
            if idx1 >= 0 and idx2 >= 0:
                self.naming_scroll_layout.removeWidget(r1["widget"])
                self.naming_scroll_layout.removeWidget(r2["widget"])
                self.naming_scroll_layout.insertWidget(idx2, r1["widget"])
                self.naming_scroll_layout.insertWidget(idx1, r2["widget"])
                rows[-2], rows[-1] = rows[-1], rows[-2]

    def _on_naming_down(self):
        """下移（同 _on_naming_up 逻辑）"""
        self._on_naming_up()

    def get_settings(self):
        mode = 'custom' if self.radio_custom.isChecked() else 'default'
        return {
            'rout_width': self.spin_rout.value(),
            'min_gap': self.spin_gap.value(),
            'outline_mode': mode,
            'outline_layer': self.combo_outline_layer.currentText() if mode == 'custom' else '',
            # DXF 导出参数
            'dxf_surface_mode': self.cbo_surface_mode.currentText(),
            'dxf_pad_as_circle': self.cbo_pad_as_circle.currentText(),
            'dxf_draft': self.cbo_draft.currentText(),
            'dxf_contour_to_hatch': self.cbo_contour_to_hatch.currentText(),
            'dxf_output_files': self.cbo_output_files.currentText(),
            'dxf_output_tz': self.chk_output_tz.isChecked(),
            # 是否标注层
            'dxf_annotate_enabled': self.chk_annotate.isChecked(),
            # 日志输出
            'dxf_log_enabled': self.chk_log_enabled.isChecked(),
        }


# ==================== 可拖拽排序列表控件 ====================
class DraggableListWidget(QListWidget):
    count_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSelectionMode(QListWidget.SingleSelection)
        self.setDragDropMode(QListWidget.InternalMove)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDefaultDropAction(Qt.MoveAction)
        self._drag_row = -1

        self.setStyleSheet("""
            QListWidget {
                border: 2px solid #CCCCCC; border-radius: 5px; padding: 3px;
                background-color: white; font-size: 12px;
            }
            QListWidget::item {
                padding: 3px 6px; margin: 1px 0;
                border-bottom: 1px solid #E0E0E0;
            }
            QListWidget::item:selected { background-color: #E8F5E9; color: #000000; }
            QListWidget::item:hover { background-color: #F5F5F5; }
        """)

    def add_item(self, text, is_checked=False):
        item = QListWidgetItem(text)
        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
        item.setCheckState(Qt.Checked if is_checked else Qt.Unchecked)
        self.addItem(item)
        self.count_changed.emit(self.count())

    def get_items(self):
        return [self.item(i).text() for i in range(self.count())]

    def get_checked_states(self):
        states = {}
        for i in range(self.count()):
            item = self.item(i)
            states[item.text()] = item.checkState() == Qt.Checked
        return states

    def set_checked_states(self, states):
        for i in range(self.count()):
            item = self.item(i)
            if item.text() in states:
                item.setCheckState(Qt.Checked if states[item.text()] else Qt.Unchecked)

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if item:
            self._drag_row = self.row(item)
            drag = QDrag(self)
            mime = self.model().mimeData([self.currentIndex()])
            drag.setMimeData(mime)
            drag.exec_(Qt.MoveAction)

    def dropEvent(self, event):
        source_row = self._drag_row
        if source_row < 0 or source_row >= self.count():
            event.ignore()
            return

        target_row = self._calc_target(event.pos().y())

        if source_row == target_row or source_row + 1 == target_row:
            event.ignore()
            return

        item = self.takeItem(source_row)
        insert_idx = target_row - 1 if source_row < target_row else target_row
        self.insertItem(insert_idx, item)
        self.setCurrentRow(insert_idx)

        event.setDropAction(Qt.MoveAction)
        event.accept()

    def _calc_target(self, y):
        for i in range(self.count()):
            r = self.visualItemRect(self.item(i))
            if y < r.top() + r.height() / 2:
                return i
        return self.count()


# ==================== 图层排序与镜像配置对话框 ====================
class LayerReorderDialog(QDialog):
    """拖拽排序对话框 - 用于调整图层处理顺序和设置镜像"""
    def __init__(self, layers, parent=None):
        super().__init__(parent)
        self.setWindowTitle("调整图层顺序 - 拖拽排序")
        self.resize(380, 580)
        self.setWindowModality(Qt.ApplicationModal)

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(6)
        main_layout.setContentsMargins(10, 10, 10, 10)

        info_label = QLabel(f"共 {len(layers)} 个图层，拖拽调整顺序，勾选复选框进行X轴镜像")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet(
            "color: #0066CC; font-weight: bold; padding: 6px; background-color: #F0F8FF; border-radius: 4px; font-size: 11px;"
        )
        main_layout.addWidget(info_label)

        list_group = QGroupBox("图层顺序")
        list_layout = QVBoxLayout(list_group)
        list_layout.setContentsMargins(6, 6, 6, 6)
        list_layout.setSpacing(4)

        mirror_btn_layout = QHBoxLayout()
        mirror_btn_layout.setSpacing(4)
        mirror_btn_layout.addWidget(QLabel("镜像:"))

        self.btn_mirror_all = QPushButton("全部勾选")
        self.btn_mirror_all.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 3px 10px; border-radius: 3px; font-size: 10px; }"
            "QPushButton:hover { background-color: #388E3C; }"
        )
        self.btn_mirror_none = QPushButton("取消全部")
        self.btn_mirror_none.setStyleSheet(
            "QPushButton { background-color: #F44336; color: white; font-weight: bold; padding: 3px 10px; border-radius: 3px; font-size: 10px; }"
            "QPushButton:hover { background-color: #D32F2F; }"
        )
        mirror_btn_layout.addWidget(self.btn_mirror_all)
        mirror_btn_layout.addWidget(self.btn_mirror_none)
        mirror_btn_layout.addStretch()
        list_layout.addLayout(mirror_btn_layout)

        self.list_widget = DraggableListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                border: 1px solid #CCCCCC; border-radius: 3px; padding: 2px;
                background-color: white; font-size: 11px;
            }
            QListWidget::item {
                padding: 2px 4px; margin: 0;
            }
            QListWidget::item:selected { background-color: #E8F5E9; color: #000000; }
            QListWidget::item:hover { background-color: #F5F5F5; }
        """)
        mirror_config = load_mirror_config()
        for layer in layers:
            is_checked = layer in mirror_config and mirror_config[layer]
            self.list_widget.add_item(layer, is_checked)
        list_layout.addWidget(self.list_widget)
        main_layout.addWidget(list_group, 1)

        # 移动按钮组
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        self.btn_move_top = QPushButton("置顶")
        self.btn_move_up = QPushButton("上移")
        self.btn_move_down = QPushButton("下移")
        self.btn_move_bottom = QPushButton("置底")
        for btn, style in zip(
            [self.btn_move_top, self.btn_move_up, self.btn_move_down, self.btn_move_bottom],
            ["#2196F3", "#4CAF50", "#FF9800", "#9C27B0"]
        ):
            btn.setStyleSheet(
                f"QPushButton {{ background-color: {style}; color: white; font-weight: bold; padding: 8px 15px; border-radius: 4px; font-size: 12px; }}"
                "QPushButton:hover { background-color: #1976D2; }" if style == "#2196F3" else
                f"QPushButton:hover {{ background-color: {style}; }}"
            )
        button_layout.addWidget(self.btn_move_top)
        button_layout.addWidget(self.btn_move_up)
        button_layout.addWidget(self.btn_move_down)
        button_layout.addWidget(self.btn_move_bottom)
        main_layout.addLayout(button_layout)

        # 配置按钮 + 确认按钮
        config_confirm_layout = QHBoxLayout()
        config_confirm_layout.setSpacing(10)
        self.btn_save_mirror = QPushButton("保存镜像配置")
        self.btn_save_mirror.setStyleSheet(
            "QPushButton { background-color: #FF9800; color: white; font-weight: bold; padding: 10px 20px; border-radius: 4px; font-size: 12px; }"
            "QPushButton:hover { background-color: #F57C00; }"
        )
        self.btn_load_mirror = QPushButton("加载镜像配置")
        self.btn_load_mirror.setStyleSheet(
            "QPushButton { background-color: #2196F3; color: white; font-weight: bold; padding: 10px 20px; border-radius: 4px; font-size: 12px; }"
            "QPushButton:hover { background-color: #1976D2; }"
        )
        config_confirm_layout.addWidget(self.btn_save_mirror)
        config_confirm_layout.addWidget(self.btn_load_mirror)
        config_confirm_layout.addStretch()

        self.btn_confirm = QPushButton("确认继续")
        self.btn_confirm.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 12px 50px; border-radius: 5px; font-size: 14px; }"
            "QPushButton:hover { background-color: #388E3C; }"
        )
        self.btn_confirm.setMinimumWidth(160)
        config_confirm_layout.addWidget(self.btn_confirm)
        main_layout.addLayout(config_confirm_layout)

        # 信号连接
        self.btn_move_top.clicked.connect(self.move_to_top)
        self.btn_move_up.clicked.connect(self.move_up)
        self.btn_move_down.clicked.connect(self.move_down)
        self.btn_move_bottom.clicked.connect(self.move_to_bottom)
        self.btn_mirror_all.clicked.connect(self.mirror_all)
        self.btn_mirror_none.clicked.connect(self.mirror_none)
        self.btn_save_mirror.clicked.connect(self.save_mirror_config)
        self.btn_load_mirror.clicked.connect(self.load_mirror_config)
        self.btn_confirm.clicked.connect(self.accept)

    def move_to_top(self):
        idx = self.list_widget.currentRow()
        if idx < 0:
            QMessageBox.warning(self, "提示", "请先点击选中一个图层")
            return
        if idx == 0:
            return
        self._move_row(idx, 0)

    def move_up(self):
        idx = self.list_widget.currentRow()
        if idx < 0:
            QMessageBox.warning(self, "提示", "请先点击选中一个图层")
            return
        if idx == 0:
            return
        self._move_row(idx, idx - 1)

    def move_down(self):
        idx = self.list_widget.currentRow()
        if idx < 0:
            QMessageBox.warning(self, "提示", "请先点击选中一个图层")
            return
        if idx == self.list_widget.count() - 1:
            return
        self._move_row(idx, idx + 1)

    def move_to_bottom(self):
        idx = self.list_widget.currentRow()
        if idx < 0:
            QMessageBox.warning(self, "提示", "请先点击选中一个图层")
            return
        last = self.list_widget.count() - 1
        if idx == last:
            return
        self._move_row(idx, last)

    def _move_row(self, source_row, target_row):
        item = self.list_widget.takeItem(source_row)
        self.list_widget.insertItem(target_row, item)
        self.list_widget.setCurrentRow(target_row)

    def mirror_all(self):
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setCheckState(Qt.Checked)

    def mirror_none(self):
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setCheckState(Qt.Unchecked)

    def get_ordered_layers(self):
        return self.list_widget.get_items()

    def get_layer_config(self):
        configs = []
        checked_states = self.list_widget.get_checked_states()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            configs.append({
                'layer': item.text(),
                'mirror': checked_states.get(item.text(), False)
            })
        return configs

    def save_mirror_config(self):
        mirror_dict = self.list_widget.get_checked_states()
        if save_mirror_config(mirror_dict):
            mirror_count = sum(1 for v in mirror_dict.values() if v)
            QMessageBox.information(self, "保存成功",
                                    f"已保存 {len(mirror_dict)} 个图层的镜像配置\n\n"
                                    f"其中 {mirror_count} 个图层需要镜像\n\n"
                                    f"保存位置:\n{COMBINED_CONFIG_FILE}\n\n"
                                    f"命名空间: mirror_config")
        else:
            QMessageBox.critical(self, "保存失败",
                                 f"保存镜像配置失败\n\n请检查目录权限:\n{GENESIS_SCRIPTS_DIR}")

    def load_mirror_config(self):
        mirror_config = load_mirror_config()
        if not mirror_config:
            QMessageBox.information(self, "提示",
                                    "配置文件中没有保存的镜像设置\n\n"
                                    "请先使用【保存镜像配置】按钮保存配置")
            return
        applied = 0
        for layer in mirror_config:
            if layer in self.list_widget.get_items():
                applied += 1
        self.list_widget.set_checked_states(mirror_config)
        QMessageBox.information(self, "已应用配置",
                                f"已加载 {applied} 个图层的镜像配置\n\n"
                                f"配置: {', '.join([k for k, v in mirror_config.items() if v][:5])}{'...' if len([k for k, v in mirror_config.items() if v]) > 5 else ''}")

# ==================== 图层选择与布局预览主对话框 ====================
class LayerSelectDialog(QDialog):
    def __init__(self, layers, parent=None):
        super().__init__(parent)
        self.setWindowTitle("DXF图纸输出  作者：LP QQ：2694551464 V2.3")
        self.resize(420, 750)
        self.setWindowModality(Qt.ApplicationModal)

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(8)

        # 顶部标题栏 + 齿轮设置按钮
        title_bar = QHBoxLayout()
        title_bar.setSpacing(5)
        title_label = QLabel(f"共有 {len(layers)} 个图层，请勾选需要处理的：")
        title_bar.addWidget(title_label)
        title_bar.addStretch()
        self.btn_settings = QPushButton("⚙")
        self.btn_settings.setFixedSize(32, 28)
        self.btn_settings.setToolTip("全局设置")
        # 防止空格/回车误触发打开设置界面：
        # NoFocus 不让它抢键盘焦点（空格不再激活它），
        # autoDefault=False 不让它成为对话框默认按钮（回车不再触发它）
        self.btn_settings.setFocusPolicy(Qt.NoFocus)
        self.btn_settings.setAutoDefault(False)
        self.btn_settings.setStyleSheet(
            "QPushButton { background-color: #607D8B; color: white; font-weight: bold; font-size: 16px; border-radius: 4px; }"
            "QPushButton:hover { background-color: #455A64; }"
        )
        title_bar.addWidget(self.btn_settings)

        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(8)

        top_layout.addLayout(title_bar)

        direction_layout = QHBoxLayout()
        direction_layout.addWidget(QLabel("排列方向："))
        self.radio_x = QCheckBox("X轴排列")
        self.radio_y = QCheckBox("Y轴排列")
        self.radio_x.setChecked(False)
        self.radio_y.setChecked(False)
        direction_layout.addWidget(self.radio_x)
        direction_layout.addWidget(self.radio_y)
        top_layout.addLayout(direction_layout)

        output_group = QGroupBox("输出设置")
        output_layout = QVBoxLayout()
        output_layout.setSpacing(6)
        output_layout.setContentsMargins(5, 5, 5, 5)

        spacing_group = QGroupBox("间距设置")
        spacing_layout = QVBoxLayout()
        spacing_layout.setSpacing(5)
        spacing_layout.setContentsMargins(5, 5, 5, 5)

        if board_width >= board_height:
            length_dim, width_dim = board_width, board_height
        else:
            length_dim, width_dim = board_height, board_width

        self.board_size_label = QLabel(f"板子尺寸: 长 {length_dim:.2f}mm × 宽 {width_dim:.2f}mm")
        self.board_size_label.setStyleSheet(
            "color: #0066CC; font-weight: bold; padding: 3px; background-color: #F0F8FF; border-radius: 3px; font-size: 11px;")
        spacing_layout.addWidget(self.board_size_label)

        self.rb_fixed_spacing = QCheckBox("固定间距模式")
        self.rb_fixed_spacing.setChecked(False)
        spacing_layout.addWidget(self.rb_fixed_spacing)

        fixed_spacing_layout = QHBoxLayout()
        fixed_spacing_layout.addWidget(QLabel("X间距:"))
        self.spin_x_spacing = QDoubleSpinBox()
        self.spin_x_spacing.setRange(10, 500)
        self.spin_x_spacing.setValue(30)
        self.spin_x_spacing.setSuffix(" mm")
        self.spin_x_spacing.setDecimals(1)
        self.spin_x_spacing.setMaximumWidth(80)
        fixed_spacing_layout.addWidget(self.spin_x_spacing)

        fixed_spacing_layout.addWidget(QLabel("Y间距:"))
        self.spin_y_spacing = QDoubleSpinBox()
        self.spin_y_spacing.setRange(10, 500)
        self.spin_y_spacing.setValue(30)
        self.spin_y_spacing.setSuffix(" mm")
        self.spin_y_spacing.setDecimals(1)
        self.spin_y_spacing.setMaximumWidth(80)
        fixed_spacing_layout.addWidget(self.spin_y_spacing)

        spacing_layout.addLayout(fixed_spacing_layout)

        self.rb_auto_spacing = QCheckBox("智能间距模式（自动计算）")
        self.rb_auto_spacing.setChecked(True)
        spacing_layout.addWidget(self.rb_auto_spacing)

        spacing_group.setLayout(spacing_layout)
        output_layout.addWidget(spacing_group)

        self.fixed_layout_group = QGroupBox("布局设置（固定模式）")
        fixed_layout_layout = QHBoxLayout()
        fixed_layout_layout.setSpacing(10)
        fixed_layout_layout.setContentsMargins(5, 5, 5, 5)

        fixed_layout_layout.addWidget(QLabel("列数:"))
        self.spin_cols = QDoubleSpinBox()
        self.spin_cols.setRange(1, 50)
        self.spin_cols.setValue(1)
        self.spin_cols.setDecimals(0)
        self.spin_cols.setMaximumWidth(70)
        fixed_layout_layout.addWidget(self.spin_cols)

        fixed_layout_layout.addWidget(QLabel("行数:"))
        self.spin_rows = QDoubleSpinBox()
        self.spin_rows.setRange(1, 50)
        self.spin_rows.setValue(1)
        self.spin_rows.setDecimals(0)
        self.spin_rows.setMaximumWidth(70)
        fixed_layout_layout.addWidget(self.spin_rows)

        fixed_layout_layout.addWidget(QLabel("旋转:"))
        self.combo_rotation = QComboBox()
        self.combo_rotation.addItems(["0°", "90°", "180°", "270°"])
        self.combo_rotation.setCurrentIndex(0)
        self.combo_rotation.setMaximumWidth(70)
        fixed_layout_layout.addWidget(self.combo_rotation)

        fixed_layout_layout.addSpacing(15)
        self.layout_selected_label = QLabel("已选: 0 层")
        self.layout_selected_label.setStyleSheet(
            "color: #FF6600; font-weight: bold; font-size: 12px; padding: 2px 8px; background-color: #FFF5E6; border: 1px solid #FFB366; border-radius: 3px;")
        fixed_layout_layout.addWidget(self.layout_selected_label)

        self.btn_save_preset = QPushButton("保存为预选层")
        self.btn_save_preset.setStyleSheet(
            "background-color: #2196F3; color: white; font-weight: bold; font-size: 11px; padding: 2px 10px; border-radius: 3px;")
        self.btn_save_preset.setToolTip("将当前已勾选的图层保存为默认配置")
        fixed_layout_layout.addWidget(self.btn_save_preset)

        fixed_layout_layout.addStretch()

        self.fixed_layout_group.setLayout(fixed_layout_layout)
        output_layout.addWidget(self.fixed_layout_group)

        output_group.setLayout(output_layout)
        top_layout.addWidget(output_group)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setMinimumHeight(150)

        scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_content)
        self.scroll_layout.setContentsMargins(8, 8, 8, 8)
        self.scroll_layout.setSpacing(3)

        self.checkboxes = []
        for layer in layers:
            cb = QCheckBox(layer)
            cb.setChecked(False)
            cb.stateChanged.connect(self.update_preview)
            cb.stateChanged.connect(self.update_selected_count)
            self.scroll_layout.addWidget(cb)
            self.checkboxes.append(cb)

        self.scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        top_layout.addWidget(scroll, 1)

        btn_layout = QHBoxLayout()
        self.btn_select_all = QPushButton("全选")
        self.btn_deselect_all = QPushButton("取消全选")

        self.btn_select_config = QPushButton("勾选配置层")
        self.btn_select_config.setStyleSheet(
            "background-color: #FF9800; color: white; font-weight: bold; padding: 6px 15px; min-width: 100px;")

        self.btn_confirm = QPushButton("确定")
        self.btn_confirm.setStyleSheet(
            "background-color: #4CAF50; color: white; font-weight: bold; padding: 6px 20px; min-width: 80px;")
        # 明确指定"确定"为对话框默认按钮：回车触发确定而不是误触发其他按钮
        self.btn_confirm.setDefault(True)

        btn_layout.addWidget(self.btn_select_all)
        btn_layout.addWidget(self.btn_deselect_all)
        btn_layout.addWidget(self.btn_select_config)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_confirm)
        top_layout.addLayout(btn_layout)

        main_layout.addWidget(top_widget, 1)

        preview_group = QGroupBox("布局预览")
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.setContentsMargins(5, 5, 5, 5)

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setBackgroundBrush(QColor("#FAFAFA"))
        self.view.setMinimumHeight(150)
        preview_layout.addWidget(self.view)

        main_layout.addWidget(preview_group, 1)

        self.btn_select_all.clicked.connect(lambda: [cb.setChecked(True) for cb in self.checkboxes])
        self.btn_deselect_all.clicked.connect(lambda: [cb.setChecked(False) for cb in self.checkboxes])
        self.btn_select_config.clicked.connect(self.select_config_layers)
        self.btn_save_preset.clicked.connect(self.save_preset_layers)
        self.btn_confirm.clicked.connect(self.accept)
        self.btn_settings.clicked.connect(self.openSettings)

        self.radio_x.stateChanged.connect(self.update_preview)
        self.radio_y.stateChanged.connect(self.update_preview)
        self.rb_fixed_spacing.stateChanged.connect(self.on_fixed_spacing_changed)
        self.rb_auto_spacing.stateChanged.connect(self.on_auto_spacing_changed)
        self.spin_x_spacing.valueChanged.connect(self.update_preview)
        self.spin_y_spacing.valueChanged.connect(self.update_preview)
        self.spin_cols.valueChanged.connect(self.update_preview)
        self.spin_rows.valueChanged.connect(self.update_preview)
        self.combo_rotation.currentIndexChanged.connect(self.update_preview)

        self.update_preview()

    def openSettings(self):
        """打开齿轮设置对话框"""
        dlg = SettingsDialog(self)
        dlg.set_layers(all_layers)
        dlg.update_layer_list(all_layers)
        if dlg.exec_() == QDialog.Accepted:
            new_s = dlg.get_settings()
            global SETTINGS
            SETTINGS.update(new_s)
            saveSettings(new_s)
            # 保存图纸层命名（独立命名空间，不影响 settings）
            naming_list = dlg.get_naming_list()
            save_layer_naming(naming_list)
            QMessageBox.information(self, "设置已保存",
                                    "全局设置已保存并生效\n\n"
                                    "· 轮廓线宽: {} mm\n"
                                    "· 最小间距: {} mm\n"
                                    "· 轮廓模式: {}\n"
                                    "· 标注层: {}\n"
                                    "· 日志输出: {}\n"
                                    "· 图纸层命名: {} 条".format(
                                        new_s['rout_width'],
                                        new_s['min_gap'],
                                        "自定义 ({})".format(new_s['outline_layer']) if new_s['outline_mode'] == 'custom' else "默认 ProfileToRout",
                                        "开" if new_s.get('dxf_annotate_enabled', True) else "关",
                                        "开" if new_s.get('dxf_log_enabled', True) else "关",
                                        len(naming_list)))

    def select_config_layers(self):
        """勾选配置文件中的图层"""
        config_layers = load_default_layers()
        if not config_layers:
            QMessageBox.information(None, "提示",
                                    "配置文件中没有默认图层设置\n\n"
                                    "请先使用【保存为预选层】按钮保存配置")
            return

        self._apply_layer_selection(config_layers)
        QMessageBox.information(None, "已应用配置",
                                f"已勾选 {len(config_layers)} 个配置图层\n\n"
                                f"配置: {', '.join(config_layers[:5])}{'...' if len(config_layers) > 5 else ''}")

    def save_preset_layers(self):
        """保存当前已勾选的图层为默认配置，支持新建或追加"""
        selected_layers = [cb.text() for cb in self.checkboxes if cb.isChecked()]

        if not selected_layers:
            QMessageBox.warning(None, "警告", "当前没有勾选任何图层\n\n请先勾选需要保存的图层")
            return

        existing_layers = load_default_layers()

        if existing_layers:
            msg_box = QMessageBox()
            msg_box.setWindowTitle("保存配置")
            msg_box.setText(f"当前已有 {len(existing_layers)} 个配置图层\n\n请选择保存方式：")

            btn_new = msg_box.addButton("新建（覆盖）", QMessageBox.AcceptRole)
            btn_append = msg_box.addButton("追加（合并）", QMessageBox.AcceptRole)
            msg_box.addButton("取消", QMessageBox.RejectRole)

            msg_box.exec_()
            clicked_button = msg_box.clickedButton()

            if clicked_button == msg_box.button(QMessageBox.Cancel):
                return
            elif clicked_button == btn_new:
                final_layers = selected_layers
                action_text = "新建"
            else:
                final_layers = list(dict.fromkeys(existing_layers + selected_layers))
                added_count = len(final_layers) - len(existing_layers)
                action_text = f"追加（新增 {added_count} 个）"
        else:
            final_layers = selected_layers
            action_text = "新建"

        if save_default_layers(final_layers):
            QMessageBox.information(None, "保存成功",
                                    f"已{action_text}保存 {len(final_layers)} 个图层为默认配置\n\n"
                                    f"保存位置:\n{COMBINED_CONFIG_FILE}\n\n"
                                    f"命名空间: layer_config\n\n"
                                    f"图层: {', '.join(final_layers[:5])}{'...' if len(final_layers) > 5 else ''}")
        else:
            QMessageBox.critical(None, "保存失败",
                                 f"保存图层配置失败\n\n请检查目录权限:\n{GENESIS_SCRIPTS_DIR}")

    def _apply_layer_selection(self, layer_names):
        """根据图层名称列表勾选对应的复选框"""
        for cb in self.checkboxes:
            cb.setChecked(False)

        matched_count = 0
        for cb in self.checkboxes:
            if cb.text() in layer_names:
                cb.setChecked(True)
                matched_count += 1

        self.update_selected_count()
        self.update_preview()

        return matched_count

    def update_selected_count(self):
        """更新已选择图层数量的显示"""
        selected_count = sum(1 for cb in self.checkboxes if cb.isChecked())

        try:
            user_cols = int(self.spin_cols.value())
            user_rows = int(self.spin_rows.value())
            capacity = user_cols * user_rows
            is_over_capacity = selected_count > capacity and self.rb_fixed_spacing.isChecked()
        except:
            is_over_capacity = False

        if is_over_capacity:
            self.layout_selected_label.setText(f" {selected_count} 层")
        else:
            self.layout_selected_label.setText(f"已选: {selected_count} 层")

        if is_over_capacity:
            layout_style = "color: #FF0000; font-weight: bold; font-size: 12px; padding: 2px 8px; background-color: #FFE6E6; border: 2px solid #FF0000; border-radius: 3px;"
        elif selected_count == 0:
            layout_style = "color: #999999; font-weight: bold; font-size: 12px; padding: 2px 8px; background-color: #F5F5F5; border: 1px solid #CCCCCC; border-radius: 3px;"
        elif selected_count <= 5:
            layout_style = "color: #FF6600; font-weight: bold; font-size: 12px; padding: 2px 8px; background-color: #FFF5E6; border: 1px solid #FFB366; border-radius: 3px;"
        else:
            layout_style = "color: #0066CC; font-weight: bold; font-size: 12px; padding: 2px 8px; background-color: #E6F3FF; border: 1px solid #66B2FF; border-radius: 3px;"

        self.layout_selected_label.setStyleSheet(layout_style)

    def on_fixed_spacing_changed(self, state):
        if state == Qt.Checked:
            self.rb_auto_spacing.setChecked(False)
            self.spin_x_spacing.setEnabled(True)
            self.spin_y_spacing.setEnabled(True)
            self.fixed_layout_group.setEnabled(True)
        self.update_preview()

    def on_auto_spacing_changed(self, state):
        if state == Qt.Checked:
            self.rb_fixed_spacing.setChecked(False)
            self.spin_x_spacing.setEnabled(False)
            self.spin_y_spacing.setEnabled(False)
            self.fixed_layout_group.setEnabled(False)
        self.update_preview()

    def update_preview(self):
        """根据当前设置绘制简易预览图"""
        self.scene.clear()

        selected_layers = [cb.text() for cb in self.checkboxes if cb.isChecked()]
        selected_count = len(selected_layers)

        if selected_count == 0:
            return

        use_auto = self.rb_auto_spacing.isChecked()
        primary_axis = 'X' if self.radio_x.isChecked() else ('Y' if self.radio_y.isChecked() else None)

        try:
            x_input = self.spin_x_spacing.value()
            y_input = self.spin_y_spacing.value()
            user_cols = int(self.spin_cols.value())
            user_rows = int(self.spin_rows.value())
            user_rot_idx = self.combo_rotation.currentIndex()
            user_rotation = [0, 90, 180, 270][user_rot_idx]
        except:
            x_input, y_input = 30, 30
            user_cols, user_rows = 1, 1
            user_rotation = 0

        if use_auto:
            x_step, y_step, cols, rows, col_distribution, is_rotated, draw_w, draw_h = self._calculate_auto_layout(
                selected_count, board_width, board_height, primary_axis
            )
        else:
            cols = user_cols
            rows = user_rows
            x_step = x_input
            y_step = y_input

            # 手动模式旋转：90°/270°时宽高互换
            if user_rotation in (90, 270):
                draw_w = board_height
                draw_h = board_width
            else:
                draw_w = board_width
                draw_h = board_height

            col_distribution = [cols] * rows

            if cols * rows < selected_count:
                rows = math.ceil(selected_count / cols)
                col_distribution = [cols] * (rows - 1) + [selected_count - cols * (rows - 1)]

        scale = 0.5
        pen = QPen(QColor("#333333"), 1)
        brush = QBrush(QColor("#87CEEB"))

        total_w = cols * draw_w * scale + (cols - 1) * (x_step - draw_w) * scale
        total_h = rows * draw_h * scale + (rows - 1) * (y_step - draw_h) * scale

        start_x = -total_w / 2
        start_y = -total_h / 2

        layer_idx = 0
        for row_idx, row_cols in enumerate(col_distribution):
            for col_idx in range(row_cols):
                if layer_idx >= selected_count:
                    break

                px = start_x + col_idx * x_step * scale
                py = start_y + row_idx * y_step * scale

                rect = QGraphicsRectItem(px, py, draw_w * scale, draw_h * scale)
                rect.setPen(pen)
                rect.setBrush(brush)
                self.scene.addItem(rect)

                layer_name = selected_layers[layer_idx]
                if len(layer_name) > 10:
                    display_name = layer_name[:8] + ".."
                else:
                    display_name = layer_name

                text = self.scene.addText(display_name)
                font = text.font()
                font.setPointSize(6)
                text.setFont(font)

                text_width = len(display_name) * 4
                text.setPos(px + (draw_w * scale - text_width) / 2, py + (draw_h * scale - 6) / 2)

                layer_idx += 1

            if layer_idx >= selected_count:
                break

        if self.scene.itemsBoundingRect().width() > 0:
            self.view.fitInView(self.scene.itemsBoundingRect(), Qt.KeepAspectRatio)
            self.view.scale(0.8, 0.8)

    def _calculate_auto_layout(self, total_count, bw, bh, primary_axis):
        """AUTO模式：黄金比例布局，对比旋转/非旋转选最接近1.618的方案"""
        if primary_axis == 'Y':
            return bw + 10, bh + 10, 1, total_count, [1] * total_count, False, bw, bh

        GOLDEN_RATIO = 1.618
        min_safe_gap = 10
        best_overall_config = None
        best_overall_score = float('inf')
        best_is_rotated = False

        for try_rotate in [False, True]:
            if try_rotate:
                eff_w = bh
                eff_h = bw
            else:
                eff_w = bw
                eff_h = bh

            panel_available_width = max(bw, bh) * 4.0 + 100
            max_cols = int((panel_available_width + min_safe_gap) / (eff_w + min_safe_gap))
            max_cols = max(1, min(max_cols, total_count))

            for cols in range(max_cols, 0, -1):
                rows = math.ceil(total_count / cols)
                total_width = cols * eff_w + (cols - 1) * min_safe_gap
                total_height = rows * eff_h + (rows - 1) * min_safe_gap
                ratio = total_width / total_height if total_height > 0 else 999
                score = abs(ratio - GOLDEN_RATIO)
                if cols <= rows:
                    score += 100

                if score < best_overall_score:
                    best_overall_score = score
                    best_overall_config = {
                        'cols': cols,
                        'rows': rows,
                        'col_dist': [cols] * rows,
                        'x_step': eff_w + 10,
                        'y_step': eff_h + 10,
                        'total_width': total_width,
                        'total_height': total_height
                    }
                    best_is_rotated = try_rotate

            for full_row_cols in range(max_cols, 1, -1):
                full_rows = total_count // full_row_cols
                remaining = total_count % full_row_cols
                if remaining == 0:
                    continue

                col_dist = [full_row_cols] * full_rows + [remaining]
                actual_rows = len(col_dist)
                total_width = full_row_cols * eff_w + (full_row_cols - 1) * min_safe_gap
                total_height = actual_rows * eff_h + (actual_rows - 1) * min_safe_gap
                ratio = total_width / total_height if total_height > 0 else 999
                score = abs(ratio - GOLDEN_RATIO)
                if full_row_cols <= actual_rows:
                    score += 100

                if score < best_overall_score:
                    best_overall_score = score
                    best_overall_config = {
                        'cols': full_row_cols,
                        'rows': actual_rows,
                        'col_dist': col_dist,
                        'x_step': eff_w + 10,
                        'y_step': eff_h + 10,
                        'total_width': total_width,
                        'total_height': total_height
                    }
                    best_is_rotated = try_rotate

        if best_overall_config:
            eff_draw_w = bh if best_is_rotated else bw
            eff_draw_h = bw if best_is_rotated else bh
            return (best_overall_config['x_step'], best_overall_config['y_step'],
                    best_overall_config['cols'], best_overall_config['rows'],
                    best_overall_config['col_dist'], best_is_rotated,
                    eff_draw_w, eff_draw_h)
        else:
            return bw + 10, bh + 10, total_count, 1, [total_count], False, bw, bh

    def get_selected(self):
        return [cb.text() for cb in self.checkboxes if cb.isChecked()]

    def get_direction(self):
        if self.radio_y.isChecked():
            return 'Y'
        elif self.radio_x.isChecked():
            return 'X'
        else:
            return None

    def get_spacing_mode(self):
        if self.rb_auto_spacing.isChecked():
            return 'auto'
        else:
            return 'fixed'

    def get_custom_spacing(self):
        rotation_idx = self.combo_rotation.currentIndex()
        return {
            'mode': self.get_spacing_mode(),
            'x_spacing': self.spin_x_spacing.value(),
            'y_spacing': self.spin_y_spacing.value(),
            'cols': int(self.spin_cols.value()),
            'rows': int(self.spin_rows.value()),
            'rotation': [0, 90, 180, 270][rotation_idx]
        }


# ==================== 文件占用检测与解锁 ====================
def is_file_locked(path):
    """检测文件是否被其他程序(exe)占用"""
    if not path or not os.path.exists(path):
        return False
    try:
        with open(path, 'a'):
            return False
    except (PermissionError, OSError):
        return True


def unlock_file_locked(path):
    """尝试关闭占用文件的进程(psutil)，成功解锁返回 True"""
    try:
        import psutil
        target = os.path.normcase(os.path.abspath(path))
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                for f in proc.open_files():
                    try:
                        if os.path.normcase(os.path.abspath(f.path)) == target:
                            proc.terminate()
                            proc.wait(timeout=5)
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                        continue
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception:
        pass
    return not is_file_locked(path)


def append_result_log(msg):
    """追加一行日志到桌面 AUTO_MI_result.log（错误/异常信息，不再弹窗）"""
    try:
        _p = os.path.join(os.path.expanduser("~"), "Desktop", "AUTO_MI_result.log")
        with open(_p, 'a', encoding='utf-8') as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass


# ==================== 主交互循环：布局计算 ====================
while True:
    while True:
        dialog = LayerSelectDialog(all_layers)
        result = dialog.exec_()

        if result == QDialog.Rejected:
            sys.exit(0)

        selected_layers = dialog.get_selected()

        if selected_layers:
            reorder_dialog = LayerReorderDialog(selected_layers)
            reorder_result = reorder_dialog.exec_()

            if reorder_result == QDialog.Rejected:
                continue

            # 获取用户配置的图层顺序和镜像设置
            layer_config = reorder_dialog.get_layer_config()
            selected_layers = [config['layer'] for config in layer_config]
            mirror_layers = {config['layer']: config['mirror'] for config in layer_config}

        user_direction = dialog.get_direction()
        spacing_config = dialog.get_custom_spacing()
        use_auto_spacing = spacing_config['mode'] == 'auto'

        if not selected_layers:
            QMessageBox.warning(None, "警告",
                                "请至少选择一个图层！\n\n"
                                "• 勾选需要处理的图层\n"
                                "• 或使用【全选】按钮快速选择")
            continue

        total_count = len(selected_layers)

        if user_direction:
            primary_axis = user_direction
            force_user_direction = True
        else:
            primary_axis = auto_primary_axis
            force_user_direction = False

        capacity_error = False

        use_rotation = False
        rotation_angle = 0

        if use_auto_spacing:
            if force_user_direction:
                if primary_axis == 'Y':
                    eff_w = board_width
                    eff_h = board_height
                    layers_per_row = 1
                    num_rows = total_count
                    col_distribution = [1] * total_count
                    use_rotation = False
                    rotation_angle = 0

                    panel_margin = 0
                    total_needed_height = num_rows * eff_h
                    panel_available_height = total_needed_height * 1.5 + 2 * panel_margin
                    remaining_height = panel_available_height - num_rows * eff_h

                    if num_rows > 1:
                        y_extra_gap = remaining_height / (num_rows + 1)
                        y_offset_step = max(eff_h + 10, eff_h + y_extra_gap)
                    else:
                        y_offset_step = eff_h + 10

                    x_offset_step = eff_w + 10

                    QMessageBox.information(None, "智能间距优化",
                                            f"已按Y轴方向排列\n"
                                            f"布局: 1列 × {num_rows}行\n"
                                            f"优化间距: Y={y_offset_step:.1f}mm")
                else:
                    min_safe_gap = 10
                    best_layout_config = None
                    best_cols = 0
                    best_total_width = float('inf')
                    best_non_rotated_config = None
                    best_non_rotated_eff_w = board_width
                    best_non_rotated_eff_h = board_height

                    reply = QMessageBox.question(None, "旋转确认",
                        "是否旋转PCS(90°)以获得更优布局？",
                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                    if reply == QMessageBox.Yes:
                        rotate_options = [False, True]
                    else:
                        rotate_options = [False]

                    for try_rotate in rotate_options:
                        if try_rotate:
                            eff_w = board_height
                            eff_h = board_width
                        else:
                            eff_w = board_width
                            eff_h = board_height

                        panel_available_width = max(board_width, board_height) * 4.0 + 100
                        max_cols_by_width = int((panel_available_width + min_safe_gap) / (eff_w + min_safe_gap))
                        max_cols_by_width = max(1, min(max_cols_by_width, total_count))

                        best_config_for_rot = None
                        best_score_for_rot = float('inf')

                        for cols in range(max_cols_by_width, 0, -1):
                            rows = math.ceil(total_count / cols)
                            total_width = cols * eff_w + (cols - 1) * min_safe_gap
                            total_height = rows * eff_h + (rows - 1) * min_safe_gap

                            if total_height > 0:
                                aspect_ratio = total_width / total_height
                            else:
                                aspect_ratio = 999

                            base_score = -cols * 3

                            if aspect_ratio < 1.0:
                                aspect_penalty = (1.0 - aspect_ratio) * 200 + 100
                            elif 1.0 <= aspect_ratio <= 1.5:
                                aspect_penalty = (1.5 - aspect_ratio) * 30
                            elif 1.5 < aspect_ratio <= 5.0:
                                aspect_penalty = abs(aspect_ratio - 3.5) * 2
                            elif 5.0 < aspect_ratio <= 8.0:
                                aspect_penalty = (aspect_ratio - 5.0) * 5
                            else:
                                aspect_penalty = (aspect_ratio - 8.0) * 20 + 15

                            row_penalty = rows * 5
                            score = base_score + aspect_penalty + row_penalty

                            if score < best_score_for_rot:
                                best_score_for_rot = score
                                best_config_for_rot = {
                                    'type': 'uniform',
                                    'cols': cols,
                                    'rows': rows,
                                    'col_distribution': [cols] * rows,
                                    'total_width': total_width,
                                    'total_height': total_height,
                                    'aspect_ratio': aspect_ratio
                                }

                        for full_row_cols in range(max_cols_by_width, 1, -1):
                            full_rows = total_count // full_row_cols
                            remaining = total_count % full_row_cols

                            if remaining == 0:
                                continue

                            col_dist = [full_row_cols] * full_rows + [remaining]
                            actual_rows = len(col_dist)

                            total_width = full_row_cols * eff_w + (full_row_cols - 1) * min_safe_gap
                            total_height = actual_rows * eff_h + (actual_rows - 1) * min_safe_gap

                            if total_height > 0:
                                aspect_ratio = total_width / total_height
                            else:
                                aspect_ratio = 999

                            base_score = -full_row_cols * 3

                            if aspect_ratio < 1.0:
                                aspect_penalty = (1.0 - aspect_ratio) * 200 + 100
                            elif 1.0 <= aspect_ratio <= 1.5:
                                aspect_penalty = (1.5 - aspect_ratio) * 30
                            elif 1.5 < aspect_ratio <= 5.0:
                                aspect_penalty = abs(aspect_ratio - 3.5) * 2
                            elif 5.0 < aspect_ratio <= 8.0:
                                aspect_penalty = (aspect_ratio - 5.0) * 5
                            else:
                                aspect_penalty = (aspect_ratio - 8.0) * 20 + 15

                            row_penalty = actual_rows * 5

                            if remaining >= full_row_cols * 0.4:
                                irregular_bonus = -10
                            else:
                                irregular_bonus = 0

                            score = base_score + aspect_penalty + row_penalty + irregular_bonus

                            if score < best_score_for_rot:
                                best_score_for_rot = score
                                best_config_for_rot = {
                                    'type': 'irregular',
                                    'cols': full_row_cols,
                                    'rows': actual_rows,
                                    'col_distribution': col_dist,
                                    'total_width': total_width,
                                    'total_height': total_height,
                                    'aspect_ratio': aspect_ratio
                                }

                        if best_config_for_rot:
                            if (best_config_for_rot['cols'] > best_cols or
                                (best_config_for_rot['cols'] == best_cols and
                                 best_config_for_rot['total_width'] < best_total_width)):
                                best_layout_config = best_config_for_rot
                                best_cols = best_config_for_rot['cols']
                                best_total_width = best_config_for_rot['total_width']
                                use_rotation = try_rotate
                                rotation_angle = 90 if try_rotate else 0
                                eff_board_width = eff_w
                                eff_board_height = eff_h

                    if not best_layout_config:
                        QMessageBox.critical(None, "错误", "无法计算最优布局")
                        continue

                    config = best_layout_config
                    layers_per_row = config['cols']
                    num_rows = config['rows']
                    col_distribution = config['col_distribution']

                    panel_margin = 0
                    panel_available_width = max(board_width, board_height) * 1.5 + 2 * panel_margin
                    panel_available_height = min(board_width, board_height) * 1.5 + 2 * panel_margin

                    min_safe_gap = 10
                    remaining_width = panel_available_width - layers_per_row * eff_board_width
                    remaining_height = panel_available_height - num_rows * eff_board_height

                    if layers_per_row > 1:
                        x_extra_gap = remaining_width / (layers_per_row + 1)
                        x_offset_step = max(eff_board_width + min_safe_gap, eff_board_width + x_extra_gap)
                    else:
                        x_offset_step = eff_board_width + min_safe_gap

                    if num_rows > 1:
                        y_extra_gap = remaining_height / (num_rows + 1)
                        y_offset_step = max(eff_board_height + min_safe_gap, eff_board_height + y_extra_gap)
                    else:
                        y_offset_step = eff_board_height + min_safe_gap

                    msg = f"已按X轴方向排列（自动优化）\n"
                    if config['type'] == 'irregular':
                        dist_str = '+'.join([str(c) for c in col_distribution])
                        msg += f"布局: {dist_str}（{num_rows}行，不均匀）\n"
                    else:
                        msg += f"布局: {layers_per_row}列 × {num_rows}行\n"
                    msg += f"间距: X={x_offset_step:.1f}mm, Y={y_offset_step:.1f}mm\n"
                    msg += f"长宽比: {config['aspect_ratio']:.2f}"

                    if use_rotation:
                        msg = f"已自动旋转90度以优化布局\n" + msg

                    QMessageBox.information(None, "智能优化提示", msg)

            else:
                # AUTO模式：黄金比例布局，对比旋转/非旋转选最接近1.618的方案
                GOLDEN_RATIO = 1.618
                min_safe_gap = 10
                best_layout_config = None
                best_golden_score = float('inf')

                for try_rotate in [False, True]:
                    if try_rotate:
                        eff_w = board_height
                        eff_h = board_width
                    else:
                        eff_w = board_width
                        eff_h = board_height

                    panel_available_width = max(board_width, board_height) * 4.0 + 100
                    max_cols_by_width = int((panel_available_width + min_safe_gap) / (eff_w + min_safe_gap))
                    max_cols_by_width = max(1, min(max_cols_by_width, total_count))

                    for cols in range(max_cols_by_width, 0, -1):
                        rows = math.ceil(total_count / cols)
                        total_width = cols * eff_w + (cols - 1) * min_safe_gap
                        total_height = rows * eff_h + (rows - 1) * min_safe_gap
                        ratio = total_width / total_height if total_height > 0 else 999
                        score = abs(ratio - GOLDEN_RATIO)
                        if cols <= rows:
                            score += 100

                        if score < best_golden_score:
                            best_golden_score = score
                            best_layout_config = {
                                'type': 'uniform',
                                'cols': cols,
                                'rows': rows,
                                'col_distribution': [cols] * rows,
                                'total_width': total_width,
                                'total_height': total_height,
                                'ratio': ratio
                            }
                            use_rotation = try_rotate
                            rotation_angle = 90 if try_rotate else 0
                            eff_board_width = eff_w
                            eff_board_height = eff_h

                    for full_row_cols in range(max_cols_by_width, 1, -1):
                        full_rows = total_count // full_row_cols
                        remaining = total_count % full_row_cols
                        if remaining == 0:
                            continue

                        col_dist = [full_row_cols] * full_rows + [remaining]
                        actual_rows = len(col_dist)
                        total_width = full_row_cols * eff_w + (full_row_cols - 1) * min_safe_gap
                        total_height = actual_rows * eff_h + (actual_rows - 1) * min_safe_gap
                        ratio = total_width / total_height if total_height > 0 else 999
                        score = abs(ratio - GOLDEN_RATIO)
                        if full_row_cols <= actual_rows:
                            score += 100

                        if score < best_golden_score:
                            best_golden_score = score
                            best_layout_config = {
                                'type': 'irregular',
                                'cols': full_row_cols,
                                'rows': actual_rows,
                                'col_distribution': col_dist,
                                'total_width': total_width,
                                'total_height': total_height,
                                'ratio': ratio
                            }
                            use_rotation = try_rotate
                            rotation_angle = 90 if try_rotate else 0
                            eff_board_width = eff_w
                            eff_board_height = eff_h

                if not best_layout_config:
                    QMessageBox.critical(None, "错误", "无法计算最优布局")
                    continue

                config = best_layout_config
                layers_per_row = config['cols']
                num_rows = config['rows']
                col_distribution = config['col_distribution']

                panel_margin = 0
                panel_available_width = max(board_width, board_height) * 1.5 + 2 * panel_margin
                panel_available_height = min(board_width, board_height) * 1.5 + 2 * panel_margin

                min_safe_gap = 10
                remaining_width = panel_available_width - layers_per_row * eff_board_width
                remaining_height = panel_available_height - num_rows * eff_board_height

                if layers_per_row > 1:
                    x_extra_gap = remaining_width / (layers_per_row + 1)
                    x_offset_step = max(eff_board_width + min_safe_gap, eff_board_width + x_extra_gap)
                else:
                    x_offset_step = eff_board_width + min_safe_gap

                if num_rows > 1:
                    y_extra_gap = remaining_height / (num_rows + 1)
                    y_offset_step = max(eff_board_height + min_safe_gap, eff_board_height + y_extra_gap)
                else:
                    y_offset_step = eff_board_height + min_safe_gap

                msg = f"AUTO黄金比例布局\n"
                msg += f"目标比例: 1 : 1.618\n"
                if config['type'] == 'irregular':
                    dist_str = '+'.join([str(c) for c in col_distribution])
                    msg += f"布局: {dist_str}（{num_rows}行，不均匀）\n"
                else:
                    msg += f"布局: {layers_per_row}列 × {num_rows}行\n"
                msg += f"间距: X={x_offset_step:.1f}mm, Y={y_offset_step:.1f}mm\n"
                msg += f"实际比例: 1 : {config['ratio']:.3f}"

                if use_rotation:
                    msg = f"已自动旋转90度\n" + msg

                QMessageBox.information(None, "智能优化提示", msg)

        else:
            x_offset_step = spacing_config['x_spacing']
            y_offset_step = spacing_config['y_spacing']
            user_cols = spacing_config['cols']
            user_rows = spacing_config['rows']
            manual_rotation = spacing_config['rotation']

            # 手动旋转：90°/270°时宽高互换
            if manual_rotation in (90, 270):
                eff_board_width = board_height
                eff_board_height = board_width
            else:
                eff_board_width = board_width
                eff_board_height = board_height

            if primary_axis == 'Y':
                layers_per_row = 1
                num_rows = total_count
                col_distribution = [1] * total_count
            else:
                layers_per_row = user_cols
                num_rows = user_rows

                capacity = layers_per_row * num_rows

                if capacity != total_count:
                    if capacity < total_count:
                        needed_rows = math.ceil(total_count / layers_per_row)
                        msg = (f"❌ 布局容量不足\n\n"
                               f"当前设置: {layers_per_row}列 × {num_rows}行 = {capacity}个位置\n"
                               f"已选图层: {total_count}个\n"
                               f"缺少位置: {total_count - capacity} 个\n\n"
                               f"请调整设置：\n"
                               f"• 建议改为: {layers_per_row}列 × {needed_rows}行（共{layers_per_row * needed_rows}个位置）\n"
                               f"• 或减少勾选图层至 {capacity} 个")
                    else:
                        excess = capacity - total_count
                        actual_rows = math.ceil(total_count / layers_per_row)
                        msg = (f"⚠️ 布局容量超出\n\n"
                               f"当前设置: {layers_per_row}列 × {num_rows}行 = {capacity}个位置\n"
                               f"已选图层: {total_count}个\n"
                               f"浪费位置: {excess} 个空位\n\n"
                               f"建议调整为:\n"
                               f"• {layers_per_row}列 × {actual_rows}行（刚好{total_count}个位置）\n"
                               f"• 或增加勾选图层至 {capacity} 个")

                    reply = QMessageBox.question(
                        None,
                        "行列数与图层数量不匹配",
                        msg + "\n\n是否返回重新设置？\n• 点击【是】返回调整\n• 点击【否】强制继续（可能布局异常）",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.Yes
                    )

                    if reply == QMessageBox.Yes:
                        capacity_error = True
                        QMessageBox.information(None, "返回调整",
                                                f"请确保: 列数 × 行数 = 已选图层数\n\n"
                                                f"当前: {layers_per_row} × {num_rows} = {capacity} ≠ {total_count}\n\n"
                                                f"点击确定后将返回主界面重新设置")
                    else:
                        if capacity < total_count:
                            num_rows = math.ceil(total_count / layers_per_row)

                        full_rows = total_count // layers_per_row
                        remaining = total_count % layers_per_row

                        if remaining == 0:
                            col_distribution = [layers_per_row] * full_rows
                        else:
                            col_distribution = [layers_per_row] * full_rows + [remaining]

                        QMessageBox.warning(None, "警告",
                                            f"将强制继续执行\n"
                                            f"实际布局: {layers_per_row}列 × {num_rows}行\n"
                                            f"可能导致部分图层无法显示或布局异常")
                else:
                    full_rows = total_count // layers_per_row
                    remaining = total_count % layers_per_row

                    if remaining == 0:
                        col_distribution = [layers_per_row] * full_rows
                    else:
                        col_distribution = [layers_per_row] * full_rows + [remaining]

        if capacity_error:
            continue

        break

    # ==================== 清理旧临时层 ====================
    temp_layers = []
    error_list = []
    ##设置当前step为操作单元
    g.COM("open_entity,job={JOB},type=step,name={STEP},iconic=no"\
          .format(JOB=g.JOB(),STEP=g.STEP()))
    g.AUX(g.COMANS)
    for layer in g.get_layers():
        if layer.endswith('-temp-auto_mi'):
            try:
                step.removeLayers(layers=layer)
            except Exception as e:
                pass

    # 预加载图纸层命名映射，验证层名对应关系
    _layer_naming_list = load_layer_naming()
    layer_name_mapping = {item['source']: item['target'] for item in _layer_naming_list if item.get('source')}

    # 检查哪些已选层有映射、哪些没有
    mapped_layers = [l for l in selected_layers if l in layer_name_mapping]
    unmapped_layers = [l for l in selected_layers if l not in layer_name_mapping]
    if unmapped_layers:
        QMessageBox.warning(None, "层名映射缺失",
            f"以下层在 layer_naming 中没有映射，DXF 将保留英文层名:\n"
            + "\n".join(unmapped_layers) +
            f"\n\n已映射: {len(mapped_layers)} 层\n未映射: {len(unmapped_layers)} 层")

    # 清理上次运行可能残留的临时层
    for existing_layer in g.get_layers():
        if existing_layer.endswith('-temp-auto_mi'):
            try:
                step.removeLayers(layers=existing_layer)
            except Exception:
                pass

    for idx, layer in enumerate(selected_layers):
        try:
            temp_layer_name = f"{layer}-temp-auto_mi"

            step.createLayer(layerName=temp_layer_name)
            temp_layers.append(temp_layer_name)

            step.setWorkLayer(layerName=layer)
            step.selectAllFeatures()
            g.COM(f'sel_copy_other,dest=layer_name,target_layer={temp_layer_name},invert=no,dx=0,dy=0,size=0,x_anchor=0,y_anchor=0,rotation=0')
            step.clearAll()

            step.displayLayer(layerName=temp_layer_name, number=1, display='no')
            # 根据轮廓设置生成轮廓
            if SETTINGS['outline_mode'] == 'custom' and SETTINGS.get('outline_layer', ''):
                outline_layer = SETTINGS['outline_layer']
                try:
                    # 将自定义轮廓层图形复制到临时层
                    step.setWorkLayer(layerName=outline_layer)
                    step.selectAllFeatures()
                    g.COM(f'sel_copy_other,dest=layer_name,target_layer={temp_layer_name},invert=no,dx=0,dy=0,size=0,x_anchor=0,y_anchor=0,rotation=0')
                    step.clearAll()
                    # 在临时层上生成轮廓（已包含轮廓层图形）
                    step.profileToRout(layerName=temp_layer_name, width=SETTINGS['rout_width'])
                except Exception as e:
                    error_list.append(f"{layer} 自定义轮廓失败({outline_layer}): {str(e)}")
                    # 回退：使用临时层自身生成轮廓
                    step.profileToRout(layerName=temp_layer_name, width=SETTINGS['rout_width'])
            else:
                step.profileToRout(layerName=temp_layer_name, width=SETTINGS['rout_width'])
            step.displayLayer(layerName=temp_layer_name, number=1, display='yes')

        except Exception as e:
            error_list.append(f"{layer} 创建临时层失败: {str(e)}")
            continue

    # ==================== 镜像操作 ====================
    for idx, layer in enumerate(selected_layers):
        try:
            temp_layer_name = f"{layer}-temp-auto_mi"

            if layer in mirror_layers and mirror_layers[layer]:
                step.setWorkLayer(layerName=temp_layer_name)

                layer_xmin = step.profileLimits.xMin
                layer_xmax = step.profileLimits.xMax
                layer_ymin = step.profileLimits.yMin
                layer_ymax = step.profileLimits.yMax

                x_anchor = (layer_xmax + layer_xmin) / 2
                y_anchor = (layer_ymax + layer_ymin) / 2

                step.selectAllFeatures()
                g.COM(f'sel_transform,mode=anchor,oper=mirror,duplicate=no,x_anchor={x_anchor:.4f},y_anchor={y_anchor:.4f},angle=0,x_scale=1,y_scale=1,x_offset=0,y_offset=0')
                step.clearAll()

            # 镜像后添加层名标注（旋转复制前）——由"是否标注层"控制
            if SETTINGS.get('dxf_annotate_enabled', True):
                step.setWorkLayer(layerName=temp_layer_name)
                # 获取实际旋转角度：自动布局用 rotation_angle，手动模式用 manual_rotation
                _actual_rot = rotation_angle if (use_auto_spacing and use_rotation) else (manual_rotation if not use_auto_spacing else 0)
                # 根据旋转角度预判：文字放在旋转后会变成"上方"的边
                if _actual_rot == 90:
                    text_x, text_y = Xmin - 3, (Ymin + Ymax) / 2.0   # 90°：左边 → 旋转后在上方
                    _text_angle = 90
                elif _actual_rot == 270:
                    text_x, text_y = Xmax + 3, (Ymin + Ymax) / 2.0   # 270°：右边 → 旋转后在上方
                    _text_angle = 270
                else:
                    text_x, text_y = Xmin - 15.0, (Ymin + Ymax) / 2.0   # 0°/180°（Y布局）：左方
                    _text_angle = 0
                try:
                    step.addText(
                        geometry=Point(x=text_x, y=text_y),
                        text=f"{layer}",
                        xSize=2500, ySize=2500, fontName="simple",
                        width=300, angle=_text_angle, mirror='no')

                except Exception as e_txt:
                    QMessageBox.warning(None, "标注警告",
                                        f"无法向 {temp_layer_name} 添加标注:\n{e_txt}")

        except Exception as e:
            error_list.append(f"{layer} 镜像失败: {str(e)}")
            continue


    # 拼版可用区域（基于板子尺寸，供后续布局计算使用）
    panel_margin = 0
    panel_available_width = max(board_width, board_height) * 1.5 + 2 * panel_margin
    panel_available_height = min(board_width, board_height) * 1.5 + 2 * panel_margin
    center_offset_x = 0
    center_offset_y = 0

    use_multi_rows = num_rows > 1

    if layers_per_row > 1:
        total_layout_width = layers_per_row * x_offset_step
        total_layout_height = num_rows * y_offset_step if use_multi_rows else y_offset_step

        panel_margin = 0
        panel_available_width = max(board_width, board_height) * 1.5 + 2 * panel_margin
        panel_available_height = min(board_width, board_height) * 1.5 + 2 * panel_margin

        center_offset_x = max(0, (panel_available_width - total_layout_width) / 2)
        center_offset_y = max(0, (panel_available_height - total_layout_height) / 2)
    elif primary_axis == 'Y':
        panel_margin = 0
        panel_available_width = max(board_width, board_height) * 1.5 + 2 * panel_margin
        center_offset_x = max(0, (panel_available_width - board_width) / 2)
        center_offset_y = 0
    else:
        panel_margin = 0
        panel_available_height = min(board_width, board_height) * 1.5 + 2 * panel_margin
        center_offset_x = 0
        center_offset_y = max(0, (panel_available_height - board_height) / 2)

    # ==================== 创建tz目标层 ====================
    output_tz_enabled = SETTINGS.get('dxf_output_tz', True)
    tz_created = False

    if not output_tz_enabled:
        success_count = 0
        layer_positions = []
        QMessageBox.information(None, "提示", "tz 层输出已禁用，跳过 tz 创建和 DXF 导出")
    else:
        if 'tz' in g.get_layers():
            step.removeLayers(layers='tz')
        step.createLayer(layerName='tz', context='misc', layerType='document', polarity='positive')
        tz_created = True

        success_count = 0
        layer_positions = []  # 存储每层在 tz 布局中的坐标 (dx_offset, dy_offset)

        for idx, layer in enumerate(selected_layers):
            try:
                temp_layer_name = f"{layer}-temp-auto_mi"

                if 'col_distribution' in locals() and col_distribution and len(col_distribution) > 0:
                    current_row = 0
                    current_col_in_row = 0
                    cumulative_count = 0

                    for row_idx, row_cols in enumerate(col_distribution):
                        if idx < cumulative_count + row_cols:
                            current_row = row_idx
                            current_col_in_row = idx - cumulative_count
                            break
                        cumulative_count += row_cols

                    dx_offset = current_col_in_row * x_offset_step + center_offset_x
                    dy_offset = -current_row * y_offset_step + center_offset_y
                elif use_multi_rows and layers_per_row > 1:
                    row = idx // layers_per_row
                    col = idx % layers_per_row
                    dx_offset = col * x_offset_step + center_offset_x
                    dy_offset = -row * y_offset_step + center_offset_y
                else:
                    if layers_per_row == 1:
                        dx_offset = center_offset_x
                        dy_offset = -idx * y_offset_step + center_offset_y
                    else:
                        dx_offset = idx * x_offset_step + center_offset_x
                        dy_offset = center_offset_y

                layer_positions.append((dx_offset, dy_offset))

                if use_auto_spacing and use_rotation:
                    # 自动旋转：先绕板子中心旋转，再复制（与手动旋转逻辑一致）
                    step.setWorkLayer(layerName=temp_layer_name)
                    cx = (step.profileLimits.xMax + step.profileLimits.xMin) / 2
                    cy = (step.profileLimits.yMax + step.profileLimits.yMin) / 2
                    step.selectAllFeatures()
                    g.COM(f'sel_transform,mode=anchor,oper=rotate,duplicate=no,x_anchor={cx:.4f},y_anchor={cy:.4f},angle={rotation_angle},x_scale=1,y_scale=1,x_offset=0,y_offset=0')
                    step.clearAll()
                    rotation_param = ",rotation=0"
                elif not use_auto_spacing and manual_rotation != 0:
                    # 手动旋转：以图层自身中心为锚点旋转
                    step.setWorkLayer(layerName=temp_layer_name)
                    cx = (step.profileLimits.xMax + step.profileLimits.xMin) / 2
                    cy = (step.profileLimits.yMax + step.profileLimits.yMin) / 2
                    step.selectAllFeatures()
                    g.COM(f'sel_transform,mode=anchor,oper=rotate,duplicate=no,x_anchor={cx:.4f},y_anchor={cy:.4f},angle={manual_rotation},x_scale=1,y_scale=1,x_offset=0,y_offset=0')
                    step.clearAll()
                    rotation_param = ",rotation=0"
                else:
                    rotation_param = ",rotation=0"

                step.setWorkLayer(layerName=temp_layer_name)
                step.selectAllFeatures()
                g.COM(f'sel_copy_other,dest=layer_name,target_layer=tz,invert=no,dx={dx_offset:.4f},dy={dy_offset:.4f},size=0,x_anchor=0,y_anchor=0{rotation_param}')
                step.clearAll()

                step.displayLayer(layerName=layer, number=1, display='no')

                success_count += 1

            except Exception as e:
                error_list.append(f"{layer}: {str(e)}")
                continue

    # ==================== 输出预览延迟 ====================
    time.sleep(0.2)

    # ==================== DXF导出 + 图纸标注 ====================
    # 适配新版 outPutDxf 接口（GenesisPy3.py）：
    #   surface_mode 值统一小写 (fill / contour)
    if not (output_tz_enabled and tz_created):
        dxf_exported = False
        dxf_path = None
        QMessageBox.information(None, "提示", "tz 层不存在或输出已禁用，跳过 DXF 导出")
    else:
        # 2. 导出 tz 层
        script_dir = os.path.join(os.path.expanduser("~"), "Desktop")
        dxf_path = None
        dxf_exported = False

        # 2.1 输出前检查目标文件是否被其他程序(exe)占用
        try:
            _candidates = [
                f"{g.JOB()}_{g.STEP()}_tz.dxf",
                f"{g.JOB()}_{g.STEP()}.dxf",
                f"{job.name}_{step.name}_tz.dxf",
                f"{job.name}_{step.name}.dxf",
                "tz.dxf",
            ]
            _locked = [os.path.join(script_dir, n) for n in _candidates
                       if is_file_locked(os.path.join(script_dir, n))]
            if _locked:
                reply = QMessageBox.question(
                    None, "输出文件被占用",
                    "检测到输出 DXF 文件正被程序(exe)占用：\n\n"
                    + "\n".join(os.path.basename(p) for p in _locked[:3])
                    + "\n\n是否关闭占用程序并继续？\n（选择“否”将返回主界面）",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                if reply == QMessageBox.Yes:
                    # 是：尝试关闭占用进程以解锁
                    for p in _locked:
                        if is_file_locked(p):
                            unlock_file_locked(p)
                    _still = [os.path.basename(p) for p in _locked if is_file_locked(p)]
                    if _still:
                        append_result_log(f"{job.name}/{step.name} 占用未解除，导出可能失败: {', '.join(_still)}")
                else:
                    # 否：返回主界面（先清理已创建的临时层）
                    for temp_layer in temp_layers:
                        try:
                            step.removeLayers(layers=temp_layer)
                        except Exception:
                            pass
                    continue
        except Exception as e:
            append_result_log(f"{job.name}/{step.name} 检查输出文件占用时出错: {e}")

        try:
            g.outPutDxf(
                job=g.JOB(), step=g.STEP(), layers='tz',
                dirPath=script_dir, prefix='', suffix='.dxf',
                surface_mode=SETTINGS['dxf_surface_mode'].lower(),
                Pad_as_Circle=SETTINGS['dxf_pad_as_circle'],
                draft=SETTINGS['dxf_draft'],
                contour_to_hatch=SETTINGS['dxf_contour_to_hatch'],
                output_files=SETTINGS['dxf_output_files'],
                units='mm',
            )
            import glob as _glob
            expected_names = [
                f"{g.JOB()}_{g.STEP()}_tz.dxf",
                f"{g.JOB()}_{g.STEP()}.dxf",
                f"{job.name}_{step.name}_tz.dxf",
                f"{job.name}_{step.name}.dxf",
                "tz.dxf",
            ]
            for name in expected_names:
                cand = os.path.join(script_dir, name)
                if os.path.exists(cand):
                    dxf_path = cand
                    dxf_exported = True
                    break
            if not dxf_exported:
                # 兜底：任意 *tz.dxf，按修改时间取最新（兼容无 job/step 前缀的命名）
                possible = sorted(
                    _glob.glob(os.path.join(script_dir, "*tz.dxf")),
                    key=os.path.getmtime, reverse=True
                )
                if possible:
                    dxf_path = possible[0]
                    dxf_exported = True
            if not dxf_exported:
                append_result_log(f"{job.name}/{step.name} 未找到导出的 tz DXF 文件，桌面现有: "
                                  f"{[os.path.basename(p) for p in _glob.glob(os.path.join(script_dir, '*.dxf'))]}")
        except Exception as e:
            append_result_log(f"{job.name}/{step.name} DXF 导出失败: {e}")



    # ============================================================
    # [图纸标注部分] 通过 ezdxf 打开 DXF 并写入文字标注（由"是否标注层"控制）
    # ============================================================
    if (dxf_exported and os.path.exists(dxf_path)
            and SETTINGS.get('dxf_annotate_enabled', True)):
        log_enabled = SETTINGS.get('dxf_log_enabled', True)
        cad_log = os.path.join(script_dir, f"{job.name}_{step.name}_cad_debug.log")
        def _log(msg):
            if not log_enabled:
                return
            try:
                with open(cad_log, 'a', encoding='utf-8') as f:
                    f.write(f"{msg}\n")
            except: pass
        try:
            if log_enabled:
                open(cad_log, 'w').close()
        except: pass
        _log("=== EZDXF 文字替换开始 ===")

        try:
            _ln_list = load_layer_naming()
            layer_mapping = {item['source']: item['target']
                            for item in _ln_list
                            if item.get('source') and item.get('target')}
            _log(f"[OK] 加载层面映射 {len(layer_mapping)} 条")
            for k, v in layer_mapping.items():
                _log(f"     映射: {k} → {v}")

            doc = ezdxf.readfile(dxf_path)
            msp = doc.modelspace()

            try:
                doc.styles.new('SONGTI', dxfattribs={'font': '宋体'})
                style_name = 'SONGTI'
            except Exception:
                style_name = 'Standard'
            text_height = min(board_width, board_height) * 2.0 / 20.0   # 字体比例为短边的 2/20
            _log(f"[OK] 字体: {style_name}, 字号: {text_height:.2f}mm (短边={min(board_width,board_height):.2f}mm × 2/20)")

            replaced = 0
            for e in list(msp):
                if e.dxftype() == 'TEXT':
                    txt = e.dxf.text
                    if txt in layer_mapping:
                        e.dxf.text = layer_mapping[txt]
                        e.dxf.style = style_name
                        e.dxf.height = text_height
                        replaced += 1
                        _log(f"[REPLACE] {txt} → {layer_mapping[txt]}")

            _log(f"[STEP] 替换 {replaced} 个文字")
            doc.save()
            _log(f"[OK] DXF 已保存: {dxf_path}")
            _log("=== EZDXF 文字替换结束 ===")
        except Exception as e:
            _log(f"[FAIL] 标注处理失败: {e}")

    # 图纸输出完成提示
    if dxf_exported and os.path.exists(dxf_path):
        QMessageBox.information(None, "图纸已输出", "图纸已输出")

    # ==================== 清理临时层 ====================
    for temp_layer in temp_layers:
        try:
            step.removeLayers(layers=temp_layer)
        except Exception as e:
            pass
    # 导出完成后移除 tz 层（成功提示已取消，不再弹窗）
    try:
        if 'tz' in g.get_layers():
            step.removeLayers(layers='tz')
    except Exception:
        pass

    # ==================== 结果提示（写入日志，不再弹窗） ====================
    try:
        _result_log = os.path.join(os.path.expanduser("~"), "Desktop", "AUTO_MI_result.log")
        with open(_result_log, 'a', encoding='utf-8') as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {job.name}/{step.name} "
                    f"处理完成，成功 {success_count}/{total_count} 层"
                    + (f"，失败 {len(error_list)} 层" if error_list else "")
                    + "\n")
            for err in error_list:
                f.write(f"    - {err}\n")
    except Exception:
        pass

    if 'dialog' in locals():
        dialog.deleteLater()
    if 'app' in locals():
        app.processEvents()
    break
