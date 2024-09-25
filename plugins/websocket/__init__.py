# =============================================================================
# System imports
import asyncio
import logging
import os
import json
import threading
import time
import websockets

# =============================================================================
# Logger setup
logger = logging.getLogger(__name__)

# =============================================================================
# Globals
run_dir = os.path.dirname(os.path.realpath(__file__))
config_file = os.path.join(run_dir,'config','websocket.json')

cs8p = None
port = None
thread = None
event_loop = None
websockets_handle = None

# =============================================================================
# Functions
def init_plugin(cs8p_):
    global cs8p,port

    logger.info('Initializing websocket plugin')

    cs8p = cs8p_

    try:
        config = json.load(open(config_file))
        port = config['port']
    except:
        logger.exception('Failed to load config file %s',config_file)

def start_plugin():
    global thread

    logger.info('Starting websocket plugin on port %d',port)
    thread = threading.Thread(target=main)
    thread.start()

def stop_plugin():
    logger.info('Stopping websocket plugin')

    if websockets_handle:
        websockets_handle.close()
        future = asyncio.run_coroutine_threadsafe(websockets_handle.wait_closed(),event_loop)
        future.result()
        logger.debug('Websocket closed')

        event_loop.call_soon_threadsafe(event_loop.stop)
        while event_loop.is_running():
            logger.debug('Waiting for event loop to stop')
            time.sleep(1)

def main():
    global event_loop,websockets_handle

    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)

    start_server = websockets.serve(on_client_connected, port=port)
    websockets_handle = event_loop.run_until_complete(start_server)
    event_loop.run_forever()

async def on_client_connected(websocket,path):
    endpoint = '{}:{}'.format(websocket.remote_address[0], websocket.remote_address[1])
    logger.info('New connection from %s',endpoint)

    try:
        async for message in websocket:
            try:
                logger.debug('Data received from %s: %s',endpoint,message)
                output = process_input(message,endpoint)
                if output:
                    output = { 'cs8p' : output }
                    json_output = json.dumps( output )
                    logger.debug('Sending data to %s: %s',endpoint,json_output)
                    await websocket.send(json_output)
            except:
                logger.exception('Error while processing data from %s',endpoint)
                raise
    finally:
        logger.info('{} disconnected'.format(endpoint))

def process_input(json_input,endpoint):
    output = None

    try:
        data = json.loads(json_input)
    except:
        logger.error( 'Received data from client "%s" not in json format',endpoint)
    else:
        if 'cs8p' not in data:
            logger.warning( 'Data from client "%s" does not contain cs8p data',endpoint)
        else:
            data = data['cs8p']
            logger.debug('data: {}'.format(data))

            if 'command' in data:
                command = data['command']

                # -------------------------------------------------------------
                # Shutters commands
                if command == 'get_shutters':
                    shutters = cs8p.get_shutters()
                    output = { 'status': 'ok', 'shutters': shutters }
                elif command == 'get_groups':
                    groups = cs8p.get_groups()
                    output = { 'status': 'ok', 'groups': groups }

                # -------------------------------------------------------------
                # Programs commands
                elif command == 'get_programs':
                    programs = cs8p.get_programs()
                    output = { 'status': 'ok', 'programs': programs }
                elif command == 'set_programs':
                    try:
                        programs = data['args']['programs']
                        cs8p.set_programs(programs)
                    except:
                        logger.exception('Failed to update programs')
                        output = { 'status': 'error' }
                    else:
                        output = { 'status': 'ok' }

                # -------------------------------------------------------------
                # Config commands
                elif command == 'get_config':
                    config = cs8p.get_config()
                    output = { 'status': 'ok', 'config': config }
                elif command == 'set_config':
                    try:
                        config = data['args']['config']
                        cs8p.set_config(config)
                    except:
                        logger.exception('Failed to update config')
                        output = { 'status': 'error' }
                    else:
                        output = { 'status': 'ok' }

                # -------------------------------------------------------------
                # Drive commands
                elif command == 'drive_shutter':
                    try:
                        command = data['args']['command']
                        shutter = data['args']['shutter']
                    except:
                        output = { 'status': 'error' }
                    else:
                        cs8p.drive_shutter(shutter,command)
                        output = { 'status': 'ok' }
                elif command == 'drive_group':
                    try:
                        command = data['args']['command']
                        group   = data['args']['group']
                    except:
                        output = { 'status': 'error' }
                    else:
                        cs8p.drive_group(group,command)
                        output = { 'status': 'ok' }

                # -------------------------------------------------------------
                # Utilities commands
                elif command == 'restart':
                    cs8p.stop( True )
                    output = { 'status': 'ok' }
    return output