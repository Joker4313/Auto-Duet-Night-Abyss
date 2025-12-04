import cv2
import numpy as np
import mss
import pydirectinput
import time
import os

# ================= 核心配置区域 =================

# 1. 区域设置
GAME_ROI = {"left": 2160, "top": 520, "width": 35, "height": 530}
BITE_ROI = {"left": 2005, "top": 950, "width": 350, "height": 350}
EXIT_CLICK_POS = (1800, 1000)

# 2. 颜色参数
RING_LOWER = np.array([6, 50, 180])
RING_UPPER = np.array([10, 69, 247])

BLUE_LOWER = np.array([110, 150, 80])
BLUE_UPPER = np.array([128, 255, 255])
FISH_LOWER = np.array([0, 0, 180])
FISH_UPPER = np.array([179, 15, 255])

# 3. 阈值设置 (关键修改点!)
COLOR_PIXEL_THRESHOLD = 1000

# 【修改】拆分为两个阈值
CONFIDENCE_SPACE = 0.85  # Space是2D固定UI，要求高一点
CONFIDENCE_E = 0.60  # E是3D悬浮UI，背景会变，必须降低要求！

# 【修改】防误触门槛提高
# 防止背景的蓝色冰块被误认为是蓝条，从100提高到500
GAME_ACTIVE_THRESHOLD = 500

# ==============================================================

# 加载模板
templates = {}
if os.path.exists("cast_icon.png"):
    templates["SPACE"] = cv2.imread("cast_icon.png", 0)
    print("✅ Space 模板加载成功")
else:
    print("❌ 警告: 没找到 cast_icon.png")

if os.path.exists("cast_icon_e.png"):
    templates["E"] = cv2.imread("cast_icon_e.png", 0)
    print("✅ E 模板加载成功 (E键模式已启用)")
else:
    print("⚠️ 未找到 cast_icon_e.png，无法识别E键")


def check_icon(sct, template):
    """通用模板匹配"""
    if template is None:
        return 0
    monitor = sct.monitors[1]
    img = np.array(sct.grab(monitor))
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
    res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(res)
    return max_val


def is_game_active(sct):
    """检测是否在小游戏中"""
    img = np.array(sct.grab(GAME_ROI))
    hsv = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    hsv = cv2.cvtColor(hsv, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, BLUE_LOWER, BLUE_UPPER)
    # 门槛提高到 500，过滤背景干扰
    return cv2.countNonZero(mask) > GAME_ACTIVE_THRESHOLD


def check_bite_by_color(sct):
    img_bgra = np.array(sct.grab(BITE_ROI))
    img_hsv = cv2.cvtColor(img_bgra, cv2.COLOR_BGRA2BGR)
    img_hsv = cv2.cvtColor(img_hsv, cv2.COLOR_BGR2HSV)
    mask_ring = cv2.inRange(img_hsv, RING_LOWER, RING_UPPER)
    return cv2.countNonZero(mask_ring)


def get_center_y(mask):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        c = max(contours, key=cv2.contourArea)
        if cv2.contourArea(c) < 10:
            return None
        x, y, w, h = cv2.boundingRect(c)
        return y + h // 2
    return None


def auto_fishing_bot():
    print("✅ 智能钓鱼机器人 (E键修复版) 已启动！")
    print("👉 正在实时打印相似度，请观察控制台数值...")
    time.sleep(2)

    with mss.mss() as sct:
        state = "IDLE"
        no_fish_timer = 0
        is_holding_space = False

        while True:
            # ================= 状态 0: 寻找时机 (IDLE) =================
            if state == "IDLE":
                # 1. 游戏活跃检查 (带Log，方便排查是否误触)
                if is_game_active(sct):
                    print("⚠️ 监测到蓝条 (Active)，切换至 PLAYING")
                    state = "PLAYING"
                    continue

                # 2. 获取相似度
                conf_space = check_icon(sct, templates.get("SPACE"))
                conf_e = check_icon(sct, templates.get("E"))

                # 【核心调试】实时打印相似度，不操作时也能看到数值
                # 这样你就能看到 E 图标到底识别了多少 (比如 0.72)
                # print(f"\r🔍 监测中... Space: {conf_space:.2f} | E: {conf_e:.2f}", end="")

                # 3. 判定逻辑
                if conf_space > CONFIDENCE_SPACE:
                    print(f"\n🚀 发现 Space (相似度:{conf_space:.2f}) -> 抛竿")
                    time.sleep(0.2)
                    pydirectinput.press("space")
                    time.sleep(2.5)
                    state = "WAITING"

                # E 键阈值独立判断 (0.60即可通过)
                elif conf_e > CONFIDENCE_E:
                    print(f"\n🚀 发现 E 键 (相似度:{conf_e:.2f}) -> 抛竿")
                    time.sleep(0.2)
                    pydirectinput.press("e")
                    time.sleep(2.5)
                    state = "WAITING"

                else:
                    # 如果都没找到，短暂停顿
                    time.sleep(0.2)

            # ================= 状态 2: 等待光圈 (WAITING) =================
            elif state == "WAITING":
                matched_pixels = check_bite_by_color(sct)
                if matched_pixels > COLOR_PIXEL_THRESHOLD:
                    print(f"\n⚡ 咬钩 (像素:{matched_pixels}) -> 提竿")
                    pydirectinput.press("space")
                    time.sleep(0.2)
                    state = "PLAYING"
                    no_fish_timer = time.time()

                time.sleep(0.05)

            # ================= 状态 3: 玩小游戏 (PLAYING) =================
            elif state == "PLAYING":
                # ... (保持原有的控鱼逻辑不变) ...
                game_img = np.array(sct.grab(GAME_ROI))
                hsv = cv2.cvtColor(game_img, cv2.COLOR_BGRA2BGR)
                hsv = cv2.cvtColor(hsv, cv2.COLOR_BGR2HSV)

                mask_bar = cv2.inRange(hsv, BLUE_LOWER, BLUE_UPPER)
                mask_fish = cv2.inRange(hsv, FISH_LOWER, FISH_UPPER)
                bar_y = get_center_y(mask_bar)
                fish_y = get_center_y(mask_fish)

                if bar_y is not None and fish_y is not None:
                    no_fish_timer = time.time()
                    diff = fish_y - bar_y
                    tolerance = 20
                    if diff < -tolerance:
                        if not is_holding_space:
                            pydirectinput.keyDown("space")
                            is_holding_space = True
                    elif diff > tolerance:
                        if is_holding_space:
                            pydirectinput.keyUp("space")
                            is_holding_space = False
                    else:
                        if is_holding_space:
                            pydirectinput.keyUp("space")
                            is_holding_space = False
                else:
                    if is_holding_space:
                        pydirectinput.keyUp("space")
                        is_holding_space = False

                    # 游戏结束检测
                    if time.time() - no_fish_timer > 3.0:
                        print("\n🎉 钓鱼结束，关闭结算...")
                        time.sleep(3.5)  # 缩短等待时间，抢时间窗口

                        print(f"🖱️ 点击退出 {EXIT_CLICK_POS}")
                        pydirectinput.moveTo(EXIT_CLICK_POS[0], EXIT_CLICK_POS[1])
                        time.sleep(0.1)
                        pydirectinput.click()

                        # 点击后只需极短等待，立刻开始寻找E图标
                        time.sleep(0.5)
                        state = "IDLE"

            # 循环末尾
            time.sleep(0.01)  # 可以注释掉这个，让IDLE响应更快

if __name__ == "__main__":
    auto_fishing_bot()
