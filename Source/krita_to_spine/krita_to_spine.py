import krita
from krita_to_spine import krita_to_spine_dialog


class KritaToSpineExtension(krita.Extension):

    def __init__(self, parent):
        super(KritaToSpineExtension, self).__init__(parent)

    def setup(self):
        # Register the plugin action
        action = krita.Krita.instance().createAction("krita_to_spine", "Export to Spine")
        action.setToolTip("Plugin that exports the layers of a document to be used with Spine.")
        action.triggered.connect(self.open_dialog)

    def open_dialog(self):
        # Open the export dialog
        self.krita_to_spine_dialog = krita_to_spine_dialog.SpineExportDialog()
        self.krita_to_spine_dialog.initialize()


        
Scripter.addExtension(KritaToSpineExtension(krita.Krita.instance()))
