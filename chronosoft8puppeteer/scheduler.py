# =============================================================================
# System imports
import datetime
import logging

# =============================================================================
# Local imports
from chronosoft8puppeteer import Parameters

# =============================================================================
# Logger setup
logger = logging.getLogger(__name__)

# =============================================================================
# Classes
class Scheduler:
    def __init__(self,channel_nb):
        self._command_duration = Parameters.remote_cmd_button_press_duration + Parameters.remote_cmd_button_release_duration
        self._wake_duration = Parameters.remote_wake_button_press_duration + Parameters.remote_wake_button_release_duration
        self._change_channel_max_duration = channel_nb * (Parameters.remote_menu_button_press_duration + Parameters.remote_menu_button_release_duration)
        self._command_max_duration = self._wake_duration + self._change_channel_max_duration + self._command_duration

        self._commands_schedule = list()

    def drive_shutter(self, shutter, commands ):
        if len(self._scheduled_commands):
            if can_run_command_before_date( self._scheduled_commands )
        command['']='aspa'
        for command in commands:
            pass

    def schedule_commands(self,commands):
        now = datetime.datetime.now()

        # Compute commands min date
        for command in commands:
            try:
                delay = command['delay']
            except:
                delay = 0
            command['min_date'] = now + delay

        commands_schedulable = False
        while commands_schedulable == False:
            commands_schedulable = True
            for command in commands:
                if not self.is_schedulable( command ):
                    commands_schedulable = False
                    break
            
            if commands_schedulable == False:
                # Shift min_date
                for command in commands:
                    command['min_date'] = command['min_date'] + 1.0
                    logger.warning('Improve with actual next feasible date')

        # Add commands to schedules commands
        for command in commands:
            self._commands_schedule.append()
