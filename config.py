# configuration file for turretclock.py

##### IR sensor settings #####

# GPIO settings
p_gpio_irsense_pin = 4          # GPIO pin for IR sensor
p_glitchfilter = 50             # GPIO glitch filter time in ms  (def: 50)

# Pendulum settings
p_period = 2e6                  # Target pendulum period in uS  (def: 2000000 (2 s))
p_offset = 0                    # Expected offset (known error) relative to target period
p_tolerance1 = 300              # "Fair" tolerance in uS (def: 300)
p_tolerance2 = 600              # "Poor" tolerance in uS (def: 600)
p_min = 1900000                 # Minimum pendulum delta time in uS (to ignore obvious bad data)
p_timeout = 2.5                 # Pendulum timeout in seconds  (def: 2.5)
p_timeoutrpt = 5                # How many timeouts before giving up?  (def: 5)
p_timeoutcmd = 'timeout.sh'     # Command to execute when p_timeoutrpt timeouts elapse


##### UI settings #####

ui_banner = ' -= Tehdassaari HQ Turret Clock Command =- '     # Banner for title bar
ui_showarrive = True            # Show pendulum arrivals?  (def: True)
ui_showdepart = False           # Show pendulum departures?  (def: False)
ui_ts = True                    # Timestamp UI output?  (def: True)
ui_tsfmt = "%H:%M:%S.%f"        # Timestamp format (strftime)  (def: "%H:%M:%S.%f")
ui_tscut = 3                    # Trim this many characters off the timestamp (def: 3)
ui_btfmt = "%H:%M:%S.%f"        # Banner time format (strftime)  (def: "%H:%M:%S.%f")
ui_btcut = 3                    # Trim this many characters off the banner times (def: 3)
ui_timeupdate = 1               # UI time display update frequency (def: 1)
ui_debug = 3                    # Debug output level (def: 0)
#ui_debug_db = False             # Database thread debug on/off
#ui_debug_env = True             # Environmental thread debug on/off
ui_debuglevel = {               # Debug levels for individual modules
        'db' : 1,               # Database module
        'env' : 3,              # Environmental monitoring module
        'p' : 1,                # Pendulum sensor module
}

ui_colors = {
        'DEBUG' : 'blue',       # Color for debug output (def: blue)
        'INFO' : 'green',       # Color for info output (def: normal)
        'WARN' : 'yellow',      # Color for warning output (def: yellow)
        'ERR' : 'error',        # Color for error output (def: error)
        'NORMAL' : 'normal',    # Color for normal (command) output (def: normal)
}


##### Database settings #####

db_engine = True                # Store beat data in database?
db_file = "turretclock.sqlite3" # Database filename (created if not present) (def: "/tmp/turretclock.sqlite3")



##### Environmental monitor settings #####

env_engine = True               # Measure the environment?
env_i2cbus = 1                  # Which I2C bus is the sensor on? (def: 1)
env_frequency = 30              # Measure environment this freuqnently (s) (def: 30)
env_delay = 0.1                 # Read delay for environment sensor (s) (def: 0.5)
env_attempts = 5                # Try to read the sensor this many times before giving up (def: 5)
env_maxtemp = 50                # Maximum temperatrure permitted (c) (def: 50)
env_mintemp = -40               # Minimum temperature permitted (c) (def: -40)
env_maxhum = 90                 # Maximum relative humidity permitted (%) (def: 90)
env_minhum = 30                 # Minimum relative humidity permitted (%) (def: 30)



##### Stats script settings #####

stats_interval = 5              # Interval about which stats script should report (min) (def: 5)

