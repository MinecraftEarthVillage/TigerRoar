import os
import sys
import random
import tkinter as tk
from pygame import mixer
from tkinter import messagebox
from pynput import keyboard
import threading

# ========== 路径处理 ==========
def get_base_path():
    """获取程序的基准路径（支持源码和打包后）"""
    if getattr(sys, 'frozen', False):
        # 打包后的EXE
        base_path = os.path.dirname(sys.executable)
    else:
        # 源码运行
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    print(f"DEBUG: 程序路径: {base_path}")  # 调试信息
    return base_path

def get_audio_files():
    """获取所有音频文件路径"""
    base_dir = get_base_path()
    audio_files = []
    
    # 1. 先在当前目录查找
    for file in os.listdir(base_dir):
        if file.lower().endswith(('.mp3', '.wav', '.ogg', '.flac')):
            audio_files.append(os.path.join(base_dir, file))
    
    # 2. 如果当前目录没有，在子目录查找
    if not audio_files:
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                if file.lower().endswith(('.mp3', '.wav', '.ogg', '.flac')):
                    audio_files.append(os.path.join(root, file))
    
    # 3. 如果还是没有，尝试在常见位置查找
    if not audio_files:
        common_dirs = [
            os.path.join(base_dir, "audio"),
            os.path.join(base_dir, "audios"),
            os.path.join(base_dir, "music"),
            os.path.join(base_dir, "sounds"),
        ]
        for dir_path in common_dirs:
            if os.path.exists(dir_path):
                for file in os.listdir(dir_path):
                    if file.lower().endswith(('.mp3', '.wav', '.ogg', '.flac')):
                        audio_files.append(os.path.join(dir_path, file))
    
    return audio_files

# ========== 初始化 ==========
base_dir = get_base_path()
os.chdir(base_dir)

# 初始化pygame mixer
mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
mixer.set_num_channels(32)

# 存储当前正在播放的声音对象
active_sounds = []

# ========== 音频播放函数 ==========
def play_random_audio():
    # 获取所有音频文件
    audio_files = get_audio_files()
    
    if not audio_files:
        message_label.config(text=f"未找到音频文件！\n请将MP3/WAV/OGG/FLAC文件放在:\n{base_dir}")
        return
    
    # 随机选择一个音频文件
    selected_file = random.choice(audio_files)
    file_name = os.path.basename(selected_file)
    
    try:
        # 使用Sound对象加载音频文件
        sound = mixer.Sound(selected_file)
        
        # 找到一个空闲的通道播放音频
        channel = mixer.find_channel()
        if channel:
            channel.play(sound)
            
            # 存储声音对象引用
            active_sounds.append(sound)
            
            # 更新状态
            status_label.config(text=f"正在播放: {file_name}\n活动音频: {len(active_sounds)}\n目录: {base_dir}")
            
            # 播放完成后清理
            def remove_sound():
                if sound in active_sounds:
                    active_sounds.remove(sound)
                    if active_sounds:
                        status_label.config(text=f"活动音频: {len(active_sounds)}")
                    else:
                        status_label.config(text="就绪 - 点击按钮或按Ctrl播放")
            
            root.after(int(sound.get_length() * 1000) + 100, remove_sound)
            
        else:
            status_label.config(text="所有通道都在使用中，请等待...")
            
    except Exception as e:
        status_label.config(text=f"播放失败: {file_name}\n错误: {str(e)}")

# ========== 快捷键处理 ==========
def on_activate():
    root.after(0, play_random_audio)

def setup_global_hotkey():
    try:
        hotkey = keyboard.HotKey(
            keyboard.HotKey.parse('<ctrl>'),
            on_activate
        )
        
        listener = keyboard.Listener(
            on_press=lambda key: hotkey.press(listener.canonical(key)),
            on_release=lambda key: hotkey.release(listener.canonical(key))
        )
        
        listener.start()
        return listener
    except Exception as e:
        print(f"快捷键设置失败: {e}")
        return None

# ========== GUI界面 ==========
root = tk.Tk()
root.title(f"随机音频播放器 - 程序目录: {os.path.basename(base_dir)}")
root.geometry("600x250")

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
status_label = tk.Label(root, text="就绪 - 点击按钮或按Ctrl播放", 
                        font=("Arial", 10), wraplength=550)
status_label.pack(pady=10)

# 消息标签
message_label = tk.Label(root, text="支持格式: MP3, WAV, OGG, FLAC\n音频文件需放在程序同一目录下", 
                         font=("Arial", 9), fg="gray")
message_label.pack(pady=5)

# 快捷键提示
hotkey_label = tk.Label(root, text="全局快捷键: Ctrl (可随时触发重叠播放)", 
                        font=("Arial", 9), fg="darkgreen")
hotkey_label.pack(pady=5)

# ========== 窗口关闭事件 ==========
def on_closing():
    mixer.stop()
    active_sounds.clear()
    if 'listener' in globals() and listener:
        listener.stop()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

# 设置全局快捷键
listener = setup_global_hotkey()

root.mainloop()