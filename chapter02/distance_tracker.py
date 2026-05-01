#!/usr/bin/env python3
from gpiozero import DistanceSensor
from time import sleep

sensor = DistanceSensor(echo=17, trigger=4)

try:
    while True:
        dis = sensor.distance * 100  # Convert from meters to centimeters
        # Convert the float to an integer and print, forcing it to flush immediately
        print(f'Distance to target: {int(dis)} cm', flush=True)
        sleep(1)
except KeyboardInterrupt:
    # Handle KeyboardInterrupt (Ctrl+C) to gracefully exit the loop
    pass
