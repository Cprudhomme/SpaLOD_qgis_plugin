# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SPAQLunicornDialog
                                 A QGIS plugin
 This plugin adds a GeoJSON layer from a Wikidata SPARQL query.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2019-10-28
        git sha              : $Format:%H$
        copyright            : (C) 2019 by SPARQL Unicorn
        email                : rse@fthiery.de
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
import re
import json
from qgis.PyQt import uic, QtWidgets
from qgis.core import QgsProject,QgsMessageLog, Qgis,QgsApplication
from qgis.PyQt.QtCore import Qt, QUrl
from qgis.PyQt.QtGui import QStandardItemModel, QDesktopServices, QIcon
from qgis.PyQt.QtWidgets import QAbstractItemView, QMessageBox, QApplication, QMenu, QAction, QFileDialog, QStyle, QProgressDialog
from rdflib.plugins.sparql import prepareQuery

from .menu.conceptcontextmenu import ConceptContextMenu
from ..dialogs.convertcrsdialog import ConvertCRSDialog
from ..dialogs.triplestoredialog import TripleStoreDialog
from ..dialogs.querylimitedinstancesdialog import QueryLimitedInstancesDialog
from ..dialogs.graphvalidationdialog import GraphValidationDialog
from ..dialogs.triplestorequickadddialog import TripleStoreQuickAddDialog
from ..dialogs.searchdialog import SearchDialog
from ..dialogs.valuemappingdialog import ValueMappingDialog
from ..dialogs.convertlayerdialog import ConvertLayerDialog
from ..dialogs.bboxdialog import BBOXDialog
from ..dialogs.dataschemadialog import DataSchemaDialog
from ..dialogs.instancedatadialog import InstanceDataDialog
from ..tabs.enrichmenttab import EnrichmentTab
from ..tabs.interlinkingtab import InterlinkingTab
from ..tasks.querylayertask import QueryLayerTask
from ..tasks.subclassquerytask import SubClassQueryTask
from ..tasks.instanceamountquerytask import InstanceAmountQueryTask
from ..tasks.instancelistquerytask import InstanceListQueryTask
from ..util.ui.uiutils import UIUtils
from ..util.ui.tooltipplaintext import ToolTipPlainText
from ..util.ui.sparqlhighlighter import SPARQLHighlighter
from ..util.ui.classtreesortproxymodel import ClassTreeSortProxyModel
from ..util.sparqlutils import SPARQLUtils

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/sparql_unicorn_dialog_base.ui'))

MESSAGE_CATEGORY = 'SPARQLUnicornDialog'

##
#  @brief The main dialog window of the SPARQLUnicorn QGIS Plugin.
class SPARQLunicornDialog(QtWidgets.QMainWindow, FORM_CLASS):
    ## The triple store configuration file
    triplestoreconf = None
    ## Prefix map
    prefixes = None

    enrichtab = None

    interlinktab = None

    conceptList = None

    completerClassList = None

    columnvars = {}

    def __init__(self, triplestoreconf={}, prefixes=[], addVocabConf={}, autocomplete={},
                 prefixstore={"normal": {}, "reversed": {}}, savedQueriesJSON={}, maindlg=None, parent=None):
        """Constructor."""
        super(SPARQLunicornDialog, self).__init__(parent)
        self.setupUi(self)
        self.setCentralWidget(self.tabWidget)
        self.prefixes = prefixes
        self.maindlg = maindlg
        self.savedQueriesJSON = savedQueriesJSON
        self.enrichtab = EnrichmentTab(self)
        self.interlinktab = InterlinkingTab(self)
        self.addVocabConf = addVocabConf
        self.autocomplete = autocomplete
        self.prefixstore = prefixstore
        self.triplestoreconf = triplestoreconf
        self.searchTripleStoreDialog = TripleStoreDialog(self.triplestoreconf, self.prefixes, self.prefixstore,
                                                         self.comboBox)
        self.layercount=0
        self.geoTreeView.customContextMenuRequested.connect(self.onContext)
        self.geoTreeViewModel = QStandardItemModel()
        self.geoTreeView.setModel(self.geoTreeViewModel)
        self.classTreeView.customContextMenuRequested.connect(self.onContext4)
        self.featureCollectionClassListModel = QStandardItemModel()
        self.geometryCollectionClassListModel = QStandardItemModel()
        self.classTreeViewModel = QStandardItemModel()
        self.proxyModel = ClassTreeSortProxyModel(self.geoTreeViewModel)
        self.featureCollectionProxyModel = ClassTreeSortProxyModel(self.featureCollectionClassListModel)
        self.geometryCollectionProxyModel = ClassTreeSortProxyModel(self.geometryCollectionClassListModel)
        self.classTreeViewProxyModel = ClassTreeSortProxyModel(self.classTreeViewModel)
        self.classTreeView.setModel(self.classTreeViewProxyModel)
        self.geoTreeView.setModel(self.proxyModel)
        self.geoTreeViewModel.clear()
        self.rootNode = self.geoTreeViewModel.invisibleRootItem()
        self.featureCollectionClassList.setModel(self.featureCollectionProxyModel)
        self.featureCollectionClassList.customContextMenuRequested.connect(self.onContext2)
        self.featureCollectionClassListModel.clear()
        self.geometryCollectionClassList.setModel(self.geometryCollectionProxyModel)
        self.geometryCollectionClassList.customContextMenuRequested.connect(self.onContext3)
        self.geometryCollectionClassListModel.clear()
        self.geoTreeView.doubleClicked.connect(self.createLayerFromTreeEntry)
        self.classTreeView.doubleClicked.connect(self.createLayerFromTreeEntry)
        #self.queryLimit.setValidator(QRegExpValidator(QRegExp("[0-9]*")))
        self.filterConcepts.textChanged.connect(lambda: self.currentProxyModel.setFilterRegExp(self.filterConcepts.text()))
        self.inp_sparql2 = ToolTipPlainText(self.queryTab, self.triplestoreconf, self.comboBox, self.columnvars,
                                            self.prefixes, self.autocomplete,self.triplestoreconf[self.comboBox.currentIndex()])
        self.inp_sparql2.move(10, 100)
        self.inp_sparql2.setMinimumSize(780, 471)
        self.inp_sparql2.document().defaultFont().setPointSize(16)
        self.inp_sparql2.setPlainText(
            "SELECT ?item ?lat ?lon WHERE {\n ?item ?b ?c .\n} LIMIT 10")
        self.inp_sparql2.columnvars = {}
        self.inp_sparql2.textChanged.connect(self.validateSPARQL)
        self.sparqlhighlight = SPARQLHighlighter(self.inp_sparql2)
        self.currentContext=self.classTreeView
        self.currentProxyModel=self.classTreeViewProxyModel
        self.currentContextModel=self.classTreeViewModel
        self.conceptSelectAction()
        self.enrichTableResult.hide()
        self.queryTemplates.currentIndexChanged.connect(self.conceptSelectAction)
        self.actionConvert_RDF_Data.triggered.connect(lambda: ConvertCRSDialog(self.triplestoreconf, self.maindlg, self).exec())
        self.actionLayer_Column_as_Variable.triggered.connect(self.inp_sparql2.createVarInputDialog)
        self.actionConvert_QGIS_Layer_To_RDF.triggered.connect(lambda: ConvertLayerDialog(self.triplestoreconf, self.maindlg.prefixes, self.maindlg, self).exec())
        self.actionTriple_Store_Settings.triggered.connect(lambda: TripleStoreDialog(self.triplestoreconf, self.prefixes, self.prefixstore,self.comboBox).exec())
        self.actionValidate_RDF_Data.triggered.connect(lambda: GraphValidationDialog(self.triplestoreconf, self.maindlg, self).exec())
        self.actionConstraint_By_BBOX.triggered.connect(lambda: BBOXDialog(self.inp_sparql2, self.triplestoreconf, self.comboBox.currentIndex()).exec())
        self.tripleStoreInfoButton.setIcon(QIcon(self.style().standardIcon(getattr(QStyle,'SP_MessageBoxInformation'))))
        self.tripleStoreInfoButton.clicked.connect(self.tripleStoreInfoDialog)
        self.loadQuery.clicked.connect(self.loadQueryFunc)
        self.saveQueryButton.clicked.connect(self.saveQueryFunc)
        self.geoTreeView.selectionModel().currentChanged.connect(self.conceptSelectAction)
        self.classTreeView.selectionModel().currentChanged.connect(self.conceptSelectAction)
        self.conceptViewTabWidget.currentChanged.connect(self.tabchanged)
        self.conceptViewTabWidget.customContextMenuRequested.connect(self.tabContextMenu)
        self.featureCollectionClassList.selectionModel().currentChanged.connect(self.collectionSelectAction)
        self.geometryCollectionClassList.selectionModel().currentChanged.connect(self.collectionSelectAction)
        self.quickAddTripleStore.clicked.connect(lambda: TripleStoreQuickAddDialog(self.triplestoreconf, self.prefixes, self.prefixstore,
                                                                 self.comboBox,self.maindlg,self).exec())
        self.show()

    def tripleStoreInfoDialog(self):
        msgBox = QMessageBox()
        msgBox.setWindowTitle("RDF Resource Information")
        thetext="<html><h3>Information about "+str(self.triplestoreconf[self.comboBox.currentIndex()]["name"])+"</h3><table border=1 cellspacing=0><tr><th>Information</th><th>Value</th></tr>"
        thetext+="<tr><td>Name</td><td>"+str(self.triplestoreconf[self.comboBox.currentIndex()]["name"])+"</td></tr>"
        thetext+="<tr><td>Type</td><td>"+str(self.triplestoreconf[self.comboBox.currentIndex()]["type"])+"</td></tr>"
        thetext+="<tr><td>Endpoint</td><td><a href=\""+str(self.triplestoreconf[self.comboBox.currentIndex()]["endpoint"])+"\">"+str(self.triplestoreconf[self.comboBox.currentIndex()]["endpoint"])+"</a></td></tr>"
        thetext+="<tr><td>Type Property</td><td><a href=\""+str(self.triplestoreconf[self.comboBox.currentIndex()]["typeproperty"])+"\">"+str(self.triplestoreconf[self.comboBox.currentIndex()]["typeproperty"])+"</a></td></tr>"
        thetext+="<tr><td>Label Property</td><td><a href=\""+str(self.triplestoreconf[self.comboBox.currentIndex()]["labelproperty"])+"\">"+str(self.triplestoreconf[self.comboBox.currentIndex()]["labelproperty"])+"</a></td></tr>"
        thetext+="</html>"
        msgBox.setText(thetext)
        msgBox.exec()

    def loadQueryFunc(self):
        if self.triplestoreconf[self.comboBox.currentIndex()]["endpoint"] in self.savedQueriesJSON:
            self.inp_sparql2.setPlainText(
                self.savedQueriesJSON[self.triplestoreconf[self.comboBox.currentIndex()]["endpoint"]][
                    self.savedQueries.currentIndex()]["query"])

    def saveQueryFunc(self):
        queryName = self.saveQueryName.text()
        if queryName is not None and queryName != "":
            __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
            if not self.triplestoreconf[self.comboBox.currentIndex()]["endpoint"] in self.savedQueriesJSON:
                self.savedQueriesJSON[self.triplestoreconf[self.comboBox.currentIndex()]["endpoint"]] = []
            self.savedQueriesJSON[self.triplestoreconf[self.comboBox.currentIndex()]["endpoint"]].append(
                {"label": queryName, "query": self.inp_sparql2.toPlainText()})
            self.savedQueries.addItem(queryName)
            f = open(os.path.join(__location__, 'savedqueries.json'), "w")
            f.write(json.dumps(self.savedQueriesJSON))
            f.close()

    currentContext=None
    currentContextModel=None
    currentProxyModel=None

    def onContext(self,position):
        self.currentContext=self.geoTreeView
        self.currentContextModel = self.geoTreeViewModel
        self.currentProxyModel = self.proxyModel
        self.createMenu(position)

    def onContext2(self, position):
        self.currentContext=self.featureCollectionClassList
        self.currentContextModel = self.featureCollectionClassListModel
        self.currentProxyModel = self.featureCollectionProxyModel
        self.createMenu(position)

    def onContext3(self, position):
        self.currentContext = self.geometryCollectionClassList
        self.currentContextModel = self.geometryCollectionClassListModel
        self.currentProxyModel = self.geometryCollectionProxyModel
        self.createMenu(position)

    def tabContextMenu(self,position):
        menu = QMenu("Menu", self.conceptViewTabWidget)
        actionsaveRDF=QAction("Save Contents as RDF")
        menu.addAction(actionsaveRDF)
        actionsaveRDF.triggered.connect(self.saveTreeToRDF)
        actionsaveClassesRDF=QAction("Save Classes as RDF")
        menu.addAction(actionsaveClassesRDF)
        actionsaveClassesRDF.triggered.connect(self.saveClassesTreeToRDF)
        actionsaveVisibleRDF=QAction("Save Visible Contents as RDF")
        menu.addAction(actionsaveVisibleRDF)
        actionsaveVisibleRDF.triggered.connect(self.saveVisibleTreeToRDF)
        menu.exec_(self.currentContext.viewport().mapToGlobal(position))



    def createMenu(self,position):
        curindex = self.currentProxyModel.mapToSource(self.currentContext.selectionModel().currentIndex())
        nodetype = self.currentContextModel.itemFromIndex(curindex).data(257)
        menu = QMenu("Menu", self.currentContext)
        actionclip=QAction("Copy IRI to clipboard")
        menu.addAction(actionclip)
        actionclip.triggered.connect(lambda: ConceptContextMenu.copyClipBoard(self.currentContextModel.itemFromIndex(self.currentProxyModel.mapToSource(self.currentContext.selectionModel().currentIndex()))))
        action = QAction("Open in Webbrowser")
        menu.addAction(action)
        action.triggered.connect(lambda: QDesktopServices.openUrl(QUrl(self.currentContextModel.itemFromIndex(self.currentProxyModel.mapToSource(self.currentContext.selectionModel().currentIndex())).data(256))))
        if nodetype!=SPARQLUtils.instancenode and nodetype!=SPARQLUtils.geoinstancenode:
            actioninstancecount=QAction("Check instance count")
            menu.addAction(actioninstancecount)
            actioninstancecount.triggered.connect(self.instanceCount)
            actiondataschema = QAction("Query data schema")
            menu.addAction(actiondataschema)
            actiondataschema.triggered.connect(lambda: DataSchemaDialog(
                self.currentContextModel.itemFromIndex(self.currentProxyModel.mapToSource(self.currentContext.selectionModel().currentIndex())).data(256),
                self.currentContextModel.itemFromIndex(self.currentProxyModel.mapToSource(self.currentContext.selectionModel().currentIndex())).data(257),
                self.currentContextModel.itemFromIndex(self.currentProxyModel.mapToSource(self.currentContext.selectionModel().currentIndex())).text(),
                self.triplestoreconf[self.comboBox.currentIndex()]["endpoint"],
                self.triplestoreconf,self.prefixes,self.comboBox.currentIndex(),
                "Data Schema View for " + SPARQLUtils.labelFromURI(str(self.currentContextModel.itemFromIndex(self.currentProxyModel.mapToSource(self.currentContext.selectionModel().currentIndex())).data(256)),
                                                                   self.triplestoreconf[
                                                                       self.comboBox.currentIndex()][
                                                                       "prefixesrev"])
                ).exec_())
            actionqueryinstances = QAction("Query all instances")
            menu.addAction(actionqueryinstances)
            actionqueryinstances.triggered.connect(self.instanceList)
            if "subclassquery" in self.triplestoreconf[self.comboBox.currentIndex()]:
                action2 = QAction("Load subclasses")
                menu.addAction(action2)
                action2.triggered.connect(self.loadSubClasses)
            actionsubclassquery = QAction("Create subclass query")
            menu.addAction(actionsubclassquery)
            actionsubclassquery.triggered.connect(self.subclassQuerySelectAction)
            actionquerysomeinstances=QAction("Add some instances as new layer")
            menu.addAction(actionquerysomeinstances)
            actionquerysomeinstances.triggered.connect(lambda: QueryLimitedInstancesDialog(
                self.triplestoreconf[self.comboBox.currentIndex()],
                self.currentContextModel.itemFromIndex(self.currentProxyModel.mapToSource(self.currentContext.selectionModel().currentIndex())).data(256),
                self.currentContextModel.itemFromIndex(self.currentProxyModel.mapToSource(self.currentContext.selectionModel().currentIndex())).data(257)
            ).exec_())
            actionaddallInstancesAsLayer = QAction("Add all instances as new layer")
            menu.addAction(actionaddallInstancesAsLayer)
            actionaddallInstancesAsLayer.triggered.connect(self.dataAllInstancesAsLayer)
        else:
            actiondataschema2 = QAction("Query data")
            menu.addAction(actiondataschema2)
            actiondataschema2.triggered.connect(self.dataInstanceView)
            actionaddInstanceAsLayer = QAction("Add instance as new layer")
            menu.addAction(actionaddInstanceAsLayer)
            actionaddInstanceAsLayer.triggered.connect(self.dataInstanceAsLayer)
        actionapplicablestyles=QAction("Find applicable styles")
        menu.addAction(actionapplicablestyles)
        actionapplicablestyles.triggered.connect(self.appStyles)
        menu.exec_(self.currentContext.viewport().mapToGlobal(position))


    def onContext4(self, position):
        self.currentContext = self.classTreeView
        self.currentContextModel = self.classTreeViewModel
        self.currentProxyModel = self.classTreeViewProxyModel
        self.createMenu(position)

    #def copyClipBoard(self):
    #    curindex = self.currentProxyModel.mapToSource(self.currentContext.selectionModel().currentIndex())
    #    concept = self.currentContextModel.itemFromIndex(curindex).data(256)
    #    cb = QApplication.clipboard()
    #    cb.clear(mode=cb.Clipboard)
    #    cb.setText(concept, mode=cb.Clipboard)

    def instanceCount(self):
        curindex = self.currentProxyModel.mapToSource(self.currentContext.selectionModel().currentIndex())
        concept = self.currentContextModel.itemFromIndex(curindex).data(256)
        label = self.currentContextModel.itemFromIndex(curindex).text()
        if not label.endswith("]"):
            self.qtaskinstance = InstanceAmountQueryTask(
                "Getting instance count for " + str(concept),
                self.triplestoreconf[self.comboBox.currentIndex()]["endpoint"], self, self.currentContextModel.itemFromIndex(curindex),self.triplestoreconf[self.comboBox.currentIndex()])
            QgsApplication.taskManager().addTask(self.qtaskinstance)

    def instanceList(self):
        curindex = self.currentProxyModel.mapToSource(self.currentContext.selectionModel().currentIndex())
        concept = self.currentContextModel.itemFromIndex(curindex).data(256)
        alreadyloadedindicator = self.currentContextModel.itemFromIndex(curindex).data(259)
        if alreadyloadedindicator!=SPARQLUtils.instancesloadedindicator:
            self.qtaskinstanceList = InstanceListQueryTask(
                "Getting instance count for " + str(concept),
                self.triplestoreconf[self.comboBox.currentIndex()]["endpoint"], self, self.currentContextModel.itemFromIndex(curindex),self.triplestoreconf[self.comboBox.currentIndex()])
            QgsApplication.taskManager().addTask(self.qtaskinstanceList)

    def dataInstanceView(self):
        curindex = self.currentProxyModel.mapToSource(self.currentContext.selectionModel().currentIndex())
        concept = self.currentContextModel.itemFromIndex(curindex).data(256)
        nodetype = self.currentContextModel.itemFromIndex(curindex).data(257)
        label = self.currentContextModel.itemFromIndex(curindex).text()
        self.instancedataDialog = InstanceDataDialog(concept,nodetype,label,self.triplestoreconf[self.comboBox.currentIndex()]["endpoint"],self.triplestoreconf,self.prefixes,self.comboBox.currentIndex())
        self.instancedataDialog.setWindowTitle("Data Instance View for "+SPARQLUtils.labelFromURI(str(concept),self.triplestoreconf[self.comboBox.currentIndex()]["prefixesrev"]))
        self.instancedataDialog.exec_()

    def dataInstanceAsLayer(self):
        curindex = self.currentProxyModel.mapToSource(self.currentContext.selectionModel().currentIndex())
        concept = self.currentContextModel.itemFromIndex(curindex).data(256)
        nodetype = self.currentContextModel.itemFromIndex(curindex).data(257)
        if nodetype==SPARQLUtils.geoinstancenode:
            if "geotriplepattern" in self.triplestoreconf[self.comboBox.currentIndex()]:
                self.qlayerinstance = QueryLayerTask(
                    "Instance to Layer: " + str(concept),
                    self.triplestoreconf[self.comboBox.currentIndex()]["endpoint"],
                    "SELECT ?"+" ?".join(self.triplestoreconf[self.comboBox.currentIndex()]["mandatoryvariables"])+" ?rel ?val\n WHERE\n {\n BIND( <" + str(concept) + "> AS ?item)\n ?item ?rel ?val . " +
                    self.triplestoreconf[self.comboBox.currentIndex()]["geotriplepattern"][0] + "\n }",
                    self.triplestoreconf[self.comboBox.currentIndex()], False, SPARQLUtils.labelFromURI(concept), None)
            else:
                self.qlayerinstance = QueryLayerTask(
                "Instance to Layer: " + str(concept),
                self.triplestoreconf[self.comboBox.currentIndex()]["endpoint"],
                "SELECT ?item ?rel ?val \n WHERE\n {\n BIND( <"+str(concept)+"> AS ?item)\n ?item ?rel ?val . \n }",
                self.triplestoreconf[self.comboBox.currentIndex()],True, SPARQLUtils.labelFromURI(concept),None)
        else:
            self.qlayerinstance = QueryLayerTask(
                "Instance to Layer: " + str(concept),
                self.triplestoreconf[self.comboBox.currentIndex()]["endpoint"],
                "SELECT ?item ?rel ?val\n WHERE\n {\n BIND( <"+str(concept)+"> AS ?item)\n ?item ?rel ?val .\n }",
                self.triplestoreconf[self.comboBox.currentIndex()],True, SPARQLUtils.labelFromURI(concept),None)
        QgsApplication.taskManager().addTask(self.qlayerinstance)

    def dataAllInstancesAsLayer(self):
        curindex = self.currentProxyModel.mapToSource(self.currentContext.selectionModel().currentIndex())
        concept = self.currentContextModel.itemFromIndex(curindex).data(256)
        nodetype = self.currentContextModel.itemFromIndex(curindex).data(257)
        progress = QProgressDialog(
            "Querying all instances for " + concept,"Abort", 0, 0, self)
        progress.setWindowTitle("Query all instances")
        progress.setWindowModality(Qt.WindowModal)
        if nodetype==SPARQLUtils.geoclassnode:
            if "geotriplepattern" in self.triplestoreconf[self.comboBox.currentIndex()]:
                self.qlayerinstance = QueryLayerTask(
                "All Instances to Layer: " + str(concept),
                    self.triplestoreconf[self.comboBox.currentIndex()]["endpoint"],
                "SELECT ?"+" ?".join(self.triplestoreconf[self.comboBox.currentIndex()]["mandatoryvariables"])+" ?rel ?val\n WHERE\n {\n ?item <"+str(self.triplestoreconf[self.comboBox.currentIndex()]["typeproperty"])+"> <"+str(concept)+"> . ?item ?rel ?val . "+self.triplestoreconf[self.comboBox.currentIndex()]["geotriplepattern"][0]+"\n }",
                self.triplestoreconf[self.comboBox.currentIndex()],False, SPARQLUtils.labelFromURI(concept),progress)
            else:
                self.qlayerinstance = QueryLayerTask(
                "All Instances to Layer: " + str(concept),
                    self.triplestoreconf[self.comboBox.currentIndex()]["endpoint"],
                "SELECT ?item ?rel ?val\n WHERE\n {\n ?item <"+str(self.triplestoreconf[self.comboBox.currentIndex()]["typeproperty"])+"> <"+str(concept)+"> .\n ?item ?rel ?val .\n }",
                self.triplestoreconf[self.comboBox.currentIndex()],True, SPARQLUtils.labelFromURI(concept),progress)
        else:
            self.qlayerinstance = QueryLayerTask(
                "All Instances to Layer: " + str(concept),
                self.triplestoreconf[self.comboBox.currentIndex()]["endpoint"],
                "SELECT ?item ?rel ?val\n WHERE\n {\n ?item <"+str(self.triplestoreconf[self.comboBox.currentIndex()]["typeproperty"])+"> <"+str(concept)+"> . ?item ?rel ?val .\n }",
                self.triplestoreconf[self.comboBox.currentIndex()],True, SPARQLUtils.labelFromURI(concept),progress)
        QgsApplication.taskManager().addTask(self.qlayerinstance)

    def appStyles(self):
        curindex = self.currentProxyModel.mapToSource(self.currentContext.selectionModel().currentIndex())
        concept = self.currentContextModel.itemFromIndex(curindex).data(256)
        label = self.currentContextModel.itemFromIndex(curindex).text()
        #self.dataschemaDialog = DataSchemaDialog(concept,label,self.triplestoreconf[self.comboBox.currentIndex()]["endpoint"],self.triplestoreconf,self.prefixes,self.comboBox.currentIndex())
        #self.dataschemaDialog.setWindowTitle("Data Schema View for "+str(concept))
        #self.dataschemaDialog.exec_()

    def createLayerFromTreeEntry(self):
        curindex = self.currentProxyModel.mapToSource(self.currentContext.selectionModel().currentIndex())
        nodetype = self.currentContextModel.itemFromIndex(curindex).data(257)
        if nodetype==SPARQLUtils.geoclassnode or nodetype==SPARQLUtils.classnode:
            self.dataAllInstancesAsLayer()
        elif nodetype==SPARQLUtils.geoinstancenode or nodetype==SPARQLUtils.instancenode:
            self.dataInstanceAsLayer()

    def loadSubClasses(self):
        print("Load SubClasses")
        curindex = self.currentProxyModel.mapToSource(self.currentContext.selectionModel().currentIndex())
        concept = self.currentContextModel.itemFromIndex(curindex).data(256)
        if "subclassquery" in self.triplestoreconf[self.comboBox.currentIndex()]:
            if "wikidata" in self.triplestoreconf[self.comboBox.currentIndex()]["endpoint"]:
                query=self.triplestoreconf[self.comboBox.currentIndex()]["subclassquery"].replace("%%concept%%",str("wd:" + concept[concept.find('(')+1:-1]))
            else:
                query=self.triplestoreconf[self.comboBox.currentIndex()]["subclassquery"].replace("%%concept%%","<"+str(concept)+">")
            prefixestoadd=""
            for endpoint in self.triplestoreconf[self.comboBox.currentIndex()]["prefixes"]:
                    prefixestoadd += "PREFIX " + endpoint + ": <" + self.triplestoreconf[self.comboBox.currentIndex()]["prefixes"][
                        endpoint] + "> \n"
            self.qtasksub = SubClassQueryTask("Querying QGIS Layer from " + self.triplestoreconf[self.comboBox.currentIndex()]["endpoint"],
                                    self.triplestoreconf[self.comboBox.currentIndex()]["endpoint"],
                                    prefixestoadd + query,None,self,
                                    self.currentContextModel.itemFromIndex(curindex),concept,self.triplestoreconf[self.comboBox.currentIndex()])
            QgsApplication.taskManager().addTask(self.qtasksub)

    def tabchanged(self,index):
        #QgsMessageLog.logMessage('Started task "{}"'.format("Tab changed! "+str(index)), MESSAGE_CATEGORY, Qgis.Info)
        if self.currentProxyModel!=None:
            self.currentProxyModel.setFilterRegExp("")
        self.filterConcepts.setText("")
        if index==0:
            self.currentProxyModel=self.proxyModel
            self.currentContext = self.geoTreeView
            self.currentContextModel = self.geoTreeViewModel
        elif index==1:
            self.currentProxyModel=self.featureCollectionProxyModel
            self.currentContext = self.featureCollectionClassList
            self.currentContextModel = self.featureCollectionClassListModel
        elif index==2:
            self.currentProxyModel=self.geometryCollectionProxyModel
            self.currentContext = self.geometryCollectionClassList
            self.currentContextModel = self.geometryCollectionClassListModel
        elif index==3:
            self.currentProxyModel=self.classTreeViewProxyModel
            self.currentContext = self.classTreeView
            self.currentContextModel = self.classTreeViewModel

    def buildUploadRDFDialog(self):
        print("todo")
        #uploaddialog = UploadRDFDialog(ttlstring, self.triplestoreconf)
        #uploaddialog.setMinimumSize(450, 250)
        #uploaddialog.setWindowTitle("Upload interlinked dataset to triple store ")
        #uploaddialog.exec_()

    def collectionSelectAction(self):
        endpointIndex = self.comboBox.currentIndex()
        if endpointIndex == 0:
            self.justloadingfromfile = False
            return
        curindex = self.currentProxyModel.mapToSource(self.currentContext.selectionModel().currentIndex())
        if self.currentContext.selectionModel().currentIndex() is not None and self.currentContextModel.itemFromIndex(
                curindex) is not None:
            concept = self.currentContextModel.itemFromIndex(curindex).data(256)
            querytext = self.triplestoreconf[endpointIndex]["querytemplate"][self.queryTemplates.currentIndex()][
            "query"].replace("?item a <%%concept%%>", "<"+concept+"> rdfs:member ?item ")
            self.inp_sparql2.setPlainText(querytext)
            self.inp_sparql2.columnvars = {}

    def subclassQuerySelectAction(self):
        endpointIndex = self.comboBox.currentIndex()
        if endpointIndex == 0:
            self.justloadingfromfile = False
            return
        curindex = self.currentProxyModel.mapToSource(self.currentContext.selectionModel().currentIndex())
        if self.currentContext.selectionModel().currentIndex() is not None and self.currentContextModel.itemFromIndex(
                curindex) is not None:
            concept = self.currentContextModel.itemFromIndex(curindex).data(256)
            querytext = self.triplestoreconf[endpointIndex]["querytemplate"][self.queryTemplates.currentIndex()][
            "query"].replace("?item a <%%concept%%>", "?item a ?con . ?con rdfs:subClassOf* <"+concept+"> ")
            self.inp_sparql2.setPlainText(querytext)
            self.inp_sparql2.columnvars = {}

    def conceptSelectAction(self):
        endpointIndex = self.comboBox.currentIndex()
        if endpointIndex == 0:
            self.justloadingfromfile = False
            return
        concept = ""
        curindex = self.currentProxyModel.mapToSource(self.currentContext.selectionModel().currentIndex())
        if self.currentContext.selectionModel().currentIndex() is not None and self.currentContextModel.itemFromIndex(
                curindex) is not None and re.match(r'.*Q[0-9]+.*', self.currentContextModel.itemFromIndex(
            curindex).text()) and not self.currentContextModel.itemFromIndex(curindex).text().startswith("http"):
            self.inp_label.setText(
                self.currentContextModel.itemFromIndex(curindex).text().split("(")[0].lower().replace(" ", "_"))
            concept = "Q" + self.currentContextModel.itemFromIndex(curindex).text().split("Q")[1].replace(")", "")
        elif self.currentContextModel.itemFromIndex(curindex) is not None:
            concept = self.currentContextModel.itemFromIndex(curindex).data(256)
        if "querytemplate" in self.triplestoreconf[endpointIndex]:
            if "wd:Q%%concept%% ." in \
                    self.triplestoreconf[endpointIndex]["querytemplate"][self.queryTemplates.currentIndex()]["query"]:
                querytext = ""
                if concept != None and concept.startswith("http"):
                    querytext = \
                        self.triplestoreconf[endpointIndex]["querytemplate"][self.queryTemplates.currentIndex()][
                            "query"].replace("wd:Q%%concept%% .", "wd:" + concept[concept.rfind('/') + 1:] + " .")
                elif concept != None:
                    querytext = \
                        self.triplestoreconf[endpointIndex]["querytemplate"][self.queryTemplates.currentIndex()][
                            "query"].replace("wd:Q%%concept%% .", "wd:" + concept + " .")
            elif "querytemplate" in self.triplestoreconf[endpointIndex] and self.triplestoreconf[endpointIndex]["querytemplate"]!=None:
                querytext = self.triplestoreconf[endpointIndex]["querytemplate"][self.queryTemplates.currentIndex()][
                    "query"].replace("%%concept%%", concept)
            #if self.queryLimit.text().isnumeric() and querytext.rfind("LIMIT") != -1:
            #    querytext = querytext[0:querytext.rfind("LIMIT")] + "LIMIT " + self.queryLimit.text()
            #elif self.queryLimit.text().isnumeric() and querytext.rfind("LIMIT") == -1:
            #    querytext = querytext + " LIMIT " + self.queryLimit.text()
            self.inp_sparql2.setPlainText(querytext)
            self.inp_sparql2.columnvars = {}
        if self.currentContext.selectionModel().currentIndex() is not None and self.currentContextModel.itemFromIndex(
                curindex) is not None and "#" in self.currentContextModel.itemFromIndex(curindex).text():
            self.inp_label.setText(self.currentContextModel.itemFromIndex(curindex).text()[
                                   self.currentContextModel.itemFromIndex(curindex).text().rfind(
                                       '#') + 1:].lower().replace(" ", "_"))
        elif self.currentContext.selectionModel().currentIndex() is not None and self.currentContextModel.itemFromIndex(
                curindex) is not None:
            self.inp_label.setText(self.currentContextModel.itemFromIndex(curindex).text()[
                                   self.currentContextModel.itemFromIndex(curindex).text().rfind(
                                       '/') + 1:].lower().replace(" ", "_"))

    ## Validates the SPARQL query in the input field and outputs errors in a label.
    #  @param self The object pointer.
    def validateSPARQL(self):
        if self.inp_sparql2.toPlainText() is not None and self.inp_sparql2.toPlainText() != "":
            try:
                if self.prefixes is not None and len(self.prefixes)>self.comboBox.currentIndex() and self.prefixes[self.comboBox.currentIndex()] != None and self.prefixes[self.comboBox.currentIndex()] != "":
                    prepareQuery(
                        "".join(self.prefixes[self.comboBox.currentIndex()]) + "\n" + self.inp_sparql2.toPlainText())
                else:
                    prepareQuery(self.inp_sparql2.toPlainText())
                self.errorLabel.setText("Valid Query")
                self.errorline = -1
                self.sparqlhighlight.errorhighlightline = self.errorline
                self.sparqlhighlight.currentline = 0
                self.inp_sparql2.errorline = None
            except Exception as e:
                match = re.search(r'line:([0-9]+),', str(e))
                start=-1
                if self.prefixes is not None and len(self.prefixes)>self.comboBox.currentIndex() and self.prefixes[
                    self.comboBox.currentIndex()] != None and self.prefixes[self.comboBox.currentIndex()] != "" and match!=None:
                    start = int(match.group(1)) - len(self.triplestoreconf[self.comboBox.currentIndex()]["prefixes"]) - 1
                elif match!=None:
                    start = int(match.group(1)) - 1
                if "line" in str(e):
                    self.errorLabel.setText(re.sub("line:([0-9]+),", "line: " + str(start) + ",", str(e)))
                    self.inp_sparql2.errorline = start - 1
                    ex = str(e)
                    start = ex.find('line:') + 5
                    end = ex.find(',', start)
                    start2 = ex.find('col:') + 4
                    end2 = ex.find(')', start2)
                    self.errorline = ex[start:end]
                    self.sparqlhighlight.errorhighlightcol = ex[start2:end2]
                    self.sparqlhighlight.errorhighlightline = self.errorline
                    self.sparqlhighlight.currentline = 0
                else:
                    self.errorLabel.setText(str(e))

    ##
    #  @brief Builds the search dialog to search for a concept or class.
    #  @param  self The object pointer
    #  @param  row the row to insert the result
    #  @param  column the column to insert the result
    #  @param  interlinkOrEnrich indicates if the dialog is meant for interlinking or enrichment
    #  @param  table the GUI element to display the result
    def buildSearchDialog(self, row, column, interlinkOrEnrich, table, propOrClass, bothOptions=False,
                          currentprefixes=None, addVocabConf=None):
        self.currentcol = column
        self.currentrow = row
        self.interlinkdialog = SearchDialog(column, row, self.triplestoreconf, self.prefixes, interlinkOrEnrich, table,
                                            propOrClass, bothOptions, currentprefixes, addVocabConf)
        self.interlinkdialog.setMinimumSize(650, 400)
        self.interlinkdialog.setWindowTitle("Search Interlink Concept")
        self.interlinkdialog.exec_()

    ##
    #  @brief Builds a value mapping dialog window for ther interlinking dialog.
    #
    #  @param self The object pointer
    #  @param row The row of the table for which to map the value
    #  @param column The column of the table for which to map the value
    #  @param table The table in which to save the value mapping result
    #  @param layer The layer which is concerned by the enrichment oder interlinking
    def buildValueMappingDialog(self, row, column, interlinkOrEnrich, table, layer):
        self.currentcol = column
        self.currentrow = row
        valuemap = None
        if table.item(row, column) != None and table.item(row, column).text() != "":
            valuemap = table.item(row, column).data(1)
        self.interlinkdialog = ValueMappingDialog(column, row, self.triplestoreconf, interlinkOrEnrich, table,
                                                  table.item(row, 3).text(), layer, valuemap)
        self.interlinkdialog.setMinimumSize(650, 400)
        self.interlinkdialog.setWindowTitle("Get Value Mappings for column " + table.item(row, 3).text())
        self.interlinkdialog.exec_()