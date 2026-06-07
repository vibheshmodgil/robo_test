from app.shared.state import (
    vision_mode_manager
)

from app.shared.hud_manager import (
    hud_manager
)


class VisionController:

    def set_mode(
        self,
        mode
    ):

        vision_mode_manager.set_state(
            mode
        )

        return {
            "success": True,
            "mode": mode
        }

    def create_panel(
        self,
        title,
        message,
        options
    ):

        panel_id = (
            hud_manager.create_panel(
                title,
                message,
                options
            )
        )

        return {
            "panelId": panel_id
        }

    def update_panel(
        self,
        panel_id,
        title,
        message,
        options
    ):

        success = (
            hud_manager.update_panel(
                panel_id,
                title,
                message,
                options
            )
        )

        return {
            "success": success
        }

    def select_panel(
        self,
        panel_id,
        selected
    ):

        success = (
            hud_manager.select_option(
                panel_id,
                selected
            )
        )

        return {
            "success": success
        }

    def close_panel(
        self,
        panel_id
    ):

        success = (
            hud_manager.close_panel(
                panel_id
            )
        )

        return {
            "success": success
        }