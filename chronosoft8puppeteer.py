#!/usr/bin/env python3

# =============================================================================
# System imports
import argparse
import datetime
import json
import logging
import logging.config
import os
import queue
import yaml
from time import sleep

# =============================================================================
# Local imports
from chronosoft8puppeteer import Parameters,Remote

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
        # Initialize restart request
        self._restart = False

        # Load main config
        main_config_file = os.path.join( config_path
                                       , 'chronosoft8-puppeteer.json')
        try:
            self._config = json.load(open(main_config_file))
        except:
            logger.error('Failed to load config file %s',main_config_file)
            raise

        # Load shutters config
        shutters_config_file = os.path.join( config_path
                                           , 'shutters.json')
        try:
            shutters_config = json.load(open(shutters_config_file))
            self._shutters = shutters_config['shutters']
        except:
            logger.error('Failed to load config file %s',shutters_config_file)
            raise

        # Load groups config
        groups_config_file = os.path.join( config_path
                                         , 'groups.json')
        try:
            groups_config = json.load(open(groups_config_file))
            self._groups = groups_config['groups']
        except:
            logger.error('Failed to load config file %s',groups_config_file)
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
            logger.error('Missing active plugins in configuration file %s',config_file)
            raise

        # Load plugins
        self._plugins = dict()
        for plugin_name in plugin_names:
            cmd = 'from plugins import {} as plugin_handle'.format(plugin_name)
            _locals = locals()
            exec(cmd,globals(),_locals)
            self._plugins[plugin_name] = _locals['plugin_handle']

        # Initialize command queue
        self._cmd_queue = queue.PriorityQueue()

    # -------------------------------------------------------------------------
    def get_shutters(self):
        return self._shutters

    def get_groups(self):
        return self._groups

    # -------------------------------------------------------------------------
    def drive_shutter(self,shutter,command):
        priority = 2

        # Stop commands are executed first
        if command == self.CMD_STOP:
            priority = 1

        self._cmd_queue.put( ( priority, datetime.datetime.now()
                             , shutter, command ) )

    def drive_group(self,group,command):
        for group_data in self._groups:
            if group_data['name'] == group:
                for shutter in group_data['shutters']:
                    self.drive_shutter( shutter,command )
                break

    # -------------------------------------------------------------------------
    def get_programs(self):
        return self._plugins['scheduling'].get_programs()

    def set_programs(self,programs):
        return self._plugins['scheduling'].set_programs(programs)

    # -------------------------------------------------------------------------
    def get_config(self):
        return { 'remote_cmd_button_press_duration' : Parameters.remote_cmd_button_press_duration }

    def set_config(self,config):
        for parameter in config:
            if parameter == 'remote_cmd_button_press_duration':
                value = float(config[parameter])
                logger.info('Setting command button press duration to %.2f s', value)
                Parameters.remote_cmd_button_press_duration = value
            else:
                logger.error('Can\'t set unknown parameter %s', parameter)

    # -------------------------------------------------------------------------
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
            shutter = cmd[2]
            command = cmd[3]

            if command == self.CMD_SHUTDOWN:
                logger.info('Received shutdown command')
                break

            logger.debug('Processing order for shutter %s: %s',shutter,command)
            self._remote.drive_shutter( shutter, command )

    def stop(self, restart = False):
        self._restart = restart
        priority = 3
        self._cmd_queue.put( ( priority, datetime.datetime.now()
                             , '', self.CMD_SHUTDOWN ) )

    # -------------------------------------------------------------------------
    def do_stop(self):
        # Stop all plugins
        for (plugin_name,plugin) in self._plugins.items():
            plugin.stop_plugin()

        self._remote.stop()

    def shall_restart(self):
        return self._restart

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

    restart = True

    while restart is True:
        try:
            cp = Chronosoft8Puppeteer()
        except:
            logger.exception('Exception catched while initializing')
        else:
            try:
                cp.start()
            except:
                logger.exception('Stopping on exception')
            
            try:
                cp.do_stop()
            except:
                logger.exception('Exception catched while stopping')

        restart = cp.shall_restart()
        if restart is True:
            logger.info('restarting')

    logger.info('Chronosoft8 Puppeteer stopping')
