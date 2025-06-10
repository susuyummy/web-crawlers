import os
import sys
import subprocess

def build_exe():
    # 安裝必要的套件
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # 構建可執行文件
    subprocess.check_call([
        "pyinstaller",
        "--onefile",
        "--name", "ptt-crawler",
        "ptt_crawler_cli.py"
    ])
    
    print("\n構建完成！")
    print("可執行文件位於 dist/ptt-crawler.exe")

if __name__ == "__main__":
    build_exe() 