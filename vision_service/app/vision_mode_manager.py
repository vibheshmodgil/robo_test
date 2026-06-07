from app.modes.vision_states import VisionStates
from app.modes.passive_mode import PassiveMode
from app.modes.follow_mode import FollowMode
from app.modes.gesture_mode import GestureMode
from app.modes.record_mode import RecordMode
from app.modes.capture_image_mode import CaptureImageMode
from app.modes.inventory_vision_mode import InventoryVisionMode

from app.shared.hud_manager import hud_manager
from app.modes.gimble_mode import GimbalMode


class VisionModeManager:

    def __init__(self):
        # Change mode at start
        self.current_state = VisionStates.INVENTORY
        # self.current_state = VisionStates.GIMBAL

        self.passive_mode = PassiveMode()
        self.follow_mode = FollowMode()
        self.gesture_mode = GestureMode()
        self.record_mode = RecordMode()
        self.capture_image_mode = CaptureImageMode()
        self.inventory_mode = InventoryVisionMode()
        self.gimbal_mode = GimbalMode()

        self.state_handler_map = {
            VisionStates.PASSIVE: self.passive_mode,
            VisionStates.FOLLOW: self.follow_mode,
            VisionStates.GESTURE: self.gesture_mode,
            VisionStates.RECORD: self.record_mode,
            VisionStates.CAPTURE_IMAGE: self.capture_image_mode,
            VisionStates.INVENTORY: self.inventory_mode,
            VisionStates.GIMBAL: self.gimbal_mode
        }

    def show_welcome(self, message="Welcome, I am Shiv"):
        """Pop the main 'Shiv' screen. Call this on wakeword detection."""
        hud_manager.show_welcome(message=message)

    def set_state(self, state):
        state = state.upper()

        new = self.state_handler_map.get(state)
        if new is None:
            print(f"\n[VISION STATE] unknown state '{state}' - ignored\n")
            return

        if state == self.current_state:
            return

        print(f"\n[VISION STATE] {state}\n")

        old = self.state_handler_map.get(self.current_state)

        # Leave the old screen (e.g. close the inventory panel)
        if old is not None and hasattr(old, "exit"):
            old.exit()

        self.current_state = state

        # Enter the new screen (e.g. open the inventory panel)
        if hasattr(new, "enter"):
            new.enter()

    def get_current_handler(self):
        return self.state_handler_map[self.current_state]