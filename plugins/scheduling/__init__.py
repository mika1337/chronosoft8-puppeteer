# =============================================================================
# System imports
import astral
import astral.sun
import datetime
import json
import logging
import os
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
location_info = None
programs_config = None
timers = list()

# =============================================================================
# Functions
def init_plugin(cs8p_):
    global cs8p

    logger.info('Initializing scheduling plugin')
    cs8p = cs8p_

    load_config()

def load_config():
    global location_info,programs_config

    # Load location configuration
    try:
        location_config = json.load(open(location_config_file))
    except:
        logger.exception('Failed to load location config file %s',location_config_file)
    else:
        # Check config file
        if 'location' not in location_config:
            logger.error('Missing location entry in config file %s',location_config)
        elif 'latitude' not in location_config['location'] or 'longitude' not in location_config['location']:
            logger.error('Missing latitude and/or longitude entry in config file %s',location_config)
        else:
            latitude  = float(location_config['location']['latitude'])
            longitude = float(location_config['location']['longitude'])
            location_info = astral.LocationInfo('Name','Region',"Time zone",latitude,longitude)

    # Load programs
    try:
        programs_config = json.load(open(programs_config_file))
    except:
        logger.exception('Failed to load config file %s',programs_config_file)
    else:
        if 'programs' not in programs_config:
            logger.error('Missing programs entry in config file %s',programs_config_file)

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
    if programs_config is None or 'programs' not in programs_config:
        return None
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

    if location_info is None or programs_config is None:
        logger.error('Error while loading config file, plugin won\'t start')
    else:
        current_day = weekdays[datetime.date.today().weekday()]
        logger.debug('Current days is %s',current_day)

        for program in programs_config['programs']:
            # Check if enable
            if program['enable'] is False:
                logger.debug('Program %s not scheduled: disabled',program['name'])
                continue

            # Check if program is for today
            if current_day not in program['days']:
                logger.debug('Program %s not scheduled: not for today',program['name'])
                continue

            # Check if program is in the future
            program_date = get_program_date(program['trigger'])
            now = datetime.datetime.now(program_date.tzinfo)
            delta = program_date - now
            delta_seconds = delta.total_seconds()
            if delta_seconds < 0:
                logger.debug('Program %s not scheduled: in the past (date was %s)',program['name'],program_date.astimezone())
                continue

            # Schedule program
            logger.info('Program %s scheduled at %s',program['name'],program_date.astimezone())
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
    logger.info('Running %s for shutters %s with command %s',program_name,shutters,command)
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
    if param['source'] == 'time':
        time = param['time']
        today = datetime.date.today()
        date = datetime.datetime.strptime(time,'%H:%M')
        date = date.replace( year=today.year, month=today.month, day=today.day)
        return date

    elif param['source'] == 'sun':
        event = param['event']
        offset = 0
        try:
            offset = int(param['offset'])
        except:
            pass

        if event in ('dawn','sunrise','noon','sunset','dusk'):
            td = datetime.datetime.today()
            return astral.sun.sun(location_info.observer,date=datetime.datetime.today())[event] + datetime.timedelta(minutes=offset)
        else:
            logger.error('Unsupported sun event "%s"',event)
            return datetime.datetime.datetime(1900,1,1)

    else:
        logger.error('Unsupported trigger source "%s"',param['source'])
        return datetime.datetime.datetime(1900,1,1)

