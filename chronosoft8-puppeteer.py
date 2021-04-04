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
_config_path = os.path.join( os.path.dirname(os.path.realpath(__file__))
                           , 'config' )

# =============================================================================
# Class
class Chronosoft8Puppet:
    CMD_UP = 'up'
    CMD_DOWN = 'down'
    CMD_STOP = 'stop'
    CMD_INT  = 'int'
    CMD_SHUTDOWN = 'shutdown'

    def __init__(self):
        config_file = os.path.join( _config_path
                                  , 'chronosoft8-puppeteer.json')
        try:
            # Load configuration
            self._config = json.load(open(config_file))
        except:
            logger.error('Failed to load config file {}'.format(config_file))
            raise

        self._debug = False
        if 'debug' in self._config:
            self._debug = self._config['debug']

        # Initialize remote object
        self._remote = Remote(self._config)

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


    def get_channels(self):
        return self._config['channels']

    def drive_channel(self,channel,command):
        try:
            channel_int = int(channel)
        except:
            for channel_name,channel_infos in self._config['channels'].items():
                if channel_infos['name'] == channel:
                    channel_int = int(channel_name)
                    break
        
        if channel_int == None:
            logger.error('Failed to identify channel {}'.format(channel))

        logger.debug('Queueing order for channel {}: {}'.format(channel_int,command))
        self._cmd_queue.put( (channel_int,command) )

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
            channel = cmd[0]
            command = cmd[1]

            if command == self.CMD_SHUTDOWN:
                logger.info('Received shutdown command')
                break

            logger.debug('Processing order for channel {}: {}'.format(channel,command))
            self._remote.drive_channel( channel, command )

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
    logger.info('Chronosoft8 Puppet starting')

    try:
        cp = Chronosoft8Puppet()
    except:
        logger.exception('Exception catch while initializing')
    else:
        try:
            cp.start()
        except:
            logger.exception('Stopping on exception')
        cp.stop()

    logger.info('Chronosoft8 Puppet stopping')
