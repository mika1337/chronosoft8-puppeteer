# =============================================================================
# System imports
import astral
import astral.sun
import datetime
import json
import logging
import os
import re
import pytz.reference
import threading

# =============================================================================
# Logger setup
logger = logging.getLogger(__name__)

# =============================================================================
# Globals
# =============================================================================
# Globals
run_dir = os.path.dirname(os.path.realpath(__file__))
config_file = os.path.join(run_dir,'config','scheduling.json')
weekdays = ('mon','tue','wed','thu','fri','sat','sun')

cs8p = None
config = None
functions = dict()
location_info = None
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
    global config,location_info

    try:
        # Load configuration
        config = json.load(open(config_file))
    except:
        logger.exception('Failed to load config file {}'.format(config_file))
        config = None
    else:
        # Check config file
        if 'location' not in config:
            logger.error('Missing location entry in config file {}'.format(config_file))
            config = None
        elif 'latitude' not in config['location'] or 'longitude' not in config['location']:
            logger.error('Missing latitude and/or longitude entry in config file {}'.format(config_file))
            config = None
        elif 'scheduling' not in config:
            logger.error('Missing scheduling entry in config file {}'.format(config_file))
            config = None
        elif 'enable' not in config['scheduling'] or 'programs' not in config['scheduling'] or 'channels' not in config['scheduling']:
            logger.error('Missing programs and/or channel entry in config file {}'.format(config_file))
            config = None
        
        latitude  = float(config['location']['latitude'])
        longitude = float(config['location']['longitude'])
        tzname = pytz.reference.LocalTimezone().tzname(datetime.datetime.now())
        location_info = astral.LocationInfo('Name','Region',tzname,latitude,longitude)

def start_plugin():
    logger.info('Starting scheduling plugin')

    schedule()

def stop_plugin():
    global timers

    logger.info('Stopping scheduling plugin')

    for timer in timers:
        timer.cancel()
    timers.clear()

def schedule():
    global timers

    for timer in timers:
        timer.cancel()
    timers.clear()

    if config == None:
        logger.error('Error while loading config file, plugin won\'t start')
    elif config['scheduling']['enable'] == False:
        logger.info('Scheduling disabled in config file')
    else:
        active_schedules = dict()
        current_day = weekdays[datetime.date.today().weekday()]
        logger.debug('Current days is {}'.format(current_day))

        for channels in config['scheduling']['channels']:
            channel_list = channels.split(',')

            for days in config['scheduling']['channels'][channels]:
                if current_day in days.split(','):
                    for program in config['scheduling']['channels'][channels][days]:
                        if program not in active_schedules:
                            active_schedules[program] = { 'channels' : list() }
                        active_schedules[program]['channels'].extend(channel_list)

        # Get schedule parameters
        for program in active_schedules:
            program_content = get_program_content(config['scheduling']['programs'][program])
            active_schedules[program]['date'] = program_content['date']
            active_schedules[program]['cmd']  = program_content['cmd']
        logger.debug('Today active schedules: {}'.format(active_schedules))

        # Schedule timers
        for program,data in active_schedules.items():
            program_date = data['date']
            now = datetime.datetime.now(program_date.tzinfo)
            delta = program_date - now
            delta_seconds = delta.total_seconds()
            if delta_seconds < 0:
                logger.info('Not scheduling {} as it is in the past'.format(program))
            else:
                logger.info('Scheduling {} for channels {} with cmd {} at {}'.format(program,data['channels'],data['cmd'],program_date.astimezone()))
                timer = threading.Timer(delta_seconds,execute_cmd, [program,data['channels'],data['cmd']] )
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

def execute_cmd(program, channels, cmd):
    logger.info('Running {} for channels {} with cmd {}'.format(program,channels,cmd))
    for channel in channels:
        cs8p.drive_channel( channel, cmd )

def get_program_content( program ):
    if 'event' in program and 'time' in program:
        program_content = dict()
        program_content['cmd']  = get_event_command(program['event'])
        program_content['date']  = get_event_date(program['time'])
        return program_content

def get_event_command( event ):
    if event == 'open':
        return cs8p.CMD_UP
    elif event == 'close':
        return cs8p.CMD_DOWN
    elif event.startswith('int'):
        return cs8p.CMD_INT

def get_event_date( param ):
    if param.startswith('='):
        match = re.search( '^=([^(]*)\(([^,]*),([^)]*)\)$', param )
        if match == None:
            logger.error('Failed to parse date "{}"'.format(param))
        else:
            function_name = match.group(1)
            param1        = match.group(2)
            param2        = match.group(3)

            date1 = get_event_date(param1)
            date2 = get_event_date(param2)
        return functions[function_name](date1,date2)

    if param in ('dawn','sunrise','noon','sunset','dusk'):
        return astral.sun.sun(location_info.observer)[param]

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