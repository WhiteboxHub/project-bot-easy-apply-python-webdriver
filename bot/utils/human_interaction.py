import pyautogui
import random
from time import sleep

def human_jitter():
    """Simulate small human mouse movements."""
    try:
        x, y = pyautogui.position()
        pyautogui.moveTo(x + random.randint(-2, 2), y + random.randint(-2, 2), duration=0.1)
    except:
        pass

def human_type(element, text: str, delay_range=(0.05, 0.2)):
    """Type text like a human."""
    for char in text:
        element.send_keys(char)
        sleep(random.uniform(*delay_range))
