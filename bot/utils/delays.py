from time import sleep
from random import randint

def buffer(speed: int=0) -> None:
    '''
    Function to wait within a period of selected random range.
    * Will not wait if input `speed <= 0`
    * Will wait within a random range of 
      - `0.6 to 1.0 secs` if `1 <= speed < 2`
      - `1.0 to 1.8 secs` if `2 <= speed < 3`
      - `1.8 to speed secs` if `3 <= speed`
    '''
    if speed<=0:
        return
    elif speed >= 1 and speed < 2:
        return sleep(randint(6,10)*0.1)
    elif speed >= 2 and speed < 3:
        return sleep(randint(10,18)*0.1)
    else:
        return sleep(randint(18,max(19, round(speed)*10))*0.1)
