#!/usr/bin/env python3

# This is just a simple daemon that will keep the last n minutes'
# light level recordings in a temporary file

import pigpio
import time
import os
import threading
import config as cfg

def fullcap(a, b, c):
    '''the capacitor has charged enough to pull the pin high'''
    global timenow, sensordata
    delta = c-timenow                                   # Stop the counter
    print(delta)
#    if delta < 0: delta += 4294967295                   # Counter wrapped
    if delta < 0:
        draincap()
        return
    sensordata.append(delta)
    time.sleep(cfg.light_read_interval)                 # Wait for the next reading
    draincap()                                          # Drain the cap to prime the next reading
    return

def writeD():
    '''store the light level in the output file, cropping if necessary'''
    global sensordata
    while True:
        time.sleep(cfg.light_store_interval)
        light_filetmp = cfg.light_filename + ".tmp"         # Temporary file
        try:
            with open(cfg.light_filename, 'r') as fin:
                data = fin.read().splitlines(True)          # Read in existing data if present
        except FileNotFoundError:
            data = [ ]
        if len(data) >= cfg.light_keepreadings:
#            data.pop(0)                                     # Remove the first entry if we need to clip one
            data = data[-cfg.light_keepreadings:]
#        data.append(str(int(sum(sensordata)/len(sensordata))) + '\n')                      # Append the new entry
#        print("storing {}".format(int(sum(sensordata)/len(sensordata))))
        if len(sensordata) > 0:
            data.append(str(cfg.light_normalise/(sum(sensordata)/len(sensordata))) + '\n')      # Append the new entry
            print("storing {}".format(cfg.light_normalise/(sum(sensordata)/len(sensordata))))
            with open(light_filetmp, 'w') as fout:
                fout.writelines(data)                           # Store entries in temporary file
            os.rename(light_filetmp, cfg.light_filename)        # Move the temporary file to the non-temporary one
        sensordata = [ ]

def draincap():
    '''drain the capacitor'''
    global timenow
    pig.set_mode(cfg.light_gpio_pin, pigpio.OUTPUT)     # Set pin to output
    pig.write(cfg.light_gpio_pin, 0)                    # Ground it to drain the cap
    time.sleep(0.2)                                     # Wait for cap to drain
    timenow = pig.get_current_tick()                    # Start the counter
    pig.set_mode(cfg.light_gpio_pin, pigpio.INPUT)      # Set pin to input
    return

def readD(pig):
    '''sensor read thread'''
    global sensordata
    pig.callback(cfg.light_gpio_pin, pigpio.RISING_EDGE, fullcap)   # Set callback for sensor pin
    draincap()              # Drain the capacitor to produce the first read
    threading.Event().wait()        # Wait forever

if __name__=='__main__':
    global sensordata
    sensordata = [ ]
    pig = pigpio.pi()   # Connect to pigpiod
    readT = threading.Thread(name='read', target=readD, args=(pig,))  # Sensor read thread
    readT.start()
    writeT = threading.Thread(name='write', target=writeD)  # Sensor write thread
    writeT.start()

    threading.Event().wait()      # Just wait forever, until keyboard interrupt
