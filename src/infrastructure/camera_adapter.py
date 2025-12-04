"""
Camera Adapter - 摄像头适配器
负责摄像头采集、图像校准、预处理
"""

import cv2
import numpy as np
from typing import Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class CameraConfig:
    """摄像头配置"""
    device_id: int = 0
    width: int = 1280
    height: int = 720
    fps: int = 30
    mirror: bool = True
    rotation: int = 0  # 0, 90, 180, 270
    brightness: float = 0
    contrast: float = 1.0
    
    @classmethod
    def from_dict(cls, config: dict) -> 'CameraConfig':
        return cls(
            device_id=config.get('device_id', 0),
            width=config.get('width', 1280),
            height=config.get('height', 720),
            fps=config.get('fps', 30),
            mirror=config.get('mirror', True),
            rotation=config.get('rotation', 0),
            brightness=config.get('brightness_adjustment', 0),
            contrast=config.get('contrast_adjustment', 1.0)
        )


class CameraAdapter:
    """摄像头适配器 - 负责视频采集和图像预处理"""
    
    def __init__(self, config: Optional[CameraConfig] = None):
        self.config = config or CameraConfig()
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_running = False
        
        # 校准参数
        self.camera_matrix: Optional[np.ndarray] = None
        self.dist_coeffs: Optional[np.ndarray] = None
        self.new_camera_matrix: Optional[np.ndarray] = None
        
        # 透视变换矩阵
        self.perspective_matrix: Optional[np.ndarray] = None
        
        # ROI区域
        self.roi: Optional[Tuple[int, int, int, int]] = None  # (x, y, w, h)
    
    def start(self) -> bool:
        """启动摄像头"""
        try:
            self.cap = cv2.VideoCapture(self.config.device_id, cv2.CAP_DSHOW)
            
            # 设置分辨率
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.config.fps)
            
            # 检查是否成功打开
            if not self.cap.isOpened():
                logger.error(f"无法打开摄像头 {self.config.device_id}")
                return False
            
            self.is_running = True
            logger.info(f"摄像头已启动: {self.config.width}x{self.config.height}@{self.config.fps}fps")
            return True
            
        except Exception as e:
            logger.error(f"启动摄像头失败: {e}")
            return False
    
    def stop(self):
        """停止摄像头"""
        self.is_running = False
        if self.cap:
            self.cap.release()
            self.cap = None
        logger.info("摄像头已停止")
    
    def get_frame(self) -> Optional[np.ndarray]:
        """获取一帧图像（已处理）"""
        if not self.cap or not self.is_running:
            return None
        
        ret, frame = self.cap.read()
        if not ret:
            return None
        
        # 应用图像处理
        frame = self._process_frame(frame)
        return frame
    
    def get_raw_frame(self) -> Optional[np.ndarray]:
        """获取原始帧（未处理）"""
        if not self.cap or not self.is_running:
            return None
        
        ret, frame = self.cap.read()
        return frame if ret else None
    
    def _process_frame(self, frame: np.ndarray) -> np.ndarray:
        """处理帧图像"""
        # 1. 畸变校正
        if self.camera_matrix is not None and self.dist_coeffs is not None:
            frame = cv2.undistort(frame, self.camera_matrix, self.dist_coeffs, 
                                  None, self.new_camera_matrix)
        
        # 2. 透视变换
        if self.perspective_matrix is not None:
            h, w = frame.shape[:2]
            frame = cv2.warpPerspective(frame, self.perspective_matrix, (w, h))
        
        # 3. 镜像
        if self.config.mirror:
            frame = cv2.flip(frame, 1)
        
        # 4. 旋转
        if self.config.rotation != 0:
            frame = self._rotate_frame(frame, self.config.rotation)
        
        # 5. 亮度/对比度调整
        if self.config.brightness != 0 or self.config.contrast != 1.0:
            frame = self._adjust_brightness_contrast(
                frame, self.config.brightness, self.config.contrast)
        
        # 6. ROI裁剪
        if self.roi:
            x, y, w, h = self.roi
            frame = frame[y:y+h, x:x+w]
        
        return frame
    
    def _rotate_frame(self, frame: np.ndarray, degrees: int) -> np.ndarray:
        """旋转帧"""
        if degrees == 90:
            return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        elif degrees == 180:
            return cv2.rotate(frame, cv2.ROTATE_180)
        elif degrees == 270:
            return cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
        return frame
    
    def _adjust_brightness_contrast(self, frame: np.ndarray, 
                                     brightness: float, contrast: float) -> np.ndarray:
        """调整亮度和对比度"""
        frame = frame.astype(np.float32)
        frame = frame * contrast + brightness
        frame = np.clip(frame, 0, 255).astype(np.uint8)
        return frame
    
    def preprocess_for_detection(self, frame: np.ndarray) -> np.ndarray:
        """
        为手势检测预处理图像
        包括降噪、色彩均衡等
        """
        # 转换为RGB（MediaPipe需要RGB格式）
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 轻微高斯模糊降噪
        frame_rgb = cv2.GaussianBlur(frame_rgb, (3, 3), 0)
        
        return frame_rgb
    
    def set_calibration(self, camera_matrix: np.ndarray, 
                        dist_coeffs: np.ndarray):
        """设置相机校准参数"""
        self.camera_matrix = camera_matrix
        self.dist_coeffs = dist_coeffs
        
        # 计算新的相机矩阵
        h, w = self.config.height, self.config.width
        self.new_camera_matrix, _ = cv2.getOptimalNewCameraMatrix(
            camera_matrix, dist_coeffs, (w, h), 1, (w, h))
    
    def set_perspective_transform(self, src_points: np.ndarray, 
                                   dst_points: np.ndarray):
        """设置透视变换"""
        self.perspective_matrix = cv2.getPerspectiveTransform(src_points, dst_points)
    
    def set_roi(self, x: int, y: int, width: int, height: int):
        """设置ROI区域"""
        self.roi = (x, y, width, height)
    
    def clear_roi(self):
        """清除ROI"""
        self.roi = None
    
    def set_mirror(self, enabled: bool):
        """设置镜像"""
        self.config.mirror = enabled
    
    def set_rotation(self, degrees: int):
        """设置旋转角度"""
        if degrees in [0, 90, 180, 270]:
            self.config.rotation = degrees
    
    @property
    def frame_size(self) -> Tuple[int, int]:
        """获取帧尺寸"""
        return (self.config.width, self.config.height)
    
    @property
    def actual_fps(self) -> float:
        """获取实际帧率"""
        if self.cap:
            return self.cap.get(cv2.CAP_PROP_FPS)
        return 0
    
    def list_available_cameras(self, max_cameras: int = 10) -> list:
        """列出可用摄像头"""
        available = []
        for i in range(max_cameras):
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            if cap.isOpened():
                available.append(i)
                cap.release()
        return available


class SafeZone:
    """安全区域 - 只有在此区域内的手势才会触发动作"""
    
    def __init__(self, x_min: float = 0.2, x_max: float = 0.8,
                 y_min: float = 0.2, y_max: float = 0.8):
        """
        Args:
            x_min, x_max: x方向的归一化范围 (0-1)
            y_min, y_max: y方向的归一化范围 (0-1)
        """
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max
    
    def is_inside(self, x: float, y: float) -> bool:
        """检查坐标是否在安全区域内"""
        return (self.x_min <= x <= self.x_max and 
                self.y_min <= y <= self.y_max)
    
    def get_screen_rect(self, screen_width: int, screen_height: int) -> Tuple[int, int, int, int]:
        """获取屏幕像素坐标矩形 (x, y, w, h)"""
        x = int(self.x_min * screen_width)
        y = int(self.y_min * screen_height)
        w = int((self.x_max - self.x_min) * screen_width)
        h = int((self.y_max - self.y_min) * screen_height)
        return (x, y, w, h)
    
    @classmethod
    def from_config(cls, config: dict) -> 'SafeZone':
        """从配置创建"""
        return cls(
            x_min=config.get('x_min', 0.2),
            x_max=config.get('x_max', 0.8),
            y_min=config.get('y_min', 0.2),
            y_max=config.get('y_max', 0.8)
        )
