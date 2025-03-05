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
        self.speedControl.duty_u16(0)
        self.speedControl.freq(50)

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

    def reset(self):
        self.inputA.value(0)
        self.inputB.value(0)
        self.speedControl.duty_u16(0)

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
        return True

    def reset(self):
        self.enable.off()

#Alert
class DoorAlerter:
    BUZZER_FREQ = 1047
    BUZZER_DUTY = 2000
    BUZZER_DURATION_IN_MS = 300
    NOTIFY_LED_ON_DURATION_IN_MS = 200
    NOTIFY_LED_OFF_DURATION_IN_MS = 200
    openLed = None
    closeLed = None
    buzzer = None

    def __init__(self, openLedPin: int, closeLedPin: int, buzzerPin: int):
        self.openLed = machine.Pin(openLedPin, machine.Pin.OUT)
        self.openLed.off()
        self.closeLed = machine.Pin(closeLedPin, machine.Pin.OUT)
        self.closeLed.off()
        self.buzzer = machine.PWM(machine.Pin(buzzerPin));
        
    def __blink(self, led, repeat=1, onTime=300, offTime=150, buzz=False):
        if buzz:
            self.buzzer.freq(1047)
        while repeat>0:
            if buzz:
                self.buzzer.duty_u16(2000)
            led.on()
            time.sleep(onTime / 1000)
            led.off()
            if buzz:
                self.buzzer.duty_u16(0)
            repeat -= 1
            if repeat > 0:
                time.sleep(offTime / 1000)

    def notifyCloseDoor(self):
        self.__blink(self.closeLed, buzz=True)
        
    def notifyOpenDoor(self):
        self.__blink(self.openLed, buzz=True)
        
    def notifyShutdown(self):
        self.__blink(self.closeLed, repeat=3, onTime=self.NOTIFY_LED_ON_DURATION_IN_MS, offTime=self.NOTIFY_LED_OFF_DURATION_IN_MS, buzz=False)

    def notifyError(self):
        self.__blink(self.closeLed, repeat=3, onTime=self.NOTIFY_LED_ON_DURATION_IN_MS, offTime=self.NOTIFY_LED_OFF_DURATION_IN_MS, buzz=False)
        
    def buzz(self):
        self.buzzer.freq(self.BUZZER_FREQ)
        self.buzzer.duty_u16(self.BUZZER_DUTY)
        time.sleep(BUZZER_DURATION_IN_MS / 1000)
        self.buzzer.duty_u16(0)

    def reset(self):
        self.buzzer.duty_u16(0)
        self.openLed.off()
        self.closeLed.off()
        
#Controller
class DoorController:
    INPUT_HOLD_SHUTDOWN_IN_MS = 3000
    CHECK_INPUT_SHUTDOWN_IN_MS = 500
    SLEEP_PERIOD_IN_MS = 500
    CHECK_INTERVAL_IN_MS = 2000
    CHECK_INPUT_SET_POSITION_IN_MS = 200
    pinConfig = None
    motorControl = None
    position = None
    alerter = None
    inputButton = None

    def __init__(self, pinConfig):
        self.pinConfig = pinConfig
        self.motorControl = MotorControl(pinConfig["motor"]["input"]["a"], pinConfig["motor"]["input"]["b"], pinConfig["motor"]["enable"])
        self.position = DoorPosition(pinConfig["position"]["enable"], pinConfig["position"]["measure"])
        self.alerter = DoorAlerter(pinConfig["alert"]["openLed"], pinConfig["alert"]["closeLed"], pinConfig["alert"]["buzzer"])
        self.inputButton = machine.Pin(pinConfig["inputButton"], machine.Pin.IN, machine.Pin.PULL_UP)        
    
    def __isShutdownSequence(self):
        shutdownHold = 0
        #If input is pressed during startup then prepare to shutdown if held down for MAX_CYCLE_FOR_SHUTDOWN * CHECK_INPUT_SLEEP_FOR_SHUTDOWN_IN_SEC
        if self.inputButton.value() == 0:#Pressed
            while True:
                if self.inputButton.value() == 1:#Released
                    return False
                self.alerter.buzz()
                time.sleep(self.CHECK_INPUT_SHUTDOWN_IN_MS / 1000)
                shutdownHold += CHECK_INPUT_SHUTDOWN_IN_MS
                if shutdownWait > self.INPUT_HOLD_SHUTDOWN_IN_MS:
                    self.alerter.notifyShutdown()
                    return True
        return False

    def __setDoorPosition(self, type: int):
        indicator = None
        if type==1:
            indicator = self.alerter.openLed
        else:
            indicator = self.alerter.closeLed
        indicator.on()
        while True:
            if self.inputButton.value() == 0:
                break
            time.sleep(CHECK_INPUT_SET_POSITION_IN_MS / 1000)
            indicator.toggle()
        indicator.off()
        if type==1:
            self.position.setOpenPosition()
            self.alerter.notifyOpenDoor()
        else:
            self.position.setClosePosition()
            self.alerter.notifyCloseDoor()

    def setOpenDoorPosition(self):
        __setDoorPosition(self, type=1)

    def setCloseDoorPosition(self):
        __setDoorPosition(self, type=0)

    def initiallize(self):
        if __isShutdownSequence(self):
            return False
        while True
            __setDoorPosition(self, type=1)#Open
            __setDoorPosition(self, type=0)#Close
            if self.position.initialize():
                break
            else
                self.alerter.notifyError()
        return True

    def watch(self):
        countButtonPressed = 0
        interval = 0
        while True:
            inputButton = machine.Pin(self.pinConfig["inputButton"], machine.Pin.IN, machine.Pin.PULL_UP)
            if inputButton.value() == 0:
                countButtonPressed += 1
                if countButtonPressed >= 4:
                    self.reset()
                    return
            else:
                countButtonPressed = 0
            if interval >= CHECK_INTERVAL_IN_MS:
                interval = 0
                if self.position.isOpen()==True:
                    self.alerter.notifyOpenDoor()
            machine.lightsleep(SLEEP_PERIOD_IN_MS)
            interval += SLEEP_PERIOD_IN_MS

    def reset(self):
        self.motorControl.reset()
        self.position.reset()
        self.alerter.reset()
        machine.reset()
        
# --- Pin Mapping on Pico
# Motor Control Pins
pinConfig = {
    "motor": {
        "enable": 16,
        "input": {
            "a": 14, 
            "b": 15
        }
    },
    "position": {
        "enable": 17,
        "measure": 26
    },
    "alert": {
        "openLed": 20
        "closeLed": 19
        "buzzer": 18
    },
    "inputButton": 9
}

doorController = DoorController(pinConfig)
if not doorController.initialize():
    sys.exit(0)

doorController.watch()
