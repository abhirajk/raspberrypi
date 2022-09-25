import sys
import signal

import RPi.GPIO as GPIO;
import time;

fanPin = 18;

def sigint_handler(sig, frame):
    print('KeyboardInterrupt is caught');
    GPIO.output(fanPin, GPIO.LOW);
    sys.exit(0)


signal.signal(signal.SIGINT, sigint_handler)

def main(args: list[str]) -> None:

    fanPin = int(args[0]);
    onTime = float(args[1]);
    offTime = float(args[2]);

    GPIO.setmode(GPIO.BCM);
    GPIO.setwarnings(False);

    GPIO.setup(fanPin, GPIO.OUT);

    state = GPIO.LOW;
    while True:
        state = GPIO.HIGH if (state == GPIO.LOW) else GPIO.LOW;
        GPIO.output(fanPin, state);
        time.sleep(offTime if (state == GPIO.LOW) else onTime);



if __name__ == '__main__':
    main(sys.argv[1:])