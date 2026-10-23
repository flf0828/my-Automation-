import cv2
import numpy as np
import mss
import time
import pydirectinput
import threading
from ultralytics import YOLO

# ================= 1. 初始化 YOLO 模型 =================
print("🔄 正在加载 YOLO 模型，请稍候...")
model = YOLO("best.pt")
print("✅ 模型加载成功！")

# ================= 全局共享变量 =================
has_monster = False       
ignore_yolo_until = 0     
keep_running = True       

# ================= 2. YOLO 专属独立线程 =================
def yolo_radar_thread():
    global has_monster, ignore_yolo_until, keep_running
    print("📡 [后台线程] YOLO 雷达已启动！")
    
    while keep_running:
        if time.time() < ignore_yolo_until:
            time.sleep(0.1)
            continue
            
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                screenshot = sct.grab(monitor)
                screen_img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_BGRA2RGB)
                
                results = model(screen_img, device='cpu', verbose=False)[0]
                
                found = False
                for box in results.boxes:
                    conf = float(box.conf[0])
                    if conf > 0.3: 
                        cls_id = int(box.cls[0])
                        if cls_id in [0, 3]: 
                            found = True
                            break
                
                has_monster = found
        except Exception as e:
            print(f"YOLO 线程异常: {e}")
            
        time.sleep(0.05) 

threading.Thread(target=yolo_radar_thread, daemon=True).start()

# ================= 3. 基础工具函数 =================
def find_image_on_screen(template_path, threshold=0.7):
    template = cv2.imread(template_path)
    if template is None: return None
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)
        screen_img = np.array(screenshot)
        screen_img = cv2.cvtColor(screen_img, cv2.COLOR_BGRA2BGR)
    result = cv2.matchTemplate(screen_img, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    if max_val >= threshold:
        h, w = template.shape[:2]
        return (max_loc[0] + w // 2, max_loc[1] + h // 2)
    return None

mp_locked_rect = None 
def lock_mp_location(template_path="mp_bar.png"):
    global mp_locked_rect
    template = cv2.imread(template_path)
    if template is None: return False
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)
        screen_img = np.array(screenshot)
        screen_img = cv2.cvtColor(screen_img, cv2.COLOR_BGRA2BGR)
    result = cv2.matchTemplate(screen_img, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    if max_val >= 0.7:
        x, y = max_loc
        h, w = template.shape[:2]
        mp_locked_rect = {"top": y, "left": x, "width": w, "height": h}
        return True
    return False

def check_mp_percentage():
    global mp_locked_rect
    if mp_locked_rect is None: return 100
    with mss.mss() as sct:
        screenshot = sct.grab(mp_locked_rect)
        img = np.array(screenshot)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, np.array([90, 50, 50]), np.array([140, 255, 255]))
        col_counts = np.sum(mask > 0, axis=0)
        h = mp_locked_rect["height"]
        w = mp_locked_rect["width"]
        valid_cols = np.where(col_counts > (h * 0.5))[0]
        if len(valid_cols) > 0:
            return (valid_cols[-1] / w) * 100
    return 100

def is_mp_gone():
    global mp_locked_rect
    if mp_locked_rect is None: return True 
    with mss.mss() as sct:
        screenshot = sct.grab(mp_locked_rect)
        img = np.array(screenshot)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, np.array([90, 50, 50]), np.array([140, 255, 255]))
        return cv2.countNonZero(mask) < 10

def is_screen_black(threshold=30):
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        region = {"top": monitor["height"]//2 - 100, "left": monitor["width"]//2 - 100, "width": 200, "height": 200}
        img = np.array(sct.grab(region))
        return np.mean(cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)) < threshold

def click_at(pos):
    if not pos: return
    x, y = pos
    pydirectinput.moveTo(x, y)
    time.sleep(0.1)
    pydirectinput.mouseDown(button='left')
    time.sleep(0.05)
    pydirectinput.mouseUp(button='left')

def use_fabao():
    print("  🛑 释放法宝并开启 P 保护...")
    pydirectinput.keyUp('a'); pydirectinput.keyUp('d'); time.sleep(0.15) 
    pydirectinput.press('h'); time.sleep(0.1); pydirectinput.press('h')
    pydirectinput.press('p'); time.sleep(0.8) 

def exit_dungeon():
    print("🚪 通关！按 M 键打开设置...")
    pydirectinput.keyUp('a'); pydirectinput.keyUp('d'); time.sleep(0.5)
    pydirectinput.press('m'); time.sleep(1.5) 
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        click_at((int(monitor["width"] * 0.5), int(monitor["height"] * 0.35)))
    time.sleep(2)

def handle_death():
    print("💀 确认死亡！紧急刹车！")
    pydirectinput.keyUp('d'); pydirectinput.keyUp('a'); pydirectinput.keyUp('l'); pydirectinput.keyUp('j')
    time.sleep(1.0) 
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        click_at((int(monitor["width"] * 0.535), int(monitor["height"] * 0.54)))
    time.sleep(2.5) 
    print("  ✅ 已返回大地图，准备重新开始。")

# ================= 4. 主控逻辑 =================
print("请在 1 秒内切换到游戏...")
time.sleep(1)

current_state = "MAP"
pydirectinput.keyUp('d'); pydirectinput.keyUp('a')

last_mp_check = 0
mp_cd_time = 0
black_count = 0 

last_wushuang_time = 0     
no_monster_start_time = 0  
was_seeing_monster = False 
map_search_start_time = 0  # 新增：记录找图开始时间

try:
    while True:
        if current_state == "MAP":
            if map_search_start_time == 0:
                map_search_start_time = time.time()
                
            print("[状态] 寻找金蟾宝宫...")
            pos = find_image_on_screen("jinchang.png", threshold=0.7)
            if pos:
                print("找到副本，点击进入！")
                click_at(pos)
                print("等待进图加载（4.5秒）...")
                time.sleep(4.5)
                pydirectinput.press('o')
                time.sleep(0.3) 
                lock_mp_location()
                black_count = 0 
                
                last_wushuang_time = time.time()
                no_monster_start_time = time.time()
                was_seeing_monster = False
                map_search_start_time = 0 # 重置找图计时
                
                current_state = "RUN_AND_SMASH"
            else:
                # 👇 新增：找图超时保险机制
                if time.time() - map_search_start_time > 2.5:
                    print("⚠️ 2.5秒未找到关卡，可能卡加载，进入自检移动状态...")
                    map_search_start_time = 0
                    current_state = "CHECK_LOADING"
                else:
                    time.sleep(0.2)

        # 👇 新增：状态自检（防卡关/误判）
        elif current_state == "CHECK_LOADING":
            print("[状态] 自检中：向右移动3秒，探测是否有怪...")
            check_start = time.time()
            
            while time.time() - check_start < 3.0:
                pydirectinput.keyDown('d')
                pydirectinput.press('u')
                
                # 如果 YOLO 扫描到了怪物，说明绝对在关卡内！
                if has_monster:
                    pydirectinput.keyUp('d')
                    print("✅ 确认在关卡内！补按一次 O，切换为战斗状态！")
                    pydirectinput.press('o')
                    
                    # 重置战斗相关变量
                    last_wushuang_time = time.time()
                    no_monster_start_time = time.time()
                    was_seeing_monster = True 
                    
                    current_state = "RUN_AND_SMASH"
                    break
                    
                time.sleep(0.05)
                
            if current_state == "CHECK_LOADING":
                # 3秒了都没看到怪，说明真的没进图，回地图去
                pydirectinput.keyUp('d')
                print("❌ 3秒未探测到怪物，退回大地图寻找。")
                current_state = "MAP"

        elif current_state == "RUN_AND_SMASH":
            current_time = time.time()

            # ===== 1. 老代码：黑屏/蓝条检测 =====
            if is_screen_black() or is_mp_gone():
                pydirectinput.keyUp('d')
                current_state = "SCAN_MODE"
                continue

            # ===== 2. 无双机制 =====
            if current_time - last_wushuang_time > 15.0:
                print("🌟 释放无双！按空格")
                pydirectinput.press('space')
                last_wushuang_time = current_time

            # ===== 3. YOLO 战斗逻辑 =====
            if current_time < ignore_yolo_until:
                pydirectinput.keyDown('d')
                pydirectinput.press('u')
                print("💨 攻击冷却中，D+U 极速狂奔...")
            else:
                if not has_monster:
                    pydirectinput.keyDown('d')
                    pydirectinput.press('u')
                    print("🏃‍♂️ 视野无怪，D+U 极速狂奔中...")
                    
                    # 3秒盲打判断
                    if was_seeing_monster:
                        no_monster_start_time = current_time
                        was_seeing_monster = False
                    elif current_time - no_monster_start_time > 3.0:
                        print("👻 超过3秒无怪且未转场，疑似遮挡/隐身，尝试原地盲打 L！")
                        pydirectinput.keyUp('d')
                        pydirectinput.press('l')
                        pydirectinput.press('l')
                        no_monster_start_time = current_time 
                        
                else:
                    was_seeing_monster = True
                    pydirectinput.keyUp('d')
                    print("💥 YOLO 发现怪物！急刹车，转身连按 4 次 L！")
                    
                    # 👇 恢复为按两次 A 防止延迟吞键
                    pydirectinput.press('a')
                    pydirectinput.press('a')
                    
                    pydirectinput.press('l')
                    pydirectinput.press('l')
                    pydirectinput.press('l')
                    pydirectinput.press('l')
                    
                    ignore_yolo_until = time.time() + 2.0
                    print("🛡️ 攻击完毕，屏蔽 YOLO 2 秒，强制跑图！")

            # ===== 4. 蓝量管理 =====
            if current_time > last_mp_check and current_time > mp_cd_time:
                mp = check_mp_percentage()
                if mp < 40: 
                    use_fabao() 
                    pydirectinput.keyDown('d') 
                    mp_cd_time = time.time() + 8 
                last_mp_check = time.time() + 1 

            time.sleep(0.01)

        elif current_state == "SCAN_MODE":
            print("🌑 发现疑似黑屏/UI消失，开启雷达扫描（0.3秒/次）...")
            missing_count = 0
            is_transition = False
            
            for i in range(3):
                time.sleep(0.3)
                if not is_mp_gone():
                    print("  🔆 蓝条恢复，判定为转场！")
                    is_transition = True
                    break
                else:
                    missing_count += 1
                    print(f"  🌑 第 {missing_count} 次未检测到蓝条...")
            
            if is_transition:
                black_count += 1
                print(f"  ✅ 转场成功，通关黑屏次数 +1 (当前 {black_count})")
                if black_count >= 4:
                    print("🏁 第 4 次黑屏结束，准备通关退出！")
                    current_state = "EXIT"
                else:
                    no_monster_start_time = time.time()
                    current_state = "RUN_AND_SMASH"
            else:
                current_state = "DEAD"

        elif current_state == "DEAD":
            handle_death()
            black_count = 0 
            current_state = "MAP"

        elif current_state == "EXIT":
            exit_dungeon()
            current_state = "MAP"

except KeyboardInterrupt:
    print("\n[停止] 用户终止脚本。")
finally:
    keep_running = False 
    pydirectinput.keyUp('d')
    pydirectinput.keyUp('a')
    pydirectinput.keyUp('u')
    pydirectinput.keyUp('l')
    pydirectinput.keyUp('j')