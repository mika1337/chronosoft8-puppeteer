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
from chronosoft8puppet import Remote

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
    CMD_INT  = 'intermediate'
    CMD_SHUTDOWN = 'shutdown'

    def __init__(self):
        # Read configuration file
        config_file = os.path.join( _config_path
                                  , 'chronosoft8-puppet.ini')
        config = configparser.ConfigParser()
        config.read( config_file )

        # Initialize remote object
        self._remote = Remote(config)

        # Read plugin list from config file
        try:
            plugin_names = config['Plugins']['active'].split(',')
        except KeyError:
            logger.error('Missing active plugins in configuration file {}'.format(config_file))
            raise

        # Load plugins
        self._plugins_constructor = list()
        for plugin_name in plugin_names:
            cmd = 'from plugins import {} as plugin_handle'.format(plugin_name)
            exec(cmd,globals())
            self._plugins_constructor.append(plugin_handle)

        # Initialize command queue
        self._cmd_queue = queue.Queue()


    def getChannelNb(self):
        return self._remote.getChannelNb()

    def driveChannel(self,channel,command):
        logger.debug('Queueing order for channel {}: {}'.format(channel,command))
        self._cmd_queue.put( (channel,command) )

    def start(self):
        # Initialize remote
        logger.info('Initializing remote')
        self._remote.initRemote()

        # Initialize plugins
        plugins = list()
        for plugin_constructor in self._plugins_constructor:
            plugin = plugin_constructor(self,config)
            logger.info('Starting plugin {}'.format(plugin.getName()))
            plugin.start()
            plugins.append(plugin)

        # Process command queue
        while True:
            cmd = self._cmd_queue.get()
            channel = cmd[0]
            command = cmd[1]

            if command == self.CMD_SHUTDOWN:
                logger.info('Received shutdown command')
                break

            logger.debug('Processing order for channel {}: {}'.format(channel,command))
            self._remote.driveChannel( channel, command )

        # Stop all plugins
        for plugin in plugins:
            plugin.stop()

        # Wait for all plugins to end
        logger.debug('Waiting plugins to end')
        for plugin in plugins:
            plugin.wait()

        logger.info('All plugins stopped, stopping remote')
        self._remote.stopRemote()


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
