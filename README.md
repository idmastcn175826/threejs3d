# GestureControlPC 🖐️

基于摄像头 + 实时手势识别的"免触碰"电脑控制系统

## 功能特点

- **摄像头背景显示**：全屏半透明背景，透明度可调
- **手势识别**：静态手势（1-5手指、拳头、OK、比心）+ 动态手势（左右划、上下推拉）
- **动作映射**：支持鼠标、键盘、系统命令、自定义脚本
- **视觉特效**：星空心心粒子特效，手势触发
- **摄像头校准**：镜像、旋转、透视矫正、Safe Zone

## 系统要求

- Windows 10/11
- Python 3.9+
- USB 摄像头或笔记本内置摄像头
- 8GB+ 内存

## 安装

```bash
# 创建虚拟环境
python -m venv venv
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 运行
python main.py
```

## 项目结构

```
GestureControlPC/
├── src/
│   ├── domain/          # 领域模型
│   ├── application/     # 应用服务层
│   ├── infrastructure/  # 技术实现层
│   └── interface/       # UI层
├── config/              # 配置文件
├── tests/               # 单元测试
├── logs/                # 日志目录
└── docs/                # 文档
```

## 手势列表

| 手势 | 默认动作 | 描述 |
|------|----------|------|
| 👆 单指 | 播放/暂停 | 伸出食指 |
| ✌️ 双指 | 上一首 | 伸出食指和中指 |
| 🤟 三指 | 下一首 | 伸出食指、中指、无名指 |
| 🖐️ 五指张开 | Alt+Tab | 五指全部张开 |
| ✊ 握拳 | 左键点击 | 握紧拳头 |
| 👌 OK | 复制 | OK手势 |
| ❤️ 双手比心 | 星空心心特效 | 双手比心触发特效 |

## 配置

编辑 `config/` 目录下的 JSON 文件自定义设置：

- `settings.json` - 全局设置
- `gestures.json` - 手势动作映射
- `effects.json` - 特效参数
- `calibration.json` - 摄像头校准

## License

MIT License
