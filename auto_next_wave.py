import pyautogui
import time
import os
import random

# ================= 自定义配置区域 =================

# 1. 退出波次设置
# 设置为您希望退出的波次。
# 脚本会根据点击“下一波”的次数来判断。
# 例如：设置为 6，代表打完第 6 波后（出现下一波或结算按钮时）点击退出。
TARGET_WAVE_COUNT = 0

# 2. 书籍颜色设置
# 可选值: 'green' (绿), 'blue' (蓝), 'purple' (紫), 'gold' (金), 'none' (不使用)
# 注意：如果您选择 'none'，脚本将跳过选书步骤，直接寻找“开始挑战”按钮。
# 如果选择其他颜色，请确保目录下有对应的截图文件（见下方文件名说明）。
SELECTED_BOOK_TYPE = "green"

# ================= 配置结束 =================


def random_click(box, offset_y_ratio=0.0):
    """
    拟人化点击函数 (前台安全模式)
    """
    # 1. 计算随机坐标
    random_x = (
        box.left
        + (box.width / 2)
        + random.randint(int(-box.width * 0.3), int(box.width * 0.3))
    )

    # y 根据 offset_y_ratio 偏移中心
    center_y = box.top + (box.height / 2)
    offset_pixels = int(box.height * offset_y_ratio)
    random_y = (
        center_y
        + offset_pixels
        + random.randint(int(-box.height * 0.1), int(box.height * 0.1))
    )

    # 2. 拟人化移动轨迹
    move_duration = random.uniform(0.15, 0.4)
    pyautogui.moveTo(
        random_x, random_y, duration=move_duration, tween=pyautogui.easeOutQuad
    )

    # 3. 拟人化点击
    time.sleep(0.1)
    pyautogui.mouseDown()
    time.sleep(0.1)
    pyautogui.mouseUp()
    print("  -> 点击完成")


def auto_click_next_wave():
    # --- 图片文件配置 ---
    img_next_wave = "next_wave_button.png"  # 下一波按钮
    img_exit_button = "exit_button.png"  # 结算界面的"退出"按钮
    img_retry_button = "retry_button.png"  # "再次进行"按钮
    img_start_challenge = "start_challenge_button.png"  # 开始挑战按钮

    # 书籍图片映射表
    book_images = {
        "green": "green_book_card.png",
        "blue": "blue_book_card.png",
        "purple": "purple_book_card.png",
        "gold": "gold_book_card.png",
        "none": None,
    }

    # 获取当前配置对应的书籍图片
    target_book_img = book_images.get(SELECTED_BOOK_TYPE)

    confidence_level = 0.8
    loop_interval = 0.1

    # --- 检查图片文件 ---
    # 基础必须文件
    required_files = [
        img_next_wave,
        img_start_challenge,
        img_exit_button,
        img_retry_button,
    ]

    # 如果配置了选书，则必须检查对应的书籍截图是否存在
    if target_book_img:
        required_files.append(target_book_img)

    missing_files = []
    for img in required_files:
        if not os.path.exists(img):
            missing_files.append(img)

    if missing_files:
        print("错误: 缺少以下图片文件，请截图并保存在同目录下：")
        for f in missing_files:
            print(f" - {f}")
        return

    print("脚本已启动！")
    print(f"【配置】目标波次: {TARGET_WAVE_COUNT}")
    print(
        f"【配置】书籍策略: {SELECTED_BOOK_TYPE} "
        + (f"({target_book_img})" if target_book_img else "(直接开始)")
    )
    print("【重要】请务必【以管理员身份运行】终端！")
    print("如需停止脚本，请使用 Ctrl+C 或将鼠标快速移动到屏幕角落。")

    pyautogui.FAILSAFE = True

    # --- 点击计数器 ---
    # 0: 还没点过
    # TARGET-1: 准备进行最后一次操作（退出）
    current_click_count = 0

    try:
        while True:
            # --- 任务 1: 检测“下一波”按钮 ---
            try:
                wave_box = pyautogui.locateOnScreen(
                    img_next_wave, confidence=confidence_level, grayscale=True
                )
                if wave_box:
                    print(f"发现【下一波】按钮... (当前计数: {current_click_count})")

                    # 逻辑：如果已经点击的次数达到了 (目标波次 - 1)，说明这一波打完就是目标波次了
                    # 例如目标是6波，点击5次下一波后，第6次遇到按钮（或结束界面）就该退出了
                    if current_click_count >= (TARGET_WAVE_COUNT - 1):
                        print(
                            f"  -> [决策] 已达第 {TARGET_WAVE_COUNT} 次操作，寻找【退出】按钮..."
                        )

                        # 寻找退出按钮
                        exit_box = pyautogui.locateOnScreen(
                            img_exit_button, confidence=confidence_level, grayscale=True
                        )
                        if exit_box:
                            print("  -> 发现【退出】按钮，点击！")
                            random_click(exit_box)

                            # 点击退出后，重置计数器
                            current_click_count = 0
                            print("  -> 计数器已重置 (0)，等待返回主界面...")

                            time.sleep(0.1)  # 等待返回大厅
                        else:
                            print(
                                "  -> 警告：计数已满，但未找到退出按钮（可能还未显示），等待中..."
                            )
                            time.sleep(0.1)
                    else:
                        print(
                            f"  -> [决策] 点击【下一波】继续 (第 {current_click_count + 1} 次)"
                        )
                        random_click(wave_box)

                        # 计数 +1
                        current_click_count += 1
                        time.sleep(0.1)

                    continue
            except pyautogui.ImageNotFoundException:
                pass

            # --- 任务 2: 检测“书籍选择界面” (新游戏开始) ---

            # 分支 A: 如果配置了具体的书籍颜色
            if target_book_img:
                try:
                    book_box = pyautogui.locateOnScreen(
                        target_book_img, confidence=confidence_level, grayscale=True
                    )
                    if book_box:
                        print(f"发现【{SELECTED_BOOK_TYPE}书籍】选项")
                        random_click(book_box, offset_y_ratio=0.35)

                        print("  已选择书籍，等待【开始挑战】按钮...")
                        time.sleep(0.1)

                        # 选完书后，寻找开始按钮
                        for i in range(10):
                            try:
                                start_box = pyautogui.locateOnScreen(
                                    img_start_challenge,
                                    confidence=confidence_level,
                                    grayscale=True,
                                )
                                if start_box:
                                    print("  发现【开始挑战】按钮，点击！")
                                    random_click(start_box)
                                    time.sleep(0.1)
                                    break
                            except pyautogui.ImageNotFoundException:
                                time.sleep(0.1)
                        continue
                except pyautogui.ImageNotFoundException:
                    pass

            # 分支 B: 如果配置为 'none' (不使用书籍)，则直接检测“开始挑战”按钮
            else:
                try:
                    start_box = pyautogui.locateOnScreen(
                        img_start_challenge, confidence=confidence_level, grayscale=True
                    )
                    if start_box:
                        print("发现【开始挑战】按钮 (无书籍模式)，点击！")
                        random_click(start_box)
                        time.sleep(0.1)  # 等待进入游戏
                        continue
                except pyautogui.ImageNotFoundException:
                    pass

            # --- 任务 3: 检测“再次进行”按钮 ---
            try:
                retry_box = pyautogui.locateOnScreen(
                    img_retry_button, confidence=confidence_level, grayscale=True
                )
                if retry_box:
                    print("发现【再次进行】按钮，点击！")
                    random_click(retry_box)
                    time.sleep(0.1)
                    continue
            except pyautogui.ImageNotFoundException:
                pass

            time.sleep(loop_interval)

    except KeyboardInterrupt:
        print("\n脚本停止")
    except Exception as e:
        print(f"运行出错: {e}")


if __name__ == "__main__":
    auto_click_next_wave()
