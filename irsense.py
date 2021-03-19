import pigpio
from queue import Queue
import os
from datetime import timedelta, datetime
from statistics import mean

import config as cfg
from commander import Commander,Command
from defs import Watchdog
import globs
from globs import dbq, uiq

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
        if isinstance(globs.newclocktime, datetime):           # clocktime was just run
            globs.clocktime += globs.realtime-globs.newclocktime # add only a partial beat
            uiq.put(('Clock time set to {}'.format(globs.clocktime.strftime(cfg.ui_btfmt)[:-cfg.ui_btcut])))
            globs.newclocktime = None
        else:
            globs.clocktime += timedelta(microseconds=cfg.p_period)    # add one pendlum period to the clock time
        hz = cfg.p_period/delta                                 # Compute pendulum frequency (Hz)
        drift = 86400*(1-1/hz)                                  # Comput drift (s/day)
        avgdrift(drift)                                         # Build the drift averages
        beatstats = "{:+} uS / {:.4f} Hz / {:.1f} BPH / {:+.1f} s/day".format(int(skew), hz, 3600*hz, drift)
        message += " ({})".format(beatstats)
        globs.beatbanner = "[ {} ]".format(beatstats)
        if cfg.db_engine: dbq.put((1, delta, hz, skew))           # store the database entry
    else:
        watchdog = Watchdog(cfg.p_timeout, pendulumTimeout)    # Start the watchdog
        globs.beatbanner = "[ Waiting for second beat ]"
        globs.clocktime = datetime.now()                      # CHANGE THIS once time assignment code exists
    prevArr = t
    if cfg.ui_showarrive: uiq.put((message, loglevel))
    watchdog.reset()                         # reset the watchdog timer

def avgdrift(drift):
    '''compute 1 minute, 1 hour, 24 hour drift'''
    if len(globs.driftavg) == 864e8/cfg.p_period: globs.driftavg.pop(0)
    globs.driftavg.append(drift)
    drift1 = mean(globs.driftavg[int(-6e7/cfg.p_period):])       # 1 minute average drift (s/day)
    drift60 = mean(globs.driftavg[int(-36e8/cfg.p_period):])     # 1 hour average drift
    drift1440 = mean(globs.driftavg)                        # 1 day average drift
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
