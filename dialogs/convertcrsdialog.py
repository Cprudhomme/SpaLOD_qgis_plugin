from qgis.PyQt import uic
from qgis.PyQt import QtWidgets
from qgis.PyQt.QtWidgets import QProgressDialog, QFileDialog
from qgis.core import QgsApplication, QgsCoordinateReferenceSystem
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtCore import QRegExp
from qgis.PyQt.QtGui import QRegExpValidator, QValidator
from ..tasks.convertcrstask import ConvertCRSTask
import os.path

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/convertcrsdialog.ui'))


##
#  @brief The main dialog window of the SPARQLUnicorn QGIS Plugin.
class ConvertCRSDialog(QtWidgets.QDialog, FORM_CLASS):
    ## The triple store configuration file
    triplestoreconf = None
    ## Prefix map
    prefixes = None
    ## LoadGraphTask for loading a graph from a file or uri
    qtask = None

    def __init__(self, triplestoreconf={}, maindlg=None, parent=None):
        """Constructor."""
        super(ConvertCRSDialog, self).__init__(parent)
        self.setupUi(self)
        self.triplestoreconf = triplestoreconf
        self.dlg = parent
        self.maindlg = maindlg
        self.projectionSelect.setCrs(QgsCoordinateReferenceSystem('EPSG:4326'))
        urlregex = QRegExp("http[s]?://(?:[a-zA-Z#]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+")
        urlvalidator = QRegExpValidator(urlregex, self)
        self.loadFromFileButton.clicked.connect(self.loadFile)
        self.startConversionButton.clicked.connect(self.startConversion)
        self.cancelButton.clicked.connect(self.close)
        # self.loadFromURIButton.clicked.connect(self.loadURI)
##

#  check_state1 methode checks  the validity of an edited graph URI
#
#@Antoine

    def check_state1(self):
        self.check_state(self.graphURIEdit)
##

#The check_state methode checks the validity of a senders request
#
#@Antoine
    def check_state(self, sender):
        validator = sender.validator()
        state = validator.validate(sender.text(), 0)[0]
        if state == QValidator.Acceptable:
            color = '#c4df9b'  # green
        elif state == QValidator.Intermediate:
            color = '#fff79a'  # yellow
        else:
            color = '#f6989d'  # red
        sender.setStyleSheet('QLineEdit { background-color: %s }' % color)
##

#The loadFile methode loads a file from your computer
#
#@Antoine
    def loadFile(self):
        dialog = QFileDialog(self.dlg)
        dialog.setFileMode(QFileDialog.AnyFile)
        self.justloadingfromfile = True
        if dialog.exec_():
            fileNames = dialog.selectedFiles()
            filepath = fileNames[0].split(".")
            self.chosenFileLabel.setText(fileNames[0])
##

# The startConversion methode allows the conversion of a graph's CRS
#
#@Antoine
    def startConversion(self):
        progress = QProgressDialog("Loading Graph and converting CRS of graph: " + self.chosenFileLabel.text(), "Abort",
                                   0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setCancelButton(None)
        self.qtask = ConvertCRSTask("Converting CRS of Graph: " + self.chosenFileLabel.text(),
                                    self.chosenFileLabel.text(), self.projectionSelect.crs(), self, progress)
        QgsApplication.taskManager().addTask(self.qtask)
##

#The loadURI methode allows the user to load graph URIs
#
#@Antoine
    def loadURI(self):
        if self.graphURIEdit.text() != "":
            progress = QProgressDialog("Loading Graph from " + self.graphURIEdit.text(), "Abort", 0, 0, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.setCancelButton(None)
            self.qtask = LoadGraphTask("Loading Graph: " + self.graphURIEdit.text(), self.graphURIEdit.text(), self,
                                       self.dlg, self.maindlg, self.triplestoreconf[0]["geoconceptquery"],
                                       self.triplestoreconf, progress)
            QgsApplication.taskManager().addTask(self.qtask)
