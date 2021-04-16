# =============================================================================
# System imports
import astral
import astral.sun
import datetime
import json
import logging
import os
import re
import threading

# =============================================================================
# Logger setup
logger = logging.getLogger(__name__)

# =============================================================================
# Globals
# =============================================================================
# Globals
run_dir = os.path.dirname(os.path.realpath(__file__))
location_config_file = os.path.join(run_dir,'config','location.json')
programs_config_file = os.path.join(run_dir,'config','programs.json')
weekdays = ('mon','tue','wed','thu','fri','sat','sun')

cs8p = None
functions = dict()
location_info = None
programs_config = None
timers = list()

# =============================================================================
# Functions
def init_plugin(cs8p_):
    global cs8p,functions

    logger.info('Initializing scheduling plugin')
    cs8p = cs8p_
    functions['mean'] = compute_mean

    load_config()

def load_config():
    global location_info,programs_config

    # Load location configuration
    try:
        location_config = json.load(open(location_config_file))
    except:
        logger.exception('Failed to load location config file {}'.format(location_config))
    else:
        # Check config file
        if 'location' not in location_config:
            logger.error('Missing location entry in config file {}'.format(location_config))
        elif 'latitude' not in location_config['location'] or 'longitude' not in location_config['location']:
            logger.error('Missing latitude and/or longitude entry in config file {}'.format(location_config))
        else:
            latitude  = float(location_config['location']['latitude'])
            longitude = float(location_config['location']['longitude'])
            location_info = astral.LocationInfo('Name','Region',"Time zone",latitude,longitude)

    # Load programs
    try:
        programs_config = json.load(open(programs_config_file))
    except:
        logger.exception('Failed to load config file {}'.format(programs_config_file))
        programs = None
    else:
        if 'programs' not in programs_config:
            logger.error('Missing programs entry in config file {}'.format(programs_config_file))
            programs_config = None

def start_plugin():
    logger.info('Starting scheduling plugin')

    schedule()

def stop_plugin():
    global timers

    logger.info('Stopping scheduling plugin')

    for timer in timers:
        timer.cancel()
    timers.clear()

def get_programs():
    return programs_config['programs']

def set_programs(programs):
    programs_config['programs'] = programs
    schedule()
    json.dump({'programs':programs},open(programs_config_file,'w'),indent=4)

def schedule():
    global timers

    for timer in timers:
        timer.cancel()
    timers.clear()

    if location_info == None or programs_config == None:
        logger.error('Error while loading config file, plugin won\'t start')
    else:
        active_programs = list()
        current_day = weekdays[datetime.date.today().weekday()]
        logger.debug('Current days is {}'.format(current_day))

        for program in programs_config['programs']:
            # Check if enable
            if program['enable'] == False:
                logger.debug('Program {} not scheduled: disabled'.format(program['name']))
                continue

            # Check if program is for today
            if current_day not in program['days']:
                logger.debug('Program {} not scheduled: not for today'.format(program['name']))
                continue

            # Check if program is in the future
            program_date = get_program_date(program['time'])
            now = datetime.datetime.now(program_date.tzinfo)
            delta = program_date - now
            delta_seconds = delta.total_seconds()
            if delta_seconds < 0:
                logger.debug('Program {} not scheduled: in the past (date was {})'.format(program['name'],program_date))
                continue

            # Schedule program
            logger.info('Program {} scheduled at {}'.format(program['name'],program_date.astimezone()))
            timer = threading.Timer(delta_seconds,execute_command, [program['name'],program['shutters'],get_program_command(program['action'])] )
            timer.start()
            timers.append( timer )

    # Schedule next day scheduling
    now = datetime.datetime.now()
    date = now.replace( hour=0, minute=1,second=0,microsecond=0 )
    tomorrow = date + datetime.timedelta(days=1)
    delta = tomorrow - now
    delta_seconds = delta.total_seconds()

    logger.info('Scheduling next day scheduling')
    timer = threading.Timer(delta_seconds,schedule)
    timer.start()
    timers.append( timer )

def execute_command(program_name, shutters, command):
    logger.info('Running {} for shutters {} with command {}'.format(program_name,shutters,command))
    for shutter in shutters:
        cs8p.drive_shutter( shutter, command )

def get_program_command( event ):
    if event == 'open':
        return cs8p.CMD_UP
    elif event == 'close':
        return cs8p.CMD_DOWN
    elif event.startswith('int'):
        return cs8p.CMD_INT

def get_program_date( param ):
    if param.startswith('='):
        match = re.search( '^=([^(]*)\(([^,]*),([^)]*)\)$', param )
        if match == None:
            logger.error('Failed to parse date "{}"'.format(param))
        else:
            function_name = match.group(1)
            param1        = match.group(2)
            param2        = match.group(3)

            date1 = get_program_date(param1)
            date2 = get_program_date(param2)
        return functions[function_name](date1,date2)

    if param in ('dawn','sunrise','noon','sunset','dusk'):
        td = datetime.datetime.today()
        return astral.sun.sun(location_info.observer,date=datetime.datetime.today())[param]

    else:
        today = datetime.date.today()
        date = datetime.datetime.strptime(param,'%H:%M')
        date = date.replace( year=today.year, month=today.month, day=today.day)
        return date

def compute_mean(date1,date2):
    if date1 < date2:
        min_date = date1
        max_date = date2
    else:
        min_date = date2
        max_date = date1

    delta = date2 - date1
    return date1 + (delta/2)