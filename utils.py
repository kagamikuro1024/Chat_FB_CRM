import asyncio
import logging
import os
import random
import time
import win32process
import win32con
import win32gui
import win32api
import ctypes
import os
from win32com.shell import shell, shellcon  # type: ignore
import sys
from colorlog import ColoredFormatter


async def type_text_input(element, text):
    """
    Gõ từng ký tự một vào element với thời gian trễ ngẫu nhiên,
    giúp mô phỏng hành vi nhập liệu của con người.
    """
    # khi ấn vào ô input thì sleep lại 1 tí
    await asyncio.sleep(random.uniform(0.5, 0.8))
    for char in text:
        element.send_keys(char)  # Gõ từng ký tự
        await asyncio.sleep(random.uniform(0.1, 0.4))  # Dừng ngẫu nhiên giữa các lần gõ

async def smooth_scroll(browser, start, end, duration=2):
    """
    Cuộn từ từ thay vì giật cục, giúp cuộn mượt mà hơn.
    - start: Vị trí bắt đầu
    - end: Vị trí kết thúc
    - duration: Thời gian cuộn (giây)
    """
    step = (end - start) / (duration * 30)  # 30 fps
    current = start

    for _ in range(int(duration * 30)):
        current += step
        browser.execute_script(f"window.scrollTo(0, {current});")
        await asyncio.sleep(0.05)  # Giữ khoảng thời gian giữa các bước



# Tạo thư mục log nếu chưa có
log_dir = "assets/logs"
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, "toolfacebook.log")

def log_message(message, level=logging.INFO):
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    if level == logging.DEBUG:
        logging.info(message)
    elif level == logging.WARNING:
        logging.warning(message)
    elif level == logging.ERROR:
        logging.error(message) # Vẫn in log ra terminal để debug dễ hơn

async def hide_process():
    # Hide window and process
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    if hwnd != 0:
        ctypes.windll.user32.ShowWindow(hwnd, 0)
        # Set process as background system process
        ctypes.windll.kernel32.SetPriorityClass(
            win32api.GetCurrentProcess(),
            win32process.BELOW_NORMAL_PRIORITY_CLASS | 
            win32process.CREATE_NO_WINDOW
        )

async def run_as_trusted():
    try:
        # Run with elevated privileges
        executable = sys.argv[0]
        params = " ".join(sys.argv[1:])
        shell.ShellExecuteEx(
            lpVerb='runas', 
            lpFile=executable,
            lpParameters=params,
            nShow=win32con.SW_HIDE
        )
    except Exception:
        pass
    
async def initialize():
    """Initialize process settings"""
    await hide_process()  # Tắt chế độ ẩn process để hiển thị cửa sổ
    await run_as_trusted()
    pass


formatter = ColoredFormatter(
    "%(log_color)s%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'bold_red',
    }
)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logging.basicConfig(level=logging.INFO, handlers=[handler])

def log_message(message, level=logging.INFO):
    """Log messages in a standardized format with colors."""
    logging.log(level, message)