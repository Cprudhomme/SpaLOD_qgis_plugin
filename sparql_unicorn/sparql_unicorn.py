# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SPAQLunicorn
                                 A QGIS plugin
 This plugin adds a GeoJSON layer from a Wikidata SPARQL query.
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2019-10-28
        git sha              : $Format:%H$
        copyright            : (C) 2019 by SPARQL Unicorn
        email                : rse@fthiery.de
        developer(s)         : Florian Thiery,  Timo Homburg
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

#import sys
#import pip
from qgis.utils import iface
from qgis.core import Qgis

from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QFileDialog
from qgis.core import QgsProject, Qgis
from qgis.core import QgsVectorLayer, QgsProject, QgsGeometry, QgsCoordinateReferenceSystem, QgsCoordinateTransform
from qgis.utils import iface
import rdflib
import requests

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .sparql_unicorn_dialog import SPAQLunicornDialog
import os.path
import re

# external libraires for SPARQL Unicorn
from SPARQLWrapper import SPARQLWrapper, JSON
#import rdflib
import json
#from convertbng.util import convert_bng, convert_lonlat

class SPAQLunicorn:
    """QGIS Plugin Implementation."""

    loadedfromfile=False

    currentgraph=None

    outputfile=""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'SPAQLunicorn_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&SPARQL Unicorn Wikidata Plugin')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('SPAQLunicorn', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToVectorMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        #a = str('numpy' in sys.modules)
        #iface.messageBar().pushMessage("load libs", a, level=Qgis.Success)

        icon_path = ':/plugins/sparql_unicorn/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Adds GeoJSON layer from a Wikidata'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginVectorMenu(
                self.tr(u'&SPARQL Unicorn Wikidata Plugin'),
                action)
            self.iface.removeToolBarIcon(action)


    def create_unicorn_layer(self):
        endpointIndex = self.dlg.comboBox.currentIndex()
        # SPARQL query
        #print(self.loadedfromfile)
        if self.loadedfromfile:
            concept = self.dlg.layerconcepts.currentText()
            geojson=self.getGeoJSONFromGeoConcept(self.currentgraph,concept)
            vlayer = QgsVectorLayer(json.dumps(geojson, sort_keys=True, indent=4),"unicorn_"+self.dlg.inp_label.text(),"ogr")
            print(vlayer.isValid())
            QgsProject.instance().addMapLayer(vlayer)
            canvas = iface.mapCanvas()
            canvas.setExtent(vlayer.extent())
            iface.messageBar().pushMessage("Add layer", "OK", level=Qgis.Success)
            #iface.messageBar().pushMessage("Error", "An error occured", level=Qgis.Critical)
            self.dlg.close()
            return
        elif endpointIndex == 0:
            endpoint_url = "https://query.wikidata.org/sparql"
        elif endpointIndex == 1:
            endpoint_url = "http://data.ordnancesurvey.co.uk/datasets/os-linked-data/apis/sparql"
        elif endpointIndex == 2:
            endpoint_url = "http://nomisma.org/query"
        elif endpointIndex == 3:
            endpoint_url = "http://kerameikos.org/query"
        elif endpointIndex == 4:
            endpoint_url = "http://linkedgeodata.org/sparql"
        elif endpointIndex== 5:
            endpoint_url = "http://dbpedia.org/sparql"
        elif endpointIndex==6:
            endpoint_url = "http://factforge.net/repositories/ff-news"
        elif endpointIndex==7:
            endpoint_url = "http://zbw.eu/beta/sparql/econ_pers/query"
        elif endpointIndex==8:
            endpoint_url = "http://sandbox.mainzed.org/osi/sparql"
            self.dlg.layerconcepts.addItem("http://www.opengis.net/ont/geosparql#Feature")
            self.dlg.layerconcepts.addItem("http://ontologies.geohive.ie/osi#County")
            self.dlg.inp_sparql.setPlainText("""SELECT ?item ?label ?geo {
            ?item a <http://ontologies.geohive.ie/osi#County>.
            ?item rdfs:label ?label.
            FILTER (lang(?label) = 'en')
            ?item ogc:hasGeometry [
            ogc:asWKT ?geo
            ] .
            }""")
        # query
        query = self.dlg.inp_sparql.toPlainText()
        sparql = SPARQLWrapper(endpoint_url, agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11")
        if endpointIndex == 0:
            sparql.setQuery(query)
        elif endpointIndex == 1:
            sparql.setQuery("PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX spatial: <http://data.ordnancesurvey.co.uk/ontology/spatialrelations/> PREFIX gaz: <http://data.ordnancesurvey.co.uk/ontology/50kGazetteer/>" + query)
        elif endpointIndex == 2:
            sparql.setQuery("PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX geo: <http://www.w3.org/2003/01/geo/wgs84_pos#> PREFIX nm: <http://nomisma.org/id/> PREFIX nmo: <http://nomisma.org/ontology#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX spatial: <http://jena.apache.org/spatial#> PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>" + query)
        elif endpointIndex == 3:
            sparql.setQuery("PREFIX crm: <http://www.cidoc-crm.org/cidoc-crm/> PREFIX crmgeo: <http://www.ics.forth.gr/isl/CRMgeo/> PREFIX crmsci: <http://www.ics.forth.gr/isl/CRMsci/> PREFIX dcterms: <http://purl.org/dc/terms/> PREFIX foaf: <http://xmlns.com/foaf/0.1/> PREFIX geo: <http://www.w3.org/2003/01/geo/wgs84_pos#> PREFIX kid: <http://kerameikos.org/id/> PREFIX kon: <http://kerameikos.org/ontology#> PREFIX org: <http://www.w3.org/ns/org#> PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>" + query)
        elif endpointIndex == 4:
            sparql.setQuery("Prefix lgdo: <http://linkedgeodata.org/ontology/> Prefix geom: <http://geovocab.org/geometry#> Prefix ogc: <http://www.opengis.net/ont/geosparql#> Prefix owl: <http://www.w3.org/2002/07/owl#> Prefix ogc: <http://www.opengis.net/ont/geosparql#> Prefix geom: <http://geovocab.org/geometry#> Prefix lgdo: <http://linkedgeodata.org/ontology/>" + query)
        elif endpointIndex == 5:
            sparql.setQuery("Prefix dbo: <http://dbpedia.org/ontology/> PREFIX geo:<http://www.w3.org/2003/01/geo/wgs84_pos#> Prefix geom: <http://geovocab.org/geometry#> Prefix ogc: <http://www.opengis.net/ont/geosparql#> Prefix owl: <http://www.w3.org/2002/07/owl#> Prefix geom: <http://geovocab.org/geometry#> Prefix lgdo: <http://linkedgeodata.org/ontology/>" + query)
        elif endpointIndex == 6:
            sparql.setQuery("PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> PREFIX geo:<http://www.w3.org/2003/01/geo/wgs84_pos#> PREFIX gn:<http://www.geonames.org/ontology#> Prefix geom: <http://geovocab.org/geometry#> Prefix ogc: <http://www.opengis.net/ont/geosparql#> Prefix owl: <http://www.w3.org/2002/07/owl#> prefix wgs84_pos: <http://www.w3.org/2003/01/geo/wgs84_pos#>" + query)
        elif endpointIndex == 8:
            sparql.setQuery("PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> Prefix geom: <http://geovocab.org/geometry#> Prefix ogc: <http://www.opengis.net/ont/geosparql#> Prefix owl: <http://www.w3.org/2002/07/owl#> Prefix osi: <http://ontologies.geohive.ie/osi#> " + query)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        #print(results)
        # geojson stuff
        features = []
        if endpointIndex == 0:
            for result in results["results"]["bindings"]:
                properties = {}
                for var in results["head"]["vars"]:
                    properties[var] = result[var]["value"]
                #print(properties)
                if result["geo"]["value"]:
                    print(QgsGeometry.fromWkt(result["geo"]["value"]).asJson())
                    #feature = { 'type': 'Feature', 'properties': { 'label': result["label"]["value"], 'item': result["item"]["value"] }, 'geometry': wkt.loads(result["geo"]["value"].replace("Point", "POINT")) }
                    feature = { 'type': 'Feature', 'properties': properties, 'geometry':  json.loads(QgsGeometry.fromWkt(result["geo"]["value"]).asJson()) }
                    features.append(feature)
            geojson = {'type': 'FeatureCollection', 'features': features }
        elif endpointIndex == 1:
            for result in results["results"]["bindings"]:
                properties = {}
                for var in results["head"]["vars"]:
                    properties[var] = result[var]["value"]
                # transform from BNG to WGS84
                myGeometryInstance = QgsGeometry.fromWkt("POINT("+str(float(result["easting"]["value"]))+" "+str(float(result["northing"]["value"]))+")")
                sourceCrs = QgsCoordinateReferenceSystem(27700)
                destCrs = QgsCoordinateReferenceSystem(4326)
                tr = QgsCoordinateTransform(sourceCrs, destCrs, QgsProject.instance())
                myGeometryInstance.transform(tr)
                print(myGeometryInstance.asJson())
                feature = { 'type': 'Feature', 'properties': properties, 'geometry': json.loads(myGeometryInstance.asJson()) }
                features.append(feature)
            geojson = {'type': 'FeatureCollection', 'features': features }
        elif endpointIndex == 2:
            for result in results["results"]["bindings"]:
                properties = {}
                for var in results["head"]["vars"]:
                    properties[var] = result[var]["value"]
                point = "POINT("+str(float(result["long"]["value"]))+" "+str(float(result["lat"]["value"]))+")"
                #print(point)
                feature = { 'type': 'Feature', 'properties': properties, 'geometry':  json.loads(QgsGeometry.fromWkt(point).asJson())  }
                features.append(feature)
            geojson = {'type': 'FeatureCollection', 'features': features }
        elif endpointIndex == 3:
            for result in results["results"]["bindings"]:
                properties = {}
                for var in results["head"]["vars"]:
                    properties[var] = result[var]["value"]
                point = "POINT("+str(float(result["long"]["value"]))+" "+str(float(result["lat"]["value"]))+")"
                #print(point)
                feature = { 'type': 'Feature', 'properties': properties, 'geometry':  json.loads(QgsGeometry.fromWkt(point).asJson())  }
                features.append(feature)
            geojson = {'type': 'FeatureCollection', 'features': features }
        elif endpointIndex == 4:
            for result in results["results"]["bindings"]:
                properties = {}
                for var in results["head"]["vars"]:
                    properties[var] = result[var]["value"]
                if result["geo"]["value"]:
                    feature = { 'type': 'Feature', 'properties': properties, 'geometry':  json.loads(QgsGeometry.fromWkt(result["geo"]["value"]).asJson()) }
                    features.append(feature)
            geojson = {'type': 'FeatureCollection', 'features': features }
        elif endpointIndex == 5:
            for result in results["results"]["bindings"]:
                properties = {}
                for var in results["head"]["vars"]:
                    properties[var] = result[var]["value"]
                if "lat" in properties and "lon" in properties:
                    feature = { 'type': 'Feature', 'properties': properties, 'geometry':  json.loads(QgsGeometry.fromWkt("POINT("+result["lat"]["value"]+" "+result["lon"]["value"]+")").asJson()) }
                    features.append(feature)
            geojson = {'type': 'FeatureCollection', 'features': features }
        elif endpointIndex == 6:
            for result in results["results"]["bindings"]:
                properties = {}
                for var in results["head"]["vars"]:
                    properties[var] = result[var]["value"]
                if "lat" in properties and "lon" in properties:
                    feature = { 'type': 'Feature', 'properties': properties, 'geometry':  json.loads(QgsGeometry.fromWkt("POINT("+result["lat"]["value"]+" "+result["lon"]["value"]+")").asJson()) }
                    features.append(feature)
            geojson = {'type': 'FeatureCollection', 'features': features }
        elif endpointIndex == 8:
            for result in results["results"]["bindings"]:
                properties = {}
                for var in results["head"]["vars"]:
                    properties[var] = result[var]["value"]
                if result["geo"]["value"]:
                    # transform from epsg:2157 to WGS84
                    #print(result["geo"]["value"].replace("<http://www.opengis.net/def/crs/EPSG/0/2157> ",""))
                    myGeometryInstance = QgsGeometry.fromWkt(result["geo"]["value"].replace("<http://www.opengis.net/def/crs/EPSG/0/2157> ",""))
                    sourceCrs = QgsCoordinateReferenceSystem(2157)
                    destCrs = QgsCoordinateReferenceSystem(4326)
                    tr = QgsCoordinateTransform(sourceCrs, destCrs, QgsProject.instance())
                    myGeometryInstance.transform(tr)
                    feature = { 'type': 'Feature', 'properties': properties, 'geometry': json.loads(myGeometryInstance.asJson()) }
                    features.append(feature)
            geojson = {'type': 'FeatureCollection', 'features': features }
        # add layer
        vlayer = QgsVectorLayer(json.dumps(geojson, sort_keys=True, indent=4),"unicorn_"+self.dlg.inp_label.text(),"ogr")
        print(vlayer.isValid())
        QgsProject.instance().addMapLayer(vlayer)
        canvas = iface.mapCanvas()
        canvas.setExtent(vlayer.extent())
        iface.messageBar().pushMessage("Add layer", "OK", level=Qgis.Success)
        #iface.messageBar().pushMessage("Error", "An error occured", level=Qgis.Critical)
        self.dlg.close()

    def getGeoConceptsFromGraph(self,graph):
        viewlist=[]
        qres = graph.query(
        """SELECT DISTINCT ?count (count(?a_class) as ?count)
        WHERE {
          ?a rdf:type ?a_class .
          ?a <http://www.opengis.net/ont/geosparql#hasGeometry> ?a_geom .
          ?a_geom <http://www.opengis.net/ont/geosparql#asWKT> ?a_wkt .
        }""")
        print(qres)
        self.dlg.layercount.setText("["+str(len(qres))+"]")
        for row in qres:
            viewlist.append(str(row[0]))
        return viewlist

    def getGeoConceptsFromWikidata(self):
        viewlist=[]
        resultlist=[]
        sparql = SPARQLWrapper("https://query.wikidata.org/sparql", agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11")
        sparql.setQuery(
        """SELECT DISTINCT ?class
        WHERE {
          ?a <http://www.wikidata.org/prop/direct/P31> ?class .
          ?a <http://www.wikidata.org/prop/direct/P625> ?a_geom .
        } LIMIT 1000""")
        print("now sending query")
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        for result in results["results"]["bindings"]:
            viewlist.append(str(result["class"]["value"]))
        print(viewlist)
        labels=self.getWikidataLabelsForQIDs(viewlist)
        print(labels)
        self.dlg.layercount.setText("["+str(len(labels))+"]")
        i=0
        sorted_labels=sorted(labels.items(),key=lambda x:x[1])
        for lab in sorted_labels:
            resultlist.append(labels[lab[0]]+"("+lab[0]+")")
            i=i+1			
        return resultlist
       
    def getWikidataLabelsForQIDs(self,qids):
        result={}
        url="https://www.wikidata.org/w/api.php?action=wbgetentities&props=labels&ids="
        i=0
        qidquery=""
        for qid in qids:
            qidquery+="Q"+qid.split("Q")[1]
            if (i%50)==0:
                print(url+qidquery+"&languages=en&format=json")
                myResponse = json.loads(requests.get(url+qidquery+"&languages=en&format=json").text)
                print(myResponse)
                for ent in myResponse["entities"]:
                    print(ent)
                    if "en" in myResponse["entities"][ent]["labels"]:
                        result[ent]=myResponse["entities"][ent]["labels"]["en"]["value"]                
                qidquery=""
            else:
                qidquery+="|"
            i=i+1
        return result
       
    def getGeoJSONFromGeoConcept(self,graph,concept):
        print(concept)
        qres = graph.query(
        """SELECT DISTINCT ?a ?rel ?val ?wkt
        WHERE {
          ?a rdf:type <"""+concept+"""> .
          ?a ?rel ?val .
          OPTIONAL { ?val <http://www.opengis.net/ont/geosparql#asWKT> ?wkt}
        }""")
        geos=[]
        geometries = {
            'type': 'FeatureCollection',
            'features': geos,
            }
        newfeature=False
        lastfeature=""
        currentgeo={}
        for row in qres:
            print(lastfeature+" - "+row[0]+" - "+str(len(row)))
            print(row)
            if(lastfeature=="" or lastfeature!=row[0]):
                if(lastfeature!=""):
                    geos.append(currentgeo)
                lastfeature=row[0]
                currentgeo={'id':row[0],'geometry':{},'properties':{}}
            if(row[3]!=None):
                print(row[3])
                if("<" in row[3]):
                    currentgeo['geometry']=json.loads(QgsGeometry.fromWkt(row[3].split(">")[1].strip()).asJson())
                else:
                    currentgeo['geometry']=json.loads(QgsGeometry.fromWkt(row[3]).asJson())
            else:
                currentgeo['properties'][str(row[1])]=str(row[2])
        return geometries

    def exportLayer(self):
        filename, _filter = QFileDialog.getSaveFileName(
            self.dlg, "Select   output file ","", "Linked data (*.rdfxml *.ttl *.n3 *.owl *.nt *.nq *.trix *.json-ld)",)
        layers = QgsProject.instance().layerTreeRoot().children()
        selectedLayerIndex = self.dlg.loadedLayers.currentIndex()
        layer = layers[selectedLayerIndex].layer()
        fieldnames = [field.name() for field in layer.fields()]
        ttlstring="<http://www.opengis.net/ont/geosparql#Feature> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class> ."
        ttlstring+="<http://www.opengis.net/ont/geosparql#SpatialObject> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class> ."
        ttlstring+="<http://www.opengis.net/ont/geosparql#Geometry> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class> ."
        ttlstring+="<http://www.opengis.net/ont/geosparql#Feature> <http://www.w3.org/2000/01/rdf-schema#subClassOf> <http://www.opengis.net/ont/geosparql#SpatialObject> ."
        for f in layer.getFeatures():
            geom = f.geometry()
            ttlstring+="<"+f["id"]+"> <http://www.opengis.net/ont/geosparql#hasGeometry> <"+f["id"]+"_geom> .\n"
            ttlstring+="<"+f["id"]+"_geom> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.opengis.net/ont/geosparql#"+str(geom.type())+"> .\n"
            ttlstring+="<http://www.opengis.net/ont/geosparql#"+str(geom.type())+"> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://www.w3.org/2002/07/owl#Class> .\n"
            ttlstring+="<http://www.opengis.net/ont/geosparql#"+str(geom.type())+"> <http://www.w3.org/2000/01/rdf-schema#subClassOf> <http://www.opengis.net/ont/geosparql#Geometry> .\n"
            ttlstring+="<"+f["id"]+"_geom> <http://www.opengis.net/ont/geosparql#asWKT> \""+geom.asWkt()+"\"^^<http://www.opengis.net/ont/geosparql#wktLiteral> .\n"
            for prop in fieldnames:
                if prop=="id":
                    continue
                elif f[prop].isdigit():
                    ttlstring+="<"+f["id"]+"> <"+prop+"> \""+f[prop]+"\"^^<http://www.w3.org/2001/XMLSchema#integer> .\n"
                elif re.match(r'^-?\d+(?:\.\d+)?$', f[prop]):
                    ttlstring+="<"+f["id"]+"> <"+prop+"> \""+f[prop]+"\"^^<http://www.w3.org/2001/XMLSchema#double> .\n"
                elif "http" in f[prop]:
                    ttlstring+="<"+f['id']+"> <"+prop+"> <"+f[prop]+"> .\n"
                else:
                    ttlstring+="<"+f['id']+"> <"+prop+"> \""+f[prop]+"\"^^<http://www.w3.org/2001/XMLSchema#string> .\n"
        g=rdflib.Graph()
        g.parse(data=ttlstring, format="ttl")
        splitted=filename.split(".")
        with open(filename, 'w') as output_file:
            output_file.write(g.serialize(format=splitted[len(splitted)-1]).decode("utf-8"))
            iface.messageBar().pushMessage("export layer successfully!", "OK", level=Qgis.Success)

    def exportLayerAsGeoJSONLD(self):
        context={
    "geojson": "https://purl.org/geojson/vocab#",
    "Feature": "geojson:Feature",
    "FeatureCollection": "geojson:FeatureCollection",
    "GeometryCollection": "geojson:GeometryCollection",
    "LineString": "geojson:LineString",
    "MultiLineString": "geojson:MultiLineString",
    "MultiPoint": "geojson:MultiPoint",
    "MultiPolygon": "geojson:MultiPolygon",
    "Point": "geojson:Point",
    "Polygon": "geojson:Polygon",
    "bbox": {
      "@container": "@list",
      "@id": "geojson:bbox"
    },
    "coordinates": {
      "@container": "@list",
      "@id": "geojson:coordinates"
    },
    "features": {
      "@container": "@set",
      "@id": "geojson:features"
    },
    "geometry": "geojson:geometry",
    "id": "@id",
    "properties": "geojson:properties",
    "type": "@type",
    "description": "http://purl.org/dc/terms/description",
    "title": "http://purl.org/dc/terms/title"
  }
        layer = layers[selectedLayerIndex].layer()
        fieldnames = [field.name() for field in layer.fields()]
        currentgeo={}
        geos=[]
        for f in layer.getFeatures():
            geom = f.geometry()
            currentgeo={'id':row[0],'geometry':json.loads(geom.asJson()),'properties':{}}
            for prop in fieldnames:
                if prop=="id":
                    currentgeo["id"]=f[prop]
                else:
                    currentgeo["properties"][prop]=f[prop]
            geos.append(currentgeo)
        featurecollection={"@context":context, "type":"FeatureCollection", "@id":"http://example.com/collections/1", "features": geos }
        return featurecollection	
			
    def loadGraph(self):
        dialog = QFileDialog(self.dlg)
        dialog.setFileMode(QFileDialog.AnyFile)
        if dialog.exec_():
            fileNames = dialog.selectedFiles()
            g = rdflib.Graph()
            filepath=fileNames[0].split(".")
            result = g.parse(fileNames[0], format=filepath[len(filepath)-1])
            print(g)
            self.currentgraph=g
            geoconcepts=self.getGeoConceptsFromGraph(g)
            self.dlg.layerconcepts.clear()
            for geo in geoconcepts:
                self.dlg.layerconcepts.addItem(geo)
            self.dlg.inp_sparql.setPlainText("""SELECT DISTINCT ?a ?rel ?val ?wkt
            WHERE {
            ?a rdf:type <"""+geoconcepts[0]+"""> .
            ?a ?rel ?val .
            OPTIONAL { ?val geo:asWKT ?wkt}
            }""")
            self.loadedfromfile=True
            return result
        return None      
        
    def loadUnicornLayers(self):
        # Fetch the currently loaded layers
        layers = QgsProject.instance().layerTreeRoot().children()
        # Populate the comboBox with names of all the loaded unicorn layers
        self.dlg.loadedLayers.clear()
        for layer in layers:
            ucl = layer.name()
            if "unicorn_" in ucl:
                self.dlg.loadedLayers.addItem(layer.name())

    def endpointselectaction(self):
        endpointIndex = self.dlg.comboBox.currentIndex()
        self.dlg.layerconcepts.clear()
        if endpointIndex==0:
            print("changing to wikidata")
            conceptlist=self.getGeoConceptsFromWikidata()
            for concept in conceptlist:
                self.dlg.layerconcepts.addItem(concept)
        elif endpointIndex==3:
            self.dlg.layerconcepts.addItem("http://www.w3.org/2003/01/geo/wgs84_pos#SpatialThing")
            self.dlg.layerconcepts.addItem("http://www.cidoc-crm.org/cidoc-crm/E53_Place")
            self.dlg.layerconcepts.addItem("http://www.ics.forth.gr/isl/CRMgeo/SP5_Geometric_Place_Expression")
        elif endpointIndex==2:
            self.dlg.layerconcepts.addItem("http://www.w3.org/2003/01/geo/wgs84_pos#SpatialThing")
            self.dlg.layerconcepts.addItem("http://www.w3.org/2004/02/skos/core#Concept")
            self.dlg.layerconcepts.addItem("http://nomisma.org/ontology#Mint")
            self.dlg.layerconcepts.addItem("http://nomisma.org/ontology#Region")
        elif endpointIndex==8:
            self.dlg.layerconcepts.addItem("http://www.opengis.net/ont/geosparql#Feature")
            self.dlg.layerconcepts.addItem("http://ontologies.geohive.ie/osi#County")
            self.dlg.layerconcepts.addItem("http://ontologies.geohive.ie/osi#Barony")
            self.dlg.layerconcepts.addItem("http://ontologies.geohive.ie/osi#Council")
            self.dlg.layerconcepts.addItem("http://ontologies.geohive.ie/osi#Townland")
            self.dlg.layerconcepts.addItem("http://ontologies.geohive.ie/osi#ElectoralDivision")
            self.dlg.layerconcepts.addItem("http://ontologies.geohive.ie/osi#GaeltachtRegion")
            self.dlg.layerconcepts.addItem("http://ontologies.geohive.ie/osi#LocalElectoralArea")
            self.dlg.layerconcepts.addItem("http://ontologies.geohive.ie/osi#MunicipalDistrict")
            self.dlg.layerconcepts.addItem("http://ontologies.geohive.ie/osi#NationalConstituency")
            self.dlg.layerconcepts.addItem("http://ontologies.geohive.ie/osi#CivilParish")
            self.dlg.layerconcepts.addItem("http://ontologies.geohive.ie/osi#RuralArea")
            self.dlg.inp_sparql.setPlainText("""SELECT ?item ?label ?geo {
            ?item a <"""+self.dlg.layerconcepts.currentText()+""">.
            ?item rdfs:label ?label.
            FILTER (lang(?label) = 'en')
            ?item ogc:hasGeometry [
            ogc:asWKT ?geo
            ] .
            } LIMIT 10""")

    def viewselectaction(self):
        endpointIndex = self.dlg.comboBox.currentIndex()
        if endpointIndex==0:
            self.dlg.inp_sparql.setPlainText("""SELECT ?item ?itemLabel ?geo {
            ?item <http://www.wikidata.org/prop/direct/P31> <http://www.wikidata.org/entity/Q"""+self.dlg.layerconcepts.currentText().split("Q")[1].replace(")","")+""">.
            ?item <http://www.wikidata.org/prop/direct/P625> ?geo .
			SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
            } LIMIT 10""")
        elif endpointIndex==2:
            self.dlg.inp_sparql.setPlainText("""SELECT ?item ?lat ?long {
            ?item a <"""+self.dlg.layerconcepts.currentText()+""">.
            ?item <http://www.w3.org/2003/01/geo/wgs84_pos#lat> ?lat .
            ?item <http://www.w3.org/2003/01/geo/wgs84_pos#long> ?long .
            } LIMIT 10""")
        elif endpointIndex==3:
            self.dlg.inp_sparql.setPlainText("""SELECT ?item ?lat ?long {
            ?item a <"""+self.dlg.layerconcepts.currentText()+""">.
            ?item <http://www.w3.org/2003/01/geo/wgs84_pos#lat> ?lat .
            ?item <http://www.w3.org/2003/01/geo/wgs84_pos#long> ?long .
            } LIMIT 10""")
        elif endpointIndex==8:
            self.dlg.inp_sparql.setPlainText("""SELECT ?item ?label ?geo {
            ?item a <"""+self.dlg.layerconcepts.currentText()+""">.
            ?item rdfs:label ?label.
            FILTER (lang(?label) = 'en')
            ?item ogc:hasGeometry [
            ogc:asWKT ?geo
            ] .
            } LIMIT 10""")

    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = SPAQLunicornDialog()
            self.dlg.comboBox.clear()
            self.dlg.comboBox.addItem('Wikidata --> ?geo required!') #0
            self.dlg.comboBox.addItem('Ordnance Survey UK --> ?easting ?northing required!') #1
            self.dlg.comboBox.addItem('nomisma.org --> ?lat ?long required!') #2
            self.dlg.comboBox.addItem('kerameikos.org --> ?lat ?long required!') #3
            self.dlg.comboBox.addItem('Linked Geodata (OSM) --> ?geo required!') #4
            self.dlg.comboBox.addItem('DBPedia --> ?lat ?lon required!') #5
            self.dlg.comboBox.addItem('Geonames --> ?lat ?lon required!') #6
            self.dlg.comboBox.addItem('German National Library (GND) --> ?lat ?lon required!') #7
            self.dlg.comboBox.addItem('Ordnance Survey Ireland --> ?geo required!') #8
            self.dlg.comboBox.currentIndexChanged.connect(self.endpointselectaction)
            self.dlg.loadedLayers.clear()
            self.dlg.layerconcepts.clear()
            self.dlg.layerconcepts.currentIndexChanged.connect(self.viewselectaction)
            self.dlg.pushButton.clicked.connect(self.create_unicorn_layer) # load action
            self.dlg.exportLayers.clicked.connect(self.exportLayer)
            self.dlg.loadFileButton.clicked.connect(self.loadGraph) # load action

        if self.first_start == False:
            self.loadUnicornLayers()

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass
