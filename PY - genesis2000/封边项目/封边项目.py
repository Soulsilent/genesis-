#!/usr/bin/env python
# coding:utf-8
import sys, os
from genesis_gateway import GenesisGateway
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QLabel, QPushButton, QListWidget, QListWidgetItem,
                             QMessageBox, QDialog, QHBoxLayout, QInputDialog, QAbstractItemView)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont


class StepEdgeBandingDialog(QMainWindow):


    def __init__(self, step_data=None, current_job=None, current_step=None,
                 xmax=None, ymax=None, pnl_num=None, set_num=None):
        super().__init__()
        self.step_data = step_data or []
        self.current_job = current_job
        self.current_step = current_step
        self.xmax = xmax
        self.ymax = ymax
        self.pnl_num = pnl_num
        self.set_num = set_num
        self.layer_config = []
        # 通过 Gateway 实时获取 JOB/STEP 名称
        self.gw = GenesisGateway(job_ver='JOB_10.05', step_ver='STEP_10.05')
        self.info_timer = QTimer(self)
        self.info_timer.timeout.connect(self.refresh_info)
        self.info_timer.start(500)
        # 一次性获取尺寸和拼版数量
        self._fetch_size_and_panel()
        self.init_ui()
        # 获取实际 STEP 列表并刷新
        self._fetch_step_list()
        # 立即刷新一次 JOB/STEP（timer 首次触发可能在标签创建前）
        self.refresh_info()

    def init_ui(self):
        self.setWindowTitle("封边工具")
        self.setGeometry(100, 100, 520, 460)
        self.setFixedSize(520, 400)

        # ── 全局样式 ──
        self.setStyleSheet("""
            QMainWindow { background: #f5f6fa; }
            QLabel { color: #2c3e50; }
            QListWidget {
                background: white; border: 1px solid #dcdde1;
                border-radius: 6px; padding: 4px; font-size: 13px;
                outline: none;
            }
            QListWidget::item { padding: 6px 8px; border-radius: 4px; }
            QListWidget::item:hover { background: #e8f0fe; }
            QListWidget::item:selected { background: #d2e3fc; }
            QPushButton {
                background: #ffffff; border: 1px solid #dcdde1;
                border-radius: 6px; padding: 7px 16px;
                font-size: 13px; color: #2c3e50; min-width: 80px;
            }
            QPushButton:hover {
                background: #e8f0fe; border-color: #3498db; color: #2980b9;
            }
            QPushButton:pressed { background: #d2e3fc; }
        """)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # ── 信息区（带背景卡片） ──
        info_card = QWidget()
        info_card.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2c3e50, stop:1 #3498db);
                border-radius: 8px; padding: 6px;
            }
            QLabel { color: white; }
        """)
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(10, 8, 10, 8)
        info_layout.setSpacing(2)

        info_font = QFont()
        info_font.setPointSize(11)
        info_font.setBold(True)

        self.job_info = QLabel(f"当前JOB: {self.current_job or '未获取'}")
        self.job_info.setFont(info_font)
        self.job_info.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(self.job_info)

        self.step_info = QLabel(f"当前STEP: {self.current_step or '未获取'}")
        step_font = QFont()
        step_font.setPointSize(10)
        self.step_info.setFont(step_font)
        self.step_info.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(self.step_info)

        sz_font = QFont()
        sz_font.setPointSize(9)
        xm = f"{self.xmax}" if self.xmax is not None else 'N/A'
        ym = f"{self.ymax}" if self.ymax is not None else 'N/A'
        sr = ""
        if self.pnl_num is not None:
            sr = f"PNL={self.pnl_num}"
            if self.set_num is not None:
                sr += f", SET={self.set_num}"
        else:
            sr = "未获取"
        self.size_info = QLabel(f"尺寸: {xm}×{ym}mm    拼版: {sr}")
        self.size_info.setFont(sz_font)
        self.size_info.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(self.size_info)

        layout.addWidget(info_card)

        # ── STEP列表 ──
        list_title = QLabel("STEP列表")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        list_title.setFont(title_font)
        layout.addWidget(list_title)

        sub_hint = QLabel("勾选需要封边的STEP，点击\"开始封边\"执行")
        sub_hint.setStyleSheet("color: #7f8c8d; font-size: 11px; margin-top: -4px;")
        layout.addWidget(sub_hint)

        self.step_list = QListWidget()
        self.step_list.setSelectionMode(QAbstractItemView.NoSelection)
        self.step_list.setMinimumHeight(100)
        self.populate_step_list()
        layout.addWidget(self.step_list)

        # ── 操作按钮行 ──
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        setting_btn = QPushButton("⚙ 封边设置")
        setting_btn.setStyleSheet("""
            QPushButton {
                background: #ffffff; border: 1px solid #95a5a6;
                border-radius: 6px; padding: 9px 20px;
                font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background: #f0f3f4; border-color: #3498db; }
        """)
        setting_btn.clicked.connect(self.show_layer_config)
        btn_layout.addWidget(setting_btn)

        start_btn = QPushButton("▶ 开始封边")
        start_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #27ae60, stop:1 #2ecc71);
                color: white; border: none; border-radius: 6px;
                padding: 9px 24px; font-size: 14px; font-weight: bold;
            }
            QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 #219a52, stop:1 #27ae60); }
            QPushButton:pressed { background: #1e8449; }
        """)
        start_btn.clicked.connect(self.start_edge_banding)
        btn_layout.addWidget(start_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #ffffff; border: 1px solid #e74c3c;
                border-radius: 6px; padding: 9px 20px;
                font-size: 13px; color: #e74c3c;
            }
            QPushButton:hover { background: #fdf2f2; border-color: #c0392b; }
        """)
        cancel_btn.clicked.connect(self.cancel_selection)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

    def _fetch_size_and_panel(self):
        """一次性获取尺寸和拼版数量（仅在初始化时执行一次）"""
        try:
            import GenesisPy3
            import genClasses
            top = genClasses.Top()
            if top.currentJob and top.currentJob in top.jobs:
                job = top.jobs[top.currentJob]
                if top.currentStep and top.currentStep in job.steps:
                    step = job.steps[top.currentStep]
                    lim = step.profileLimits
                    if lim and not (lim.xMin == 0 and lim.xMax == 0 and lim.yMin == 0 and lim.yMax == 0):
                        self.xmax = lim.xMax
                        self.ymax = lim.yMax
                    g = GenesisPy3.Genesis()
                    job_name = g.JOB()
                    pnl_text = ""
                    if job_name and 'pnl' in job.steps:
                        g.INFO(units='mm', entity_type='step', entity_path='%s/pnl' % job_name, data_type='SR', parameters='nx+ny')
                        nx = list(map(int, g.doinfo["gSRnx"]))
                        ny = list(map(int, g.doinfo["gSRny"]))
                        pnl_num = sum(a * b for a, b in zip(nx, ny))
                        self.pnl_num = pnl_num
                        pnl_text = f"PNL={pnl_num}"
                        if 'set' in job.steps:
                            g.INFO(units='mm', entity_type='step', entity_path='%s/set' % job_name, data_type='SR', parameters='nx+ny')
                            snx = list(map(int, g.doinfo["gSRnx"]))
                            sny = list(map(int, g.doinfo["gSRny"]))
                            set_num = sum(a * b for a, b in zip(snx, sny))
                            self.set_num = set_num
                            pnl_text += f", SET={set_num}"
                    if hasattr(self, 'size_info'):
                        xm = f"{self.xmax}" if self.xmax is not None else 'N/A'
                        ym = f"{self.ymax}" if self.ymax is not None else 'N/A'
                        self.size_info.setText(f"尺寸: {xm}×{ym}mm    拼版: {pnl_text or '未获取'}")
        except Exception:
            pass

    def refresh_info(self):
        """通过 Gateway 实时刷新 JOB/STEP 名称（500ms 定时）"""
        try:
            pid = self.gw.get_genesis_PID()
            if pid:
                job_name = self.gw.get_JobsStepName(pid, getval='job')
                step_name = self.gw.get_JobsStepName(pid, getval='step')
                if job_name:
                    self.current_job = job_name.strip()
                    self.job_info.setText(f"当前JOB: {self.current_job}")
                if step_name:
                    self.current_step = step_name.strip()
                    self.step_info.setText(f"当前STEP: {self.current_step}")
        except Exception:
            pass

        # 后备：通过 GenesisPy3 获取（Gateway 失败时）
        if not self.current_job or self.current_job == '未获取':
            try:
                import GenesisPy3
                g = GenesisPy3.Genesis()
                jn = g.JOB()
                if jn:
                    self.current_job = jn.strip()
                    self.job_info.setText(f"当前JOB: {self.current_job}")
                sn = g.STEP()
                if sn:
                    self.current_step = sn.strip()
                    self.step_info.setText(f"当前STEP: {self.current_step}")
            except Exception:
                pass

    def _fetch_step_list(self):
        """从 Genesis 获取当前 JOB 的实际 STEP 列表"""
        try:
            import genClasses
            top = genClasses.Top()
            if top.currentJob and top.currentJob in top.jobs:
                job = top.jobs[top.currentJob]
                steps = []
                for s in job.steps:
                    if s not in steps:
                        steps.append(s)
                if steps:
                    self.step_data = [[s] for s in steps]
                    self.populate_step_list()
        except Exception:
            pass

    def populate_step_list(self):
        """填充STEP列表（带复选框）"""
        self.step_list.clear()
        for entry in self.step_data:
            item = QListWidgetItem(entry[0])
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.step_list.addItem(item)

    def show_layer_config(self):
        """弹出封边设置对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("封边设置")
        dialog.setFixedSize(280, 420)
        dialog.setStyleSheet("""
            QDialog { background: #f5f6fa; }
            QLabel { color: #2c3e50; font-size: 13px; }
            QListWidget {
                background: white; border: 1px solid #dcdde1;
                border-radius: 6px; padding: 4px;
            }
            QListWidget::item { padding: 5px; border-radius: 3px; }
            QListWidget::item:hover { background: #e8f0fe; }
            QPushButton {
                background: white; border: 1px solid #dcdde1;
                border-radius: 4px; padding: 6px 14px; font-size: 12px;
            }
            QPushButton:hover { background: #e8f0fe; border-color: #3498db; }
        """)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(12, 12, 12, 12)

        title = QLabel("层配置")
        title.setStyleSheet("font-size: 15px; font-weight: bold;")
        layout.addWidget(title)

        hint = QLabel("勾选需要处理的层，可自定义增加/删除")
        hint.setStyleSheet("color: #7f8c8d; font-size: 11px; margin-top: -4px;")
        layout.addWidget(hint)

        list_widget = QListWidget()
        for layer in sorted(self.layer_config):
            item = QListWidgetItem(layer)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            list_widget.addItem(item)
        layout.addWidget(list_widget)

        btn_row = QHBoxLayout()
        add_btn = QPushButton("+ 增加")
        del_btn = QPushButton("− 删除")
        btn_row.addWidget(add_btn)
        btn_row.addWidget(del_btn)
        layout.addLayout(btn_row)

        def add_layer():
            text, ok = QInputDialog.getText(dialog, "增加层", "输入层名称:")
            if ok and text.strip():
                name = text.strip()
                for i in range(list_widget.count()):
                    if list_widget.item(i).text() == name:
                        return
                item = QListWidgetItem(name)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Checked)
                list_widget.addItem(item)

        def delete_layer():
            current = list_widget.currentItem()
            if current:
                row = list_widget.row(current)
                list_widget.takeItem(row)

        add_btn.clicked.connect(add_layer)
        del_btn.clicked.connect(delete_layer)

        ok_btn = QPushButton("✓ 确定")
        ok_btn.setStyleSheet("""
            QPushButton {
                background: #3498db; color: white; border: none;
                border-radius: 4px; padding: 8px; font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background: #2980b9; }
        """)
        ok_btn.clicked.connect(dialog.accept)
        layout.addWidget(ok_btn)

        if dialog.exec_() == QDialog.Accepted:
            new_config = []
            for i in range(list_widget.count()):
                if list_widget.item(i).checkState() == Qt.Checked:
                    new_config.append(list_widget.item(i).text())
            self.layer_config = new_config

    def start_edge_banding(self):
        """开始封边 — 收集勾选的STEP并执行封边逻辑"""
        checked = []
        for i in range(self.step_list.count()):
            if self.step_list.item(i).checkState() == Qt.Checked:
                checked.append(self.step_list.item(i).text())
        if not checked:
            QMessageBox.warning(self, "警告", "请至少勾选一个STEP！")
            return
        # 执行封边逻辑（从 FPCpyqt5.py 移植）
        self.close()
        for step_name in checked:
            if step_name == 'pnl' or step_name == 'set':
                pnl_fb()

    def cancel_selection(self):
        self.close()



def pnl_fb():
    """双面板封边 — 从 FPCpyqt5.py 移植"""
    from genesisGeometry import Point, Segment
    import GenesisPy3
    import genClasses
    top = genClasses.Top()
    g = GenesisPy3.Genesis()
    job = top.jobs[top.currentJob]
    step = job.steps[top.currentStep]

    if g.STEP() != 'pnl':
        QMessageBox.warning(None, '提示', '请选择PNL步骤！')
        sys.exit()
    g.COM("open_entity,job={JOB},type=step,name={STEP},iconic=no" \
          .format(JOB=g.JOB, STEP=g.STEP))
    g.AUX(g.COMANS)

    try:
        Xmin = step.profileLimits.xMin
        Xmax = step.profileLimits.xMax
        Ymin = step.profileLimits.yMin
        Ymax = step.profileLimits.yMax
    except (AttributeError, TypeError):
        QMessageBox.warning(None, '提示', '未创建PR线！')
        sys.exit()

    if Xmin == 0 and Xmax == 0 and Ymin == 0 and Ymax == 0:
        QMessageBox.warning(None, '提示', '未创建PR线！')
        sys.exit()

    g.COM('filter_reset,filter_name=popup')
    step.clearAll()

    # 获取拼版信息
    job_name = g.JOB()
    if not job_name:
        QMessageBox.warning(None, '提示', '无法获取当前JOB名称！')
        sys.exit()
    g.INFO(units='mm', entity_type='step', entity_path='%s/pnl' % job_name, data_type='SR', parameters='nx+ny')
    list_nx = g.doinfo["gSRnx"]
    list_yx = g.doinfo["gSRny"]
    list_nx_int = list(map(int, list_nx))
    list_yx_int = list(map(int, list_yx))
    pnl_num = sum(a * b for a, b in zip(list_nx_int, list_yx_int))

    if 'set' in job.steps:
        g.INFO(units='mm', entity_type='step', entity_path='%s/set' % job_name, data_type='SR', parameters='nx+ny')
        set_nx = g.doinfo["gSRnx"]
        set_yx = g.doinfo["gSRny"]
        set_nx_int = list(map(int, set_nx))
        set_yx_int = list(map(int, set_yx))
        set_num = sum(a * b for a, b in zip(set_nx_int, set_yx_int))
    if 'set' in job.steps:
        pnl_num = pnl_num * set_num

    g.COM('delete_unused_sym,job=%s' % (g.JOB()))
    pb_layer = ['gtl', 'gbl', 'ck1', 'ck2', 'gko', 'f1', 'mk', 'gto', 'gbo']
    special_symbols = {
        'ck1': 'mb-2c-cov',
        'ck2': 'mb-2c-cov',
        'gto': 'mb-2c-ss',
        'gbo': 'mb-2c-ss'
    }
    for layer in pb_layer:
        if step.isLayersExist(layer):
            step.setWorkLayer(layer)
            profile_params = {'gko': 3, 'gtl': 3000, 'gbl': 3000}
            if layer in profile_params:
                step.profileToRout(layer, profile_params[layer])
            symbol_prefix = special_symbols.get(layer, f'mb-2c-{layer}')
            corners = [
                (Xmin + 3, Ymin + 3, f'{symbol_prefix}-a'),
                (Xmin + 3, Ymax - 3, f'{symbol_prefix}-b'),
                (Xmax - 3, Ymax - 3, f'{symbol_prefix}-c'),
                (Xmax - 3, Ymin + 3, f'{symbol_prefix}-d')
            ]
            for x, y, symbol in corners:
                step.addPad(Point(x=x, y=y), symbol)
                g.COM('sel_break')
            if layer in ['gtl', 'gbl', 'gto', 'gbo']:
                mirror = 'yes' if layer in ['gbl', 'gbo'] else 'no'
                text_x = Xmin + 163 if layer in ['gbl', 'gbo'] else Xmin + 64
                step.addText(
                    geometry=Point(x=text_x, y=Ymin + 1.6),
                    text="$$job $$layer (+) %s*%s*%sPCS/PNL LP $$YY$$MM$$DD" % (round(Xmax), round(Ymax), int(pnl_num)),
                    xSize=2000, ySize=2500, fontName="simple", width=300, mirror=mirror)
            if layer in ['f1', 'ck1', 'ck2']:
                font = "canned_57" if layer == 'f1' else "simple"
                x_size = 3022 if layer == 'f1' else 2000
                y_size = 4216 if layer == 'f1' else 2500
                width = 500 if layer == 'f1' else 300
                layer_text = "$$job" if layer == 'f1' else "$${job}  $${layer}"
                step.addText(
                    geometry=Point(x=Xmin + 163, y=Ymax - 5),
                    text=layer_text, xSize=x_size, ySize=y_size,
                    txt_type='canned_text', fontName=font, width=width)
            step.clearAll()
    g.COM('delete_unused_sym,job=%s' % (g.JOB()))
    QMessageBox.information(None, '提示', '完成！')


if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("双面板封边")
        app.setOrganizationName("Genesis Tools")
        
        step_data = []
        
        w = StepEdgeBandingDialog(step_data)
        w.show()
        
        sys.exit(app.exec())
    except Exception as e:
        print(f"应用程序启动失败: {e}")
        sys.exit(1)
