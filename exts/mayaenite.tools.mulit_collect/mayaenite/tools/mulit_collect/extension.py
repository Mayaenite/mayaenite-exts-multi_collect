import weakref
import asyncio
import os
from functools import partial
import pathlib
import time
from typing import Callable
import omni
import omni.ext
import omni.kit.ui
import omni.ui as ui
from omni.kit.tool.collect.collector import Collector,FlatCollectionTextureOptions
from omni.kit.tool.collect.progress_popup import ProgressPopup
from omni.kit.window.content_browser import get_content_window
from omni.kit.browser.asset import get_instance as get_asset_browser_instance
import carb

########################################################################
class BROWSER_TYPES:
    """  """
    ASSSET  = 0
    CONTENT = 1
#----------------------------------------------------------------------
def Get_Content_Browser():
    content_browser_ref = weakref.ref(get_content_window(), lambda ref: self.destroy())
    content_browser = content_browser_ref()
    return content_browser
#----------------------------------------------------------------------
def get_Selected_Browser():
    """Returns witch browser is currently the active browser"""
    if Get_Content_Browser()._window._window.selected_in_dock:
        return BROWSER_TYPES.CONTENT
    elif get_asset_browser_instance().window.selected_in_dock:
        return BROWSER_TYPES.ASSSET
    return None

#----------------------------------------------------------------------
def get_Selected_Files_From_Active_Browser():
    """Returns witch browser is currently the active browser"""
    active_browser = get_Selected_Browser()
    selected_file = []

    if active_browser == BROWSER_TYPES.CONTENT:
        active_browser = Get_Content_Browser()
        selected_file  = active_browser.get_current_selections(pane=2)

    elif active_browser == BROWSER_TYPES.ASSSET:
         active_browser = get_asset_browser_instance().browser_widget
         selected_file  = [sel.url for sel in active_browser.detail_selection]
    
    return selected_file


########################################################################
class Data_Return_Types:
    """  """
    Name = 0
    Path = 1

class AssetItem(ui.AbstractItem):
    """Single item of the model"""

    def __init__(self, assetpath:str):
        super().__init__()
        self.asset_path_model = ui.SimpleStringModel(assetpath)
        self.asset_name_model = ui.SimpleStringModel(pathlib.Path(assetpath).stem)

class Asset_Files_Model(ui.AbstractItemModel):
    """
    Represents the list of commands registered in Kit.
    It is used to make a single level tree appear like a simple list.
    """
    #----------------------------------------------------------------------
    def __init__(self):
        super().__init__()
        self._save_location = str()
        self._asset_files = []
    #----------------------------------------------------------------------
    def get_save_location(self) -> str:
        """  """
        return self._save_location
    #----------------------------------------------------------------------
    def set_save_location(self, folderPath:str):
        """  """
        self._save_location = folderPath
    #----------------------------------------------------------------------
    save_location = property(get_save_location,set_save_location)
    #----------------------------------------------------------------------
    def clear_item_children(self):
        """Called by subscribe_on_change"""
        self._asset_files = []
        self._item_changed(None)
    #----------------------------------------------------------------------
    def get_item_children(self, item=None):
        """Returns all the children when the widget asks it."""
        if item is not None:
            # Since we are doing a flat list, we return the children of root only.
            # If it's not root we return.
            return []

        return self._asset_files
    #----------------------------------------------------------------------
    def get_item_value_model_count(self, item):
        """The number of columns"""
        return 1
    #----------------------------------------------------------------------
    def get_item_value_model(self, item, item_data_id) -> ui.SimpleStringModel:
        """
        Return value model.
        It's the object that tracks the specific value.
        In our case we use ui.SimpleStringModel.
        """ 
        if item_data_id == Data_Return_Types.Name and item and isinstance(item, AssetItem):
            return item.asset_name_model
        elif item_data_id == Data_Return_Types.Path and item and isinstance(item, AssetItem):
            return item.asset_path_model
    #----------------------------------------------------------------------
    def remove_item(self, item: AssetItem) -> None: 
        """
        Removes the item from the model.
        """
        if item in self._asset_files:
            self._asset_files.remove(item)
            self._item_changed(None)
    #----------------------------------------------------------------------
    def add_item(self, assetPath: str) -> None: 
        """
        Adds a new AssetItem with the givin asset file path.
        """
        if not self.contains_asset_file(assetPath):
            item = AssetItem(assetPath)
            self._asset_files.append(item)
            self._item_changed(None)
    #----------------------------------------------------------------------
    def get_all_item_values(self, item_data_id) -> list:
        """
        Return all the item data model values.
        """ 
        if item_data_id in [Data_Return_Types.Name,Data_Return_Types.Path]:
            return [self.get_item_value_model(item,item_data_id).as_string for item in self._asset_files]
    #----------------------------------------------------------------------
    def contains_asset_file(self, assetPath) -> bool:
        """ Checks if the assetpath allready exists within the model """
        return assetPath in self.get_all_item_values(Data_Return_Types.Path)
    #----------------------------------------------------------------------
    def remove_Assets_Selected_In_View(self,view:ui.TreeView):
        current_children = self.get_item_children()
        for item in view.selection:
            if isinstance(item,AssetItem) and self.contains_asset_file(item.asset_path_model.as_string):
                self.remove_item(item)
    #----------------------------------------------------------------------
    def add_Selected_Assets_From_Active_Browser(self):
        for url in get_Selected_Files_From_Active_Browser():
            self.add_item(url)
########################################################################
class Asset_Collector_Window(ui.Window):
    """  """

    #----------------------------------------------------------------------
    def __init__(self,name:str,**kwargs) -> None:
        """ Constructor """
        super().__init__(name,**kwargs)

        #----------------------------------------------------------------------
        def set_save_location_to_selected_content_browser_directory():
            selection = Get_Content_Browser().get_current_selections(pane=1)
            if len(selection):
                self._data_model.save_location = selection[0]
                self.save_location_field.model.set_value(self._data_model._save_location)

        #----------------------------------------------------------------------
        def _do_asset_collection() -> None:
            """  """
            files_to_be_collected = self._data_model._asset_files[::]
            #----------------------------------------------------------------------
            def do_next():
                """  """
                if len(files_to_be_collected):
                    assetFile : AssetItem = files_to_be_collected.pop()
                    collect_dir = os.path.join(self._data_model.save_location,assetFile.asset_name_model.as_string).replace("\\","/")
                    self._start_collecting(assetFile.asset_path_model.as_string,collect_dir,False,False,False,2,do_next)
            # for assetFile in self._data_model._asset_files:
            #     collect_dir = os.path.join(self._data_model.save_location,assetFile.asset_name_model.as_string).replace("\\","/")
            #     assetFile : AssetItem
            #     self._start_collecting(assetFile.asset_path_model.as_string,collect_dir,False,False,False,2)

            assetFile : AssetItem = files_to_be_collected.pop()
            collect_dir = os.path.join(self._data_model.save_location,assetFile.asset_name_model.as_string).replace("\\","/")
            self._start_collecting(assetFile.asset_path_model.as_string,collect_dir,False,False,False,2,do_next)

        with self.frame:

            with ui.VStack():

                with ui.ScrollingFrame(height=ui.Fraction(8),
                                       horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_OFF,
                                       vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
                                       style_type_name_override="TreeView"):
                    self._data_model = Asset_Files_Model()
                    self._data_view  = ui.TreeView(self._data_model,root_visible=False,header_visible=False,style={"TreeView.Item": {"margin": 4}})
                
                with ui.HStack(height=50):
                    ui.Button("Add", clicked_fn   = self._data_model.add_Selected_Assets_From_Active_Browser)
                    ui.Button("Remove",clicked_fn = lambda : self._data_model.remove_Assets_Selected_In_View(self._data_view))
                    ui.Button("Reset", clicked_fn = self._data_model.clear_item_children)

                with ui.HStack(height=20):
                    label = ui.Label("Save Location",width=100)
                    self.save_location_field = ui.StringField() 
                    user_profile = os.environ["USERPROFILE"]
                    self.save_location_field.model.set_value(user_profile)
                    ui.Button("Set To Content",width=150, clicked_fn=set_save_location_to_selected_content_browser_directory)
                ui.Button("Collect", clicked_fn  = _do_asset_collection)
    
    def _show_progress_popup(self):
        progress_popup = ProgressPopup("Collecting")
        progress_popup.progress = 0
        progress_popup.show()

        return progress_popup
    #----------------------------------------------------------------------
    def _start_collecting(self,usd_path,collect_folder,usd_only,flat_collection,material_only,texture_option,finish_callback: Callable[[], None] = None,):
        progress_popup = self._show_progress_popup()
        progress_popup.status_text = "Collecting dependencies..."
        collector = Collector(
            usd_path,
            collect_folder,
            usd_only,
            flat_collection,
            material_only,
            texture_option=FlatCollectionTextureOptions(texture_option),
        )

        collector_weakref = weakref.ref(collector)

        def on_cancel():
            carb.log_info("Cancelling collector...")
            if not collector_weakref():
                return

            collector_weakref().cancel()

        progress_popup.set_cancel_fn(on_cancel)

        def on_progress(step, total):
            progress_popup.status_text = f"Collecting USD {os.path.basename(usd_path)}..."
            if total != 0:
                progress_popup.progress = float(step) / total
            else:
                progress_popup.progress = 0.0

        def on_finish():
            if finish_callback:
                finish_callback()
            

            progress_popup.hide()

            if not collector_weakref():
                return
            collector_weakref().destroy()

        asyncio.ensure_future(collector.collect(on_progress, on_finish))

    #----------------------------------------------------------------------
    def _destroy(self) -> None:
        """  """
        self._data_model = None
        self._data_view = None

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
        
    def on_shutdown(self):
        if self._window:
            self._window.destroy()
            self._window = None

        ui.Workspace.set_show_window_fn(MayaeniteToolsMulit_collectExtension.WINDOW_NAME, None)

    def show_window(self, menu_path: str, visible: bool):
        if visible:
            self._window = Asset_Collector_Window(MayaeniteToolsMulit_collectExtension.WINDOW_NAME)
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
