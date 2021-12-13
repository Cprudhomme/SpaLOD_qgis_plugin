from ..util.sparqlutils import SPARQLUtils
from qgis.core import Qgis
from qgis.PyQt.QtCore import QItemSelectionModel
from qgis.PyQt.QtGui import QStandardItem
from qgis.PyQt.QtWidgets import QHeaderView
from qgis.core import (
    QgsTask, QgsMessageLog,
)

MESSAGE_CATEGORY = 'GeoCollectionsQueryTask'


class GeoCollectionsQueryTask(QgsTask):

    def __init__(self, description, triplestoreurl, query, triplestoreconf, sparql, queryvar, labelvar, featureOrGeoCollection, layercount,
                 geoClassList, examplequery, geoClassListGui, completerClassList, dlg,graph=None):
        super().__init__(description, QgsTask.CanCancel)
        self.exception = None
        self.triplestoreurl = triplestoreurl
        self.triplestoreconf = triplestoreconf
        self.query = query
        self.dlg = dlg
        self.layercount = layercount
        self.labelvar = labelvar
        self.classvar = queryvar
        self.graph=graph
        self.featureOrGeoCollection=featureOrGeoCollection
        if featureOrGeoCollection:
            self.dlg.conceptViewTabWidget.setTabText(1, "FeatureCollections")
        else:
            self.dlg.conceptViewTabWidget.setTabText(2, "GeometryCollections")
        self.completerClassList = completerClassList
        self.completerClassList["completerClassList"] = {}
        self.queryvar = queryvar
        self.sparql = sparql
        self.geoClassListGui = geoClassListGui
        self.amountoflabels = -1
        self.geoClassList = geoClassList
        self.examplequery = examplequery
        self.resultlist = []
        self.viewlist = []

    def run(self):
        #QgsMessageLog.logMessage('Started task "{}"'.format(self.description()), MESSAGE_CATEGORY, Qgis.Info)
        if self.graph==None:
            results = SPARQLUtils.executeQuery(self.triplestoreurl,self.query,self.triplestoreconf)
        else:
            results=self.graph.query(self.query)
        if results==False:
            return False
        #QgsMessageLog.logMessage('Started task "{}"'.format(str(results)), MESSAGE_CATEGORY, Qgis.Info)
        for result in results["results"]["bindings"]:
            viewlistentry={}
            QgsMessageLog.logMessage('Started task "{}"'.format(str(self.queryvar)), MESSAGE_CATEGORY, Qgis.Info)
            if self.queryvar in result:
                self.viewlist.append(viewlistentry)
                viewlistentry["uri"]=str(result[self.queryvar]["value"])
                if self.labelvar in result:
                    viewlistentry["label"]=str(result[self.labelvar]["value"])
                if self.classvar in result:
                    viewlistentry["class"] = str(result[self.classvar]["value"])
                if "members" in result:
                    viewlistentry["members"] = str(result["members"]["value"])
        #QgsMessageLog.logMessage('Started task "{}"'.format(str(self.viewlist)), MESSAGE_CATEGORY, Qgis.Info)
        return True

    def finished(self, result):
        self.geoClassList.clear()
        self.geoClassListGui.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.geoClassListGui.header().setStretchLastSection(False)
        self.geoClassListGui.header().setMinimumSectionSize(self.dlg.classTreeView.width())
        if len(self.resultlist) > 0:
            first = True
            if self.featureOrGeoCollection:
                self.dlg.conceptViewTabWidget.setTabText(1, "FeatureCollections (" + str(len(self.resultlist)) + ")")
            else:
                self.dlg.conceptViewTabWidget.setTabText(2, "GeometryCollections (" + str(len(self.resultlist)) + ")")
            for concept in self.resultlist:
                # self.layerconcepts.addItem(concept)
                item = QStandardItem()
                item.setData(concept["uri"], 256)
                item.setData(SPARQLUtils.collectionclassnode, 257)
                if self.featureOrGeoCollection:
                    item.setIcon(SPARQLUtils.featurecollectionicon)
                else:
                    item.setIcon(SPARQLUtils.geometrycollectionicon)
                itemtext=""
                if "label" in concept:
                    itemtext=concept["label"]+" ("+concept["uri"][concept["uri"].rfind('/') + 1:]+")"
                else:
                    itemtext=SPARQLUtils.labelFromURI(concept["uri"])
                if "members" in concept:
                    itemtext+=" ["+str(concept["members"])+"]"
                item.setText(itemtext)
                self.geoClassList.appendRow(item)
            self.sparql.updateNewClassList()
            self.geoClassListGui.selectionModel().setCurrentIndex(self.geoClassList.index(0, 0),
                                                                  QItemSelectionModel.SelectCurrent)
            if self.featureOrGeoCollection:
                    self.dlg.viewselectactionFeatureCollection()
            else:
                    self.dlg.viewselectactionGeometryCollection()
        elif len(self.viewlist) > 0:
            if self.featureOrGeoCollection:
                self.dlg.conceptViewTabWidget.setTabText(1, "FeatureCollections (" + str(len(self.viewlist)) + ")")
            else:
                self.dlg.conceptViewTabWidget.setTabText(2, "GeometryCollections (" + str(len(self.viewlist)) + ")")
            for concept in self.viewlist:
                # self.layerconcepts.addItem(concept)
                item = QStandardItem()
                item.setData(concept["uri"], 256)
                item.setData(SPARQLUtils.collectionclassnode, 257)
                itemtext=""
                if "label" in concept:
                    itemtext=concept["label"]+" ("+concept["uri"][concept["uri"].rfind('/') + 1:]+")"
                else:
                    itemtext=SPARQLUtils.labelFromURI(concept["uri"])
                if "members" in concept:
                    itemtext+=" ["+str(concept["members"])+"]"
                item.setText(itemtext)
                if self.featureOrGeoCollection:
                    item.setIcon(SPARQLUtils.featurecollectionicon)
                    item.setToolTip("FeatureCollection " + str(item.text()) + ": <br>" + SPARQLUtils.treeNodeToolTip)
                else:
                    item.setIcon(SPARQLUtils.geometrycollectionicon)
                    item.setToolTip("GeometryCollection " + str(item.text()) + ": <br>" + SPARQLUtils.treeNodeToolTip)
                self.geoClassList.appendRow(item)
            self.sparql.updateNewClassList()
            self.geoClassListGui.selectionModel().setCurrentIndex(self.geoClassList.index(0, 0),
                                                                  QItemSelectionModel.SelectCurrent)
            if self.featureOrGeoCollection:
                    self.dlg.viewselectactionFeatureCollection()
            else:
                    self.dlg.viewselectactionGeometryCollection()
        if self.amountoflabels != -1:
            self.layercount.setText("[" + str(self.amountoflabels) + "]")
