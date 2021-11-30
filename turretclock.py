#!/usr/bin/env python3

import time
from datetime import datetime, timedelta
import threading
#from queue import Queue
import pigpio
from os.path import exists
import os

import config as cfg
import globs
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

def readNtpDrift(omtime = 0):
    '''read the ntp.drift file to track oscillator drift, and reread on changes'''
    nmtime = os.stat(cfg.ntpdriftfile).st_mtime
    if nmtime > omtime:
        f = open(cfg.ntpdriftfile,"r")
        globs.ntpdrift = float(f.readline())
        f.close()
        omtime = nmtime
    threading.Timer(cfg.ntpdriftint, readNtpDrift, [omtime]).start()

def loadState():
    '''load the saved state if it exists'''
    try:
        f = open(cfg.statefile,"r")
        globs.driftstate = float(f.readline())
        drift1m = float(f.readline())
        drift1h = float(f.readline())
        drift1d = float(f.readline())
        f.close()
        # Add elements generated from old daily average
        adrift1d = (86400*drift1d-3540*drift1h-60*drift1m)/82800
        for x in range(int(82800/(cfg.p_period/1e6))):
            globs.driftavg.append(adrift1d)
        # Add elements generated from old hourly average
        adrift1h = (3600*drift1h-60*drift1m)/3540
        for x in range(int(3540/(cfg.p_period/1e6))):
            globs.driftavg.append(adrift1h)
        # Add elements from old minute average
        for x in range(int(60/(cfg.p_period/1e6))):
            globs.driftavg.append(drift1m)
    except:
        uiq.put(('WARNING: State file not loaded','WARN'))

def saveState():
    '''periodically write the state file'''
    if len(globs.driftavg) > 0:
        try:
            f = open(cfg.statefile,"w")
            f.writelines([
                str((globs.clocktime-globs.realtime).total_seconds()) + "\n",   # Clock error
                str(globs.driftavgs[0]) + "\n",                                 # 1 minute drift
                str(globs.driftavgs[1]) + "\n",                                 # 1 hour drift
                str(globs.driftavgs[2]) + "\n"                                  # 1 day drift
            ])
            f.close()
        except:
            uiq.put(('WARNING: Failed to save state file','WARN'))
    threading.Timer(cfg.stateint, saveState).start()

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
        # Load saved state, if it exists, then start the state save thread
        loadState()
        threading.Timer(cfg.stateint, saveState).start()

        # Database thread
        if cfg.db_engine:
            dbT = threading.Thread(name='db', target=dbstore.dbD)
            dbT.daemon = True
            dbT.start()
        else:
            uiq.put(('WARNING: Database storage disabled.','WARN'))

        # Environment thread
        if cfg.env_engine:
            envT = threading.Thread(name='env', target=environment.envD, args=(pig,))
            envT.daemon = True
            envT.start()

        # MQTT thread
        if cfg.mqtt_engine:
            mqttT = threading.Thread(name='mqtt', target=mqttclient.mqttD)
            mqttT.daemon = True
            mqttT.start()

        # Light sensor thread
        if cfg.light_engine:
            lightsenseT = threading.Thread(name='lightsense', target=lightsense.lightsenseD, args=(pig,))
            lightsenseT.daemon = True
            lightsenseT.start()

        # ntp.drift reader
        readNtpDrift()

        # Clock monitor thread
        pendulumT = threading.Thread(name='p', target=irsense.pendulumD, args=(pig,))
        pendulumT.daemon = True
        pendulumT.start()

    c.loop()

    forever = threading.Event(); forever.wait()
    pd.cancel()
    pa.cancel()
    pig.stop()

