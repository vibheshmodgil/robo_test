from app.models.hologram_panel import HologramPanel


class HudManager:
    """
    ONE persistent HUD panel.

    There is exactly one panel on screen at all times. It shows the base
    "Hi, I am Shiv" screen when idle, and morphs its content in place when a
    mode wants to display a step or a reply. Because a second panel is never
    created, panels can never stack or overlap, and there is always something
    on screen (so passive mode is no longer blank).

    The backend (Java) drives content through the same create / update / close
    API as before - those calls now all act on this single panel.
    """

    BASE_TITLE = "SHIV"
    BASE_MESSAGE = "Hi, I am Shiv"

    def __init__(self):
        self.panel = None

    # ------------------------------------------------------------------
    #  the one panel
    # ------------------------------------------------------------------
    def _ensure(self):
        if self.panel is None:
            self.panel = HologramPanel(
                key="main",
                width_frac=0.42,
                height_frac=0.34,        # a touch taller -> room for wrapped text
                offset=(0.0, -0.1),
            )
            # show ONCE so the entrance animation plays a single time
            self.panel.show(
                title=self.BASE_TITLE,
                message=self.BASE_MESSAGE,
                options=[],
            )
        return self.panel

    def _set_content(self, title, message, options=None):
        """Morph the panel in place. Attributes are set directly (not via
        show()) so the entrance animation is NOT replayed on every change."""
        panel = self._ensure()
        panel.title = title if title is not None else self.BASE_TITLE
        panel.message = message if message is not None else ""
        panel.options = options or []
        panel.selected_index = None
        return panel

    # ------------------------------------------------------------------
    #  base / welcome screen
    # ------------------------------------------------------------------
    def show_welcome(self, title=None, message=None):
        """Show the base 'Hi, I am Shiv' screen (e.g. on wakeword)."""
        return self._set_content(
            title or self.BASE_TITLE,
            message if message is not None else self.BASE_MESSAGE,
        )

    def show_main(self, title=None, message=None):
        return self.show_welcome(title, message)

    def reset_to_base(self):
        self._set_content(self.BASE_TITLE, self.BASE_MESSAGE)

    # ------------------------------------------------------------------
    #  API used by VisionController - all act on the SAME panel
    # ------------------------------------------------------------------
    def create_panel(self, title, message, options=None, **kwargs):
        self._set_content(title, message, options)
        return "main"

    def update_panel(self, panel_id, title, message, options=None):
        self._set_content(title, message, options)
        return True

    def select_option(self, panel_id, selected):
        panel = self._ensure()
        panel.selected_index = selected
        return True

    def close_panel(self, panel_id):
        # Never actually remove the panel - fall back to the base screen so the
        # HUD is never empty and the next mode reuses the same panel.
        self.reset_to_base()
        return True

    # ------------------------------------------------------------------
    #  renderer hooks
    # ------------------------------------------------------------------
    def get_active_panels(self):
        return [self._ensure()]

    def update(self):
        # single persistent panel -> nothing to garbage collect
        pass


# Shared singleton:  from app.shared.hud_manager import hud_manager
hud_manager = HudManager()