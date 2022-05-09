import os
from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtCore import Qt, QEvent
from qgis.core import QgsProject
from qgis.PyQt.QtWidgets import QMessageBox, QTableWidgetItem, QComboBox, QHBoxLayout,  QPushButton, QWidget, QStyledItemDelegate
from qgis.PyQt.QtGui import QFontMetrics, QStandardItem
from ..dialogs.whattoenrichdialog import EnrichmentDialog
from ..enrichmenttab import EnrichmentTab
from ..dialogs.triplestoredialog import TripleStoreDialog
from ..dialogs.warningLayerdlg import WarningLayerDlg
from ..dialogs.triplestoredialog import TripleStoreDialog

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/Enrichment.ui'))

MESSAGE_CATEGORY = 'Enrichment MainWindow'

##

#The Main window of the Enrichment feature containing the "EnrichmentMainWindow" class
#
#@Antoine
class EnrichmentMainWindow(QtWidgets.QMainWindow, FORM_CLASS):
    ## The triple store configuration file

    sparqlunicorndlg = None
    exportColConfig = {}


    def __init__(self,layers, addVocabConf, triplestoreconf, prefixes, prefixstore, comboBox, maindlg=None,  parent=None):
        """Constructor."""
        super(EnrichmentMainWindow, self).__init__(parent)
        self.sparqlunicorndlg = maindlg
        self.setupUi(self)

        self.loadUnicornLayers(layers)
        self.addVocabConf = addVocabConf
        self.prefixes = prefixes
        self.triplestoreconf = triplestoreconf
        self.searchTripleStoreDialog = TripleStoreDialog(triplestoreconf, prefixes, prefixstore,comboBox)

        self.enrichtab = EnrichmentTab(self)



        self.enrichTable.cellClicked.connect(self.createEnrichSearchDialog)
        #self.enrichTable.cellClicked.setToolTip('Will open the interlink search dialog when clicked.')
        self.addEnrichedLayerButton.clicked.connect(self.enrichtab.addEnrichedLayer)
        self.addEnrichedLayerButton.setToolTip('Will add the enriched layer to QGIS layers when clicked')
        self.startEnrichment.clicked.connect(self.enrichtab.enrichLayerProcess)
        self.startEnrichment.setToolTip('Will start enriching the selected layers when clicked.')
        self.loadLayerEnrich.clicked.connect(self.loadLayerForEnrichment)
        self.loadLayerEnrich.setToolTip('Loads your current layer in the "Enrichment Table"')
        self.addEnrichedLayerRowButton.clicked.connect(self.addEnrichRow)
        self.addEnrichedLayerRowButton.setToolTip('Will add a row to the "Enrichment Table" when clicked')
        self.whattoenrich.clicked.connect(self.createWhatToEnrich)
        self.whattoenrich.setToolTip('will open the "Enrichment Search" dialog when clicked.')
        # self.refreshLayersEnrich.clicked.connect(self.sparqlunicorndlg.loadUnicornLayers)



    def loadUnicornLayers(self, layers):
        # Populate the comboBox with names of all the loaded unicorn layers

        for layer in layers:
            ucl = layer.name()
            # if type(layer) == QgsMapLayer.VectorLayer:
            # self.loadedLayers.addItem(layer.name())
            # self.chooseLayerInterlink.addItem(layer.name())
            self.chooseLayerEnrich.addItem(layer.name())


# functions:

#  @brief Builds the search dialog to search for a concept or class.
#  @param  self The object pointer
#  @param  row the row to insert the result
#  @param  column the column to insert the result
#  @param  interlinkOrEnrich indicates if the dialog is meant for interlinking or enrichment
#  @param  table the GUI element to display the result
# def buildSearchDialog(self, row, column, interlinkOrEnrich, table, propOrClass, bothOptions=False,
#                       currentprefixes=None, addVocabConf=None):
#     self.currentcol = column
#     self.currentrow = row
#     self.interlinkdialog = SearchDialog(column, row, self.triplestoreconf, self.prefixes, interlinkOrEnrich, table,
#                                         propOrClass, bothOptions, currentprefixes, addVocabConf)
#     self.interlinkdialog.setMinimumSize(650, 400)
#     self.interlinkdialog.setWindowTitle("Search Interlink Concept")
#     self.interlinkdialog.exec_()

    def createEnrichSearchDialog(self, row=-1, column=-1):
        if column == 1:
            self.sparqlunicorndlg.buildSearchDialog(row, column, False, self.enrichTable, False, False, None, self.addVocabConf)
        if column == 6:
            self.sparqlunicorndlg.buildSearchDialog(row, column, False, self.enrichTable, False, False, None, self.addVocabConf)
    #
    # def createEnrichSearchDialogProp(self, row=-1, column=-1):
    #     self.buildSearchDialog(row, column, False, self.findIDPropertyEdit, True, False, None, self.addVocabConf)


    ##

    #  @brief Deletes a row from the table in the enrichment dialog.
    #
    #  @param  send The sender of the request
    #
    def deleteEnrichRow(self, send):
        w = send.sender().parent()
        row = self.enrichTable.indexAt(w.pos()).row()
        self.enrichTable.removeRow(row);
        self.enrichTable.setCurrentCell(0, 0)

    ##
    #  @brief Adds a new row to the table in the enrichment dialog.
    #
    #  @param  self The object pointer
    #
    # Check if wrongly using the button causes python error (may need to add a warning ui/py)

    def addEnrichRow(self):
        layers = QgsProject.instance().layerTreeRoot().children()
        selectedLayerIndex = self.chooseLayerEnrich.currentIndex()
        if  selectedLayerIndex == -1:
            dlg = WarningLayerDlg()
            dlg.show()
            dlg.exec_()
        else:
            layer = layers[selectedLayerIndex].layer()

            self.enrichTableResult.hide()
            fieldnames = [field.name() for field in layer.fields()]
            item = QTableWidgetItem("new_column")
            # item.setFlags(QtCore.Qt.ItemIsEnabled)
            row = self.enrichTable.rowCount()
            self.enrichTable.insertRow(row)
            self.enrichTable.setItem(row, 0, item)
            cbox = QComboBox()
            cbox.addItem("Get Remote")
            cbox.addItem("No Enrichment")
            cbox.addItem("Exclude")
            self.enrichTable.setCellWidget(row, 3, cbox)
            cbox = QComboBox()
            cbox.addItem("Enrich Value")
            cbox.addItem("Enrich URI")
            cbox.addItem("Enrich Both")
            self.enrichTable.setCellWidget(row, 4, cbox)
            cbox = CheckableComboBox()
            for fieldd in fieldnames:
                cbox.addItem(fieldd)
            self.enrichTable.setCellWidget(row, 5, cbox)
            itemm = QTableWidgetItem("http://www.w3.org/2000/01/rdf-schema#label")
            self.enrichTable.setItem(row, 6, itemm)
            itemm = QTableWidgetItem("")
            self.enrichTable.setItem(row, 7, itemm)
            itemm = QTableWidgetItem("")
            self.enrichTable.setItem(row, 8, itemm)




    ##
    #  @brief Creates a What To Enrich dialog with parameters given.
    #
    #  @param self The object pointer
    def createWhatToEnrich(self):
        if self.enrichTable.rowCount() == 0:
            return
        layers = QgsProject.instance().layerTreeRoot().children()
        selectedLayerIndex = self.chooseLayerEnrich.currentIndex()
        layer = layers[selectedLayerIndex].layer()
        self.searchTripleStoreDialog = EnrichmentDialog(self.triplestoreconf, self.prefixes, self.enrichTable, layer,
                                                        None, None)
        self.searchTripleStoreDialog.setMinimumSize(700, 500)
        self.searchTripleStoreDialog.setWindowTitle("Enrichment Search")
        self.searchTripleStoreDialog.exec_()


    def loadLayerForEnrichment(self):

        layers = QgsProject.instance().layerTreeRoot().children()
        selectedLayerIndex = self.chooseLayerEnrich.currentIndex()
        if  selectedLayerIndex == -1 or len(layers) == 0:
            dlg = WarningLayerDlg()
            dlg.show()
            dlg.exec_()
        else:
            # if len(layers) == 0:
            #     return
            layer = layers[selectedLayerIndex].layer()
            self.enrichTableResult.hide()
            while self.enrichTableResult.rowCount() > 0:
                self.enrichTableResult.removeRow(0);
            self.enrichTable.show()
            self.addEnrichedLayerRowButton.setEnabled(True)
            try:
                fieldnames = [field.name() for field in layer.fields()]
                while self.enrichTable.rowCount() > 0:
                    self.enrichTable.removeRow(0);
                row = 0
                self.enrichTable.setColumnCount(9)
                self.enrichTable.setHorizontalHeaderLabels(
                    ["Column", "EnrichmentConcept", "TripleStore", "Strategy", "content", "ID Column", "ID Property",
                     "ID Domain", "Language"])
                for field in fieldnames:
                    item = QTableWidgetItem(field)
                    item.setFlags(Qt.ItemIsEnabled)
                    currentRowCount = self.enrichTable.rowCount()
                    self.enrichTable.insertRow(row)
                    self.enrichTable.setItem(row, 0, item)

                    cbox = QComboBox()
                    cbox.addItem("No Enrichment")
                    cbox.addItem("Keep Local")
                    cbox.addItem("Keep Remote")
                    cbox.addItem("Replace Local")
                    cbox.addItem("Merge")
                    cbox.addItem("Ask User")
                    cbox.addItem("Exclude")
                    self.enrichTable.setCellWidget(row, 3, cbox)

                    cbox = QComboBox()
                    cbox.addItem("Enrich Value")
                    cbox.addItem("Enrich URI")
                    cbox.addItem("Enrich Both")
                    self.enrichTable.setCellWidget(row, 4, cbox)

                    cbox = CheckableComboBox()
                    for fieldd in fieldnames:
                        cbox.addItem(fieldd)
                    
                    self.enrichTable.setCellWidget(row, 5, cbox)
                    itemm = QTableWidgetItem("http://www.w3.org/2000/01/rdf-schema#label")
                    self.enrichTable.setItem(row, 6, itemm)
                    itemm = QTableWidgetItem("")
                    self.enrichTable.setItem(row, 7, itemm)
                    itemm = QTableWidgetItem("")
                    self.enrichTable.setItem(row, 8, itemm)
                    celllayout = QHBoxLayout()
                    upbutton = QPushButton("Up")
                    removebutton = QPushButton("Remove", self)
                    removebutton.clicked.connect(self.deleteEnrichRow)
                    downbutton = QPushButton("Down")
                    celllayout.addWidget(upbutton)
                    celllayout.addWidget(downbutton)
                    celllayout.addWidget(removebutton)
                    w = QWidget()
                    w.setLayout(celllayout)
                    optitem = QTableWidgetItem()
                    # self.enrichTable.setCellWidget(row,4,w)
                    # self.enrichTable.setItem(row,3,cbox)
                    row += 1
                self.originalRowCount = row

            except:
                msgBox = QMessageBox()
                msgBox.setWindowTitle("Layer not compatible for enrichment!")
                msgBox.setText("The chosen layer is not supported for enrichment. You possibly selected a raster layer")
                msgBox.exec()
                return

    ##
    #  @brief Shows the configuration table after creating an enrichment result.
    #
    #  @param  self The object pointer
    #
    def showConfigTable(self):
        self.enrichTableResult.hide()
        self.enrichTable.show()
        self.startEnrichment.setText("Start Enrichment")
        self.startEnrichment.clicked.disconnect()
        self.startEnrichment.clicked.connect(self.enrichtab.enrichLayerProcess)

# class CheckableComboBox2(QgsCheckableComboBox):

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.activated.connect(self.afterActivated)   

#     def afterActivated(self):
#         for i in range ( self.model().rowCount()):
#             item = self.model().item(i)  
#             if item.checkState() == Qt.Checked:
#                 self.setCurrentIndex(i)
#                 self.model().itemCheckStateChanged.emit()
#                 return


class CheckableComboBox(QComboBox):

    # Subclass Delegate to increase item height
    class Delegate(QStyledItemDelegate):
        def sizeHint(self, option, index):
            size = super().sizeHint(option, index)
            size.setHeight(20)
            return size

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Make the combo editable to set a custom text, but readonly
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        # Make the lineedit the same color as QPushButton
        # palette = qApp.palette()
        # palette.setBrush(QPalette.Base, palette.button())
        # self.lineEdit().setPalette(palette)

        # Use custom delegate
        self.setItemDelegate(CheckableComboBox.Delegate())

        # Update the text when an item is toggled
        self.model().dataChanged.connect(self.updateText)

        # Hide and show popup when clicking the line edit
        self.lineEdit().installEventFilter(self)
        self.closeOnLineEditClick = False

        # Prevent popup from closing when clicking on an item
        self.view().viewport().installEventFilter(self)

    def resizeEvent(self, event):
        # Recompute text to elide as needed
        self.updateText()
        super().resizeEvent(event)

    def eventFilter(self, object, event):

        if object == self.lineEdit():
            if event.type() == QEvent.MouseButtonRelease:
                if self.closeOnLineEditClick:
                    self.hidePopup()
                else:
                    self.showPopup()
                return True
            return False

        if object == self.view().viewport():
            if event.type() == QEvent.MouseButtonRelease:
                index = self.view().indexAt(event.pos())
                item = self.model().item(index.row())

                if item.checkState() == Qt.Checked:
                    item.setCheckState(Qt.Unchecked)
                else:
                    item.setCheckState(Qt.Checked)
                return True
        return False

    def showPopup(self):
        super().showPopup()
        # When the popup is displayed, a click on the lineedit should close it
        self.closeOnLineEditClick = True

    def hidePopup(self):
        super().hidePopup()
        # Used to prevent immediate reopening when clicking on the lineEdit
        self.startTimer(100)
        # Refresh the display text when closing
        self.updateText()

    def timerEvent(self, event):
        # After timeout, kill timer, and reenable click on line edit
        self.killTimer(event.timerId())
        self.closeOnLineEditClick = False

    def updateText(self):
        texts = []
        for i in range(self.model().rowCount()):
            if self.model().item(i).checkState() == Qt.Checked:
                texts.append(self.model().item(i).text())
        text = ", ".join(texts)

        # Compute elided text (with "...")
        metrics = QFontMetrics(self.lineEdit().font())
        elidedText = metrics.elidedText(text, Qt.ElideRight, self.lineEdit().width())
        self.lineEdit().setText(elidedText)

    def addItem(self, text, data=None):
        item = QStandardItem()
        item.setText(text)
        if data is None:
            item.setData(text)
        else:
            item.setData(data)
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
        item.setData(Qt.Unchecked, Qt.CheckStateRole)
        self.model().appendRow(item)

    def addItems(self, texts, datalist=None):
        for i, text in enumerate(texts):
            try:
                data = datalist[i]
            except (TypeError, IndexError):
                data = None
            self.addItem(text, data)

    def currentData(self):
        # Return the list of selected items data
        res = []
        for i in range(self.model().rowCount()):
            if self.model().item(i).checkState() == Qt.Checked:
                res.append(self.model().item(i).data())
        return res