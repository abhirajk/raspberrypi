import sys
import signal

import RPi.GPIO as GPIO;

fanPin = 18;

def main(args: list[str]) -> None:

    fanPin = int(args[0]);

    GPIO.setmode(GPIO.BCM);
    GPIO.setwarnings(False);

    GPIO.setup(fanPin, GPIO.OUT);
    GPIO.output(fanPin, GPIO.LOW);


if __name__ == '__main__':
    main(sys.argv[1:])