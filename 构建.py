import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_and_install_dependencies():
    """检查并安装所有必需的依赖"""
    required_packages = [
        'pygame',
        'pynput',
        'pyinstaller'
    ]
    
    print("正在检查并安装依赖包...")
    for package in required_packages:
        try:
            __import__(package.split('.')[0])
            print(f"✓ {package} 已安装")
        except ImportError:
            print(f"正在安装 {package}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])

def convert_jpg_to_ico(jpg_path, ico_path):
    """将JPG图片转换为ICO格式"""
    try:
        from PIL import Image
        img = Image.open(jpg_path)
        img.save(ico_path, format='ICO', sizes=[(32, 32), (64, 64), (128, 128)])
        return True
    except ImportError:
        print("请安装PIL库: pip install pillow")
        return False
    except Exception as e:
        print(f"图标转换失败: {e}")
        return False

def get_icon_path():
    """获取图标文件路径，自动转换格式"""
    # 优先使用ICO文件
    ico_files = list(Path('.').glob('*.ico'))
    if ico_files:
        return str(ico_files[0])
    
    # 如果没有ICO，尝试转换JPG
    jpg_files = list(Path('.').glob('*.png'))
    if jpg_files:
        jpg_file = jpg_files[0]
        ico_file = Path(jpg_file.stem + '.ico')
        
        if convert_jpg_to_ico(jpg_file, ico_file):
            return str(ico_file)
    
    return 'NONE'

def build_exe():
    """构建EXE文件"""
    print("开始构建EXE文件...")
    
    # 获取图标路径
    icon_path = get_icon_path()
    icon_arg = f'--icon={icon_path}' if icon_path != 'NONE' else '--icon=NONE'
    
    # PyInstaller配置
    pyinstaller_args = [
        'pyinstaller',
        '--onefile',           # 单文件
        '--windowed',          # 无控制台窗口
        '--name=随机音频播放器', # EXE名称
        icon_arg,              # 图标参数（修改这里）
        '--add-data=虎啸.pyw;.', # 包含脚本
        '--hidden-import=pygame',
        '--hidden-import=pygame.mixer',
        '--hidden-import=pynput',
        '--hidden-import=pynput.keyboard',
        '--hidden-import=tkinter',
        '虎啸.pyw'
    ]
    
    
    try:
        subprocess.check_call(pyinstaller_args)
        print("✓ EXE构建完成！")
    except subprocess.CalledProcessError as e:
        print(f"✗ 构建失败: {e}")
        return False
    
    return True

def cleanup_and_move():
    """清理临时文件并移动EXE"""
    print("正在清理和移动文件...")
    
    # 源EXE路径
    source_exe = Path('dist') / '随机音频播放器.exe'
    
    if source_exe.exists():
        # 移动到当前目录
        target_exe = Path('随机音频播放器.exe')
        shutil.move(str(source_exe), str(target_exe))
        
        # 清理构建文件
        if Path('build').exists():
            shutil.rmtree('build')
        if Path('dist').exists():
            shutil.rmtree('dist')
        if Path('随机音频播放器.spec').exists():
            os.remove('随机音频播放器.spec')
        
        print(f"✓ EXE已创建: {target_exe}")
        return True
    else:
        print("✗ EXE文件未找到")
        return False

def main():
    print("=" * 50)
    print("随机音频播放器 - EXE打包工具")
    print("=" * 50)
    
    # 检查当前目录是否有脚本文件
    if not Path('虎啸.pyw').exists():
        print("错误: 请在包含'虎啸.pyw'的目录中运行此脚本")
        input("按回车键退出...")
        return
    
    # 安装依赖
    check_and_install_dependencies()
    
    # 构建EXE
    if build_exe():
        # 移动和清理
        if cleanup_and_move():
            print("\n" + "=" * 50)
            print("打包完成！")
            print("使用说明:")
            print("1. 将 '随机音频播放器.exe' 复制到任何包含音频文件的目录")
            print("2. 双击运行即可播放该目录下的音频")
            print("3. 支持格式: MP3, WAV, OGG, FLAC")
            print("4. 快捷键: Ctrl键全局触发播放")
            print("=" * 50)
        else:
            print("✗ 文件移动失败")
    else:
        print("✗ 打包过程失败")
    
    input("\n按回车键退出...")

if __name__ == '__main__':
    main()