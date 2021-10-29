import os
import re
import json
from qgis.PyQt import uic
from qgis.PyQt import QtWidgets
from qgis.PyQt import QtCore
from qgis.core import QgsProject
from qgis.PyQt.QtCore import QRegExp, QSortFilterProxyModel,Qt,QUrl
from qgis.PyQt.QtGui import QRegExpValidator,QStandardItemModel,QDesktopServices
from qgis.PyQt.QtWidgets import QComboBox,QCompleter,QTableWidgetItem,QHBoxLayout,QPushButton,QWidget,QAbstractItemView,QListView,QMessageBox,QApplication,QMenu,QAction
from rdflib.plugins.sparql import prepareQuery
from .whattoenrich import EnrichmentDialog
from .convertcrsdialog import ConvertCRSDialog
from .tooltipplaintext import ToolTipPlainText
from .enrichmenttab import EnrichmentTab
from .interlinkingtab import InterlinkingTab
from .triplestoredialog import TripleStoreDialog
from .triplestorequickadd import TripleStoreQuickAddDialog
from .searchdialog import SearchDialog
from .sparqlhighlighter import SPARQLHighlighter
from .valuemapping import ValueMappingDialog
from .bboxdialog import BBOXDialog
from .loadgraphdialog import LoadGraphDialog

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'sparql_unicorn_dialog_base_simp.ui'))

##
#  @brief The main dialog window of the SPARQLUnicorn QGIS Plugin.
class SPAQLunicornDialog(QtWidgets.QDialog, FORM_CLASS):
	## The triple store configuration file
    triplestoreconf=None
	## Prefix map
    prefixes=None

    enrichtab=None

    interlinktab=None

    conceptList=None

    completerClassList=None

    columnvars={}


super(SPAQLunicornDialog, self).__init__(parent)
    self.setupUi(self)
    self.prefixes=prefixes
    self.maindlg=maindlg
    self.savedQueriesJSON=savedQueriesJSON
    self.menuEnrichment=Enrichment_MainWindow(self)
    self.menuInterlink=Interlink_MainWindow(self)
    self.addVocabConf=addVocabConf
    self.autocomplete=autocomplete
    self.prefixstore=prefixstore
    self.triplestoreconf=triplestoreconf
    self.searchTripleStoreDialog=TripleStoreDialog(self.triplestoreconf,self.prefixes,self.prefixstore,self.comboBox)
    self.geoClassTree.setEditTriggers(QAbstractItemView.NoEditTriggers)
    self.geoClassTree.setAlternatingRowColors(True)
    self.geoClassTree.setViewMode(QTreeView.TreeMode)
    self.geoClassTree.setContextMenuPolicy(Qt.CustomContextMenu)
    self.geoClassTree.customContextMenuRequested.connect(self.onContext)
    self.geoClassTreeModel=QStandardItemModel()
    self.proxyModel = QSortFilterProxyModel(self)
    self.proxyModel.sort(0)
    self.proxyModel.setSourceModel(self.geoClassTreeModel)
    self.geoClassTree.setModel(self.proxyModel)
    self.geoClassTreeModel.clear()
    self.queryLimit.setValidator(QRegExpValidator(QRegExp("[0-9]*")))
    self.filterConcepts.textChanged.connect(self.setFilterFromText)
    self.inp_sparql2=ToolTipPlainText(self.tab,self.triplestoreconf,self.comboBox,self.columnvars,self.prefixes,self.autocomplete)
    self.inp_sparql2.move(10,130)
    self.inp_sparql2.setMinimumSize(780,401)
    self.inp_sparql2.document().defaultFont().setPointSize(16)
    self.inp_sparql2.setPlainText("SELECT ?item ?lat ?lon WHERE {\n ?item ?b ?c .\n ?item <http://www.wikidata.org/prop:P123> ?def .\n}")
    self.inp_sparql2.columnvars={}
    self.inp_sparql2.textChanged.connect(self.validateSPARQL)
    self.sparqlhighlight = SPARQLHighlighter(self.inp_sparql2)
    #self.areaconcepts.hide()
    #self.areas.hide()
    #self.label_8.hide()
    #self.label_9.hide()
    #self.savedQueries.hide()
    #self.loadQuery.hide()
    #self.saveQueryButton.hide()
    #self.saveQueryName.hide()
    #self.savedQueryLabel.hide()
    #self.saveQueryName_2.hide()
    self.enrichTableResult.hide()
    self.queryTemplates.currentIndexChanged.connect(self.viewselectaction)
    self.bboxButton.clicked.connect(self.getPointFromCanvas)
    self.interlinkTable.cellClicked.connect(self.createInterlinkSearchDialog)
    self.enrichTable.cellClicked.connect(self.createEnrichSearchDialog)
    self.convertTTLCRS.clicked.connect(self.buildConvertCRSDialog)
    self.chooseLayerInterlink.clear()
    self.searchClass.clicked.connect(self.createInterlinkSearchDialog)
    urlregex = QRegExp("http[s]?://(?:[a-zA-Z#]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+")
    urlvalidator = QRegExpValidator(urlregex, self)
    self.interlinkNameSpace.setValidator(urlvalidator)
    self.interlinkNameSpace.textChanged.connect(self.check_state3)
    self.interlinkNameSpace.textChanged.emit(self.interlinkNameSpace.text())
    self.addEnrichedLayerButton.clicked.connect(self.enrichtab.addEnrichedLayer)
    self.startEnrichment.clicked.connect(self.enrichtab.enrichLayerProcess)
    self.exportInterlink.clicked.connect(self.enrichtab.exportEnrichedLayer)
    self.loadQuery.clicked.connect(self.loadQueryFunc)
    self.saveQueryButton.clicked.connect(self.saveQueryFunc)
    self.exportMappingButton.clicked.connect(self.interlinktab.exportMapping)
    self.importMappingButton.clicked.connect(self.interlinktab.loadMapping)
    self.loadLayerInterlink.clicked.connect(self.loadLayerForInterlink)
    self.loadLayerEnrich.clicked.connect(self.loadLayerForEnrichment)
    self.addEnrichedLayerRowButton.clicked.connect(self.addEnrichRow)
    self.geoClassTree.selectionModel().selectionChanged.connect(self.viewselectaction)
    self.loadFileButton.clicked.connect(self.buildLoadGraphDialog)
    self.refreshLayersInterlink.clicked.connect(self.loadUnicornLayers)
    self.btn_loadunicornlayers.clicked.connect(self.loadUnicornLayers)
    self.whattoenrich.clicked.connect(self.createWhatToEnrich)
    self.quickAddTripleStore.clicked.connect(self.buildQuickAddTripleStore)
    self.loadTripleStoreButton.clicked.connect(self.buildCustomTripleStoreDialog)
    self.loadUnicornLayers()
