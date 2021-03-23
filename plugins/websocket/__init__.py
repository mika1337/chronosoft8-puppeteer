# =============================================================================
# System imports
import asyncio
import configparser
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
cs8p = None

run_dir = os.path.dirname(os.path.realpath(__file__))
config_file = os.path.join(run_dir,'config','websocket.ini')
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

    config = configparser.ConfigParser()
    config.read( config_file )
    port = config['websocket']['port']

def start_plugin():
    global thread

    logger.info('Starting websocket plugin on port {}'.format(port))
    thread = threading.Thread(target=main)
    thread.start()

def stop_plugin():
    logger.info('Stopping websocket plugin')
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
    logger.info('New connection from {}'.format(endpoint))

    try:
        async for message in websocket:
            logger.debug('Data received from {}: {}'.format(endpoint,message))
            output = process_input(message,endpoint)
            if output:
                output = { 'cs8p' : output }
                json_output = json.dumps( output )
                logger.debug('Sending data to {}: {}'.format(endpoint,json_output))
                await websocket.send(json_output)
    finally:
        logger.info('{} disconnected'.format(endpoint))

def process_input(json_input,endpoint):
    output = None

    try:
        data = json.loads(json_input)
    except:
        logger.error( 'Received data from client "{}" not in json format'.\
                      format(endpoint) )
    else:
        if 'cs8p' not in data:
            logger.warning( 'Data from client "{}" does not contain cs8p data'.\
                            format(endpoint) )
        else:
            data = data['cs8p']
            logger.debug('data: {}'.format(data))

            if 'cmd' in data:
                cmd = data['cmd']
                if cmd == 'get_channels':
                    channels = cs8p.get_channels()
                    channels_with_name = dict()
                    for channel in channels:
                        channels_with_name[channel] = cs8p.get_channel_name(channel)
                    output = { 'status': 'ok', 'channels': channels_with_name }
                elif cmd == 'drive':
                    try:
                        cmd = data['args']['cmd']
                        channel = data['args']['channel']
                    except:
                        output = { 'status': 'error' }
                    else:
                        cs8p.drive_channel(channel,cmd)
                        output = { 'status': 'ok' }
    return output
                    
