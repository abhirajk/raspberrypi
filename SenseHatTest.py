from sense_hat import SenseHat

import signal
import sys

sense = SenseHat()

def sigint_handler(sig, frame):
    print('KeyboardInterrupt is caught');
    sense.clear();
    sys.exit(0)


signal.signal(signal.SIGINT, sigint_handler)

def main(args: list[str]) -> None:


    while True:
        # Take readings from all three sensors
        t = sense.get_temperature()
        p = sense.get_pressure()
        h = sense.get_humidity()

        # Round the values to one decimal place
        t = round(t, 1)
        p = round(p, 1)
        h = round(h, 1)

        # Create the message
        # str() converts the value to a string so it can be concatenated
        message = "Temperature: " + str(t) + " Pressure: " + str(p) + " Humidity: " + str(h)

        # Display the scrolling message
        sense.show_message(message, scroll_speed=0.1, text_colour=(55,55,55));

if __name__ == '__main__':
    main(sys.argv[1:])