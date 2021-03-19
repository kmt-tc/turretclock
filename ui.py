# UI elements

import commander
from commander import Commander,Command
#import time
from datetime import datetime, timedelta, date
import urwid
import threading
import time
import re

import config as cfg
import globs
from globs import uiq

class cmds(Command):
    def do_set(self, *args):
        '''set/reset/display a configuration variable\nUsage: set <variable> [arguments]'''
        if len(args) == 1:
            uiq.put(('{} is set to \'{}\''.format(args[0], cfg.__dict__[args[0]])))
            return

    def do_echo(self, *args):
        '''echo - Just echoes all the arguments'''
        return ' '.join(args)

    def do_raise(self, *args):
        raise Exception('Somme Error')

    def do_resetdrift(self, *args):
        '''reset the drift statistics'''
        globs.driftavg = []
        uiq.put(('Drift statistics reset'))

    def do_db(self, *args):
        '''set/display database parameters
Usage: db [cmd] [args]
    where cmd/args are:
        (nothing)   display database engine status
        debug       display/set database debug output
            (none)  display database debug output status
            [0-3]   set database debug output level
'''
        if len(args) == 0:
            if cfg.db_engine: uiq.put(('Database storage is on'))
            else: uiq.put(('Database storage is off'))
        else:
            cmd = args[0].lower()
            if cmd == 'debug':
                if len(args) == 1: switchdebug('Database', 'db')
                else: switchdebug('Database', 'db', args[1])

#                    if cfg.ui_debug_db: uiq.put(('Database debug output is off'))
#                    else: uiq.put(('Database debug output is on'))
#                elif args[1].lower() == 'on':
#                    cfg.ui_debug_db = True
#                    uiq.put(('Database debug output is on'))
#                elif args[1].lower() == 'off':
#                    cfg.ui_debug_db = False
#                    uiq.put(('Database debug output is off'))
#                else:
#                    uiq.put(('ERROR: Database debug setting must be \'on\' or \'off\'', 'ERR'))
#                    return
            else:
                uiq.put(('ERROR: Invalid db command', 'ERR'))

    def do_env(self, *args):
        '''set/display environmental sensor parameters
Usage: env [cmd] [args]
where cmd/args are:
    (nothing)   display environmental sensor status
    debug       display/set environmental sensor debug output
        (none)  display environmental sensor debug output status
        [0-3]   set environmental sensor debug output level
'''
        if len(args) == 0:
            if cfg.env_engine:
                uiq.put(('Current temperature is {} C and humidity is {}%'.format(globs.temperature, globs.humidity)))
            else:
                uiq.put(('Environmental sensors disabled'))
        else:
            cmd = args[0].lower()
            if cmd == 'debug':
                if len(args) == 1: switchdebug('Environmental sensors', 'env')
                else: switchdebug('Environmental sensors', 'env', args[1])

    def do_pendulum(self, *args):
        '''set/display pendulum parameters
where cmd/args are:
    (nothing)       display pendulum sensor status
    arr[ive]        display pendulum arrival notification status
        [on|off]    set pendulum arrival notificions on or off
    dep[art]        display pendulum departure notification status
        [on|off]    set pendulum departure notifications on or off
    debug           display pendulum sensor debug output status
        [0-3]       set pendulum sensor debug output level
'''
        if len(args) == 0:
            pass                                        # CHANGE what's a good default output?
        else:
            cmd = args[0].lower()
            if cmd == 'debug':
                if len(args) == 1: switchdebug('Pendulum sensor', 'p')
                else: switchdebug('Pendulum sensor', 'p', args[1])
            elif cmd == 'arr' or cmd == 'arrive':
                if len(args) == 1:
                    if cfg.ui_showarrive: uiq.put(('Pendulum arrival notifications on'))
                    else: uiq.put(('Pendulum arrival notifications off'))
                    return
                elif str(args[1]).lower() == 'on': cfg.ui_showarrive = True
                elif str(args[1]).lower() == 'off': cfg.ui_showarrive = False
                else: uiq.put(('ERROR: Pendulum arrival notifications must be \'off\' or \'on\''), 'ERR')
                self.do_pendulum('arr')
            elif cmd == 'dep' or cmd == 'depart':
                if len(args) == 1:
                    if cfg.ui_showdepart: uiq.put(('Pendulum departure notifications on'))
                    else: uiq.put(('Pendulum departure notifications off'))
                    return
                elif str(args[1]).lower() == 'on': cfg.ui_showdepart = True
                elif str(args[1]).lower() == 'off': cfg.ui_showdepart = False
                else: uiq.put(('ERROR: Pendulum departure notifications must be \'off\' or \'on\''), 'ERR')
                self.do_pendulum('dep')
            else: uiq.put(('ERROR: Invalid pendulum command'))

    def do_clocktime(self, *args):
        '''set/display the (physical) clock time
Usage: clocktime            Display the current physical clock time
            ([HH:]MM|now)   Set the clock time on the next beat
'''
        if len(args) == 0:
            uiq.put(('Clock time is {}'.format(globs.clocktime.strftime(cfg.ui_btfmt)[:-cfg.ui_btcut])))
            return
        elif args[0].lower() == 'now':
            globs.clocktime = datetime.now()
        else:
            try:
                newclocktime = re.compile(r'((\d{1,2})?\D?(\d{2}))').search(args[0]).groups()
            except AttributeError:
                uiq.put(('ERROR: Time must be in format [HH:]MM','ERR'))
                return
            if newclocktime[1] is None: newclockhour = globs.clocktime.hour
            else:
                try:
                    newclockhour = int(newclocktime[1])
                    if newclockhour < 0 or newclockhour > 23:
                        raise ValueError
                except ValueError:
                    uiq.put(('ERROR: Hour must be 0-23','ERR'))
                    return
            try:
                newclockmin = int(newclocktime[2])
                if newclockmin < 0 or newclockmin > 59:
                    raise ValueError
            except ValueError:
                uiq.put(('ERROR: Minute must be 0-59','ERR'))
                return
            globs.clocktime = globs.clocktime.replace(hour=newclockhour, minute=newclockmin, second=0, microsecond=0)
        globs.newclocktime = datetime.now()

    def do_debug(self, *args):
        '''set/display the debug output level\nUsage: debug [0|1|2|3]'''
        if len(args) == 0:
            uiq.put(('Debug level is {}'.format(cfg.ui_debug)))
        else:
            try:
                newdbg = int(args[0])
                if newdbg < 0 or newdbg > 3:
                    raise ValueError
            except ValueError:
                uiq.put(('ERROR: Debug level must be 0-3','ERR'))
                return
            cfg.ui_debug = newdbg
            uiq.put(('Debug level set to {}'.format(cfg.ui_debug)))

def switchdebug(mname, mcode, mode=None):
    '''switch debug modes interactively'''
    if not mode:
        uiq.put(('{} debug output level is {}'.format(mname, cfg.ui_debuglevel[mcode])))
#        if cfg.ui_debuglevel[mcode]: uiq.put(('{} debug output is on'.format(mname)))
#        else: uiq.put(('{} debug output is off'.format(mname)))
        return
    else:
        try:
            newlevel = int(mode)
            if not 0 <= newlevel <= 3:
                raise ValueError
            cfg.ui_debuglevel[mcode] = newlevel
        except ValueError:
            uiq.put(('ERROR: {} debug setting must be 0-3'.format(mname), 'ERR'))

#    elif mode.lower() == 'on':
#        cfg.ui_debugmod[mcode] = True
#        switchdebug(mname, mcode)
#        uiq.put(('{} debug output is on'.format(mname)))
#    elif mode.lower() == 'off':
#        cfg.ui_debugmod[mcode] = False
#        globals()[varname] = False
#        uiq.put(('{} debug output is off'.format(mname)))
#    else:
#        uiq.put(('ERROR: {} debug setting must be \'on\' or \'off\''.format(mname), 'ERR'))
    switchdebug(mname, mcode)

def debug(msg, level=1):
    '''debugging output, level = debug level (default 1)'''
    try:
        if cfg.ui_debuglevel[threading.current_thread().name] >= level: uiq.put((msg, 'DEBUG'))
    except KeyError:                                        # This is necessary for when environment.py is called directly
        pass

def error(msg):
    '''error message - display and halt'''
    uiq.put((msg, 'ERR'))

def outputD(c):
    '''output def(c = commander handle)'''
    uiq.put(('UI thread initialised', 'DEBUG'))
    while True:
        updateUItime(c)
        if uiq.empty():
            time.sleep(cfg.ui_timeupdate)
        else:
            item = uiq.get()
            if type(item) == str: item = (item, 'NORMAL')         # No message priority was specified
#            if item[1] == 'DEBUG':
#                try: item[2]
#                except IndexError:
#                    item = (*item, 1)                            # Default to debug level 1
#                if type(item[2]) != int:
#                    uiq("Invalid debug level encountered", 'ERR')
#                elif cfg.ui_debug < item[2]:                        # Debug level is too low to show this item
#                    continue
            if cfg.ui_ts:
                ts = datetime.now().strftime(cfg.ui_tsfmt)[:-cfg.ui_tscut] + " - "  # Format timestamp
                item = (ts + item[0].replace('\n', '\n' + ' '*len(ts)), item[1])    # Add timestamp and spaces to align multiline output
            c.output(item[0],cfg.ui_colors[item[1]])

def updateUItime(c):
    '''update the times in the status bar
    '''
    headertext = '{0}\n\nReal Time: {1} >> {2:^+8.3f}s >> Clock Time: {3}\n{4}\n{5}\nTemperature: {6} C - Humidity {7}%\n'.format(
            cfg.ui_banner,
            globs.realtime.strftime(cfg.ui_btfmt)[:-cfg.ui_btcut],
            (globs.clocktime-globs.realtime).total_seconds(),
            globs.clocktime.strftime(cfg.ui_btfmt)[:-cfg.ui_btcut],
            globs.beatbanner,
            globs.driftbanner,
            globs.temperature,
            globs.humidity
    )
    c.header=urwid.Text(headertext, align='center')
    c.header=urwid.AttrWrap(c.header, 'reversed')
#    threading.Timer(cfg.ui_timeupdate, updateUItime, args=[c]).start()
