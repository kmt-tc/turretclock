#!/usr/bin/env python3

import time
from datetime import datetime
import threading
#from queue import Queue
import pigpio
from os.path import exists
import os

import config as cfg
import irsense
import ui
from ui import uiq, error
from commander import Commander,Command
import dbstore
import environment
import mqttclient
import lightsense

def checkconfig():
    '''check the config file for sanity'''
    configerrs = 0

    try:
        if not isinstance(cfg.p_gpio_irsense_pin, int) or not 1 <= cfg.p_gpio_irsense_pin <= 40:    # FIXME look for actual gpio pins
            raise ValueError
    except:
        error('ERROR: p_gpio_irsense_pin must be 0-40')
        configerrs += 1

    try:
        if not isinstance(cfg.p_glitchfilter, int) or not 0 <= cfg.p_glitchfilter <= 300000:
            raise ValueError
    except:
        error('ERROR: p_glitchfilter must be an integer 0-300000')
        configerrs += 1

    try:
        if not isinstance(cfg.p_period, (float, int)) or cfg.p_period < 0:
            raise ValueError
    except:
        error('ERROR: p_period must be a positive number')
        configerrs += 1

    try:
        if not isinstance(cfg.p_offset, (float, int)) or not -cfg.p_period < cfg.p_offset < cfg.p_period:
            raise ValueError
    except:
        error('ERROR: p_offset must be a number of magnitude less than p_period')
        configerrs += 1

    try:
        if not isinstance(cfg.p_tolerance2, (float, int)) or not cfg.p_period > cfg.p_tolerance2 >= cfg.p_tolerance1:
            raise ValueError
    except:
        error('ERROR: p_tolerance2 must be a number between p_tolerance1 and p_period')
        configerrs += 1

    try:
        if not isinstance(cfg.p_tolerance1, (float, int)) or not cfg.p_tolerance2 > cfg.p_tolerance1 > 0:
            raise ValueError
    except:
        error('ERROR: p_tolerance1 must be a number between 0 and p_tolerance2') 
        configerrs += 1

    try:
        if not isinstance(cfg.p_min, (float, int)) or not 0 < cfg.p_min < cfg.p_period:
            raise ValueError
    except:
        error('ERROR: p_min must be a number between 0 and p_period')
        configerrs += 1

    try:
        if not isinstance(cfg.p_timeout, (float, int)) or cfg.p_timeout < 0:
            raise ValueError
    except:
        error('ERROR: p_timeout must be a positive number')
        configerrs += 1

    if not isinstance(cfg.p_timeoutcmd, str):
        cfg.p_timeoutcmd = None
    else:
        if cfg.p_timeoutcmd[0] != '/':
            cfg.p_timeoutcmd = os.getcwd() + '/' + cfg.p_timeoutcmd
        if not exists(cfg.p_timeoutcmd):
            error('ERROR: Timeout command {} does not exist'.format(cfg.p_timeoutcmd))
            configerrs += 1
        else:
            if not os.access(cfg.p_timeoutcmd, os.X_OK):
                error('ERROR: Timeout command {} is not executable'.format(cfg.p_timeoutcmd))
                configerrs += 1

    try:
        if not isinstance(cfg.p_timeoutrpt, int) or cfg.p_timeoutrpt < 0:
            raise ValueError
    except:
        error('ERROR: p_timeoutrpt must be a positive integer')
        configerrs += 1

    try:
        if not isinstance(cfg.ui_showarrive, bool):
            raise ValueError
    except:
        error('ERROR: p_showarrive must be boolean')
        configerrs += 1

    try:
        if not isinstance(cfg.ui_showdepart, bool):
            raise ValueError
    except:
        config('ERROR: ui_showdepart must be boolean')
        configerrs += 1

    try:
        if not isinstance(cfg.ui_ts, bool):
            raise ValueError
    except:
        error('ERROR: ui_ts must be boolean')
        configerrs += 1

    return configerrs

if __name__ == '__main__':
    pig = pigpio.pi()   # Connect to pigpiod
    c = Commander(cfg.ui_banner, cmd_cb=ui.cmds())    # Start up Commander interface

    # Start output thread
    outputT = threading.Thread(name='ui', target=ui.outputD, args=(c,))            # UI
    outputT.start()

    # Check the config file for sanity
    configerrs = checkconfig()

    if configerrs == 1:
        error('ERROR: 1 configuration error found - Cannot continue')
    elif configerrs:
        error('ERROR: {} configuration errors found - Cannot continue'.format(configerrs))
    else:
        # Build other threads
        if cfg.db_engine:
            dbT = threading.Thread(name='db', target=dbstore.dbD)
            dbT.daemon = True
            dbT.start()
        else:
            uiq.put(('WARNING: Database storage disabled.','WARN'))
        if cfg.env_engine:
            envT = threading.Thread(name='env', target=environment.envD, args=(pig,))
            envT.daemon = True
            envT.start()
        if cfg.mqtt_engine:
            mqttT = threading.Thread(name='mqtt', target=mqttclient.mqttD)
            mqttT.daemon = True
            mqttT.start()
        if cfg.light_engine:
            lightsenseT = threading.Thread(name='lightsense', target=lightsense.lightsenseD, args=(pig,))
            lightsenseT.daemon = True
            lightsenseT.start()
        pendulumT = threading.Thread(name='p', target=irsense.pendulumD, args=(pig,))
        pendulumT.daemon = True
        pendulumT.start()

    c.loop()

    forever = threading.Event(); forever.wait()
    pd.cancel()
    pa.cancel()
    pig.stop()

