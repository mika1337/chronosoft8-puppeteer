#!/usr/bin/env python3

# =============================================================================
# System imports
import argparse
import json
import logging
import logging.config
import os
import queue
import yaml
from time import sleep

# =============================================================================
# Local imports
from chronosoft8puppeteer import Remote

# =============================================================================
# Logger setup
logger = logging.getLogger(__name__)

# =============================================================================
# Globals
config_path = os.path.join( os.path.dirname(os.path.realpath(__file__))
                           , 'config' )

# =============================================================================
# Class
class Chronosoft8Puppeteer:
    CMD_UP = 'up'
    CMD_DOWN = 'down'
    CMD_STOP = 'stop'
    CMD_INT  = 'int'
    CMD_SHUTDOWN = 'shutdown'

    def __init__(self):
        # Load main config
        main_config_file = os.path.join( config_path
                                       , 'chronosoft8-puppeteer.json')
        try:
            self._config = json.load(open(main_config_file))
        except:
            logger.error('Failed to load config file {}'.format(main_config_file))
            raise

        # Load shutters config
        shutters_config_file = os.path.join( config_path
                                           , 'shutters.json')
        try:
            shutters_config = json.load(open(shutters_config_file))
            self._shutters = shutters_config['shutters']
        except:
            logger.error('Failed to load config file {}'.format(shutters_config_file))
            raise

        # Debug
        self._debug = False
        if 'debug' in self._config:
            self._debug = self._config['debug']

        # Initialize remote object
        self._remote = Remote(self._config,self._shutters)

        # Read plugin list from config file
        try:
            plugin_names = self._config['plugins']
        except KeyError:
            logger.error('Missing active plugins in configuration file {}'.format(config_file))
            raise

        # Load plugins
        self._plugins = dict()
        for plugin_name in plugin_names:
            cmd = 'from plugins import {} as plugin_handle'.format(plugin_name)
            _locals = locals()
            exec(cmd,globals(),_locals)
            self._plugins[plugin_name] = _locals['plugin_handle']

        # Initialize command queue
        self._cmd_queue = queue.Queue()


    def get_shutters(self):
        return self._shutters

    def drive_shutter(self,shutter,command):
        self._cmd_queue.put( (shutter,command) )

    def get_programs(self):
        return self._plugins['scheduling'].get_programs()

    def set_programs(self,programs):
        return self._plugins['scheduling'].set_programs(programs)

    def start(self):
        # Initialize remote
        logger.info('Initializing remote')
        self._remote.start()

        # Initialize and start plugins
        for (plugin_name,plugin) in self._plugins.items():
            # Initialize plugin
            plugin.init_plugin(self)

            # Start plugin
            plugin.start_plugin()

        # Process command queue
        while True:
            cmd = self._cmd_queue.get()
            shutter = cmd[0]
            command = cmd[1]

            if command == self.CMD_SHUTDOWN:
                logger.info('Received shutdown command')
                break

            logger.debug('Processing order for shutter {}: {}'.format(shutter,command))
            self._remote.drive_shutter( shutter, command )

    def stop(self):
        # Stop all plugins
        for (plugin_name,plugin) in self._plugins.items():
            plugin.stop_plugin()

        self._remote.stop()


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
    logger.info('Chronosoft8 Puppeteer starting')

    try:
        cp = Chronosoft8Puppeteer()
    except:
        logger.exception('Exception catch while initializing')
    else:
        try:
            cp.start()
        except:
            logger.exception('Stopping on exception')
        cp.stop()

    logger.info('Chronosoft8 Puppeteer stopping')
