from collections.abc import Iterable

from ..util.ui.uiutils import UIUtils
from ..util.sparqlutils import SPARQLUtils
from qgis.core import Qgis, QgsTask, QgsMessageLog
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QStandardItem
from qgis.PyQt.QtWidgets import QMessageBox

MESSAGE_CATEGORY = 'DataSchemaQueryTask'

class DataSchemaQueryTask(QgsTask):
    """This shows how to subclass QgsTask"""

    def __init__(self, description, triplestoreurl, query, searchTerm,prefixes, searchResultModel,triplestoreconf, progress,dlg,styleprop=None):
        super().__init__(description, QgsTask.CanCancel)
        QgsMessageLog.logMessage('Started task "{}"'.format(self.description()), MESSAGE_CATEGORY, Qgis.Info)
        self.exception = None
        self.triplestoreurl = triplestoreurl
        self.query = query
        self.styleprop=styleprop
        self.dlg=dlg
        self.progress = progress
        self.prefixes= prefixes
        self.invprefixes=SPARQLUtils.invertPrefixes(triplestoreconf["prefixes"])
        self.labels = None
        self.searchResultModel=searchResultModel
        self.triplestoreconf=triplestoreconf
        if self.progress!=None:
            newtext = "\n".join(self.progress.labelText().split("\n")[0:-1])
            self.progress.setLabelText(newtext + "\nCurrent Task: Executing query (1/2)")
        self.progress = progress
        self.urilist = None
        self.sortedatt = None
        self.searchTerm = searchTerm
        self.results = None

    def run(self):
        QgsMessageLog.logMessage('Started task "{}"'.format(self.description()), MESSAGE_CATEGORY, Qgis.Info)
        QgsMessageLog.logMessage('Started task "{}"'.format(self.searchTerm), MESSAGE_CATEGORY, Qgis.Info)
        if self.searchTerm == "":
            return False
        if isinstance(self.prefixes, Iterable):
            results = SPARQLUtils.executeQuery(self.triplestoreurl,"".join(self.prefixes) + self.query,self.triplestoreconf)
        else:
            results = SPARQLUtils.executeQuery(self.triplestoreurl, str(self.prefixes).replace("None","") + self.query,
                                                   self.triplestoreconf)
        if results == False:
            return False
        #self.searchResult.model().clear()
        if len(results["results"]["bindings"]) == 0:
            return False
        if self.progress!=None:
            newtext = "\n".join(self.progress.labelText().split("\n")[0:-1])
            self.progress.setLabelText(newtext + "\nCurrent Task: Processing results (2/2)")
        maxcons = int(results["results"]["bindings"][0]["countcon"]["value"])
        self.sortedatt = {}
        for result in results["results"]["bindings"]:
            if maxcons!=0 and str(maxcons)!="0":
                self.sortedatt[result["rel"]["value"][result["rel"]["value"].rfind('/') + 1:]] = {"amount": round(
                    (int(result["countrel"]["value"]) / maxcons) * 100, 2), "concept":result["rel"]["value"]}
                if "valtype" in result and result["valtype"]["value"]!="":
                    self.sortedatt[result["rel"]["value"][result["rel"]["value"].rfind('/') + 1:]]["valtype"]=result["valtype"]["value"]
        self.labels={}
        if "propertylabelquery" in self.triplestoreconf:
            self.labels=SPARQLUtils.getLabelsForClasses(self.sortedatt.keys(), self.triplestoreconf["propertylabelquery"], self.triplestoreconf,
                                        self.triplestoreurl)
        else:
            self.labels = SPARQLUtils.getLabelsForClasses(self.sortedatt.keys(),
                                                          None,
                                                          self.triplestoreconf,
                                                          self.triplestoreurl)
        for lab in self.labels:
            if lab in self.sortedatt:
                self.sortedatt[lab]["label"]=self.labels[lab]
        return True

    def finished(self, result):
        while self.searchResultModel.rowCount()>0:
            self.searchResultModel.removeRow(0)
        if self.sortedatt != None:
            if len(self.sortedatt)==0:
                self.searchResultModel.insertRow(0)
                item = QStandardItem()
                item.setText("No results found")
                self.searchResultModel.setItem(0,0,item)
            else:
                UIUtils.fillAttributeTable(self.sortedatt, self.invprefixes, self.dlg, self.searchResultModel,
                                           SPARQLUtils.classnode,
                                           "Check this item if you want it to be queried")
        else:
            msgBox = QMessageBox()
            msgBox.setText("The dataschema search query did not yield any results!")
            msgBox.exec()
        self.searchResultModel.setHeaderData(0, Qt.Horizontal, "Selection")
        self.searchResultModel.setHeaderData(1, Qt.Horizontal, "Attribute")
        self.searchResultModel.setHeaderData(2, Qt.Horizontal, "Sample Instances")
        self.progress.close()
