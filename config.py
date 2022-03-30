# configuration file for turretclock.py

##### General #####

ntpdriftfile = '/var/lib/ntp/ntp.drift'   # ntpd drift file (for oscillator drift adjustment)
ntpdriftint = 5                 # Polling interval for ntp drift file in seconds (def: 5)
statefile = '/run/turretclock/turretclock.state'    # State save file
stateint = 60                   # State file save interval in seconds (def: 60)


##### IR sensor settings #####

# GPIO settings
p_gpio_irsense_pin = 4          # GPIO pin for IR sensor
p_glitchfilter = 50             # GPIO glitch filter time in ms  (def: 50)

# Pendulum settings
p_period = 2e6                  # Target pendulum period in uS  (def: 2000000 (2 s))
p_offset = 0                    # Expected offset (known error) relative to target period
p_tolerance1 = 300              # "Fair" tolerance in uS (def: 300)
p_tolerance2 = 600              # "Poor" tolerance in uS (def: 600)
p_maxskew = 5000                # Maximum absolute value skew in uS (to ignore obvious bad data)
p_timeout = 2.5                 # Pendulum timeout in seconds  (def: 2.5)
p_timeoutrpt = 5                # How many timeouts before giving up?  (def: 5)
p_timeoutcmd = 'timeout.sh'     # Command to execute when p_timeoutrpt timeouts elapse


##### UI settings #####

ui_banner = ' -= HQ Turret Clock Command =- '     # Banner for title bar
ui_showarrive = True            # Show pendulum arrivals?  (def: True)
ui_showdepart = False           # Show pendulum departures?  (def: False)
ui_ts = True                    # Timestamp UI output?  (def: True)
ui_tsfmt = "%H:%M:%S.%f"        # Timestamp format (strftime)  (def: "%H:%M:%S.%f")
ui_tscut = 3                    # Trim this many characters off the timestamp (def: 3)
ui_btfmt = "%H:%M:%S.%f"        # Banner time format (strftime)  (def: "%H:%M:%S.%f")
ui_btcut = 3                    # Trim this many characters off the banner times (def: 3)
ui_timeupdate = 1               # UI time display update frequency (def: 1)
ui_debug = 3                    # Debug output level (def: 0)
ui_debuglevel = {               # Debug levels for individual modules
        'db' : 1,               # Database module
        'env' : 1,              # Environmental monitoring module
        'p' : 2,                # Pendulum sensor module
        'mqtt' : 1,             # MQTT module
        'lightsense' : 3,       # Light sensor module
}
ui_colors = {                   # UI colours
        'DEBUG' : 'blue',       # Color for debug output (def: blue)
        'INFO' : 'green',       # Color for info output (def: normal)
        'WARN' : 'yellow',      # Color for warning output (def: yellow)
        'ERR' : 'error',        # Color for error output (def: error)
        'NORMAL' : 'normal',    # Color for normal (command) output (def: normal)
}


##### Database settings #####

db_engine = True                # Store beat data in database?
db_file = "/run/turretclock/turretclock.sqlite3" # Database filename (created if not present) (def: "/tmp/turretclock.sqlite3")
db_stats_interval = 5           # snmpstats.py reports statistics for this many mionutes (def: 5)
db_dump_interval = 10080        # dbclean.py drops data older than this many minutes (def: 10080 (1 week))


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
env_humskew = 10                # Maximum allowed humidity change between readings (def: 10)
env_tempskew = 10               # Maximum allowed temperature change between readings (def: 10)


##### MQTT settings #####

mqtt_engine = True              # Publish to an MQTT broker?
mqtt_broker = 'localhost'       # Hostname or IP address of MQTT broker to connect to (def: localhost)
mqtt_port = 1883                # MQTT port number (def: 1883)
mqtt_keepalive = 60             # MQTT keepalive interval (def: 60)
mqtt_topicbase = 'turretclock'  # MQTT topic base (def: turretclock)
mqtt_p_arrive = True            # Report pendulum arrivals? (def: True)
mqtt_p_depart = False           # Report pendulum departures? (def: False)
mqtt_telemetry = True           # Report periodic telemetry (def: True)
mqtt_telemetry_interval = 40    # Telemetry interval in seconds (def: 60)


##### Light sensor settings #####

light_engine = False             # Gather light sensor readings?
light_gpio_pin = 17             # GPIO pin for light sensor reads
light_keepreadings = 10         # Number of light sensor readings to store
light_read_interval = 5             # Interval between light sensor readings
light_store_interval = 60           # interval between writing light level average to data file
light_normalise = 70000             # normailise light level readings to this value
light_filename = '/run/turretclock/lightlevels' # File in which to store light level readings

