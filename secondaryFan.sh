#!/bin/sh
### BEGIN INIT INFO
# Provides:          secondaryFan.sh
# Required-Start:    $local_fs $named $time $syslog
# Required-Stop:     $local_fs $named $time $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Description:       Start secondary fan
### END INIT INFO

start() {
  echo "Starting secondary fan"
  python /home/pi/raspberrypi/startSecondaryFan.py 18 30 60
}

stop() {
  echo "Stopping secondary fan"
  pkill -f startSecondaryFan.py
  python /home/pi/raspberrypi/stopSecondaryFan.py 18
}

case "$1" in
  start)
    start
    ;;
  stop)
    stop
    ;;
  *)
esac