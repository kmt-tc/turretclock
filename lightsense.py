#!/usr/bin/env python3

# Light sensor module

import pigpio
import time
import os
import threading
import config as cfg
from globs import mqq
from defs import Watchdog
from ui import debug

def fullcap(a, b, c):
    '''the capacitor has charged enough to pull the pin high'''
    global timenow, sensordata
    delta = c-timenow                                   # Stop the counter
    print(delta)
#    if delta < 0: delta += 4294967295                   # Counter wrapped
    if delta < 0:
        draincap()
        return
    debug('Light sensor read took {} ticks'.format(delta), 3)
    sensordata.append(delta)
    time.sleep(cfg.light_read_interval)                 # Wait for the next reading
    draincap()                                       # Drain the cap to prime the next reading
    return

def storeD():
    '''store the light level in the output file, cropping if necessary'''
    global sensordata, watchdog
    watchdog.reset()                                    # Reset the watchdog
    light_filetmp = cfg.light_filename + ".tmp"         # Temporary file
    try:
        with open(cfg.light_filename, 'r') as fin:
            data = fin.read().splitlines(True)          # Read in existing data if present
    except FileNotFoundError:
        data = [ ]
    if len(data) >= cfg.light_keepreadings:
        data = data[-cfg.light_keepreadings:]
#    data.append(str(int(sum(sensordata)/len(sensordata))) + '\n')                      # Append the new entry
#    print("storing {}".format(int(sum(sensordata)/len(sensordata))))
    if len(sensordata) > 0:
        sensestore = cfg.light_normalise/(sum(sensordata)/len(sensordata))
        data.append(str(sensestore) + '\n')      # Append the new entry
#        print("storing {}".format(cfg.light_normalise/(sum(sensordata)/len(sensordata))))
        with open(light_filetmp, 'w') as fout:
            fout.writelines(data)                           # Store entries in temporary file
        os.rename(light_filetmp, cfg.light_filename)        # Move the temporary file to the non-temporary one
        debug('Storing light sensor average {}'.format(sensestore), 2)
        if cfg.mqtt_engine:
            mqq.put(('lightSense',{ 'brightness': format(sensestore) }))
    sensordata = [ ]

def draincap():
    '''drain the capacitor'''
    global timenow, pig
    pig.set_mode(cfg.light_gpio_pin, pigpio.OUTPUT)     # Set pin to output
    pig.write(cfg.light_gpio_pin, 0)                    # Ground it to drain the cap
    time.sleep(0.2)                                     # Wait for cap to drain
    timenow = pig.get_current_tick()                    # Start the counter
    pig.set_mode(cfg.light_gpio_pin, pigpio.INPUT)      # Set pin to input
    return

#def readD(pig):
#    '''sensor read thread'''
#    global sensordata
#    pig.callback(cfg.light_gpio_pin, pigpio.RISING_EDGE, fullcap)   # Set callback for sensor pin
#    draincap()              # Drain the capacitor to produce the first read
#    threading.Event().wait()        # Wait forever

def lightsenseD(pig):
    global sensordata, watchdog
    sensordata = [ ]
    watchdog = Watchdog(cfg.light_store_interval, storeD)
    pig.callback(cfg.light_gpio_pin, pigpio.RISING_EDGE, fullcap)   # Set callback for sensor pin
    draincap()                 # Drain the capacitor to produce the first read
    threading.Event().wait()        # Wait forever
