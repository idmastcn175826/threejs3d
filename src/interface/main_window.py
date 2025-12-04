"""
Main Window - 主窗口
GestureControlPC 的主界面，包含摄像头显示、叠加层和控制功能
"""

import sys
import logging
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QApplication, QSystemTrayIcon,
    QMenu, QAction, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSize, pyqtSlot, QThread
from PyQt5.QtGui import QImage, QPixmap, QIcon, QFont, QPainter, QColor

import numpy as np

from .overlay import OverlayWidget, ParticleOverlay
from .config_ui import ConfigDialog
from ..application.orchestrator import Orchestrator, SystemState
from ..domain.gesture import GestureEvent, GestureType

logger = logging.getLogger(__name__)


class CameraWidget(QLabel):
    """摄像头显示组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(640, 480)
        self._opacity = 0.6
    
    def set_frame(self, frame: np.ndarray):
        """设置帧图像"""
        if frame is None:
            return
        
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        
        # BGR转RGB
        frame_rgb = frame[..., ::-1].copy()
        
        q_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)
        
        # 缩放到组件大小
        scaled_pixmap = pixmap.scaled(
            self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        
        self.setPixmap(scaled_pixmap)
    
    def set_opacity(self, opacity: float):
        """设置透明度"""
        self._opacity = opacity
        self.setStyleSheet(f"background-color: rgba(0, 0, 0, {int((1-opacity)*255)});")


class MainWindow(QMainWindow):
    """主窗口"""
    
    gesture_triggered = pyqtSignal(str, str)  # gesture_name, action_name
    # 线程安全信号
    _frame_ready = pyqtSignal(object)  # 帧数据就绪信号
    _gesture_detected = pyqtSignal(object, object)  # 手势检测信号
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("GestureControlPC - 手势控制")
        self.setMinimumSize(800, 600)
        self.resize(1280, 720)
        
        # 初始化调度器
        self.orchestrator = Orchestrator()
        
        # UI组件
        self.camera_widget: CameraWidget = None
        self.overlay: OverlayWidget = None
        self.particle_overlay: ParticleOverlay = None
        
        # 状态
        self._is_running = False
        self._is_fullscreen = False
        
        # 定时器
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_frame)
        
        # 系统托盘
        self.tray_icon: QSystemTrayIcon = None
        
        self._init_ui()
        self._init_tray()
        self._connect_signals()
        
        logger.info("主窗口已初始化")
    
    def _init_ui(self):
        """初始化UI"""
        # 中央组件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 摄像头容器（使用相对布局实现叠加）
        self.camera_container = QWidget()
        self.camera_container.setStyleSheet("background-color: #1a1a2e;")
        self.camera_container.setMinimumSize(640, 480)
        
        # 摄像头显示
        self.camera_widget = CameraWidget(self.camera_container)
        
        # 叠加层
        self.overlay = OverlayWidget(self.camera_container)
        
        # 粒子叠加层
        self.particle_overlay = ParticleOverlay(self.camera_container)
        
        main_layout.addWidget(self.camera_container, 1)
        
        # 初始化子组件大小
        self._resize_overlays()
        
        # 控制栏
        control_bar = self._create_control_bar()
        main_layout.addWidget(control_bar)
        
        # 设置窗口样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #16213e;
            }
            QPushButton {
                background-color: #0f3460;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1a508b;
            }
            QPushButton:pressed {
                background-color: #0d2d50;
            }
            QPushButton:checked {
                background-color: #e94560;
            }
            QLabel {
                color: white;
            }
        """)
    
    def _create_control_bar(self) -> QWidget:
        """创建控制栏"""
        bar = QFrame()
        bar.setFixedHeight(60)
        bar.setStyleSheet("background-color: #0f3460;")
        
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 10, 20, 10)
        
        # 开始/停止按钮
        self.btn_start = QPushButton("▶ 开始")
        self.btn_start.setCheckable(True)
        self.btn_start.clicked.connect(self._toggle_running)
        
        # 全屏按钮
        self.btn_fullscreen = QPushButton("⛶ 全屏")
        self.btn_fullscreen.clicked.connect(self._toggle_fullscreen)
        
        # 设置按钮
        self.btn_settings = QPushButton("⚙ 设置")
        self.btn_settings.clicked.connect(self._show_settings)
        
        # 特效测试按钮
        self.btn_effect = QPushButton("✨ 特效")
        self.btn_effect.clicked.connect(self._test_effect)
        
        # 状态标签
        self.label_status = QLabel("就绪")
        self.label_status.setStyleSheet("color: #00ff00; font-size: 14px;")
        
        # FPS标签
        self.label_fps = QLabel("FPS: --")
        self.label_fps.setStyleSheet("color: #00ffff; font-size: 14px;")
        
        # 手势标签
        self.label_gesture = QLabel("手势: --")
        self.label_gesture.setStyleSheet("color: #ffff00; font-size: 14px;")
        
        layout.addWidget(self.btn_start)
        layout.addWidget(self.btn_fullscreen)
        layout.addWidget(self.btn_settings)
        layout.addWidget(self.btn_effect)
        layout.addStretch()
        layout.addWidget(self.label_gesture)
        layout.addWidget(self.label_fps)
        layout.addWidget(self.label_status)
        
        return bar
    
    def _init_tray(self):
        """初始化系统托盘"""
        self.tray_icon = QSystemTrayIcon(self)
        
        # 创建托盘菜单
        tray_menu = QMenu()
        
        action_show = QAction("显示", self)
        action_show.triggered.connect(self.show)
        
        action_start = QAction("开始/停止", self)
        action_start.triggered.connect(self._toggle_running)
        
        action_quit = QAction("退出", self)
        action_quit.triggered.connect(self._quit_app)
        
        tray_menu.addAction(action_show)
        tray_menu.addAction(action_start)
        tray_menu.addSeparator()
        tray_menu.addAction(action_quit)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._tray_activated)
        
        # 设置图标（使用默认图标）
        self.tray_icon.setIcon(self.style().standardIcon(
            self.style().SP_ComputerIcon
        ))
        self.tray_icon.show()
    
    def _connect_signals(self):
        """连接信号"""
        # 连接线程安全信号到槽函数（主线程执行）
        self._frame_ready.connect(self._handle_frame_update)
        self._gesture_detected.connect(self._handle_gesture_detected)
        
        # 状态变更回调（从主线程调用，安全）
        self.orchestrator.on_state_change(self._on_state_change)
        
        # 注意：手势回调在工作线程中执行，只能发射信号
        self.orchestrator.on_gesture(self._emit_gesture_signal)
    
    def _on_state_change(self, old_state: SystemState, new_state: SystemState):
        """状态变更回调"""
        state_names = {
            SystemState.STOPPED: "已停止",
            SystemState.STARTING: "启动中...",
            SystemState.RUNNING: "运行中",
            SystemState.PAUSED: "已暂停",
            SystemState.STOPPING: "停止中...",
            SystemState.ERROR: "错误"
        }
        self.label_status.setText(state_names.get(new_state, "未知"))
    
    def _toggle_running(self):
        """切换运行状态"""
        if self._is_running:
            self._stop()
        else:
            self._start()
    
    def _start(self):
        """启动系统"""
        if self.orchestrator.start():
            self._is_running = True
            self.btn_start.setText("⏹ 停止")
            self.btn_start.setChecked(True)
            self.label_status.setText("运行中")
            self.label_status.setStyleSheet("color: #00ff00; font-size: 14px;")
            
            # 启动更新定时器
            self.update_timer.start(33)  # ~30fps
            
            logger.info("系统已启动")
    
    def _stop(self):
        """停止系统"""
        self.update_timer.stop()
        self.orchestrator.stop()
        
        self._is_running = False
        self.btn_start.setText("▶ 开始")
        self.btn_start.setChecked(False)
        self.label_status.setText("已停止")
        self.label_status.setStyleSheet("color: #ff6600; font-size: 14px;")
        
        logger.info("系统已停止")
    
    def _update_frame(self):
        """更新帧显示 - 在主线程中安全调用"""
        try:
            if not self._is_running:
                return
                
            result = self.orchestrator.get_latest_result()
            if result:
                frame = result.get('frame')
                if frame is not None:
                    self.camera_widget.set_frame(frame)
                
                # 更新叠加层
                landmarks = result.get('landmarks', [])
                self.overlay.set_landmarks(landmarks)
                
                gesture_event = result.get('gesture_event')
                if gesture_event and self.orchestrator.gesture_service:
                    try:
                        name = self.orchestrator.gesture_service.get_gesture_name(
                            gesture_event.gesture_type
                        )
                        self.overlay.set_gesture(gesture_event.gesture_type, name)
                        self.label_gesture.setText(f"手势: {name}")
                    except Exception:
                        pass
                
                # 更新FPS
                fps = result.get('fps', 0)
                self.overlay.set_fps(fps)
                self.label_fps.setText(f"FPS: {fps:.1f}")
                
                # 更新粒子
                if self.orchestrator.action_service:
                    try:
                        particles = self.orchestrator.action_service.effect_renderer.particle_pool.get_active_particles()
                        self.particle_overlay.set_particles(particles)
                    except Exception:
                        pass
        except Exception as e:
            logger.debug(f"帧更新异常: {e}")
    
    def _toggle_fullscreen(self):
        """切换全屏"""
        if self._is_fullscreen:
            self.showNormal()
            self.btn_fullscreen.setText("⛶ 全屏")
        else:
            self.showFullScreen()
            self.btn_fullscreen.setText("⛶ 退出全屏")
        
        self._is_fullscreen = not self._is_fullscreen
    
    def _show_settings(self):
        """显示设置对话框"""
        config = self.orchestrator.config_manager.settings.copy()
        config['gesture_mappings'] = self.orchestrator.config_manager.get_gesture_mappings()
        
        dialog = ConfigDialog(config, self)
        dialog.config_changed.connect(self._apply_config)
        dialog.exec_()
    
    def _apply_config(self, config: dict):
        """应用配置"""
        # 更新配置管理器
        for key, value in config.items():
            if key != 'gesture_mappings':
                self.orchestrator.config_manager.update_setting(key, value)
        
        # 保存配置
        self.orchestrator.save_config()
        
        # 重新加载
        self.orchestrator.reload_config()
        
        # 更新显示
        display = config.get('display', {})
        opacity = display.get('background_opacity', 0.6)
        self.camera_widget.set_opacity(opacity)
        
        self.overlay.set_display_options(
            skeleton=display.get('show_skeleton', True),
            gesture=display.get('show_gesture_name', True),
            fps=display.get('show_fps', True)
        )
        
        logger.info("配置已应用")
    
    def _test_effect(self):
        """测试特效"""
        if self._is_running:
            self.orchestrator.trigger_effect("star_heart", (0.5, 0.5))
            self.overlay.show_action_feedback("✨ 星空心心 ✨", 1500)
    
    def _emit_gesture_signal(self, event: GestureEvent, result):
        """发射手势信号（在工作线程中调用）"""
        # 通过信号传递到主线程
        self._gesture_detected.emit(event, result)
    
    @pyqtSlot(object, object)
    def _handle_gesture_detected(self, event, result):
        """处理手势检测（在主线程中执行）"""
        try:
            if result and result.success:
                action = result.action
                self.overlay.show_action_feedback(
                    f"✓ {action.display_name}", 800
                )
                self.gesture_triggered.emit(
                    event.gesture_type.name,
                    action.action_value
                )
        except Exception as e:
            logger.debug(f"手势处理异常: {e}")
    
    @pyqtSlot(object)
    def _handle_frame_update(self, result):
        """处理帧更新（在主线程中执行）"""
        # 预留接口，当前由定时器拉取
        pass
    
    def _tray_activated(self, reason):
        """托盘图标激活"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()
            self.activateWindow()
    
    def _quit_app(self):
        """退出应用"""
        self._stop()
        QApplication.quit()
    
    def _resize_overlays(self):
        """调整叠加层大小"""
        container_size = self.camera_container.size()
        w, h = container_size.width(), container_size.height()
        if w > 0 and h > 0:
            self.camera_widget.setGeometry(0, 0, w, h)
            self.overlay.setGeometry(0, 0, w, h)
            self.particle_overlay.setGeometry(0, 0, w, h)
    
    def showEvent(self, event):
        """窗口显示事件"""
        super().showEvent(event)
        # 延迟调整大小，确保布局完成
        QTimer.singleShot(100, self._resize_overlays)
    
    def resizeEvent(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)
        self._resize_overlays()
    
    def closeEvent(self, event):
        """关闭事件"""
        # 最小化到托盘
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "GestureControlPC",
            "程序已最小化到系统托盘",
            QSystemTrayIcon.Information,
            2000
        )
    
    def keyPressEvent(self, event):
        """按键事件"""
        if event.key() == Qt.Key_Escape:
            if self._is_fullscreen:
                self._toggle_fullscreen()
        elif event.key() == Qt.Key_Space:
            self._toggle_running()
        elif event.key() == Qt.Key_F11:
            self._toggle_fullscreen()


def run_app():
    """运行应用程序"""
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName("GestureControlPC")
    app.setStyle('Fusion')
    
    # 设置全局字体
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    run_app()
