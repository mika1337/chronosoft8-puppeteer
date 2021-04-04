# =============================================================================
# System imports
import logging
import RPi.GPIO as RPiGPIO

# =============================================================================
# Logger setup
logger = logging.getLogger(__name__)

# =============================================================================
# Classes
class GPIO:
    IN  = 0
    OUT = 1

    _initialized = False

    def __init__(self,name,channel,inout,default_value=0,active_high=True,debug=False):
        self._name    = name
        self._channel = channel
        self._inout   = inout
        self._active_high = active_high
        self._debug = debug

        logger.debug('Initializing GPIO {:<10} channel={} inout={} default={} active_high={} debug={}'
            .format( self._name
                   , self._channel
                   , "in" if inout == GPIO.IN else "out"
                   , default_value
                   , self._active_high
                   , self._debug ))

        if self._debug == False:
            if GPIO._initialized == False:
                self._initialize()

            rpigpio_inout = RPiGPIO.IN if inout == GPIO.IN else RPiGPIO.OUT
            initial_state = None
            if inout == GPIO.IN:
                RPiGPIO.setup( self._channel
                            , rpigpio_inout )
            else:
                initial_state = RPiGPIO.LOW
                if (self._active_high == True  and default_value == 1) or \
                (self._active_high == False and default_value == 0):
                    initial_state = RPiGPIO.HIGH
                RPiGPIO.setup( self._channel
                            , rpigpio_inout
                            , initial=initial_state)

    def __del__(self):
        if self._debug == False:
            RPiGPIO.cleanup( self._channel )

    def _initialize(self):
        logger.debug('Initializing RpiGPIO module')
        RPiGPIO.setmode(RPiGPIO.BOARD)
        GPIO._initialized = True

    def set(self,value):
        if self._inout == GPIO.IN:
            logger.error('Can\'t set input GPIO {}'.format(self._name))
        else:
            physical_value = value if self._active_high == True else not value
            logger.debug('Setting GPIO {:<10} to {} (logical value)'.format(self._name,1 if value else 0))
            if self._debug == False:
                RPiGPIO.output( self._channel, physical_value )
