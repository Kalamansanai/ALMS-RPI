import RPi.GPIO as GPIO

LED_GREEN = 24
LED_RED = 23


def setup():
    GPIO.setwarnings(False)
    GPIO.cleanup()
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(LED_RED, GPIO.OUT)
    GPIO.setup(LED_GREEN, GPIO.OUT)

def g_on():
    GPIO.output(LED_GREEN, GPIO.HIGH)

def g_off():
    GPIO.output(LED_GREEN, GPIO.LOW)

def r_on():
    GPIO.output(LED_RED, GPIO.HIGH)

def r_off():
    GPIO.output(LED_RED, GPIO.LOW)

def cleanup():
    GPIO.cleanup()