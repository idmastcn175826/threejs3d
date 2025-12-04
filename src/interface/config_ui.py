"""
Config UI - 配置界面
提供手势映射、摄像头校准、特效设置等配置功能
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QSlider, QCheckBox, QComboBox, QPushButton,
    QGroupBox, QFormLayout, QSpinBox, QDoubleSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from typing import Dict, Any


class ConfigDialog(QDialog):
    """配置对话框"""
    
    config_changed = pyqtSignal(dict)
    
    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        
        self.config = config.copy()
        self.setWindowTitle("设置")
        self.setMinimumSize(600, 500)
        
        self._init_ui()
        self._load_config()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        
        # 标签页
        tab_widget = QTabWidget()
        
        # 显示设置
        tab_widget.addTab(self._create_display_tab(), "显示")
        
        # 摄像头设置
        tab_widget.addTab(self._create_camera_tab(), "摄像头")
        
        # 识别设置
        tab_widget.addTab(self._create_recognition_tab(), "识别")
        
        # 手势映射
        tab_widget.addTab(self._create_gesture_tab(), "手势映射")
        
        # 特效设置
        tab_widget.addTab(self._create_effects_tab(), "特效")
        
        layout.addWidget(tab_widget)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        btn_save = QPushButton("保存")
        btn_save.clicked.connect(self._save_config)
        
        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self.reject)
        
        btn_reset = QPushButton("重置默认")
        btn_reset.clicked.connect(self._reset_config)
        
        button_layout.addWidget(btn_reset)
        button_layout.addStretch()
        button_layout.addWidget(btn_cancel)
        button_layout.addWidget(btn_save)
        
        layout.addLayout(button_layout)
    
    def _create_display_tab(self) -> QWidget:
        """创建显示设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 透明度设置
        group_opacity = QGroupBox("背景透明度")
        opacity_layout = QFormLayout(group_opacity)
        
        self.slider_opacity = QSlider(Qt.Horizontal)
        self.slider_opacity.setRange(10, 90)
        self.slider_opacity.setValue(60)
        self.label_opacity = QLabel("60%")
        self.slider_opacity.valueChanged.connect(
            lambda v: self.label_opacity.setText(f"{v}%")
        )
        
        opacity_row = QHBoxLayout()
        opacity_row.addWidget(self.slider_opacity)
        opacity_row.addWidget(self.label_opacity)
        opacity_layout.addRow("透明度:", opacity_row)
        
        layout.addWidget(group_opacity)
        
        # 显示选项
        group_display = QGroupBox("显示选项")
        display_layout = QVBoxLayout(group_display)
        
        self.check_skeleton = QCheckBox("显示手部骨架")
        self.check_skeleton.setChecked(True)
        
        self.check_gesture = QCheckBox("显示手势名称")
        self.check_gesture.setChecked(True)
        
        self.check_fps = QCheckBox("显示FPS")
        self.check_fps.setChecked(True)
        
        self.check_safe_zone = QCheckBox("显示安全区域")
        self.check_safe_zone.setChecked(True)
        
        self.check_blur = QCheckBox("背景模糊")
        self.check_blur.setChecked(False)
        
        display_layout.addWidget(self.check_skeleton)
        display_layout.addWidget(self.check_gesture)
        display_layout.addWidget(self.check_fps)
        display_layout.addWidget(self.check_safe_zone)
        display_layout.addWidget(self.check_blur)
        
        layout.addWidget(group_display)
        layout.addStretch()
        
        return widget
    
    def _create_camera_tab(self) -> QWidget:
        """创建摄像头设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        group = QGroupBox("摄像头设置")
        form = QFormLayout(group)
        
        # 设备选择
        self.combo_device = QComboBox()
        self.combo_device.addItems(["摄像头 0", "摄像头 1", "摄像头 2"])
        form.addRow("摄像头设备:", self.combo_device)
        
        # 分辨率
        self.combo_resolution = QComboBox()
        self.combo_resolution.addItems(["1280x720", "1920x1080", "640x480"])
        form.addRow("分辨率:", self.combo_resolution)
        
        # 帧率
        self.spin_fps = QSpinBox()
        self.spin_fps.setRange(15, 60)
        self.spin_fps.setValue(30)
        form.addRow("帧率:", self.spin_fps)
        
        # 镜像
        self.check_mirror = QCheckBox("水平镜像")
        self.check_mirror.setChecked(True)
        form.addRow("", self.check_mirror)
        
        # 旋转
        self.combo_rotation = QComboBox()
        self.combo_rotation.addItems(["0°", "90°", "180°", "270°"])
        form.addRow("旋转:", self.combo_rotation)
        
        layout.addWidget(group)
        
        # 校准按钮
        btn_calibrate = QPushButton("校准摄像头")
        btn_calibrate.clicked.connect(self._calibrate_camera)
        layout.addWidget(btn_calibrate)
        
        layout.addStretch()
        
        return widget
    
    def _create_recognition_tab(self) -> QWidget:
        """创建识别设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 检测置信度
        group_detection = QGroupBox("检测参数")
        form = QFormLayout(group_detection)
        
        self.spin_detection_conf = QDoubleSpinBox()
        self.spin_detection_conf.setRange(0.3, 0.95)
        self.spin_detection_conf.setSingleStep(0.05)
        self.spin_detection_conf.setValue(0.7)
        form.addRow("检测置信度:", self.spin_detection_conf)
        
        self.spin_tracking_conf = QDoubleSpinBox()
        self.spin_tracking_conf.setRange(0.3, 0.95)
        self.spin_tracking_conf.setSingleStep(0.05)
        self.spin_tracking_conf.setValue(0.5)
        form.addRow("跟踪置信度:", self.spin_tracking_conf)
        
        layout.addWidget(group_detection)
        
        # 防误触设置
        group_anti = QGroupBox("防误触设置")
        anti_form = QFormLayout(group_anti)
        
        self.spin_hold_time = QSpinBox()
        self.spin_hold_time.setRange(50, 500)
        self.spin_hold_time.setValue(150)
        self.spin_hold_time.setSuffix(" ms")
        anti_form.addRow("保持时间:", self.spin_hold_time)
        
        self.spin_cooldown = QSpinBox()
        self.spin_cooldown.setRange(200, 2000)
        self.spin_cooldown.setValue(700)
        self.spin_cooldown.setSuffix(" ms")
        anti_form.addRow("冷却时间:", self.spin_cooldown)
        
        layout.addWidget(group_anti)
        
        # 安全区域
        group_safe = QGroupBox("安全区域")
        safe_form = QFormLayout(group_safe)
        
        self.check_safe_zone_enabled = QCheckBox("启用安全区域")
        self.check_safe_zone_enabled.setChecked(True)
        safe_form.addRow("", self.check_safe_zone_enabled)
        
        layout.addWidget(group_safe)
        layout.addStretch()
        
        return widget
    
    def _create_gesture_tab(self) -> QWidget:
        """创建手势映射标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 手势映射表
        self.table_gestures = QTableWidget()
        self.table_gestures.setColumnCount(4)
        self.table_gestures.setHorizontalHeaderLabels(["手势", "动作类型", "动作", "冷却时间"])
        self.table_gestures.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(self.table_gestures)
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        btn_add = QPushButton("添加")
        btn_add.clicked.connect(self._add_gesture_mapping)
        
        btn_remove = QPushButton("删除")
        btn_remove.clicked.connect(self._remove_gesture_mapping)
        
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_remove)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        return widget
    
    def _create_effects_tab(self) -> QWidget:
        """创建特效设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 星空心心设置
        group = QGroupBox("星空心心特效")
        form = QFormLayout(group)
        
        self.check_effect_enabled = QCheckBox("启用特效")
        self.check_effect_enabled.setChecked(True)
        form.addRow("", self.check_effect_enabled)
        
        self.spin_particle_count = QSpinBox()
        self.spin_particle_count.setRange(50, 500)
        self.spin_particle_count.setValue(150)
        form.addRow("粒子数量:", self.spin_particle_count)
        
        self.spin_effect_duration = QSpinBox()
        self.spin_effect_duration.setRange(500, 3000)
        self.spin_effect_duration.setValue(1500)
        self.spin_effect_duration.setSuffix(" ms")
        form.addRow("持续时间:", self.spin_effect_duration)
        
        self.check_glow = QCheckBox("发光效果")
        self.check_glow.setChecked(True)
        form.addRow("", self.check_glow)
        
        self.check_twinkle = QCheckBox("闪烁效果")
        self.check_twinkle.setChecked(True)
        form.addRow("", self.check_twinkle)
        
        layout.addWidget(group)
        
        # 测试按钮
        btn_test = QPushButton("测试特效")
        btn_test.clicked.connect(self._test_effect)
        layout.addWidget(btn_test)
        
        layout.addStretch()
        
        return widget
    
    def _load_config(self):
        """加载配置到UI"""
        display = self.config.get('display', {})
        self.slider_opacity.setValue(int(display.get('background_opacity', 0.6) * 100))
        self.check_skeleton.setChecked(display.get('show_skeleton', True))
        self.check_gesture.setChecked(display.get('show_gesture_name', True))
        self.check_fps.setChecked(display.get('show_fps', True))
        self.check_blur.setChecked(display.get('blur_enabled', False))
        
        camera = self.config.get('camera', {})
        self.combo_device.setCurrentIndex(camera.get('device_id', 0))
        self.check_mirror.setChecked(camera.get('mirror', True))
        self.spin_fps.setValue(camera.get('fps', 30))
        
        recognition = self.config.get('recognition', {})
        self.spin_detection_conf.setValue(recognition.get('min_detection_confidence', 0.7))
        self.spin_tracking_conf.setValue(recognition.get('min_tracking_confidence', 0.5))
        self.spin_hold_time.setValue(recognition.get('static_gesture_hold_time_ms', 150))
        self.spin_cooldown.setValue(recognition.get('gesture_cooldown_ms', 700))
        
        safe_zone = self.config.get('safe_zone', {})
        self.check_safe_zone_enabled.setChecked(safe_zone.get('enabled', True))
        
        # 加载手势映射
        self._load_gesture_mappings()
    
    def _load_gesture_mappings(self):
        """加载手势映射到表格"""
        mappings = self.config.get('gesture_mappings', [])
        self.table_gestures.setRowCount(len(mappings))
        
        for i, mapping in enumerate(mappings):
            self.table_gestures.setItem(i, 0, QTableWidgetItem(mapping.get('display_name', '')))
            self.table_gestures.setItem(i, 1, QTableWidgetItem(mapping.get('action_type', '')))
            self.table_gestures.setItem(i, 2, QTableWidgetItem(mapping.get('action', '')))
            self.table_gestures.setItem(i, 3, QTableWidgetItem(str(mapping.get('cooldown_ms', 500))))
    
    def _save_config(self):
        """保存配置"""
        self.config['display'] = {
            'background_opacity': self.slider_opacity.value() / 100,
            'show_skeleton': self.check_skeleton.isChecked(),
            'show_gesture_name': self.check_gesture.isChecked(),
            'show_fps': self.check_fps.isChecked(),
            'blur_enabled': self.check_blur.isChecked()
        }
        
        self.config['camera'] = {
            'device_id': self.combo_device.currentIndex(),
            'mirror': self.check_mirror.isChecked(),
            'fps': self.spin_fps.value()
        }
        
        self.config['recognition'] = {
            'min_detection_confidence': self.spin_detection_conf.value(),
            'min_tracking_confidence': self.spin_tracking_conf.value(),
            'static_gesture_hold_time_ms': self.spin_hold_time.value(),
            'gesture_cooldown_ms': self.spin_cooldown.value()
        }
        
        self.config['safe_zone'] = {
            'enabled': self.check_safe_zone_enabled.isChecked()
        }
        
        self.config_changed.emit(self.config)
        self.accept()
    
    def _reset_config(self):
        """重置为默认配置"""
        reply = QMessageBox.question(
            self, "确认", "确定要重置为默认设置吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # TODO: 加载默认配置
            pass
    
    def _calibrate_camera(self):
        """校准摄像头"""
        QMessageBox.information(self, "校准", "摄像头校准功能开发中...")
    
    def _add_gesture_mapping(self):
        """添加手势映射"""
        row = self.table_gestures.rowCount()
        self.table_gestures.insertRow(row)
    
    def _remove_gesture_mapping(self):
        """删除手势映射"""
        row = self.table_gestures.currentRow()
        if row >= 0:
            self.table_gestures.removeRow(row)
    
    def _test_effect(self):
        """测试特效"""
        QMessageBox.information(self, "特效测试", "请在主界面做比心手势测试特效")
