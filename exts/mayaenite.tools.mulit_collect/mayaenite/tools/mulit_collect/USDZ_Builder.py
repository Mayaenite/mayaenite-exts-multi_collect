from pxr import Usd
import pathlib
import omni.ui as ui

########################################################################
class USDZ_Builder():
    """  """
    #----------------------------------------------------------------------
    def __init__(self,folders,progbar:ui.ProgressBar = None) -> None:
        """ Constructor """
        self.folders = folders
        self._current_task = 0
        self._total_task_count = len(self.folders)
        self.progbar = progbar
        for folder in self.folders:
            folder = pathlib.Path(folder)
            usdz_file = folder.as_posix()+".usdz"
            file_list = self.get_All_Files_In_Folder(folder)
            self.build_USDZ_File(folder.as_posix(),usdz_file,file_list)
            if self.progbar:
                self._current_task += 1
                self.progbar.model.set_value(float(self._current_task)/self._total_task_count)
    #----------------------------------------------------------------------
    def get_All_Files_In_Folder(self,folder:pathlib.Path) -> list:
        """  """
        file_list = []
        for item in folder.glob("**/*"):
            if item.is_file():
                file_list.append(item.as_posix())
        return file_list
    
    def build_USDZ_File(self,base_folder,usdz_file,files):
        with Usd.ZipFileWriter.CreateNew(usdz_file) as usdzWriter:
            for f in files:
                relative_path = f.replace(base_folder+"/","")
                usdzWriter.AddFile(f,relative_path)