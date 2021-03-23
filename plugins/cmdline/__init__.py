# =============================================================================
# System imports
import logging
import threading

# =============================================================================
# Logger setup
logger = logging.getLogger(__name__)

# =============================================================================
# Globals
cs8p = None
thread = None

# =============================================================================
# Functions
def init_plugin(cs8p_):
    global cs8p

    logger.info('Initializing command line plugin')
    cs8p = cs8p_

def start_plugin():
    global thread

    logger.info('Starting command line plugin')
    thread = threading.Thread(target=main)
    thread.start()

def stop_plugin():
    pass

def main():
    while True:
        cmd = input('Enter command: ')
        if cmd.startswith('u'):
            cs8p.drive_channel(int(cmd[1]),cs8p.CMD_UP)
        elif cmd.startswith('d'):
            cs8p.drive_channel(int(cmd[1]),cs8p.CMD_DOWN)
        elif cmd.startswith('s'):
            cs8p.drive_channel(int(cmd[1]),cs8p.CMD_STOP)
        elif cmd.startswith('i'):
            cs8p.drive_channel(int(cmd[1]),cs8p.CMD_INT)
        elif cmd == "q":
            cs8p.drive_channel(0,cs8p.CMD_SHUTDOWN)
            break
