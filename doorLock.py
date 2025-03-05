import machine
import time
import math
import sys

#Motor Control
class MotorControl:
    inputA = None;
    inputB = None;
    speedControl = None;
    
    def __init__(self, inputAPin: int, inputBPin: int, enablePin: int):
        self.inputA = machine.Pin(inputAPin, machine.Pin.OUT);
        self.inputA.off()
        self.inputB = machine.Pin(inputBPin, machine.Pin.OUT);
        self.inputB.off()
        self.speedControl = machine.PWM(machine.Pin(enablePin))
        self.speedControl.freq(50)
        self.speedControl.duty_u16(0)

    def rotate(self, speed, direction):
        if speed > 100: speed=100
        if speed < 0: speed=0
        if direction == 0:
            self.inputA.value(0)
            self.inputB.value(0)
            speed = 0
        self.speedControl.duty_u16(int(speed/100*65536))
        if direction < 0:
            self.inputA.value(0)
            self.inputB.value(1)
        if direction > 0:
            self.inputA.value(1)
            self.inputB.value(0)

#Position
class DoorPosition:
    OPEN = 1
    UNKNOWN = 0
    LOCKED = -1
    margin = 1000
    openPosition = -1
    closePosition = -1
    currentPosition = -1
    openBoundary = [0, 0]
    closeBoundary = [0, 0]
    measure = None
    enable = None
    
    def __init__(self, enablePin: int, measurePin: int):
        self.enable = machine.Pin(enablePin, machine.Pin.OUT)
        self.enable.off()
        self.measure = machine.ADC(measurePin)
    
    def check(self):
        self.start()
        self.currentPosition = self.measure.read_u16()
        self.stop()        
    
    def isOpen(self, margin=None):
        self.check()
        return self.position()==self.OPEN
    
    def position(self):
        if self.openPosition!=-1:
            if self.currentPosition>=self.openBoundary[0] and self.currentPosition<=self.openBoundary[1]:
                return self.OPEN
        if self.closePosition!=-1:
            if self.currentPosition>self.closeBoundary[0] and self.currentPosition<self.closeBoundary[1]:
                return self.LOCKED
        return self.UNKNOWN
    
    def start(self):
        self.enable.on()
        time.sleep(0.1)
    
    def stop(self):
        self.enable.off()
        
    def setOpenPosition(self):
        self.check()
        self.openPosition = self.currentPosition
        
    def setClosePosition(self):
        self.check()
        self.closePosition = self.currentPosition
        
    def initialize(self):
        doorRange = math.fabs(self.closePosition - self.openPosition)
        openRange = math.fabs(doorRange * 0.80)
        closeRange = math.fabs(doorRange * 0.20)
        marginRange = math.fabs(doorRange * 0.10)
        factor = 1
        if self.closePosition < self.openPosition:
            factor = -1
        openRangeA = (self.openPosition - (factor * marginRange));
        openRangeB = (self.openPosition + (factor * openRange));
        if openRangeA>openRangeB:
            self.openBoundary = [openRangeB, openRangeA]
        else:
            self.openBoundary = [openRangeA, openRangeB]
        closeRangeA = (self.closePosition + (factor * marginRange));
        closeRangeB = (self.closePosition - (factor * closeRange));
        if closeRangeA>closeRangeB:
            self.closeBoundary = [closeRangeB, closeRangeA]
        else:
            self.closeBoundary = [closeRangeA, closeRangeB]
        
        


MOTOR_INPUT_1_PIN=14 
MOTOR_INPUT_2_PIN=15
MOTOR_ENABLE_1_2_PIN=16
motorControl = MotorControl(MOTOR_INPUT_1_PIN, MOTOR_INPUT_2_PIN, MOTOR_ENABLE_1_2_PIN)

POSITION_ENABLE_PIN = 17
POSITION_MEASURE_PIN = 26
doorPosition = DoorPosition(POSITION_ENABLE_PIN, POSITION_MEASURE_PIN)

#Alert
class DoorAlert:
    openLed = None
    closeLed = None
    buzzer = None

    def __init__(self, openLedPin: int, closeLedPin: int, buzzerPin: int):
        self.openLed = machine.Pin(openLedPin, machine.Pin.OUT)
        self.openLed.off()
        self.closeLed = machine.Pin(closeLedPin, machine.Pin.OUT)
        self.closeLed.off()
        self.buzzer = machine.PWM(machine.Pin(buzzerPin));
        
    def __blink(self, led, repeat=1, onTime=0.3, offTime=0.15, buzz=False):
        if buzz:
            self.buzzer.freq(1047)
        while repeat>0:
            if buzz:
                self.buzzer.duty_u16(2000)
            led.on()
            time.sleep(onTime)
            led.off()
            if buzz:
                self.buzzer.duty_u16(0)
            repeat -= 1
            if repeat > 0:
                time.sleep(offTime)
        
    def ackOpen(self):
        self.__blink(self.openLed, buzz=True)

    def ackClose(self):
        self.__blink(self.closeLed, buzz=True)
        
    def doorOpen(self):
        self.__blink(self.openLed, buzz=True)
        
    def shutdown(self):
        self.__blink(self.closeLed, repeat=3, onTime=0.2, offTime=0.2, buzz=False)
    
    def buzz(self):
        self.buzzer.freq(1047)
        self.buzzer.duty_u16(2000)
        time.sleep(0.3)
        self.buzzer.duty_u16(0)


BUZZER_PIN = 18
CLOSE_LED_PIN = 19
OPEN_LED_PIN = 20
alert = DoorAlert(OPEN_LED_PIN, CLOSE_LED_PIN, BUZZER_PIN)

SET_PIN = 9
setButton = machine.Pin(SET_PIN, machine.Pin.IN, machine.Pin.PULL_UP)

#Setting the initial positions
MAX_CYCLE_FOR_SHUTDOWN = 3
shutdownCycle = 0
if setButton.value() == 0:
    while True:
        if setButton.value() == 1:
            break
        alert.buzz()
        time.sleep(0.5)
        shutdownCycle += 1
        if shutdownCycle > MAX_CYCLE_FOR_SHUTDOWN:
            alert.shutdown()
            sys.exit(0);

alert.openLed.on()
onState = True
while True:
    if setButton.value() == 0:
        doorPosition.setOpenPosition()
        break
    time.sleep(0.2)
    if onState:
        alert.openLed.off()
        onState = False
    else:
        alert.openLed.on()
        onState = True
alert.ackOpen()
time.sleep(0.5)
alert.closeLed.on()
onState = True
while True:
    if setButton.value() == 0:
        doorPosition.setClosePosition()
        break
    time.sleep(0.2)
    if onState:
        alert.closeLed.off()
        onState = False
    else:
        alert.closeLed.on()
        onState = True
alert.ackClose()

doorPosition.initialize()

countSetButton = 0
SLEEP_PERIOD_IN_MS = 500
CHECK_INTERVAL_IN_MS = 2000
interval = 0
while True:
    startTime = time.time()
    if machine.Pin(SET_PIN, machine.Pin.IN, machine.Pin.PULL_UP).value() == 0:
        countSetButton += 1
        if countSetButton >= 4:
            machine.reset()
    else:
        countSetButton = 0
    if interval >= CHECK_INTERVAL_IN_MS:
        interval = 0
        if doorPosition.isOpen()==True:
            alert.doorOpen()
        print(":", end="")
    print(".", end="")
    machine.lightsleep(SLEEP_PERIOD_IN_MS)
    interval += SLEEP_PERIOD_IN_MS
