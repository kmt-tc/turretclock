#!/usr/bin/env python3

# SI7021 temperature/humidity sensor module
# Call this directly to return temperature and humidity on separate lines e.g. for snmp stats

# Based on http://abyz.me.uk/rpi/pigpio/code/Si7021_py.zip

import pigpio
import time
import threading
import config as cfg
import globs
from globs import uiq
from ui import debug

def sicrc(data):
    '''crc function for the si7021'''
    rem = 0
    for b in data:
        rem ^= b
        for bit in range(8):
            if rem & 128:
                rem = (rem << 1) ^ 0x31
            else:
                rem = (rem << 1)
    return rem & 0xFF

def temphumid(pig):
    '''returns temperature and humidity (pig = pigpiod handle)'''
#    debug('Entering temphumid(pig)', 3)
    temperature = 999
    humidity = 999
    tattempts = 0
    hattempts = 0

    # Get I2C bus
    bus = pig.i2c_open(cfg.env_i2cbus, 0x40)

    while tattempts <= cfg.env_attempts and (temperature < cfg.env_mintemp or temperature > cfg.env_maxtemp):
        # Request temperature - no hold master mode
        try:
            pig.i2c_write_device(bus, [0xF3])
        except:
            tattempts += 1
            continue
        time.sleep(cfg.env_delay)

        # Read temperature and CRC
        c, t = pig.i2c_read_device(bus, 3)
        debug('Read from temperature sensor: {}, {}'.format(str(c),str(t)), 3)

        # Check CRC and compute temperature in C
        if sicrc(t) == 0:
            try: temperature = round((175.72 * ((t[0]<<8) + t[1])/65536.0) - 46.85,1)
            except IndexError:
                tattempts += 1
                if tattempts == cfg.env_attempts: temperature = 999
                debug('Temperature sensor failure', 2)
        else:
            tattempts += 1
            if tattempts == cfg.env_attempts: temperature = 999
            debug('Temperature read CRC failure', 2)
            time.sleep(cfg.env_delay)

    while hattempts <= cfg.env_attempts and (humidity < cfg.env_minhum or humidity > cfg.env_maxhum):
        # Request humidity - no hold master mode
        try:
            pig.i2c_write_device(bus, [0xF5])
        except:
            hattempts += 1
            continue
        time.sleep(cfg.env_delay)

        # Read humidity and CRC
        c, rh = pig.i2c_read_device(bus, 3)
        debug('Read from humidity sensor: {}, {}'.format(str(c),str(rh)), 3)

        # Check CRC and compute RH
        if sicrc(rh) == 0:
            try: humidity = round((125.0 * ((rh[0]<<8) + rh[1]))/65536.0) - 6
            except IndexError:
                hattempts += 1
                if hattempts == cfg.env_attempts: humidity = 999
                debug('Humidity sensor failure', 2)
        else:
            hattempts += 1
            if hattempts == cfg.env_attempts: humidity = 999
            debug('Humidity read CRC failure', 2)
            time.sleep(cfg.env_delay)

    # Close the handle
    pig.i2c_close(bus)

    return temperature, humidity

def envD(pig):
    '''environmental data thread (pig = pigpiod handle)'''
    debug('Environmental data thread initialising')

    if cfg.env_frequency-3*cfg.env_delay < 0:
        uiq.put(('ERROR: env_frequency too low (must be at least {})'.format(3*cfg.env_delay), 'ERR'))
        return
    while True:
#        debug('Calling temphumid(pig)', 3)
        globs.temperature, globs.humidity = temphumid(pig)
#        debug('Returned from temphumid(pig)', 3)
        debug('Read temperature {} and humidity {}'.format(globs.temperature, globs.humidity), 2)
        time.sleep(cfg.env_frequency-3*cfg.env_delay)

if __name__ == '__main__':
    pig = pigpio.pi()   # Connect to pigpiod
    temperature, humidity = temphumid(pig)
    print('{}\n{}'.format(temperature, humidity))

