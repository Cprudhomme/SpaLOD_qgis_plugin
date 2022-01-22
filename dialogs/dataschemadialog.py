
from qgis.PyQt.QtWidgets import QDialog, QHeaderView, QTableWidgetItem, QProgressDialog
from qgis.PyQt.QtCore import Qt, QUrl
from qgis.PyQt import uic
from qgis.gui import QgsMapCanvas, QgsMapToolPan
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QStandardItem,QStandardItemModel
from qgis.PyQt.QtCore import QSortFilterProxyModel
from qgis.core import Qgis, QgsVectorLayer, QgsRasterLayer, QgsProject, QgsGeometry, QgsCoordinateReferenceSystem, \
    QgsCoordinateTransform, QgsPointXY,QgsApplication, QgsMessageLog

from ..util.ui.uiutils import UIUtils
from ..tasks.dataschemaquerytask import DataSchemaQueryTask
from ..tasks.datasamplequerytask import DataSampleQueryTask
from ..tasks.findstylestask import FindStyleQueryTask
from ..tasks.querylayertask import QueryLayerTask
from ..util.sparqlutils import SPARQLUtils
import os.path


MESSAGE_CATEGORY = 'DataSchemaDialogggg'

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/dataschemadialog.ui'))

# Class representing a search dialog which may be used to search for concepts or properties.
class DataSchemaDialog(QDialog, FORM_CLASS):

    ##
    #  @brief Initializes the search dialog
    #
    #  @param self The object pointer
    #  @param column The column of the GUI widget which called this dialog, if any
    #  @param row The row of the GUI widget which called this dialog, if any
    #  @param triplestoreconf The triple store configuration of the plugin
    #  @param prefixes A list of prefixes known to the plugin
    #  @param interlinkOrEnrich indicates whether this dialog was called from an enrichment or interlinking dialog
    #  @param table The GUI element ot return the result to
    #  @param propOrClass indicates whether a class or a property can be searched
    #  @param bothOptions indicates whether both a class or property may be searched
    #  @param currentprefixes Description for currentprefixes
    #  @param addVocab Description for addVocab
    #  @return Return description
    #
    #  @details More details
    #
    def __init__(self, concept,concepttype,label,triplestoreurl,triplestoreconf,prefixes,title="Data Schema View"):
        super(QDialog, self).__init__()
        self.setupUi(self)
        self.concept=concept
        self.concepttype=concepttype
        self.label=label
        self.prefixes=prefixes
        self.styleprop=[]
        self.alreadyloadedSample=[]
        self.triplestoreconf=triplestoreconf
        self.triplestoreurl=triplestoreurl
        if concepttype==SPARQLUtils.geoclassnode:
            self.setWindowIcon(SPARQLUtils.geoclassicon)
            self.setWindowTitle(title+" (GeoClass)")
        else:
            self.setWindowIcon(SPARQLUtils.classicon)
            self.setWindowTitle(title+" (Class)")
        self.dataSchemaNameLabel.setText(str(label)+" (<a href=\""+str(concept)+"\">"+str(concept[concept.rfind('/')+1:])+"</a>)")
        self.queryAllInstancesButton.clicked.connect(self.queryAllInstances)
        self.vl = QgsVectorLayer("Point", "temporary_points", "memory")
        self.map_canvas.setDestinationCrs(QgsCoordinateReferenceSystem(3857))
        actionPan = QAction("Pan", self)
        actionPan.setCheckable(True)
        actionPan.triggered.connect(lambda: self.map_canvas.setMapTool(self.toolPan))
        self.toolPan = QgsMapToolPan(self.map_canvas)
        self.toolPan.setAction(actionPan)
        self.map_canvas.hide()
        uri = "url=http://a.tile.openstreetmap.org/{z}/{x}/{y}.png&zmin=0&type=xyz&zmax=19&crs=EPSG3857"
        self.mts_layer = QgsRasterLayer(uri, 'OSM', 'wms')
        QgsMessageLog.logMessage(str(self.mts_layer), MESSAGE_CATEGORY, Qgis.Info)
        QgsMessageLog.logMessage(str(self.mts_layer.isValid()), MESSAGE_CATEGORY, Qgis.Info)
        if not self.mts_layer.isValid():
            print("Layer failed to load!")
        self.map_canvas.setExtent(self.mts_layer.extent())
        self.map_canvas.setLayers([self.mts_layer])
        self.map_canvas.setCurrentLayer(self.mts_layer)
        self.map_canvas.setMapTool(self.toolPan)
        header =self.dataSchemaTableView.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tablemodel=QStandardItemModel()
        self.tablemodel.setHeaderData(0, Qt.Horizontal, "Selection")
        self.tablemodel.setHeaderData(1, Qt.Horizontal, "Attribute")
        self.tablemodel.setHeaderData(2, Qt.Horizontal, "Sample Instances")
        self.tablemodel.insertRow(0)
        self.filter_proxy_model = QSortFilterProxyModel()
        self.filter_proxy_model.setSourceModel(self.tablemodel)
        self.filter_proxy_model.setFilterKeyColumn(1)
        self.dataSchemaTableView.setModel(self.filter_proxy_model)
        item = QStandardItem()
        item.setText("Loading...")
        self.tablemodel.setItem(0,0,item)
        self.dataSchemaTableView.entered.connect(lambda modelindex: UIUtils.showTableURI(modelindex, self.dataSchemaTableView, self.statusBarLabel))
        self.dataSchemaTableView.doubleClicked.connect(lambda modelindex: UIUtils.openTableURL(modelindex, self.dataSchemaTableView))
        self.filterTableEdit.textChanged.connect(self.filter_proxy_model.setFilterRegExp)
        self.dataSchemaTableView.clicked.connect(self.loadSamples)
        self.okButton.clicked.connect(self.close)
        QgsMessageLog.logMessage('Started task "{}"'.format(self.triplestoreconf), "DataSchemaDialog", Qgis.Info)
        self.getAttributeStatistics(self.concept,triplestoreurl)


    def queryAllInstances(self):
        querydepth=self.graphQueryDepthBox.value()
        if int(querydepth)>1:
            query=SPARQLUtils.expandRelValToAmount("SELECT ?" + " ?".join(self.triplestoreconf[
                                       "mandatoryvariables"]) + " ?rel ?val\n WHERE\n {\n ?item <"+self.triplestoreconf["typeproperty"]+"> <" + str(
                self.concept) + ">  .\n " +
            self.triplestoreconf["geotriplepattern"][0] + "\n ?item ?rel ?val . }",querydepth)
            self.qlayerinstance = QueryLayerTask(
            "Instance to Layer: " + str(self.concept),
            self.concept,
            self.triplestoreconf["endpoint"],
            query,
            self.triplestoreconf, False, SPARQLUtils.labelFromURI(self.concept), None,self.graphQueryDepthBox.value(),self.shortenURICheckBox.isChecked(),self.styleprop)
        else:
            self.qlayerinstance = QueryLayerTask(
            "Instance to Layer: " + str(self.concept),
                self.concept,
            self.triplestoreconf["endpoint"],
            "SELECT ?" + " ?".join(self.triplestoreconf[
                                       "mandatoryvariables"]) + " ?rel ?val\n WHERE\n {\n ?item <"+self.triplestoreconf["typeproperty"]+"> <" + str(
                self.concept) + "> .\n ?item ?rel ?val . " +
            self.triplestoreconf["geotriplepattern"][0] + "\n }",
            self.triplestoreconf, False, SPARQLUtils.labelFromURI(self.concept), None,self.graphQueryDepthBox.value(),self.shortenURICheckBox.isChecked(),self.styleprop)
        QgsApplication.taskManager().addTask(self.qlayerinstance)

    def loadSamples(self,modelindex):
        row=modelindex.row()
        column=modelindex.column()
        if column==2 and row not in self.alreadyloadedSample:
            relation = str(self.dataSchemaTableView.model().index(row, column-1).data(256))
            self.qtask2 = DataSampleQueryTask("Querying dataset schema.... (" + self.label + ")",
                                             self.triplestoreurl,
                                             self,
                                             self.concept,
                                             relation,
                                             column,row,self.triplestoreconf,self.tablemodel,self.map_canvas)
            QgsApplication.taskManager().addTask(self.qtask2)
            self.alreadyloadedSample.append(row)
        #elif column==2 and row==self.dataSchemaTableView.model().rowCount()-1 and row not in self.alreadyloadedSample:
        #    relation = str(self.dataSchemaTableView.model().index(row, column-1).data(256))
        #    self.qtask3 = FindStyleQueryTask("Querying styles for dataset.... (" + self.label + ")",
        #                                     self.triplestoreurl,
        #                                     self,
        #                                     self.concept,
        #                                     column,row,self.triplestoreconf)
        #    QgsApplication.taskManager().addTask(self.qtask3)

    ##
    #  @brief Gives statistics about most commonly occuring properties from a certain class in a given triple store.
    #  
    #  @param [in] self The object pointer
    #  @return A list of properties with their occurance given in percent
    def getAttributeStatistics(self, concept="wd:Q3914", endpoint_url="https://query.wikidata.org/sparql"):
        QgsMessageLog.logMessage('Started task "{}"'.format(self.triplestoreconf), "DataSchemaDialog", Qgis.Info)
        QgsMessageLog.logMessage('Started task "{}"'.format(str(self.triplestoreconf["endpoint"])), "DataSchemaDialog",
                                 Qgis.Info)
        QgsMessageLog.logMessage('Started task "{}"'.format(self.triplestoreconf["whattoenrichquery"]), "DataSchemaDialog",
                                 Qgis.Info)
        if self.concept == "" or self.concept is None or "whattoenrichquery" not in self.triplestoreconf:
            return
        concept = "<" + self.concept + ">"
        progress = QProgressDialog("Querying dataset schema....", "Abort", 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setWindowIcon(SPARQLUtils.sparqlunicornicon)
        progress.setCancelButton(None)
        self.qtask = DataSchemaQueryTask("Querying dataset schema.... (" + self.label + ")",
                                           self.triplestoreurl,
                                           self.triplestoreconf[
                                               "whattoenrichquery"].replace("%%concept%%", concept),
                                           self.concept,
                                           None,
                                           self.tablemodel,self.triplestoreconf, progress,self,self.styleprop)
        QgsApplication.taskManager().addTask(self.qtask)
