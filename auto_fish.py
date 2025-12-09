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

# =========================================================
# 2. 多区域参数配置 (请填入实际值)
# =========================================================

# 【区域 1】净界岛
ZONE1_LOWER = np.array([6, 50, 180])
ZONE1_UPPER = np.array([11, 75, 255])

# 【区域 2】冰湖城
ZONE2_LOWER = np.array([1, 115, 170])
ZONE2_UPPER = np.array([105, 120, 255])

# 【区域 3】下水道
ZONE3_LOWER = np.array([1, 0, 80])  # <--- 请替换
ZONE3_UPPER = np.array([11, 30, 255])  # <--- 请替换

# =========================================================

# 3. 小游戏颜色
BLUE_LOWER = np.array([110, 150, 80])
BLUE_UPPER = np.array([128, 255, 255])
FISH_LOWER = np.array([0, 0, 180])
FISH_UPPER = np.array([179, 15, 255])

# 4. 阈值设置
COLOR_PIXEL_THRESHOLD = 1000
CONFIDENCE_SPACE = 0.85
CONFIDENCE_E = 0.60
GAME_ACTIVE_THRESHOLD = 500

# 全局变量，用于存储当前选中的参数
CURRENT_RING_LOWER = None
CURRENT_RING_UPPER = None

# ==============================================================

# 加载模板
templates = {}
if os.path.exists("assets/images/cast_icon.png"):
    templates["SPACE"] = cv2.imread("assets/images/cast_icon.png", 0)
    print("✅ Space 模板加载成功")
else:
    print("❌ 警告: 没找到 cast_icon.png")

if os.path.exists("assets/images/cast_icon_e.png"):
    templates["E"] = cv2.imread("assets/images/cast_icon_e.png", 0)
    print("✅ E 模板加载成功")
else:
    print("⚠️ 未找到 cast_icon_e.png")


def select_zone():
    """启动时让用户选择区域"""
    global CURRENT_RING_LOWER, CURRENT_RING_UPPER

    print("\n" + "=" * 30)
    print("   🎣 请选择当前钓鱼区域")
    print("=" * 30)
    print(" 1. 净界岛")
    print(" 2. 冰湖城")
    print(" 3. 下水道")
    print("=" * 30)

    choice = input("请输入序号 (1/2/3) 并回车: ").strip()

    if choice == "2":
        CURRENT_RING_LOWER = ZONE2_LOWER
        CURRENT_RING_UPPER = ZONE2_UPPER
        print("✅ 已加载冰湖城参数")
    elif choice == "3":
        CURRENT_RING_LOWER = ZONE3_LOWER
        CURRENT_RING_UPPER = ZONE3_UPPER
        print("✅ 已加载下水道参数")
    else:
        # 默认选1
        CURRENT_RING_LOWER = ZONE1_LOWER
        CURRENT_RING_UPPER = ZONE1_UPPER
        print("✅ 已加载净界岛参数")


def check_bite_current_zone(sct):
    """
    【专一检测】只检测当前选定区域的颜色
    """
    img_bgra = np.array(sct.grab(BITE_ROI))
    img_hsv = cv2.cvtColor(img_bgra, cv2.COLOR_BGRA2BGR)
    img_hsv = cv2.cvtColor(img_hsv, cv2.COLOR_BGR2HSV)

    # 只使用选定的那组参数，杜绝其他区域干扰
    mask = cv2.inRange(img_hsv, CURRENT_RING_LOWER, CURRENT_RING_UPPER)

    return cv2.countNonZero(mask)


def check_icon(sct, template):
    if template is None:
        return 0
    monitor = sct.monitors[1]
    img = np.array(sct.grab(monitor))
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
    res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(res)
    return max_val


def is_game_active(sct):
    img = np.array(sct.grab(GAME_ROI))
    hsv = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    hsv = cv2.cvtColor(hsv, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, BLUE_LOWER, BLUE_UPPER)
    return cv2.countNonZero(mask) > GAME_ACTIVE_THRESHOLD


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
    # 1. 启动时先选区
    select_zone()

    print("⏳ 3秒后开始运行，请切换回游戏...")
    time.sleep(3)
    print("✅ 智能钓鱼机器人已启动！")

    with mss.mss() as sct:
        state = "IDLE"
        no_fish_timer = 0
        is_holding_space = False

        while True:
            # ================= 状态 0: 寻找时机 (IDLE) =================
            if state == "IDLE":
                if is_game_active(sct):
                    print("⚠️ 监测到蓝条 (Active)，切换至 PLAYING")
                    state = "PLAYING"
                    continue

                conf_space = check_icon(sct, templates.get("SPACE"))
                conf_e = check_icon(sct, templates.get("E"))

                if conf_space > CONFIDENCE_SPACE:
                    print(f"\n🚀 发现 Space (相似度:{conf_space:.2f}) -> 抛竿")
                    time.sleep(0.2)
                    pydirectinput.press("space")
                    time.sleep(2.5)
                    state = "WAITING"

                elif conf_e > CONFIDENCE_E:
                    print(f"\n🚀 发现 E 键 (相似度:{conf_e:.2f}) -> 抛竿")
                    time.sleep(0.2)
                    pydirectinput.press("e")
                    time.sleep(2.5)
                    state = "WAITING"

                else:
                    time.sleep(0.2)

            # ================= 状态 2: 等待光圈 (WAITING) =================
            elif state == "WAITING":
                # 使用专一检测函数
                matched_pixels = check_bite_current_zone(sct)

                if matched_pixels > COLOR_PIXEL_THRESHOLD:
                    print(f"\n⚡ 咬钩 (像素:{matched_pixels}) -> 提竿")
                    pydirectinput.press("space")
                    time.sleep(0.2)
                    state = "PLAYING"
                    no_fish_timer = time.time()

                time.sleep(0.05)

            # ================= 状态 3: 玩小游戏 (PLAYING) =================
            elif state == "PLAYING":
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

                    if time.time() - no_fish_timer > 3.0:
                        print("\n🎉 钓鱼结束，关闭结算...")
                        time.sleep(1.5)

                        print(f"🖱️ 点击退出 {EXIT_CLICK_POS}")
                        pydirectinput.moveTo(EXIT_CLICK_POS[0], EXIT_CLICK_POS[1])
                        time.sleep(0.1)
                        pydirectinput.click()

                        time.sleep(0.5)
                        state = "IDLE"


if __name__ == "__main__":
    auto_fishing_bot()
