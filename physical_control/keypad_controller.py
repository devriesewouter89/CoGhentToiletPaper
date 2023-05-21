import sys
import signal
from enum import Enum

import RPi.GPIO as GPIO
from rgb1602 import rgb1602
import time


class Mode(Enum):
    SETUP = 0
    ROLL = 1
    TEST = 2


class KeypadController:
    def __init__(self):
        self.lcd = rgb1602.RGB1602(16, 2)
        GPIO.setmode(GPIO.BCM)
        # Define keys
        self.lcd_key = 0
        self.key_in = 0

        self.btnRIGHT = {"GPIO": 20, "name": "button right"}  # 0
        self.btnUP = {"GPIO": 17, "name": "button up"}  # 0  # 1
        self.btnDOWN = {"GPIO": 18, "name": "button down"}  # 0  # 2
        self.btnLEFT = {"GPIO": 19, "name": "button left"}  # 0 # 3
        self.btnSELECT = {"GPIO": 16, "name": "button select"}  # 0  # 4

        GPIO.setup(self.btnUP.get("GPIO"), GPIO.IN)
        GPIO.setup(self.btnLEFT.get("GPIO"), GPIO.IN)
        GPIO.setup(self.btnSELECT.get("GPIO"), GPIO.IN)
        GPIO.setup(self.btnDOWN.get("GPIO"), GPIO.IN)
        GPIO.setup(self.btnRIGHT.get("GPIO"), GPIO.IN)

        self.mode = Mode.ROLL

    def set_message(self, row, text):
        self.lcd.setCursor(0, row)
        self.lcd.clear()
        self.lcd.printout(text)
        
    def set_messages(self, text_row0, text_row1):
        self.lcd.clear()
        self.lcd.setCursor(0, 0)
        self.lcd.printout(text_row0)
        self.lcd.setCursor(0, 1)
        self.lcd.printout(text_row1)
        

    @staticmethod
    def add_event_function(btn: int, function):
        GPIO.add_event_detect(btn, GPIO.RISING,
                              callback=function, bouncetime=100)

    def read_lcd_buttons(self, channel):
        if channel == 17:
            print(self.btnUP)
            self.mode = Mode((self.mode.value + 1) % 3)
        if channel == 18:
            print(self.btnDOWN)
            self.mode = Mode((self.mode.value - 1) % 3)

        if self.mode == Mode.SETUP:
            self.set_message(0, "SETUP")
            if channel == 16:
                print(self.btnSELECT)
            if channel == 19:
                print(self.btnLEFT)
                self.blink(2.0)
            if channel == 20:
                print(self.btnRIGHT)
                self.breath(0x02)  # 0x03 red 0x02
        if self.mode == Mode.ROLL:
            self.set_message(0, "ROLL")
            if channel == 16:
                print(self.btnSELECT)
            if channel == 19:
                print(self.btnLEFT)
            if channel == 20:
                print(self.btnRIGHT)
        if self.mode == Mode.TEST:
            self.set_message(0, "TEST")
            if channel == 16:
                print(self.btnSELECT)
            if channel == 19:
                print(self.btnLEFT)
                self.blink(2.0)
            if channel == 20:
                print(self.btnRIGHT)
                self.breath(0x02)  # 0x03 red 0x02

    def blink(self, _time):
        self.lcd.blinkLED()
        time.sleep(_time)
        self.lcd.noBlinkLED()

    def breath(self, color):
        for i in range(0, 255, 1):
            self.lcd.setPWM(color, i)
            time.sleep(0.005)

        time.sleep(0.5)
        for i in range(254, 0, -1):
            self.lcd.setPWM(color, i)
            time.sleep(0.005)

        time.sleep(0.5)

    @staticmethod
    def on_exit(sig, func=None):
        print("exit handler")
        GPIO.cleanup()


if __name__ == '__main__':
    key = KeypadController()
    key.set_message(0, "hello there!")
    key.add_event_function(key.btnRIGHT.get("GPIO"), key.read_lcd_buttons)
    key.add_event_function(key.btnLEFT.get("GPIO"), key.read_lcd_buttons)
    key.add_event_function(key.btnUP.get("GPIO"), key.read_lcd_buttons)
    key.add_event_function(key.btnDOWN.get("GPIO"), key.read_lcd_buttons)
    signal.signal(signal.SIGINT, key.on_exit)
    signal.pause()
