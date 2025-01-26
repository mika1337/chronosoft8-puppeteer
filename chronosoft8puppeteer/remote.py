#!/usr/bin/env python3

# =============================================================================
# System imports
import logging
import time

# =============================================================================
# Local imports
from chronosoft8puppeteer import GPIO,Parameters

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

    def __init__( self, config, shutters ):
        # Process main configuration
        try:
            # GPIO configuration
            return_gpio_channel   = int(config['gpio']['pins']['return'])
            validate_gpio_channel = int(config['gpio']['pins']['validate'])
            up_gpio_channel       = int(config['gpio']['pins']['up'])
            stop_gpio_channel     = int(config['gpio']['pins']['stop'])
            down_gpio_channel     = int(config['gpio']['pins']['down'])
            power_gpio_channel    = int(config['gpio']['pins']['power'])
        except KeyError:
            logger.error('Missing parameter(s) in main configuration file')
            raise
        except ValueError:
            logger.error('Invalid parameter value in main configuration file')
            raise

        active_high = True
        try:
            active_low = config['gpio']['config']['active_low']
        except:
            pass
        else:
            if active_low:
                active_high = False

        self._debug = False
        if 'debug' in config:
            self._debug = config['debug']

        # Process shutters configuration
        try:
            # Shutter/channel configuration
            self._shutters = dict()
            self._channel_list = list()
            for shutter in shutters:
                channel = int(shutter['channel'])
                if channel < 1 or channel > 8:
                    raise ValueError('Channel must be between 1 and 8')
                if channel in self._channel_list:
                    raise ValueError('Duplicate channel {}'.format(channel))
                self._channel_list.append(channel)
                self._shutters[shutter['name']] = shutter

            self._channel_list.sort()
            if len(self._channel_list) == 0:
                raise ValueError('No channel configured')

            if 1 not in self._channel_list:
                raise ValueError('Channel 1 must be configured')
        except KeyError:
            logger.error('Missing parameter(s) in shutters configuration file')
            raise
        except ValueError:
            logger.error('Invalid parameter value in shutters configuration file')
            raise

        # Setup GPIOs
        self._buttons = dict()
        self._buttons['return']   = GPIO( "Return"  , return_gpio_channel  , GPIO.OUT, 0, active_high=active_high, debug=self._debug)
        self._buttons['validate'] = GPIO( "Validate", validate_gpio_channel, GPIO.OUT, 0, active_high=active_high, debug=self._debug)
        self._buttons['up']       = GPIO( "Up"      , up_gpio_channel      , GPIO.OUT, 0, active_high=active_high, debug=self._debug)
        self._buttons['stop']     = GPIO( "Stop"    , stop_gpio_channel    , GPIO.OUT, 0, active_high=active_high, debug=self._debug)
        self._buttons['down']     = GPIO( "Down"    , down_gpio_channel    , GPIO.OUT, 0, active_high=active_high, debug=self._debug)
        self._relay_power         = GPIO( "Power"   , power_gpio_channel   , GPIO.OUT, 0, active_high=active_high, debug=self._debug)

        self._last_btn_press_date = 0

    def start( self ):
        if self._debug == True:
            logger.warn('Debug enabled, not powering up remote')
        else:
            logger.debug('Waiting in case remote was powered on startup')
            self._relay_power.set(0)
            time.sleep(1)

            logger.info('Powering up remote')
            self._relay_power.set(1)
            self._last_btn_press_date = time.time()
            time.sleep(Parameters.remote_boot_duration)
            self._press_button( self.BTN_VALIDATE )
            self._press_button( self.BTN_VALIDATE )

            # Sometimes the remote seems to boot with hour already set, in this case the preceeding validate button
            # double press would lead to no being on main screen. Double press on return button let us return to
            # main screen in all situation
            self._press_button( self.BTN_RETURN )
            self._press_button( self.BTN_RETURN )
            time.sleep(Parameters.remote_boot_duration)

            logger.info('Configuring {} channels'.format(len(self._channel_list)))
            # Disable all channels (the first can't be disabled, but will be reinitialised)
            self._press_button( self.BTN_VALIDATE, press_duration=3 )
            for channel in range( 8 ):
                self._press_button( self.BTN_DOWN )
                self._press_button( self.BTN_VALIDATE )

            # Enable selected channels
            self._press_button( self.BTN_VALIDATE, press_duration=3 )
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
        self._relay_power.set(0)

    def drive_shutter( self, shutter, command ):
        if shutter not in self._shutters:
            logger.error('Can\'t drive unknown shutter {}'.format(shutter))
            return
        channel = self._shutters[shutter]['channel']

        # Change channel to targeted
        if self._channel_list[self._current_channel_index] != channel:
            logger.info('Changing channel {} => {}'.format(self._channel_list[self._current_channel_index],channel))
            while self._channel_list[self._current_channel_index] != channel:
                self._press_button(self.BTN_RETURN)
                self._current_channel_index = self._current_channel_index + 1
                if self._current_channel_index >= len(self._channel_list):
                    self._current_channel_index = 0

        # Check if override exists for current shutter
        try:
            commands = self._shutters[shutter]['override'][command]
        except:
            commands = [command,]

        for command in commands:
            if command == self.CMD_UP:
                logger.info('Sending channel {} {} order'.format(channel,command))
                self._press_button( self.BTN_UP
                                  , press_duration  =Parameters.remote_cmd_button_press_duration
                                  , release_duration=Parameters.remote_cmd_button_release_duration )
            elif command == self.CMD_DOWN:
                logger.info('Sending channel {} {} order'.format(channel,command))
                self._press_button( self.BTN_DOWN
                                  , press_duration  =Parameters.remote_cmd_button_press_duration
                                  , release_duration=Parameters.remote_cmd_button_release_duration )
            elif command == self.CMD_STOP:
                logger.info('Sending channel {} {} order'.format(channel,command))
                self._press_button( self.BTN_STOP
                                  , press_duration  =Parameters.remote_cmd_button_press_duration
                                  , release_duration=Parameters.remote_cmd_button_release_duration )
            elif command == self.CMD_INT:
                logger.info('Sending channel {} {} order'.format(channel,command))
                self._press_button( self.BTN_STOP,self.BTN_DOWN
                                  , press_duration  =Parameters.remote_cmd_button_press_duration
                                  , release_duration=Parameters.remote_cmd_button_release_duration )
            elif command.startswith('wait '):
                seconds = float(command.split(' ')[1])
                logger.info('Waiting {} seconds for channel {}'.format(seconds,channel))
                time.sleep(seconds)
            else:
                logger.error('Unknown command {}'.format(command))

    def _press_button( self, *args, **kwargs ):
        # Check if remote is sleeping
        now = time.time()
        if now - self._last_btn_press_date > Parameters.remote_sleep_timer_duration - Parameters.remote_sleep_timer_margin:
            if now - self._last_btn_press_date < Parameters.remote_sleep_timer_duration:
                time.sleep(Parameters.remote_sleep_timer_margin)
            logger.debug('Waking remote from sleep')
            self._buttons[self.BTN_VALIDATE].set(1)
            time.sleep(Parameters.remote_wake_button_press_duration)
            self._buttons[self.BTN_VALIDATE].set(0)
            time.sleep(Parameters.remote_wake_button_release_duration)

        press_duration   = Parameters.remote_menu_button_press_duration
        release_duration = Parameters.remote_menu_button_release_duration
        # Grab duration from parameters
        if 'press_duration' in kwargs:
            press_duration = kwargs['press_duration']
        if 'release_duration' in kwargs:
            release_duration = kwargs['release_duration']

        # Drive buttons
        for btn in args:
            self._buttons[btn].set(1)
        time.sleep(press_duration)
        for btn in args:
            self._buttons[btn].set(0)
        self._last_btn_press_date = time.time()
        time.sleep(release_duration)
