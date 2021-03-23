#!/usr/bin/env python3

# =============================================================================
# System imports
import argparse
import configparser
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
        # Read configuration file
        config_file = os.path.join( _config_path
                                  , 'chronosoft8-puppeteer.ini')
        self._config = configparser.ConfigParser()
        self._config.read( config_file )

        # Initialize remote object
        self._remote = Remote(self._config)

        # Read plugin list from config file
        try:
            plugin_names = self._config['Plugins']['active'].split(',')
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
        return self._remote.get_channels()
    
    def get_channel_name(self,channel):
        try:
            name = self._config['Channels'][str(channel)]
        except:
            return None
        return name

    def drive_channel(self,channel,command):
        logger.debug('Queueing order for channel {}: {}'.format(channel,command))
        self._cmd_queue.put( (channel,command) )

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

    cp = Chronosoft8Puppet()
    cp.start()

    logger.info('Chronosoft8 Puppet stopping')
