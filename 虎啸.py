import os
import sys
import random
import json
import tkinter as tk
from pygame import mixer
from tkinter import messagebox, ttk
from pynput import keyboard
import threading
from tkinter import simpledialog

# ========== 配置管理 ==========
CONFIG_FILE = "config.json"
DEFAULT_HOTKEY = "<ctrl>+<alt>"

def load_config():
    """加载配置文件"""
    config_path = os.path.join(get_base_path(), CONFIG_FILE)
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"hotkey": DEFAULT_HOTKEY, "hotkey_display": DEFAULT_HOTKEY}
    return {"hotkey": DEFAULT_HOTKEY, "hotkey_display": DEFAULT_HOTKEY}

def save_config(config):
    """保存配置文件"""
    config_path = os.path.join(get_base_path(), CONFIG_FILE)
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

# ========== 路径处理 ==========
def get_base_path():
    """获取程序的基准路径（支持源码和打包后）"""
    if getattr(sys, 'frozen', False):
        # 打包后的EXE
        base_path = os.path.dirname(sys.executable)
    else:
        # 源码运行
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    print(f"DEBUG: 程序路径: {base_path}")
    return base_path

def get_audio_files():
    """获取所有音频文件路径"""
    base_dir = get_base_path()
    audio_files = []
    
    for file in os.listdir(base_dir):
        if file.lower().endswith(('.mp3', '.wav', '.ogg', '.flac')):
            audio_files.append(os.path.join(base_dir, file))
    
    if not audio_files:
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                if file.lower().endswith(('.mp3', '.wav', '.ogg', '.flac')):
                    audio_files.append(os.path.join(root, file))
    
    return audio_files

# ========== 初始化 ==========
base_dir = get_base_path()
os.chdir(base_dir)

# 加载配置
config = load_config()
current_hotkey = config.get("hotkey", DEFAULT_HOTKEY)
current_hotkey_display = config.get("hotkey_display", DEFAULT_HOTKEY)

# 初始化pygame mixer
mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
mixer.set_num_channels(32)

# 存储当前正在播放的声音对象
active_sounds = []

# 全局变量
listener = None
key_recording = False
recorded_keys = []

# ========== 音频播放函数 ==========
def play_random_audio():
    audio_files = get_audio_files()
    
    if not audio_files:
        message_label.config(text=f"未找到音频文件！\n请将MP3/WAV/OGG/FLAC文件放在:\n{base_dir}")
        return
    
    selected_file = random.choice(audio_files)
    file_name = os.path.basename(selected_file)
    
    try:
        sound = mixer.Sound(selected_file)
        channel = mixer.find_channel()
        if channel:
            channel.play(sound)
            active_sounds.append(sound)
            
            status_label.config(text=f"正在播放: {file_name}\n活动音频: {len(active_sounds)}")
            
            def remove_sound():
                if sound in active_sounds:
                    active_sounds.remove(sound)
                    if active_sounds:
                        status_label.config(text=f"活动音频: {len(active_sounds)}")
                    else:
                        status_label.config(text=f"就绪 - 点击按钮或按{current_hotkey_display}播放")
            
            root.after(int(sound.get_length() * 1000) + 100, remove_sound)
        else:
            status_label.config(text="所有通道都在使用中，请等待...")
            
    except Exception as e:
        status_label.config(text=f"播放失败: {file_name}\n错误: {str(e)}")

# ========== 快捷键处理 ==========
def on_activate():
    root.after(0, play_random_audio)

def stop_global_hotkey():
    """停止当前的全局快捷键监听"""
    global listener
    if listener:
        listener.stop()
        listener = None

def setup_global_hotkey(hotkey_str=None):
    """设置全局快捷键"""
    global listener, current_hotkey, current_hotkey_display
    
    if hotkey_str is None:
        hotkey_str = current_hotkey
    
    # 停止现有的监听器
    stop_global_hotkey()
    
    try:
        # 验证热键格式
        hotkey = keyboard.HotKey(
            keyboard.HotKey.parse(hotkey_str),
            on_activate
        )
        
        listener = keyboard.Listener(
            on_press=lambda key: hotkey.press(listener.canonical(key)),
            on_release=lambda key: hotkey.release(listener.canonical(key))
        )
        
        listener.start()
        
        # 更新显示
        hotkey_label.config(text=f"全局快捷键: {current_hotkey_display}")
        status_label.config(text=f"就绪 - 点击按钮或按{current_hotkey_display}播放")
        
        print(f"快捷键设置成功: {hotkey_str}")
        return listener
    except Exception as e:
        print(f"快捷键设置失败: {e}")
        # 如果设置失败，使用默认热键
        try:
            default_hotkey = keyboard.HotKey(
                keyboard.HotKey.parse(DEFAULT_HOTKEY),
                on_activate
            )
            
            listener = keyboard.Listener(
                on_press=lambda key: default_hotkey.press(listener.canonical(key)),
                on_release=lambda key: default_hotkey.release(listener.canonical(key))
            )
            
            listener.start()
            
            # 恢复默认设置
            current_hotkey = DEFAULT_HOTKEY
            current_hotkey_display = DEFAULT_HOTKEY
            config["hotkey"] = DEFAULT_HOTKEY
            config["hotkey_display"] = DEFAULT_HOTKEY
            save_config(config)
            
            hotkey_label.config(text=f"全局快捷键: {DEFAULT_HOTKEY}")
            status_label.config(text="就绪 - 点击按钮或按{DEFAULT_HOTKEY}播放")
            
            print(f"已恢复默认快捷键: {DEFAULT_HOTKEY}")
            return listener
        except Exception as e2:
            print(f"默认快捷键也设置失败: {e2}")
            messagebox.showerror("错误", f"快捷键设置失败！\n错误: {e}\n请使用默认快捷键{DEFAULT_HOTKEY}")
            return None

# ========== 设置界面 ==========
def open_settings():
    """打开设置窗口"""
    settings_window = tk.Toplevel(root)
    settings_window.title("快捷键设置")
    settings_window.geometry("450x300")
    settings_window.resizable(False, False)
    settings_window.transient(root)
    settings_window.grab_set()
    
    # 中心化窗口
    settings_window.update_idletasks()
    x = root.winfo_x() + (root.winfo_width() - settings_window.winfo_width()) // 2
    y = root.winfo_y() + (root.winfo_height() - settings_window.winfo_height()) // 2
    settings_window.geometry(f"+{x}+{y}")
    
    # 当前设置显示
    current_label = tk.Label(settings_window, text="当前快捷键:", font=("Arial", 10))
    current_label.pack(pady=(10, 5))
    
    current_hotkey_label = tk.Label(settings_window, 
                                    text=current_hotkey_display, 
                                    font=("Arial", 12, "bold"),
                                    fg="blue")
    current_hotkey_label.pack(pady=(0, 15))
    
    # 按键记录区域
    record_frame = tk.Frame(settings_window)
    record_frame.pack(pady=10)
    
    record_label = tk.Label(record_frame, text="按下新的快捷键组合:", font=("Arial", 10))
    record_label.pack()
    
    key_display = tk.Label(record_frame, text="请按下一个组合键...", 
                          font=("Arial", 10), 
                          bg="#f0f0f0", 
                          width=40, height=3,
                          relief="solid",
                          borderwidth=1,
                          wraplength=350)
    key_display.pack(pady=10)
    
    # 状态变量
    recording = False
    key_combination = []
    key_listener = None
    
    def on_key_press(key):
        """按键按下事件"""
        nonlocal recording, key_combination
        
        if not recording:
            return
        
        try:
            # 获取按键名称
            key_name = None
            if hasattr(key, 'char') and key.char:
                # 字母数字键
                key_name = key.char
            elif hasattr(key, 'name'):
                # 特殊键
                key_name = key.name
            
            if key_name:
                # 添加到组合键
                if key_name not in key_combination:
                    key_combination.append(key_name)
                
                # 更新显示
                display_text = ""
                for k in key_combination:
                    if k in ['ctrl', 'ctrl_l', 'ctrl_r']:
                        display_text += "Ctrl + "
                    elif k in ['alt', 'alt_l', 'alt_r']:
                        display_text += "Alt + "
                    elif k in ['shift', 'shift_l', 'shift_r']:
                        display_text += "Shift + "
                    elif k in ['cmd', 'super', 'win']:
                        display_text += "Win + "
                    elif len(k) == 1 and k.isprintable():
                        display_text += k.upper() + " + "
                    else:
                        display_text += k.capitalize() + " + "
                
                if display_text.endswith(" + "):
                    display_text = display_text[:-3]
                
                key_display.config(text=display_text, fg="blue")
                
        except Exception as e:
            print(f"按键处理错误: {e}")
    
    def on_key_release(key):
        """按键释放事件"""
        nonlocal recording, key_combination
        
        if not recording:
            return
        
        # 检查是否所有键都已释放
        if not key_combination:
            stop_recording()
    
    def start_recording():
        """开始录制快捷键"""
        nonlocal recording, key_combination, key_listener
        
        recording = True
        key_combination = []
        key_display.config(text="请按下组合键...", fg="red")
        start_button.config(state="disabled")
        stop_button.config(state="normal")
        apply_button.config(state="disabled")
        
        # 启动键盘监听
        key_listener = keyboard.Listener(
            on_press=on_key_press,
            on_release=on_key_release)
        key_listener.start()
    
    def stop_recording():
        """停止录制快捷键"""
        nonlocal recording, key_listener
        
        recording = False
        key_display.config(fg="black")
        start_button.config(state="normal")
        stop_button.config(state="disabled")
        apply_button.config(state="normal")
        
        # 停止键盘监听
        if key_listener:
            key_listener.stop()
    
    def apply_hotkey():
        """应用新的快捷键"""
        nonlocal key_combination
        
        if not key_combination:
            messagebox.showwarning("警告", "请先录制快捷键！")
            return
        
        # 检查是否包含修饰键
        has_modifier = False
        for key in key_combination:
            if key in ['ctrl', 'ctrl_l', 'ctrl_r', 'alt', 'alt_l', 'alt_r', 
                      'shift', 'shift_l', 'shift_r', 'cmd', 'super', 'win']:
                has_modifier = True
                break
        
        # if not has_modifier:
            # messagebox.showwarning("警告", "快捷键必须包含至少一个修饰键（Ctrl, Alt, Shift, Win）！")
            # return
        
        # 构建热键字符串和显示字符串
        hotkey_parts = []
        display_parts = []
        
        for key in key_combination:
            # 构建pynput格式的热键部分
            if key in ['ctrl', 'ctrl_l', 'ctrl_r']:
                hotkey_parts.append('<ctrl>')
                display_parts.append('Ctrl')
            elif key in ['alt', 'alt_l', 'alt_r']:
                hotkey_parts.append('<alt>')
                display_parts.append('Alt')
            elif key in ['shift', 'shift_l', 'shift_r']:
                hotkey_parts.append('<shift>')
                display_parts.append('Shift')
            elif key in ['cmd', 'super', 'win']:
                hotkey_parts.append('<cmd>')
                display_parts.append('Win')
            elif len(key) == 1 and key.isprintable():
                hotkey_parts.append(key)
                display_parts.append(key.upper())
            else:
                # 其他特殊键，尝试添加尖括号
                hotkey_parts.append(f'<{key}>')
                display_parts.append(key.capitalize())
        
        # 移除重复的修饰键
        seen_modifiers = set()
        unique_hotkey_parts = []
        unique_display_parts = []
        
        for h_part, d_part in zip(hotkey_parts, display_parts):
            if h_part in ['<ctrl>', '<alt>', '<shift>', '<cmd>']:
                if h_part not in seen_modifiers:
                    seen_modifiers.add(h_part)
                    unique_hotkey_parts.append(h_part)
                    unique_display_parts.append(d_part)
            else:
                unique_hotkey_parts.append(h_part)
                unique_display_parts.append(d_part)
        
        # 构建最终的字符串
        hotkey_str = "+".join(unique_hotkey_parts)
        display_str = " + ".join(unique_display_parts)
        
        print(f"尝试设置快捷键: {hotkey_str}")
        
        # 更新配置
        global current_hotkey, current_hotkey_display
        current_hotkey = hotkey_str
        current_hotkey_display = display_str
        
        config["hotkey"] = hotkey_str
        config["hotkey_display"] = display_str
        
        # 保存配置
        if save_config(config):
            # 重新设置全局快捷键
            setup_global_hotkey(hotkey_str)
            
            # 更新显示
            current_hotkey_label.config(text=display_str)
            
            messagebox.showinfo("成功", f"快捷键已设置为: {display_str}")
        else:
            messagebox.showerror("错误", "保存配置失败！")
    
    def reset_to_default():
        """重置为默认快捷键"""
        global current_hotkey, current_hotkey_display
        current_hotkey = DEFAULT_HOTKEY
        current_hotkey_display = DEFAULT_HOTKEY
        
        config["hotkey"] = DEFAULT_HOTKEY
        config["hotkey_display"] = DEFAULT_HOTKEY
        
        if save_config(config):
            setup_global_hotkey(DEFAULT_HOTKEY)
            current_hotkey_label.config(text=DEFAULT_HOTKEY)
            key_display.config(text="请按下一个组合键...")
            messagebox.showinfo("成功", f"已重置为默认快捷键：{DEFAULT_HOTKEY}")
        else:
            messagebox.showerror("错误", "保存配置失败！")
    
    # 按钮框架
    button_frame = tk.Frame(settings_window)
    button_frame.pack(pady=20)
    
    start_button = tk.Button(button_frame, text="开始录制", 
                            command=start_recording, width=12)
    start_button.grid(row=0, column=0, padx=5)
    
    stop_button = tk.Button(button_frame, text="停止录制", 
                           command=stop_recording, width=12, state="disabled")
    stop_button.grid(row=0, column=1, padx=5)
    
    apply_button = tk.Button(button_frame, text="应用", 
                            command=apply_hotkey, width=12, state="disabled")
    apply_button.grid(row=0, column=2, padx=5)
    
    # 重置按钮
    reset_button = tk.Button(settings_window, text="重置为默认", 
                            command=reset_to_default, width=15)
    reset_button.pack(pady=10)
    
    # 提示文本
    tip_label = tk.Label(settings_window, 
                        text="提示: 快捷键必须包含至少一个修饰键（Ctrl, Alt, Shift, Win）\n例如: Ctrl+Shift+A, Alt+Space, Win+R",
                        font=("Arial", 8), fg="gray", justify="left")
    tip_label.pack(pady=10)
    
    # 窗口关闭时的清理
    def on_settings_close():
        stop_recording()
        settings_window.destroy()
    
    settings_window.protocol("WM_DELETE_WINDOW", on_settings_close)

# ========== GUI界面 ==========
root = tk.Tk()
root.title(f"随机音频播放器 - 程序目录: {os.path.basename(base_dir)}")
root.geometry("600x300")

# 菜单栏
menubar = tk.Menu(root)
root.config(menu=menubar)

settings_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="设置", menu=settings_menu)
settings_menu.add_command(label="快捷键设置", command=open_settings)

# 显示当前目录
dir_label = tk.Label(root, text=f"程序目录: {base_dir}", 
                     font=("Arial", 9), fg="blue", wraplength=550)
dir_label.pack(pady=5)

# 播放按钮
play_button = tk.Button(root, text="随机播放 (可重叠)", command=play_random_audio, 
                        font=("Arial", 14), bg="#4CAF50", fg="white",
                        padx=20, pady=10)
play_button.pack(pady=10)

# 状态标签
status_label = tk.Label(root, text=f"就绪 - 点击按钮或按{current_hotkey_display}播放", 
                        font=("Arial", 10), wraplength=550)
status_label.pack(pady=10)

# 消息标签
message_label = tk.Label(root, text="支持格式: MP3, WAV, OGG, FLAC\n音频文件需放在程序同一目录下", 
                         font=("Arial", 9), fg="gray")
message_label.pack(pady=5)

# 快捷键提示
hotkey_label = tk.Label(root, text=f"全局快捷键: {current_hotkey_display}", 
                        font=("Arial", 9), fg="darkgreen")
hotkey_label.pack(pady=5)

# 设置按钮
settings_button = tk.Button(root, text="快捷键设置", 
                           command=open_settings, width=15)
settings_button.pack(pady=5)

# ========== 窗口关闭事件 ==========
def on_closing():
    mixer.stop()
    active_sounds.clear()
    stop_global_hotkey()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

# 设置全局快捷键
listener = setup_global_hotkey()

root.mainloop()