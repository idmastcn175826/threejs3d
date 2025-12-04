"""
MediaPipe Adapter - MediaPipe 手势识别适配器
封装 MediaPipe Hands 进行手部关键点检测和手势分类
"""

import numpy as np
from typing import Optional, List, Tuple
import logging
import math
from collections import deque
import time

try:
    import mediapipe as mp
except ImportError:
    mp = None
    logging.warning("MediaPipe 未安装，手势识别功能不可用")

from ..domain.gesture import (
    GestureType, GestureState, GestureEvent, 
    HandLandmarks, GestureStateMachine
)

logger = logging.getLogger(__name__)


class MediaPipeAdapter:
    """MediaPipe 手势识别适配器"""
    
    def __init__(self, 
                 max_num_hands: int = 2,
                 min_detection_confidence: float = 0.7,
                 min_tracking_confidence: float = 0.5):
        
        if mp is None:
            raise RuntimeError("MediaPipe 未安装")
        
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        
        # 状态机
        self.state_machine = GestureStateMachine()
        
        # 动态手势检测历史
        self._position_history: deque = deque(maxlen=20)
        self._last_positions: dict = {}  # 每只手的历史位置
        
        # 上一次检测结果
        self._last_landmarks: List[HandLandmarks] = []
        self._last_gesture: Optional[GestureType] = None
        
        logger.info("MediaPipe 手势识别适配器已初始化")
    
    def process_frame(self, frame: np.ndarray) -> Tuple[List[HandLandmarks], Optional[GestureEvent]]:
        """
        处理视频帧，检测手部并识别手势
        
        Args:
            frame: RGB格式的图像帧
            
        Returns:
            (手部关键点列表, 手势事件)
        """
        results = self.hands.process(frame)
        
        landmarks_list = []
        gesture_event = None
        
        if results.multi_hand_landmarks:
            for hand_landmarks, handedness in zip(
                results.multi_hand_landmarks, 
                results.multi_handedness
            ):
                # 提取关键点
                landmarks = self._extract_landmarks(hand_landmarks, handedness)
                landmarks_list.append(landmarks)
                
                # 识别手势
                gesture = self._classify_gesture(landmarks)
                
                # 更新位置历史（用于动态手势检测）
                self._update_position_history(landmarks)
                
                # 检测动态手势
                dynamic_gesture = self._detect_dynamic_gesture(landmarks)
                if dynamic_gesture:
                    gesture = dynamic_gesture
                
                # 状态机更新
                state, should_trigger = self.state_machine.update(gesture)
                
                if should_trigger and gesture:
                    # 计算手势中心位置
                    palm_center = landmarks.get_palm_center()
                    if palm_center:
                        gesture_event = GestureEvent(
                            gesture_type=gesture,
                            confidence=landmarks.confidence,
                            handedness=landmarks.handedness,
                            position=(palm_center[0], palm_center[1]),
                            state=state,
                            landmarks=landmarks
                        )
        else:
            # 没有检测到手，重置状态机
            self.state_machine.update(None)
        
        self._last_landmarks = landmarks_list
        return landmarks_list, gesture_event
    
    def _extract_landmarks(self, hand_landmarks, handedness) -> HandLandmarks:
        """提取手部关键点"""
        landmarks = []
        for lm in hand_landmarks.landmark:
            landmarks.append((lm.x, lm.y, lm.z))
        
        return HandLandmarks(
            landmarks=landmarks,
            handedness=handedness.classification[0].label,
            confidence=handedness.classification[0].score
        )
    
    def _classify_gesture(self, landmarks: HandLandmarks) -> GestureType:
        """
        分类静态手势
        基于手指伸展状态判断手势类型
        """
        if len(landmarks.landmarks) < 21:
            return GestureType.UNKNOWN
        
        # 获取各手指伸展状态
        fingers_extended = [
            landmarks.is_finger_extended(i) for i in range(5)
        ]
        thumb, index, middle, ring, pinky = fingers_extended
        
        # 计数伸展的手指
        extended_count = sum(fingers_extended)
        
        # 识别手势
        # 握拳：所有手指都收起
        if extended_count == 0:
            return GestureType.FIST
        
        # 五指张开
        if extended_count == 5:
            return GestureType.FIVE_FINGERS
        
        # 单指（食指）
        if index and not middle and not ring and not pinky:
            return GestureType.ONE_FINGER
        
        # 双指（剪刀手）
        if index and middle and not ring and not pinky:
            return GestureType.TWO_FINGERS
        
        # 三指
        if index and middle and ring and not pinky:
            return GestureType.THREE_FINGERS
        
        # 四指
        if index and middle and ring and pinky and not thumb:
            return GestureType.FOUR_FINGERS
        
        # OK手势：拇指和食指接触
        if self._is_ok_gesture(landmarks):
            return GestureType.OK
        
        # 点赞：只有拇指伸展
        if thumb and not index and not middle and not ring and not pinky:
            return GestureType.THUMBS_UP
        
        # 比心：检测单手比心手势
        if self._is_heart_gesture(landmarks):
            return GestureType.HEART
        
        # 摇滚手势
        if index and pinky and not middle and not ring:
            return GestureType.ROCK
        
        return GestureType.UNKNOWN
    
    def _is_ok_gesture(self, landmarks: HandLandmarks) -> bool:
        """检测OK手势（拇指和食指尖接近）"""
        thumb_tip = landmarks.get_landmark(4)
        index_tip = landmarks.get_landmark(8)
        
        if thumb_tip and index_tip:
            distance = math.sqrt(
                (thumb_tip[0] - index_tip[0])**2 +
                (thumb_tip[1] - index_tip[1])**2
            )
            return distance < 0.05  # 归一化距离阈值
        return False
    
    def _is_heart_gesture(self, landmarks: HandLandmarks) -> bool:
        """检测单手比心手势"""
        # 拇指和食指尖接近形成心形顶部
        thumb_tip = landmarks.get_landmark(4)
        index_tip = landmarks.get_landmark(8)
        
        if thumb_tip and index_tip:
            tip_distance = math.sqrt(
                (thumb_tip[0] - index_tip[0])**2 +
                (thumb_tip[1] - index_tip[1])**2
            )
            # 其他手指收起
            fingers = [landmarks.is_finger_extended(i) for i in range(2, 5)]
            if tip_distance < 0.08 and not any(fingers):
                return True
        return False
    
    def _update_position_history(self, landmarks: HandLandmarks):
        """更新位置历史（用于动态手势检测）"""
        palm_center = landmarks.get_palm_center()
        if palm_center:
            hand_key = landmarks.handedness
            if hand_key not in self._last_positions:
                self._last_positions[hand_key] = deque(maxlen=20)
            
            self._last_positions[hand_key].append({
                'position': palm_center,
                'timestamp': time.time()
            })
    
    def _detect_dynamic_gesture(self, landmarks: HandLandmarks) -> Optional[GestureType]:
        """
        检测动态手势（滑动、挥手等）
        基于位置历史分析运动轨迹
        """
        hand_key = landmarks.handedness
        if hand_key not in self._last_positions:
            return None
        
        history = self._last_positions[hand_key]
        if len(history) < 5:
            return None
        
        # 获取最近的几个位置
        recent_positions = list(history)[-10:]
        
        if len(recent_positions) < 5:
            return None
        
        # 计算运动向量
        start_pos = recent_positions[0]['position']
        end_pos = recent_positions[-1]['position']
        
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]
        
        # 计算运动时间
        time_elapsed = recent_positions[-1]['timestamp'] - recent_positions[0]['timestamp']
        
        if time_elapsed < 0.1 or time_elapsed > 0.8:
            return None
        
        # 运动距离阈值
        min_distance = 0.15
        
        # 判断滑动方向
        if abs(dx) > min_distance and abs(dx) > abs(dy) * 1.5:
            # 水平滑动
            if dx > 0:
                return GestureType.SWIPE_RIGHT
            else:
                return GestureType.SWIPE_LEFT
        
        elif abs(dy) > min_distance and abs(dy) > abs(dx) * 1.5:
            # 垂直滑动
            if dy > 0:
                return GestureType.SWIPE_DOWN
            else:
                return GestureType.SWIPE_UP
        
        return None
    
    def detect_double_hand_heart(self, landmarks_list: List[HandLandmarks]) -> bool:
        """检测双手比心手势"""
        if len(landmarks_list) < 2:
            return False
        
        left_hand = None
        right_hand = None
        
        for lm in landmarks_list:
            if lm.handedness == "Left":
                left_hand = lm
            else:
                right_hand = lm
        
        if not left_hand or not right_hand:
            return False
        
        # 检查两只手的食指和拇指是否接近
        left_index = left_hand.get_landmark(8)
        right_index = right_hand.get_landmark(8)
        left_thumb = left_hand.get_landmark(4)
        right_thumb = right_hand.get_landmark(4)
        
        if all([left_index, right_index, left_thumb, right_thumb]):
            # 计算指尖距离
            index_distance = math.sqrt(
                (left_index[0] - right_index[0])**2 +
                (left_index[1] - right_index[1])**2
            )
            thumb_distance = math.sqrt(
                (left_thumb[0] - right_thumb[0])**2 +
                (left_thumb[1] - right_thumb[1])**2
            )
            
            # 双手形成心形的条件
            return index_distance < 0.1 and thumb_distance < 0.15
        
        return False
    
    def draw_landmarks(self, frame: np.ndarray, 
                       landmarks_list: List[HandLandmarks]) -> np.ndarray:
        """在帧上绘制手部关键点"""
        if mp is None:
            return frame
        
        # 需要将HandLandmarks转换回MediaPipe格式进行绘制
        # 这里我们手动绘制
        for landmarks in landmarks_list:
            points = [(int(lm[0] * frame.shape[1]), int(lm[1] * frame.shape[0])) 
                      for lm in landmarks.landmarks]
            
            # 绘制关键点
            for point in points:
                cv2.circle(frame, point, 4, (0, 255, 0), -1)
            
            # 绘制连接线
            connections = [
                # 拇指
                (0, 1), (1, 2), (2, 3), (3, 4),
                # 食指
                (0, 5), (5, 6), (6, 7), (7, 8),
                # 中指
                (9, 10), (10, 11), (11, 12),
                # 无名指
                (13, 14), (14, 15), (15, 16),
                # 小指
                (0, 17), (17, 18), (18, 19), (19, 20),
                # 手掌
                (5, 9), (9, 13), (13, 17)
            ]
            
            for start, end in connections:
                if start < len(points) and end < len(points):
                    cv2.line(frame, points[start], points[end], (0, 255, 255), 2)
        
        return frame
    
    def get_gesture_name(self, gesture: GestureType) -> str:
        """获取手势中文名称"""
        names = {
            GestureType.UNKNOWN: "未知",
            GestureType.ONE_FINGER: "单指",
            GestureType.TWO_FINGERS: "双指",
            GestureType.THREE_FINGERS: "三指",
            GestureType.FOUR_FINGERS: "四指",
            GestureType.FIVE_FINGERS: "五指张开",
            GestureType.FIST: "握拳",
            GestureType.OK: "OK",
            GestureType.THUMBS_UP: "点赞",
            GestureType.THUMBS_DOWN: "踩",
            GestureType.HEART: "比心",
            GestureType.DOUBLE_HEART: "双手比心",
            GestureType.ROCK: "摇滚",
            GestureType.SWIPE_LEFT: "左划",
            GestureType.SWIPE_RIGHT: "右划",
            GestureType.SWIPE_UP: "上划",
            GestureType.SWIPE_DOWN: "下划",
            GestureType.PUSH: "推",
            GestureType.PULL: "拉",
            GestureType.CIRCLE: "画圈",
            GestureType.DOUBLE_TAP: "双击"
        }
        return names.get(gesture, "未知")
    
    def release(self):
        """释放资源"""
        self.hands.close()
        logger.info("MediaPipe 适配器已释放")


# 需要导入cv2用于draw_landmarks
try:
    import cv2
except ImportError:
    cv2 = None
