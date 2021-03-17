#!/usr/bin/env python3

# =============================================================================
# System imports
import argparse
import configparser
import logging
import logging.config
import os
import time
import yaml

# =============================================================================
# Local imports
from chronosoft8puppet import GPIO

# =============================================================================
# Logger setup
logger = logging.getLogger(__name__)

# =============================================================================
# Globals
_config_path = os.path.join( os.path.dirname(os.path.realpath(__file__))
                           , 'config' )

# =============================================================================
# Class
class Chronosoft8Puppet:
    def __init__(self):
        # Load configuration
        config_file = os.path.join( _config_path
                                  , 'chronosoft8-puppet.ini')
        config = configparser.ConfigParser()
        config.read( config_file )

        try:
            return_gpio_channel   = int(config['GPIO']['return'])
            validate_gpio_channel = int(config['GPIO']['validate'])
            up_gpio_channel       = int(config['GPIO']['up'])
            stop_gpio_channel     = int(config['GPIO']['stop'])
            down_gpio_channel     = int(config['GPIO']['down'])
        except KeyError:
            logger.error('Missing parameter(s) in configuration file {}'.format(config_file))
            raise
        except ValueError:
            logger.error('Invalid parameter value in configuration file {}'.format(config_file))
            raise

        active_high = True
        try:
            active_low = config['GPIO']['active_low']
        except:
            pass

        if active_low:
            active_high = False

        # Setup GPIOs
        self._btn_ret  = GPIO( "Return"  , return_gpio_channel  , GPIO.OUT, 0, active_high=active_high)
        self._btn_val  = GPIO( "Validate", validate_gpio_channel, GPIO.OUT, 0, active_high=active_high)
        self._btn_up   = GPIO( "Up"      , up_gpio_channel      , GPIO.OUT, 0, active_high=active_high)
        self._btn_stop = GPIO( "Stop"    , up_gpio_channel      , GPIO.OUT, 0, active_high=active_high)
        self._btn_down = GPIO( "Down"    , up_gpio_channel      , GPIO.OUT, 0, active_high=active_high)

    def start(self):
        time.sleep(1)
        self._btn_ret.set(True)
        self._btn_val.set(True)
        time.sleep(0.05)
        self._btn_val.set(False)
        time.sleep(1)
        self._btn_ret.set(False)

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
