
from functools import partial
import omni.ext
import omni.kit.ui
import omni.ui as ui
from . import Collector_Window

# Any class derived from `omni.ext.IExt` in top level module (defined in `python.modules` of `extension.toml`) will be
# instantiated when extension gets enabled and `on_startup(ext_id)` will be called. Later when extension gets disabled
# on_shutdown() is called.
class MayaeniteToolsMulit_collectExtension(omni.ext.IExt):
    # ext_id is current extension id. It can be used with extension manager to query additional information, like where
    # this extension is located on filesystem.
    WINDOW_NAME = "Multi Asset Collector"
    MENU_PATH = f"Window/Utilities/{WINDOW_NAME}"

    def on_startup(self):
        self._window = None

        ui.Workspace.set_show_window_fn(
            MayaeniteToolsMulit_collectExtension.WINDOW_NAME,
            partial(self.show_window, MayaeniteToolsMulit_collectExtension.MENU_PATH),
        )

        editor_menu = omni.kit.ui.get_editor_menu()
        if editor_menu:
            self._menu = editor_menu.add_item(MayaeniteToolsMulit_collectExtension.MENU_PATH, self.show_window, toggle=True, value=False)
        # self.show_window(MayaeniteToolsMulit_collectExtension.WINDOW_NAME,True)

    def on_shutdown(self):
        if self._window:
            self._window._destroy()
            self._window.destroy()
            self._window = None
        ui.Workspace.set_show_window_fn(MayaeniteToolsMulit_collectExtension.WINDOW_NAME, None)
        editor_menu = omni.kit.ui.get_editor_menu()
        editor_menu.remove_item(self._menu)
        del self._menu
        
    def show_window(self, menu_path: str, visible: bool):
        if visible:
            self._window = Collector_Window.Asset_Collector_Window(MayaeniteToolsMulit_collectExtension.WINDOW_NAME)
            self._window.set_visibility_changed_fn(self._visiblity_changed_fn)
        elif self._window:
            self._window.visible = False

    def _set_menu(self, checked: bool):
        """Set the menu to create this window on and off"""
        editor_menu = omni.kit.ui.get_editor_menu()
        if editor_menu:
            editor_menu.set_value(MayaeniteToolsMulit_collectExtension.MENU_PATH, checked)

    def _visiblity_changed_fn(self, visible):
        self._set_menu(visible)
