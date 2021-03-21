# =============================================================================
# System imports
import logging
from threading import Thread

# =============================================================================
# Logger setup
logger = logging.getLogger(__name__)

# =============================================================================
# Classes
class CmdLine(Thread):
    def __init__(self,chronosoft8puppet,config):
        super().__init__()
        self._cs8p = chronosoft8puppet
        self._channel_nb = self._cs8p.getChannelNb()
        self._name = 'Command line'

    def getName(self):
        return self._name

    def run(self):
        logger.info('Plugin {} starting'.format(self._name))
        while True:
            cmd = input('Enter command ? ')
            if cmd.startswith('u'):
                self._cs8p.driveChannel(int(cmd[1]),self._cs8p.CMD_UP)
            elif cmd.startswith('d'):
                self._cs8p.driveChannel(int(cmd[1]),self._cs8p.CMD_DOWN)
            elif cmd.startswith('s'):
                self._cs8p.driveChannel(int(cmd[1]),self._cs8p.CMD_STOP)
            elif cmd.startswith('i'):
                self._cs8p.driveChannel(int(cmd[1]),self._cs8p.CMD_INT)
            elif cmd == "q":
                self._cs8p.driveChannel(0,self._cs8p.CMD_SHUTDOWN)
                break

    def stop(self):
        pass

    def wait(self):
        pass
