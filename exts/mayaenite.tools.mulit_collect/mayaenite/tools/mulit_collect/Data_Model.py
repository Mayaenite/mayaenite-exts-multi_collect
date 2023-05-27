import omni.ui as ui
import pathlib
from . import Utils
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
        for url in Utils.get_Selected_Files_From_Active_Browser():
            self.add_item(url)