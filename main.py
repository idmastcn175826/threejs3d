#!/usr/bin/env python3
"""
GestureControlPC - 手势控制电脑系统
主入口文件

基于摄像头 + 实时手势识别的免触碰电脑控制系统
支持手势识别、动作映射、视觉特效（星空心心）

使用方法:
    python main.py              # 启动图形界面
    python main.py --headless   # 无界面模式（仅识别）
    python main.py --test       # 运行测试
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))


def setup_logging(level: str = "INFO"):
    """配置日志"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / "gesture_control.log", encoding='utf-8')
        ]
    )


def run_gui():
    """运行图形界面"""
    from src.interface.main_window import run_app
    run_app()


def run_headless():
    """无界面模式运行"""
    from src.application.orchestrator import Orchestrator
    
    logging.info("以无界面模式启动...")
    
    orchestrator = Orchestrator()
    
    def on_gesture(event, result):
        if result and result.success:
            logging.info(f"手势触发: {event.gesture_type.name} -> {result.action.display_name}")
    
    orchestrator.on_gesture(on_gesture)
    
    if orchestrator.start():
        logging.info("系统已启动，按 Ctrl+C 停止")
        try:
            import time
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            logging.info("收到停止信号")
        finally:
            orchestrator.stop()
    else:
        logging.error("启动失败")
        sys.exit(1)


def run_tests():
    """运行测试"""
    import pytest
    sys.exit(pytest.main(["-v", "tests/"]))


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="GestureControlPC - 手势控制电脑系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py                # 启动图形界面
  python main.py --headless     # 无界面模式
  python main.py --test         # 运行测试
  python main.py --log DEBUG    # 调试模式
        """
    )
    
    parser.add_argument(
        "--headless", 
        action="store_true",
        help="无界面模式运行"
    )
    
    parser.add_argument(
        "--test", 
        action="store_true",
        help="运行单元测试"
    )
    
    parser.add_argument(
        "--log", 
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="日志级别 (默认: INFO)"
    )
    
    args = parser.parse_args()
    
    # 配置日志
    setup_logging(args.log)
    
    logging.info("=" * 50)
    logging.info("GestureControlPC v1.0.0")
    logging.info("=" * 50)
    
    if args.test:
        run_tests()
    elif args.headless:
        run_headless()
    else:
        run_gui()


if __name__ == "__main__":
    main()
