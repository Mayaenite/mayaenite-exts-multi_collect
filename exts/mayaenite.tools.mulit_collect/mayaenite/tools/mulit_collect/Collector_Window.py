import os
import asyncio
from typing import Callable
import weakref
from . import Utils
from . import Data_Model
from .USDZ_Builder import USDZ_Builder
import carb
import omni.ui as ui
from omni.ui import color as cl
from omni.kit.tool.collect.collector import Collector,FlatCollectionTextureOptions
from omni.kit.tool.collect.progress_popup import ProgressPopup
from pxr import Usd

########################################################################
class Asset_Collector_Window(ui.Window):
    """  """

    #----------------------------------------------------------------------
    def __init__(self,name:str,**kwargs) -> None:
        """ Constructor """
        super().__init__(name,**kwargs)
        self._current_task = 0
        self._total_task_count = 0
        #----------------------------------------------------------------------
        def set_save_location_to_selected_content_browser_directory():
            selection = Utils.Get_Content_Browser().get_current_selections(pane=1)
            if len(selection):
                self._data_model.save_location = selection[0]
                self.save_location_field.model.set_value(self._data_model._save_location)

        #----------------------------------------------------------------------
        def _do_asset_collection() -> None:
            """  """
            files_to_be_collected = self._data_model._asset_files[::]
            self._current_task = 0
            self._total_task_count = len(files_to_be_collected)
            self._created_folders = []
            for assetFile in files_to_be_collected:
                collect_dir = os.path.join(self._data_model.save_location,assetFile.asset_name_model.as_string).replace("\\","/")
                self._created_folders.append(collect_dir)
            #----------------------------------------------------------------------
            def build_usdz_files() -> None:
                """  """
                builder = USDZ_Builder(self._created_folders,self._usdz_progress)
            #----------------------------------------------------------------------
            def do_next():
                """  """
                if len(files_to_be_collected):
                    assetFile : Data_Model.AssetItem = files_to_be_collected.pop()
                    collect_dir = os.path.join(self._data_model.save_location,assetFile.asset_name_model.as_string).replace("\\","/")
                    if len(files_to_be_collected):
                        self._start_collecting(assetFile.asset_path_model.as_string,collect_dir,False,False,False,2,do_next)
                    else:
                        self._start_collecting(assetFile.asset_path_model.as_string,collect_dir,False,False,False,2,build_usdz_files)
                    
                    self._current_task += 1
                    self._master_progress.model.set_value(float(self._current_task)/self._total_task_count)

            assetFile : Data_Model.AssetItem = files_to_be_collected.pop()
            collect_dir = os.path.join(self._data_model.save_location,assetFile.asset_name_model.as_string).replace("\\","/")
            if len(files_to_be_collected):
                self._start_collecting(assetFile.asset_path_model.as_string,collect_dir,False,False,False,2,do_next)
            else:
                self._start_collecting(assetFile.asset_path_model.as_string,collect_dir,False,False,False,2,build_usdz_files)
            self._current_task += 1
            self._master_progress.model.set_value(float(self._current_task)/self._total_task_count)

        with self.frame:

            with ui.VStack(spacing=10):

                with ui.ScrollingFrame(height=ui.Fraction(8),
                                       horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_OFF,
                                       vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
                                       style_type_name_override="TreeView"):
                    self._data_model = Data_Model.Asset_Files_Model()
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

                with ui.HStack(height=20,spacing=10):
                    ui.Button("Collect",width=175, clicked_fn  = _do_asset_collection)
                    self._master_progress = ui.ProgressBar()

                with ui.HStack(height=20,spacing=ui.Fraction(3)):
                    label_style = {"Label": {"font_size": 20, "color": cl.black, "alignment":ui.Alignment.LEFT_CENTER }}
                    checkbox_style = {"CheckBox":{"color": cl("#ff5555"), "border_radius": 5, "background_color": cl(0.35), "font_size": 20}}
                    self._generate_usdz_option = ui.CheckBox(width=0,style=checkbox_style)
                    ui.Label("Generate usdz files", width=20, style=label_style)
                    self._usdz_progress = ui.ProgressBar()

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
        self._master_progress = None
        self._generate_usdz_option = None
        self._usdz_progress = None