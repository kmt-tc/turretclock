import pigpio
from queue import Queue
import os
from datetime import timedelta, datetime
from statistics import mean

import config as cfg
from commander import Commander,Command
from defs import Watchdog
import globs
from globs import dbq, uiq, mqq

timeoutrpt = 0

def pendulumTimeout():
    '''pendulumTimeout() is called when the pendulum doesn't arrive for cfg.p_timeout seconds
    '''
    global timeoutrpt, watchdog, pa, pd, prevArr, prevDep
    watchdog.reset()                        # Need this to trigger again in cfg.p_timeout seconds
    timeoutrpt += 1
    uiq.put(('WARNING:  Beat timeout after {} seconds! ({}/{})'.format(cfg.p_timeout, timeoutrpt, cfg.p_timeoutrpt), 'WARN'))
    if timeoutrpt == cfg.p_timeoutrpt:         # We've reached the maximum number of misses
        timeoutrpt = 0                       # Reset this for when the clock restarts
        uiq.put(('ERROR:  Too many missed beats.  Resetting monitor thread.', 'ERR'))
        globs.beatbanner = "[ Waiting for first beat ]"
        prevArr = 0
        prevDep = 0
#        pa.cancel()                         # Kill the pendulum arrival monitor thread
#        pd.cancel()                         # Kill the pendulum departure monitor
        watchdog.stop()                   # Kill the watchdog
        try: cfg.p_timeoutcmd
        except AttributeError: pass
        else:
            uiq.put(('Executing timeout command \'{}\''.format(cfg.p_timeoutcmd),'DEBUG'))
            os.system(cfg.p_timeoutcmd)    # Run a specified command on timeout

def pendulumArrive(g, L, t):
    '''pendulumArrive(gpio, level, tick) - pendulum has arrived at IR sensor gate
    '''
    global prevArr, watchdog, timeoutrpt, clocktime
    loglevel = 'INFO'                           # Default to INFO, change to WARN or ERR if necessary
    timeoutrpt = 0
    message = "beat detect"
    if prevArr:
        delta = t-prevArr
        if delta < 0: delta += 4294967295              # counter wrapped
        if delta < cfg.p_min:                                   # Absurd arrival time, ignore
            uiq.put(('Absurd arrival delta {} uS ignored.'.format(delta),'DEBUG'))
            return
        skew = delta-cfg.p_period
        if abs(cfg.p_offset-skew) > cfg.p_tolerance2:          # Pendulum period is outside "bad" tolerance
            loglevel = 'ERR'
        elif abs(cfg.p_offset-skew) > cfg.p_tolerance1:        # Pendulum period is outside "warn" tolerance
            loglevel = 'WARN'
        globs.realtime = datetime.now()
        hz = cfg.p_period/delta                                 # Compute pendulum frequency (Hz)
        drift = 86400*(1-1/hz)                                  # Compute drift (s/day)
        if isinstance(globs.newclocktime, datetime):           # clocktime was just run
            globs.clocktime += globs.realtime-globs.newclocktime # add only a partial beat
            if cfg.ui_btcut > 0:
                uiq.put(('Clock time set to {}'.format(globs.clocktime.strftime(cfg.ui_btfmt)[:-cfg.ui_btcut])))
            else:
                uiq.put(('Clock time set to {}'.format(globs.clocktime.strftime(cfg.ui_btfmt))))
            globs.newclocktime = None
        else:
            globs.clocktime += timedelta(microseconds=cfg.p_period)    # add one pendlum period to the clock time
            # Build drift averages only when manual time *hasn't* been set (otherwise we get a ridiculous average)
            avgdrift(drift)                                     
        beatstats = "{:+} uS / {:.4f} Hz / {:.1f} BPH / {:+.1f} s/day".format(int(skew), hz, 3600*hz, drift)
        message += " ({})".format(beatstats)
        globs.beatbanner = "[ {} ]".format(beatstats)
        if cfg.db_engine: dbq.put((1, delta, hz, skew))           # store the database entry
        if cfg.mqtt_engine:
            if cfg.mqtt_p_arrive:
                mqq.put(('beatArrive',{ 'delta': delta, 'Hz': hz, 'skew': skew }))  # publish beat to MQTT
            if cfg.mqtt_telemetry:
                globs.telemetry.append(skew)
            if cfg.ui_btcut > 0:
                mqrt = globs.realtime.strftime(cfg.ui_btfmt)[:-cfg.ui_btcut]
                mqct = globs.clocktime.strftime(cfg.ui_btfmt)[:-cfg.ui_btcut]
                mqdt = '{0:.6f}'.format((globs.clocktime-globs.realtime).total_seconds())[:-cfg.ui_btcut]
            else:
                mqrt = globs.realtime.strftime(cfg.ui_btfmt)
                mqct = globs.clocktime.strftime(cfg.ui_btfmt)
                mqdt = '{0:.6f}'.format((globs.clocktime-globs.realtime).total_seconds())
            mqq.put(('clocktime',{
                'realtime' : mqrt,
                'clocktime' : mqct,
                'delta' : mqdt
            }))
    else:
        watchdog = Watchdog(cfg.p_timeout, pendulumTimeout)    # Start the watchdog
        globs.beatbanner = "[ Waiting for second beat ]"
        globs.clocktime = datetime.now()                      # CHANGE THIS once time assignment code exists
    prevArr = t
    if cfg.ui_showarrive: uiq.put((message, loglevel))
    watchdog.reset()                         # reset the watchdog timer

def avgdrift(drift):
    '''compute 1 minute, 1 hour, 24 hour drift'''
    if len(globs.driftavg) >= 864e8/cfg.p_period:
        globs.driftavg.pop(0)
    globs.driftavg.append(drift)
    drift1 = mean(globs.driftavg[int(-6e7/cfg.p_period):])       # 1 minute average drift (s/day)
    drift60 = mean(globs.driftavg[int(-36e8/cfg.p_period):])     # 1 hour average drift
    drift1440 = mean(globs.driftavg[int(-864e8/cfg.p_period):])  # 1 day average drift
    globs.driftbanner = "Drift Average: {:+.1f}, {:+.1f}, {:+.1f} s/day".format(drift1, drift60, drift1440)

def pendulumDepart(g, L, t):
    '''pendulumDepart(gpio, level, tick) - pendulum has left IR sensor gate

    '''
    global prevArr,prevDep
    delta = t-prevDep
    if delta < 0: delta += 4294967295       # counter wrapped
    if delta < cfg.p_min:                   # Absurd departure time, ignore
        uiq.put(('Absurd departure delta {} uS ignored.'.format(delta),'DEBUG'))
        return
    if prevArr == 0: return                    # Ignore departure if the first arrival has not been seen
    hz = cfg.p_period/delta
    skew = delta-cfg.p_period
    message = "pendulum departure at " + str(t)
    prevDep = t
    if cfg.ui_showdepart: uiq.put((message, 'INFO'))
    if cfg.db_engine: dbq.put((0, delta, hz, skew))
    if cfg.mqtt_engine and cfg.mqtt_p_depart:
        mqq.put(('beatDepart',{ 'delta': delta, 'Hz': hz, 'skew': skew }))  # publish beat to MQTT

def pendulumD(pig):
    '''pendulum monitoring thread
    '''
    pig.set_mode(cfg.p_gpio_irsense_pin, pigpio.INPUT)
    pig.set_glitch_filter(cfg.p_gpio_irsense_pin, cfg.p_glitchfilter)
    global prevArr, prevDep, watchdog, pa, pd
    prevArr = 0
    prevDep = 0

    # Set a callback for every pendulum cross
    pig.set_pull_up_down(cfg.p_gpio_irsense_pin, pigpio.PUD_OFF)
    pd = pig.callback(cfg.p_gpio_irsense_pin, pigpio.RISING_EDGE, pendulumDepart)
    pa = pig.callback(cfg.p_gpio_irsense_pin, pigpio.FALLING_EDGE, pendulumArrive)

    uiq.put(('pendulum monitor thread initialised', 'DEBUG'))
