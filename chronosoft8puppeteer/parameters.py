# =============================================================================
# System imports
import logging

# =============================================================================
# Logger setup
logger = logging.getLogger(__name__)

# =============================================================================
# Classes
class Parameters:
    remote_boot_duration = 1.0
    remote_init_duration = 1.0

    remote_menu_button_press_duration   = 0.1
    remote_menu_button_release_duration = 0.13

    remote_cmd_button_press_duration   = 1.5
    remote_cmd_button_release_duration = 0.2

    remote_sleep_timer_margin   = 1.0
    remote_sleep_timer_duration = 15.0

    remote_wake_button_press_duration   = 0.1
    remote_wake_button_release_duration = 0.5