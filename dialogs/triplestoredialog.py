from qgis.PyQt.QtWidgets import QDialog, QLabel, QLineEdit,QPushButton,QListWidget,QPlainTextEdit,QComboBox,QCheckBox,QMessageBox,QListWidgetItem,QProgressDialog
from qgis.PyQt.QtCore import QRegExp,Qt
from qgis.PyQt import uic
from qgis.core import QgsApplication
from qgis.PyQt.QtCore import QSettings
from qgis.PyQt.QtGui import QRegExpValidator,QValidator,QIntValidator
from ..util.sparqlhighlighter import SPARQLHighlighter
from ..tasks.detecttriplestoretask import DetectTripleStoreTask
import os.path
import json

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/triplestoredialog.ui'))

class TripleStoreDialog(QDialog,FORM_CLASS):

    triplestoreconf=""

    def __init__(self,triplestoreconf,prefixes,prefixstore,comboBox):
        super(QDialog, self).__init__()
        self.setupUi(self)
        self.triplestoreconf=triplestoreconf
        self.prefixstore=prefixstore
        self.comboBox=comboBox
        self.prefixes=prefixes
        for item in triplestoreconf:
            self.tripleStoreChooser.addItem(item["name"])
        self.tripleStoreChooser.currentIndexChanged.connect(self.loadTripleStoreConfig)
        #self.addTripleStoreButton.clicked.connect(self.addNewSPARQLEndpoint)
        urlregex = QRegExp("http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+")
        urlvalidator = QRegExpValidator(urlregex, self)
        self.tripleStoreEdit.setValidator(urlvalidator)
        self.tripleStoreEdit.textChanged.connect(self.check_state1)
        self.tripleStoreEdit.textChanged.emit(self.tripleStoreEdit.text())
        self.tripleStoreEdit.setToolTip("Add your triplestore's URL ")
        self.epsgEdit.setValidator(QIntValidator(1, 100000))
        prefixregex = QRegExp("[a-z]+")
        prefixvalidator = QRegExpValidator(prefixregex, self)

        ##
        #tripleStorePrefixNameEdit uses the setValidator to verify and validate
        #the prefix modification
        #When the user hovers over the tripleStorePrefixNameEdit button will activate
        #and it's text will appear
        #
        #@Antoine
        self.tripleStorePrefixNameEdit.setValidator(prefixvalidator)
        self.tripleStorePrefixNameEdit.setToolTip('Type in the name of your prefixe')
        ##
        #
        #
        #
        #@Antoine
        self.addPrefixButton.clicked.connect(self.addPrefixToList)
        self.addPrefixButton.setToolTip('Adds selected prefix to the triplestore')
        ##
        #When the remove Prefix button is clicked the prefix will be removed from
        #the prefix list
        #When the user hovers over the removePrefixButton button will activate
        #and it's text will appear
        #@Antoine
        self.removePrefixButton.clicked.connect(self.removePrefixFromList)
        self.removePrefixButton.setToolTip('Removes the selected prefixes from the result list.')
        ##
        #when the test Connect button is click it will test est the validity of
        #your SPARQL endpoint via the use of testTripleStoreConnection
        #When the user hovers over the testConnect button will activate
        #and it's text will appear
        #@Antoine
        self.testConnectButton.clicked.connect(self.testTripleStoreConnection)
        self.testConnectButton.setToolTip('Will test the validity of your SPARQL endpoint.')
        ##
        #when the deleteTripleStore button is click it delete the triplestore from
        #the list
        #When the user hovers over the deleteTripleStore button will activate
        #and it's text will appear
        #@Antoine
        self.deleteTripleStore.clicked.connect(self.deleteTripleStoreFunc)
        self.deleteTripleStore.setToolTip('Deletes the selected triplestore.')
        ##
        #when the resetConfiguration button is clicked it will Restore the triple
        #store to its default configuration
        #When the user hovers over the deleteTripleStore button will activate
        #and it's text will appear
        #@Antoine
        self.resetConfiguration.clicked.connect(self.restoreFactory)
        self.resetConfiguration.setToolTip('Restores the triple store to its default configuration.')
        ##
        #when the newTripleStore button is clicked it will allow the user to add
        #a new TripleStore
        #When the user hovers over the newTripleStore button will activate
        #and it's text will appear
        #@Antoine
        self.newTripleStore.clicked.connect(self.createNewTripleStore)
        self.newTripleStore.setToolTip("Will allow you to type in your new triplestore's information.")
        ##
        #This line determines that sparqlhighlighter is equivalent to SPARQLHighlighter
        #@Antoine
#self.exampleQuery.textChanged.connect(self.validateSPARQL)
        self.sparqlhighlighter = SPARQLHighlighter(self.exampleQuery)
        ##
        #tripleStorePrefixEdit uses the setValidator to verify the validit of
        #the triple store name edit
        #tripleStorePrefixEdit connects to check_state2 via textChanged
        #
        #@Antoine
        self.tripleStorePrefixEdit.setValidator(urlvalidator)
        self.tripleStorePrefixEdit.textChanged.connect(self.check_state2)
        self.tripleStorePrefixEdit.textChanged.emit(self.tripleStorePrefixEdit.text())
        ##
        #when the tripleStoreApply button is clicked it will apply the users
        #TripleStore
        #When the user hovers over the tripleStoreApply button setToolTip will activate
        #and it's text will appear
        #@Antoine
        self.tripleStoreApplyButton.clicked.connect(self.applyCustomSPARQLEndPoint)
        self.tripleStoreApplyButton.setToolTip('Will apply your triplestore')
        ##
        #when the tripleStoreClose button is clicked it will close the
        #TripleStore dialog
        #When the user hovers over the tripleStoreClose button setToolTip will activate
        #and it's text will appear
        #@Antoine
        self.tripleStoreCloseButton.clicked.connect(self.closeTripleStoreDialog)
        self.tripleStoreCloseButton.setToolTip('Will close the dialog.')
        ##
        #when the detectConfiguration button is clicked it will test the validity
        #of the users current Triple store configuration
        #When the user hovers over the detectConfiguration button setToolTip will activate
        #and it's text will appear
        #@Antoine
        self.detectConfiguration.clicked.connect(self.detectTripleStoreConfiguration)
        self.detectConfiguration.setToolTip('Will test the validity of your configuration.')
        ##
        #When the user hovers over the tripleStoreNameEdit button setToolTip will activate
        #and it's text will appear
        #@Antoine
        self.tripleStoreNameEdit.setToolTip("Add your triplestore's name")
        s = QSettings() #getting proxy from qgis options settings
        self.proxyEnabled = s.value("proxy/proxyEnabled")
        self.proxyType = s.value("proxy/proxyType")
        self.proxyHost = s.value("proxy/proxyHost")
        self.proxyPort = s.value("proxy/proxyPort")
        self.proxyUser = s.value("proxy/proxyUser")
        self.proxyPassword = s.value("proxy/proxyPassword")
        #tripleStoreApplyButton = QPushButton("Reset Configuration",self)
        #tripleStoreApplyButton.move(330,560)
        #tripleStoreApplyButton.clicked.connect(self.resetTripleStoreConfig)
##
#The loadTripleStoreConfig will allow users to load their TripleStore configuration
#@Antoine
    def loadTripleStoreConfig(self):
        if self.tripleStoreChooser.currentIndex()<len(self.triplestoreconf):
            self.tripleStoreEdit.setText(self.triplestoreconf[self.tripleStoreChooser.currentIndex()]["endpoint"])
            self.tripleStoreNameEdit.setText(self.triplestoreconf[self.tripleStoreChooser.currentIndex()]["name"])
            self.prefixList.clear()
            # msgBox=QMessageBox()
            # msgBox.setWindowTitle("Mandatory variables missing!")
            # msgBox.setText("The SPARQL query is missing the following mandatory variables: ")
            # msgBox.exec()
            for prefix in self.triplestoreconf[self.tripleStoreChooser.currentIndex()]["prefixes"]:
                self.prefixList.addItem(prefix)
            self.prefixList.sortItems()
            if "active" in self.triplestoreconf[self.tripleStoreChooser.currentIndex()]:
                self.activeCheckBox.setChecked(self.triplestoreconf[self.tripleStoreChooser.currentIndex()]["active"])
            if "crs" in self.triplestoreconf[self.tripleStoreChooser.currentIndex()]:
                self.epsgEdit.setText(str(self.triplestoreconf[self.tripleStoreChooser.currentIndex()]["crs"]))
            else:
                self.epsgEdit.setText("4326")
            self.exampleQuery.setPlainText(self.triplestoreconf[self.tripleStoreChooser.currentIndex()]["querytemplate"][0]["query"])

##
#The closeTripleStoreDialog will allow the user to close the TripleStore Dialog
#@Antoine
    def closeTripleStoreDialog(self):
        self.close()
##
#The testTripleStoreConnection methode allows the plugi to test the validity of the users TripleStore URL
#@Antoine
    def testTripleStoreConnection(self,calledfromotherfunction=False,showMessageBox=True,query="SELECT ?a ?b ?c WHERE { ?a ?b ?c .} LIMIT 1"):
        progress = QProgressDialog("Checking connection to triple store "+self.tripleStoreEdit.text()+"...", "Abort", 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setCancelButton(None)
        progress.show()
        self.qtask=DetectTripleStoreTask("Checking connection to triple store "+self.tripleStoreEdit.text()+"...",self.triplestoreconf,self.tripleStoreEdit.text(),self.tripleStoreNameEdit.text(),True,False,self.prefixes,self.prefixstore,self.tripleStoreChooser,self.comboBox,False,None,progress)
        QgsApplication.taskManager().addTask(self.qtask)
##
#The detectTripleStoreConfiguration methode detects the user's current TripleStore configuration.
#@Antoine
    def detectTripleStoreConfiguration(self):
        progress = QProgressDialog("Detecting configuration for triple store "+self.tripleStoreEdit.text()+"...", "Abort", 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setCancelButton(None)
        progress.show()
        self.qtask=DetectTripleStoreTask("Detecting configuration for triple store "+self.tripleStoreEdit.text()+"...",self.triplestoreconf,self.tripleStoreEdit.text(),self.tripleStoreNameEdit.text(),False,True,self.prefixes,self.prefixstore,self.tripleStoreChooser,self.comboBox,False,None,progress)
        QgsApplication.taskManager().addTask(self.qtask)

    ##
    #  @brief Adds a new SPARQL endpoint to the triple store registry
    #
    #  @param [in] self The object pointer
    def addNewSPARQLEndpoint(self):
        self.addTripleStore=True
        self.applyCustomSPARQLEndPoint()

    ##
    #  @brief Addes a new SPARQL endpoint to the triple store registry
    #
    #  @param [in] self The object pointer
    def deleteTripleStoreFunc(self):
        if self.tripleStoreChooser.currentIndex()!=0:
            del self.triplestoreconf[self.tripleStoreChooser.currentIndex()]
            self.tripleStoreChooser.clear()
            for item in self.triplestoreconf:
                self.tripleStoreChooser.addItem(item["name"])
##
#
#
#
#@Antoine
    def createNewTripleStore(self):
        self.tripleStoreChooser.addItem("New triple store")
        self.tripleStoreChooser.setCurrentIndex(self.tripleStoreChooser.count()-1)
        self.tripleStoreNameEdit.setText("New triple store")
        self.tripleStoreEdit.setText("")
##
#The restoreFactory methode restores all triplestores to their original configuration
#
#@Antoine
    def restoreFactory(self):
        __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        with open(os.path.join(__location__, 'triplestoreconf.json'),'r') as myfile:
            data=myfile.read()
        self.triplestoreconf=json.loads(data)
        self.tripleStoreChooser.clear()
        for item in self.triplestoreconf:
            self.tripleStoreChooser.addItem(item["name"])
        self.writeConfiguration()
        msgBox=QMessageBox()
        msgBox.setWindowTitle("Triple Store Settings Reset!")
        msgBox.setText("Triple store settings have been reset to default!")
        msgBox.exec()
        return

    ##
    #  @brief Adds a prefix to the list of prefixes in the search dialog window.
    #
    #  @param [in] self The object pointer
    def addPrefixToList(self):
        item=QListWidgetItem()
        item.setData(0,"PREFIX "+self.tripleStorePrefixNameEdit.text()+":<"+self.tripleStorePrefixEdit.text()+">")
        item.setText("PREFIX "+self.tripleStorePrefixNameEdit.text()+":<"+self.tripleStorePrefixEdit.text()+">")
        self.prefixList.addItem(item)

    ##
    #  @brief Removes a prefix from the list of prefixes in the search dialog window.
    #
    #  @param [in] self The object pointer
    def removePrefixFromList(self):
        item=QListWidgetItem()
        for item in self.prefixList.selectedItems():
            self.prefixList.removeItemWidget(item)
##
#The writeConfiguration methode allows the user to manually set up their
#TripleStore configuration
#@Antoine
    def writeConfiguration(self):
        __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        f = open(os.path.join(__location__, "triplestoreconf_personal.json"), "w")
        f.write(json.dumps(self.triplestoreconf,indent=2))
        f.close()
##
#The applyCustomSPARQLEndPoint  methode allows the user to apply their custom
#SPARQLEndpoint to the plugin
#@Antoine
    def applyCustomSPARQLEndPoint(self):
        if not self.testTripleStoreConnection(True):
           return
        if self.tripleStoreNameEdit.text()=="":
           msgBox=QMessageBox()
           msgBox.setWindowTitle("Triple Store Name is missing!")
           msgBox.setText("Please enter a triple store name")
           msgBox.exec()
           return
        #self.endpoints.append(self.tripleStoreEdit.text())
        self.comboBox.addItem(self.tripleStoreNameEdit.text())
        curprefixes=[]
        for i in range(self.prefixList.count()):
            curprefixes.append(self.prefixList.item(i).text()	)
        if self.addTripleStore:
            index=len(self.triplestoreconf)
            self.tripleStoreChooser.addItem(self.tripleStoreNameEdit.text()	)
            self.triplestoreconf.append({})
            self.triplestoreconf[index]["querytemplate"]=[]
            self.triplestoreconf[index]["querytemplate"].append({})
            self.triplestoreconf[index]["querytemplate"][0]["label"]="Example Query"
            self.triplestoreconf[index]["querytemplate"][0]["query"]=self.exampleQuery.toPlainText()
        else:
            index=self.tripleStoreChooser.currentIndex()
        self.triplestoreconf[index]={}
        self.triplestoreconf[index]["endpoint"]=self.tripleStoreEdit.text()
        self.triplestoreconf[index]["name"]=self.tripleStoreNameEdit.text()
        self.triplestoreconf[index]["mandatoryvariables"]=[]
        self.triplestoreconf[index]["mandatoryvariables"].append(self.queryVarEdit.text())
        self.triplestoreconf[index]["mandatoryvariables"].append(self.queryVarItemEdit.text())
        self.triplestoreconf[index]["prefixes"]=curprefixes
        self.triplestoreconf[index]["crs"]=self.epsgEdit.text()
        self.triplestoreconf[index]["active"]=self.activeCheckBox.isChecked()
        self.addTripleStore=False
##
#The check_state1 methode checks the state of the tripleStoreEdit
#@Antoine
    def check_state1(self):
        self.check_state(self.tripleStoreEdit)
##
#The check_state2 methode verifies the state of user's edit of a TripleStore
#prefix
#@Antoine
    def check_state2(self):
        self.check_state(self.tripleStorePrefixEdit)
##
#check_state verifies the state of validator
#@Antoine
    def check_state(self,sender):
        validator = sender.validator()
        state = validator.validate(sender.text(), 0)[0]
        if state == QValidator.Acceptable:
            color = '#c4df9b' # green
        elif state == QValidator.Intermediate:
            color = '#fff79a' # yellow
        else:
            color = '#f6989d' # red
        sender.setStyleSheet('QLineEdit { background-color: %s }' % color)
