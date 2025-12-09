# Auto-Duet-Night-Abyss

二重螺旋自动脚本，包含钓鱼自动化和波次管理功能。

## 📋 项目简介

主要包含两个核心功能模块：

- **auto_fish.py** - 自动钓鱼脚本，支持多区域和自动钓鱼
- **auto_next_wave.py** - 自动波次管理脚本，支持自动选择多倍书、自动点击下一波次、自动退出

## 🚀 快速开始

### 系统要求

- Python >= 3.12
- Windows 操作系统
- 游戏以2560*1440分辨率运行
- 脚本需要以管理员身份运行

### 安装依赖

```bash
# 使用 pip 安装
pip install -r requirements.txt

# 或使用 uv（推荐）
uv pip install -r requirements.txt
```

### 核心依赖包

该项目使用以下主要依赖：

- **pyautogui** - GUI 自动化控制（鼠标、键盘）
- **opencv-python** - 图像处理和识别
- **mss** - 屏幕快速截图
- **keyboard** - 键盘事件监听
- **pydirectinput** - 后台直接输入（游戏兼容性更好）

## 📁 项目结构

```
.
├── auto_fish.py           # 钓鱼自动化脚本
├── auto_next_wave.py      # 波次管理脚本
├── get_config.py          # 配置文件解析
├── config.yaml            # 主配置文件
├── requirements.txt       # Python 依赖列表
├── pyproject.toml         # 项目元数据
└── README.md              # 本文件
```

## ⚙️ 配置说明

### config.yaml 主要参数

```yaml
# 通用设置
loop_interval: 0.1                    # 循环间隔（秒）
confidence: 0.8                       # 图像识别置信度(0.0-1.0)

# 游戏逻辑
target_wave_count: 3                  # 目标波数（到第几波结束停止）
selected_book_type: "green"           # 选择多倍书策略: green/blue/purple/gold/none

# 图像资源
image_paths:
  next_wave: "assets/images/next_wave_button.png"
  exit: "assets/images/exit_button.png"
  # ... 其他图像资源
```

### auto_fish.py 配置参数

```python
# 区域设置
GAME_ROI = {"left": 2160, "top": 520, "width": 35, "height": 530}
BITE_ROI = {"left": 2005, "top": 950, "width": 350, "height": 350}

# 多区域颜色范围（HSV）
ZONE1_LOWER = np.array([6, 50, 180])      # 净界岛
ZONE2_LOWER = np.array([1, 115, 170])    # 冰湖城
ZONE3_LOWER = np.array([1, 0, 80])       # 下水道

# 阈值
COLOR_PIXEL_THRESHOLD = 1000
CONFIDENCE_SPACE = 0.85
```

### auto_next_wave.py 配置参数

```python
TARGET_WAVE_COUNT = 0                 # 退出波次数
SELECTED_BOOK_TYPE = "green"          # 选书类型: green/blue/purple/gold/none
```

## 🎮 使用方法

### 运行钓鱼脚本（需管理员权限）

```bash
python auto_fish.py
```

或者使用uv(推荐)

```bash
uv run auto_fish.py
```

钓鱼脚本将：
1. 监听游戏画面中的鱼吃钩提示
2. 自动检测钓竿状态
3. 按下 `E` 键进行收竿
4. 自动钓鱼小游戏
5. 持续循环直到主动退出

### 运行波次管理脚本

```bash
python auto_next_wave.py
```

波次脚本将：
1. 自动选择指定颜色的多倍书
2. 点击"开始挑战"按钮
3. 根据设置自动点击"下一波"
4. 在达到目标波数后退出游戏

## 🔧 高级用法

### 自定义配置

1. **修改 config.yaml** 来调整全局参数
2. **运行脚本前准备截图** - 将游戏界面的按钮和卡牌截图放在 `assets/images/` 目录下
3. **调整置信度** - 如果识别不准，降低 `confidence` 值

### 调试技巧

- 设置 `loop_interval: 0.5` 以减缓脚本速度便于调试
- 降低 `confidence` 值如 `0.7` 来提高图像识别容错率
- 检查屏幕分辨率是否与 ROI 坐标匹配

## ⚠️ 重要提示

- **合法性** - 使用此脚本前请确保符合游戏的服务条款
- **风险** - 本项目基于图像识别和模拟点击，游戏需保持前台运行，使用自动化脚本可能导致账号风险，请谨慎使用
- **屏幕分辨率** - 所有坐标设置基于2560*1440p分辨率，如分辨率不同需自行调整区域坐标和重新截图

## 📸 资源文件

需要在 `assets/images/` 目录下准备以下截图：

- `next_wave_button.png` - "下一波"按钮
- `exit_button.png` - "退出"按钮
- `retry_button.png` - "重试"按钮
- `start_challenge_button.png` - "开始挑战"按钮
- `green_book_card.png` - 绿色多倍书
- `blue_book_card.png` - 蓝色多倍书
- `purple_book_card.png` - 紫色多倍书
- `gold_book_card.png` - 金色多倍书

## 🛠️ 故障排查

| 问题 | 解决方案 |
|------|--------|
| 脚本找不到按钮 | 检查 `confidence` 值，尝试降低至 0.7-0.75 |
| 坐标错误 | 确认游戏窗口分辨率与配置中的 ROI 坐标一致 |
| 图像资源缺失 | 运行脚本前确保所有 PNG 文件在 `assets/images/` 目录 |
| 点击无效 | 确保游戏窗口在前台，尝试使用 `pydirectinput` 替代 `pyautogui` |

## 📝 许可证

私有项目 - 仅供个人使用

## 👨‍💻 作者

Joker4313
