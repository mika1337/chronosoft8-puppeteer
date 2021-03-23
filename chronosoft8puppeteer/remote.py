#!/usr/bin/env python3

# =============================================================================
# System imports
import logging
import time

# =============================================================================
# Local imports
from chronosoft8puppeteer import GPIO

# =============================================================================
# Logger setup
logger = logging.getLogger(__name__)

# =============================================================================
# Class
class Remote:
    BTN_RETURN = 'return'
    BTN_VALIDATE = 'validate'
    BTN_UP = 'up'
    BTN_STOP = 'stop'
    BTN_DOWN = 'down'

    CMD_UP = 'up'
    CMD_DOWN = 'down'
    CMD_STOP = 'stop'
    CMD_INT  = 'int'

    def __init__( self, config ):
        # Load configuration
        try:
            # Channel configuration
            self._channel_list = list()
            for channel in config['Channels'].keys():
                channel = int(channel)
                if channel < 1 or channel > 8:
                    raise ValueError('Channel must be between 1 and 8')
                if channel in self._channel_list:
                    raise ValueError('Duplicate channel {}'.format(channel))
                self._channel_list.append(channel)

            self._channel_list.sort()
            if len(self._channel_list) == 0:
                raise ValueError('No channel configured')

            if 1 not in self._channel_list:
                raise ValueError('Channel 1 must be configured')

            # GPIO configuration
            return_gpio_channel   = int(config['GPIO']['return'])
            validate_gpio_channel = int(config['GPIO']['validate'])
            up_gpio_channel       = int(config['GPIO']['up'])
            stop_gpio_channel     = int(config['GPIO']['stop'])
            down_gpio_channel     = int(config['GPIO']['down'])
            power_gpio_channel    = int(config['GPIO']['power'])
        except KeyError:
            logger.error('Missing parameter(s) in configuration file')
            raise
        except ValueError:
            logger.error('Invalid parameter value in configuration file')
            raise

        active_high = True
        try:
            active_low = config['GPIO']['active_low']
        except:
            pass

        if active_low:
            active_high = False

        # Setup GPIOs
        self._buttons = dict()
        self._buttons['return']   = GPIO( "Return"  , return_gpio_channel  , GPIO.OUT, 0, active_high=active_high)
        self._buttons['validate'] = GPIO( "Validate", validate_gpio_channel, GPIO.OUT, 0, active_high=active_high)
        self._buttons['up']       = GPIO( "Up"      , up_gpio_channel      , GPIO.OUT, 0, active_high=active_high)
        self._buttons['stop']     = GPIO( "Stop"    , stop_gpio_channel    , GPIO.OUT, 0, active_high=active_high)
        self._buttons['down']     = GPIO( "Down"    , down_gpio_channel    , GPIO.OUT, 0, active_high=active_high)
        self._rly_power = GPIO( "Power"   , power_gpio_channel   , GPIO.OUT, 0, active_high=active_high)

        self._last_btn_press_date = 0

    def start( self, fast_init=False ):
        logger.debug('Waiting in case remote was powered on startup')
        time.sleep(1)

        logger.info('Powering up remote')
        self._rly_power.set(1)
        self._last_btn_press_date = time.time()
        time.sleep(2)
        self._press_button( self.BTN_VALIDATE )
        self._press_button( self.BTN_VALIDATE )

        # Sometimes the remote seems to boot with hour already set, in this case the preceeding validate button
        # double press would lead to no being on main screen. Double press on return button let us return to
        # main screen in all situation
        self._press_button( self.BTN_RETURN )
        self._press_button( self.BTN_RETURN )

        if fast_init == True:
            logger.warn('Fast init (no channel configuration)')
        else:
            logger.info('Configuring {} channels'.format(len(self._channel_list)))
            # Disable all channels (the first can't be disabled, but will be reinitialised)
            self._press_button( self.BTN_VALIDATE, duration=3 )
            for channel in range( 8 ):
                self._press_button( self.BTN_DOWN )
                self._press_button( self.BTN_VALIDATE )

            # Enable selected channels
            self._press_button( self.BTN_VALIDATE, duration=3 )
            for channel in range( 1, 9 ):
                if channel in self._channel_list:
                    self._press_button( self.BTN_UP )
                else:
                    self._press_button( self.BTN_DOWN )
                self._press_button( self.BTN_VALIDATE )

        self._current_channel_index = 0
        logger.info('Current channel is {}'.format(self._channel_list[self._current_channel_index]))

    def stop( self ):
        logger.info('Powering down remote')
        self._rly_power.set(0)

    def drive_channel( self, channel, command ):
        if channel not in self._channel_list:
            logger.error('Can\'t drive not configured channel {}'.format(channel))
            return

        # Change channel to targeted
        if self._channel_list[self._current_channel_index] != channel:
            logger.info('Changing channel {} => {}'.format(self._channel_list[self._current_channel_index],channel))
            while self._channel_list[self._current_channel_index] != channel:
                self._press_button(self.BTN_RETURN)
                self._current_channel_index = self._current_channel_index + 1
                if self._current_channel_index >= len(self._channel_list):
                    self._current_channel_index = 0

        logger.info('Sending channel {} {} order'.format(channel,command))
        if command == self.CMD_UP:
            self._press_button(self.BTN_UP,duration=0.5)
        elif command == self.CMD_DOWN:
            self._press_button(self.BTN_DOWN,duration=0.5)
        elif command == self.CMD_STOP:
            self._press_button(self.BTN_STOP,duration=0.5)
        elif command == self.CMD_INT:
            self._press_button(self.BTN_STOP,self.BTN_DOWN,duration=0.5)
        else:
            logger.error('Unknown command {}'.format(command))

    def get_channels(self):
        return self._channel_list

    def _press_button( self, *args, **kwargs ):
        # Check if remote is sleeping
        now = time.time()
        if now - self._last_btn_press_date > 14:
            if now - self._last_btn_press_date < 16:
                time.sleep(1)
            logger.debug('Waking remote from sleep')
            self._buttons[self.BTN_VALIDATE].set(1)
            time.sleep(0.1)
            self._buttons[self.BTN_VALIDATE].set(0)
            time.sleep(0.5)

        # Grab duration from parameters
        if 'duration' in kwargs:
            duration = kwargs['duration']
        else:
            duration=0.1

        # Drive buttons
        for btn in args:
            self._buttons[btn].set(1)
        time.sleep(duration)
        for btn in args:
            self._buttons[btn].set(0)
        self._last_btn_press_date = time.time()
        time.sleep(0.2)


# =============================================================================
# Main
if __name__ == '__main__':
    # -------------------------------------------------------------------------
    # Arg parse
    parser = argparse.ArgumentParser()
    parser.add_argument('-d','--dev', help='enable development logging', action='store_true')
    args = parser.parse_args()

    # -------------------------------------------------------------------------
    # Logging config
    config_path = os.path.join( os.path.dirname(os.path.realpath(__file__))
                              , 'config' )
    if args.dev:
        logging_conf_path = os.path.join( config_path, 'logging-dev.yaml' )
    else:
        logging_conf_path = os.path.join( config_path, 'logging-prod.yaml' )
    with open(logging_conf_path, 'rt') as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)

    # -------------------------------------------------------------------------
    logger.info('Chronosoft8 Puppet starting')

    cp = Chronosoft8Puppet()
    cp.start()

    logger.info('Chronosoft8 Puppet stopping')
