from time import sleep

def scroll_to_bottom(driver, container_selector, pause_time=1):
    """Scroll down a container until the end or limit reached."""
    last_height = driver.execute_script(f"return document.querySelector('{container_selector}').scrollHeight")
    while True:
        driver.execute_script(f"document.querySelector('{container_selector}').scrollTo(0, document.querySelector('{container_selector}').scrollHeight)")
        sleep(pause_time)
        new_height = driver.execute_script(f"return document.querySelector('{container_selector}').scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def smooth_scroll(driver, element):
    """Scroll an element into view smoothly."""
    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
