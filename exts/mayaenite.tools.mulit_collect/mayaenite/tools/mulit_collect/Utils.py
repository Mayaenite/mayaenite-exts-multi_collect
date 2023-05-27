import weakref
import omni.kit.window.content_browser
import omni.kit.browser.asset

########################################################################
class BROWSER_TYPES:
    """  """
    ASSSET  = 0
    CONTENT = 1
#----------------------------------------------------------------------
def Get_Content_Browser():
    content_browser_ref = weakref.ref(omni.kit.window.content_browser.get_content_window())
    # content_browser_ref = weakref.ref(omni.kit.window.content_browser.get_content_window(), lambda ref: self.destroy())
    content_browser = content_browser_ref()
    return content_browser
#----------------------------------------------------------------------
def get_Selected_Browser():
    """Returns witch browser is currently the active browser"""
    ints = omni.kit.browser.asset.get_instance()
    if Get_Content_Browser()._window._window.selected_in_dock:
        return BROWSER_TYPES.CONTENT
    elif omni.kit.browser.asset.get_instance().window.selected_in_dock:
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
         active_browser = omni.kit.browser.asset.get_instance().browser_widget
         selected_file  = [sel.url for sel in active_browser.detail_selection]
    
    return selected_file