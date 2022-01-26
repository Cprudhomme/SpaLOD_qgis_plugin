from SPARQLWrapper import SPARQLWrapper, JSON, GET, POST, BASIC, DIGEST
import urllib
import requests
import sys
from urllib.request import urlopen
import json
from qgis.core import Qgis, QgsGeometry
from qgis.core import QgsMessageLog
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import QSettings
from rdflib import Graph

MESSAGE_CATEGORY = "SPARQLUtils"


class SPARQLUtils:
    supportedLiteralTypes = {"http://www.opengis.net/ont/geosparql#wktLiteral": "wkt",
                             "http://www.opengis.net/ont/geosparql#gmlLiteral": "gml",
                             "http://www.opengis.net/ont/geosparql#wkbLiteral": "wkb",
                             "http://www.opengis.net/ont/geosparql#geoJSONLiteral": "geojson",
                             "http://www.opengis.net/ont/geosparql#kmlLiteral": "kml",
                             "http://www.opengis.net/ont/geosparql#dggsLiteral": "dggs"}

    namespaces={"rdfs":"http://www.w3.org/2000/01/rdf-schema#","owl":"http://www.w3.org/2002/07/owl#","dc":"http://purl.org/dc/terms/","skos":"http://www.w3.org/2004/02/skos/core#"}

    annotationnamespaces=["http://www.w3.org/2004/02/skos/core#","http://www.w3.org/2000/01/rdf-schema#","http://purl.org/dc/terms/"]

    geoproperties={"http://www.opengis.net/ont/geosparql#asWKT":"DatatypeProperty",
                   "http://www.opengis.net/ont/geosparql#asGML": "DatatypeProperty",
                   "http://www.opengis.net/ont/geosparql#asKML": "DatatypeProperty",
                   "http://www.opengis.net/ont/geosparql#asGeoJSON": "DatatypeProperty",
                   "http://www.opengis.net/ont/geosparql#hasGeometry": "ObjectProperty",
                   "http://www.opengis.net/ont/geosparql#hasDefaultGeometry": "ObjectProperty",
                   "http://www.w3.org/2003/01/geo/wgs84_pos#geometry": "DatatypeProperty",
                   "http://www.georss.org/georss/point": "DatatypeProperty",
                   "http://www.w3.org/2006/vcard/ns#hasGeo": "ObjectProperty",
                   "http://www.w3.org/2003/01/geo/wgs84_pos#lat":"DatatypeProperty",
                   "http://www.w3.org/2003/01/geo/wgs84_pos#long": "DatatypeProperty",
                   "http://www.semanticweb.org/ontologies/2015/1/EPNet-ONTOP_Ontology#hasLatitude": "DatatypeProperty",
                   "http://www.semanticweb.org/ontologies/2015/1/EPNet-ONTOP_Ontology#hasLongitude": "DatatypeProperty",
                   "http://schema.org/geo": "ObjectProperty",
                   "http://geovocab.org/geometry#geometry": "ObjectProperty",
                   "http://www.w3.org/ns/locn#geometry": "ObjectProperty",
                   "http://rdfs.co/juso/geometry": "ObjectProperty",
                   "http://www.wikidata.org/prop/direct/P625":"DatatypeProperty",
                   "http://www.wikidata.org/prop/direct/P3896": "DatatypeProperty",
    }

    styleproperties={
        "http://www.opengis.net/ont/geosparql#style"
    }

    graphResource = ["solid:forClass"]

    authmethods={"HTTP BASIC":BASIC,"HTTP DIGEST":DIGEST}

    classicon=QIcon(":/icons/resources/icons/class.png")
    classschemaicon=QIcon(":/icons/resources/icons/classschema.png")
    geoclassschemaicon=QIcon(":/icons/resources/icons/geoclassschema.png")
    classlinkicon=QIcon(":/icons/resources/icons/classlink.png")
    linkedgeoclassicon=QIcon(":/icons/resources/icons/linkedgeoclass.png")
    addclassicon=QIcon(":/icons/resources/icons/addclass.png")
    addgeoclassicon=QIcon(":/icons/resources/icons/addgeoclass.png")
    addgeoinstanceicon=QIcon(":/icons/resources/icons/addgeoinstance.png")
    addinstanceicon=QIcon(":/icons/resources/icons/addinstance.png")
    countinstancesicon=QIcon(":/icons/resources/icons/countinstances.png")
    geoclassicon=QIcon(":/icons/resources/icons/geoclass.png")
    instanceicon=QIcon(":/icons/resources/icons/instance.png")
    instancelinkicon=QIcon(":/icons/resources/icons/instancelink.png")
    linkeddataicon=QIcon(":/icons/resources/icons/linkeddata.png")
    validationicon=QIcon(":/icons/resources/icons/validation2.png")
    halfgeoclassicon=QIcon(":/icons/resources/icons/halfgeoclass.png")
    annotationpropertyicon=QIcon(":/icons/resources/icons/annotationproperty.png")
    geoannotationpropertyicon=QIcon(":/icons/resources/icons/geoannotationproperty.png")
    objectpropertyicon=QIcon(":/icons/resources/icons/objectproperty.png")
    geoobjectpropertyicon=QIcon(":/icons/resources/icons/geoobjectproperty.png")
    datatypepropertyicon=QIcon(":/icons/resources/icons/datatypeproperty.png")
    geodatatypepropertyicon=QIcon(":/icons/resources/icons/geodatatypeproperty.png")
    geometrycollectionicon=QIcon(":/icons/resources/icons/geometrycollection.png")
    featurecollectionicon=QIcon(":/icons/resources/icons/featurecollection.png")
    featurecollectionToRDFicon=QIcon(":/icons/resources/icons/featurecollectionToRDF.png")
    geoinstanceicon=QIcon(":/icons/resources/icons/geoinstance.png")
    sparqlunicornicon=QIcon(':/icons/resources/icons/sparqlunicorn.png')
    classnode="Class"
    geoclassnode="GeoClass"
    linkedgeoclassnode="LinkedGeoClass"
    instancenode="Instance"
    objectpropertynode="ObjectProperty"
    datatypepropertynode="DatatypeProperty"
    geoinstancenode="GeoInstance"
    collectionclassnode="CollectionClass"
    instancesloadedindicator="InstancesLoaded"
    treeNodeToolTip="Double click to load, right click for menu"

    @staticmethod
    def executeQuery(triplestoreurl, query,triplestoreconf=None):
        results=False
        if isinstance(triplestoreurl, str):
            s = QSettings()  # getting proxy from qgis options settings
            proxyEnabled = s.value("proxy/proxyEnabled")
            proxyType = s.value("proxy/proxyType")
            proxyHost = s.value("proxy/proxyHost")
            proxyPort = s.value("proxy/proxyPort")
            proxyUser = s.value("proxy/proxyUser")
            proxyPassword = s.value("proxy/proxyPassword")
            if proxyHost != None and proxyHost != "" and proxyPort != None and proxyPort != "":
                QgsMessageLog.logMessage('Proxy? ' + str(proxyHost), MESSAGE_CATEGORY, Qgis.Info)
                proxy = urllib.request.ProxyHandler({'http': proxyHost})
                opener = urllib.request.build_opener(proxy)
                urllib.request.install_opener(opener)
            QgsMessageLog.logMessage('Started task "{}"'.format(query.replace("<","").replace(">","")), MESSAGE_CATEGORY, Qgis.Info)
            sparql = SPARQLWrapper(triplestoreurl)
            if triplestoreconf!=None and "auth" in triplestoreconf and "userCredential" in triplestoreconf["auth"] \
                    and triplestoreconf["auth"]["userCredential"]!="" \
                    and "userPassword" in triplestoreconf["auth"] \
                    and triplestoreconf["auth"]["userPassword"] != None:
                #QgsMessageLog.logMessage('Credentials? ' + str(triplestoreconf["auth"]["userCredential"])+" "+str(triplestoreconf["auth"]["userPassword"]), MESSAGE_CATEGORY, Qgis.Info)
                if "method" in triplestoreconf["auth"] and triplestoreconf["auth"]["method"] in SPARQLUtils.authmethods:
                    sparql.setHTTPAuth(SPARQLUtils.authmethods[triplestoreconf["auth"]["method"]])
                else:
                    sparql.setHTTPAuth(BASIC)
                sparql.setCredentials(triplestoreconf["auth"]["userCredential"], triplestoreconf["auth"]["userPassword"])
            sparql.setQuery(query)
            sparql.setMethod(GET)
            sparql.setReturnFormat(JSON)
            try:
                results = sparql.queryAndConvert()
                if "status_code" in results:
                    QgsMessageLog.logMessage("Result: " + str(results), MESSAGE_CATEGORY, Qgis.Info)
                    raise Exception
            except Exception as e:
                try:
                    sparql = SPARQLWrapper(triplestoreurl,
                                           agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11")
                    sparql.setQuery(query)
                    if triplestoreconf != None and "auth" in triplestoreconf and "userCredential" in triplestoreconf["auth"] \
                            and triplestoreconf["auth"]["userCredential"] != "" \
                            and "userPassword" in triplestoreconf["auth"] \
                            and triplestoreconf["auth"]["userPassword"] != None:
                        #QgsMessageLog.logMessage(
                        #    'Credentials? ' + str(triplestoreconf["auth"]["userCredential"]) + " " + str(
                        #       triplestoreconf["auth"]["userPassword"]), MESSAGE_CATEGORY, Qgis.Info)
                        if "method" in triplestoreconf["auth"] and triplestoreconf["auth"][
                            "method"] in SPARQLUtils.authmethods:
                            sparql.setHTTPAuth(SPARQLUtils.authmethods[triplestoreconf["auth"]["method"]])
                        else:
                            sparql.setHTTPAuth(BASIC)
                        sparql.setCredentials(triplestoreconf["auth"]["userCredential"],
                                              triplestoreconf["auth"]["userPassword"])
                    sparql.setMethod(POST)
                    sparql.setReturnFormat(JSON)
                    results = sparql.queryAndConvert()
                    if "status_code" in results:
                        QgsMessageLog.logMessage("Result: " + str(results), MESSAGE_CATEGORY, Qgis.Info)
                        raise Exception
                except:
                    QgsMessageLog.logMessage("Exception: " + str(e), MESSAGE_CATEGORY, Qgis.Info)
                    if "OntopUnsupportedInputQueryException: The expression Exists" in str(e):
                        return "Exists error"
                    return False
        else:
            graph=triplestoreurl
            QgsMessageLog.logMessage("Graph: " + str(triplestoreurl), MESSAGE_CATEGORY, Qgis.Info)
            QgsMessageLog.logMessage("Query: " + str(query), MESSAGE_CATEGORY, Qgis.Info)
            if graph!=None:
                results=json.loads(graph.query(query).serialize(format="json"))
        QgsMessageLog.logMessage("Result: " + str(results), MESSAGE_CATEGORY, Qgis.Info)
        return results

    @staticmethod
    def invertPrefixes(prefixes):
        #QgsMessageLog.logMessage("Invert Prefixes: " + str(prefixes), MESSAGE_CATEGORY, Qgis.Info)
        inv_map = {v: k for k, v in prefixes.items()}
        return inv_map

    @staticmethod
    def labelFromURI(uri,prefixlist=None):
        if "#" in uri:
            prefix=uri[:uri.rfind("#")+1]
            if prefixlist!=None and prefix in prefixlist:
                return str(prefixlist[prefix])+":"+str(uri[uri.rfind("#") + 1:])
            return uri[uri.rfind("#") + 1:]
        if "/" in uri:
            prefix=uri[:uri.rfind("/")+1]
            if prefixlist!=None and prefix in prefixlist:
                return str(prefixlist[prefix])+":"+str(uri[uri.rfind("/") + 1:])
            return uri[uri.rfind("/") + 1:]
        return uri

    @staticmethod
    def shortenLiteral(literal,numchars):
        return literal[numchars:]

    @staticmethod
    def expandRelValToAmount(query,amount):
        QgsMessageLog.logMessage('ExpandQuery '+str(amount)+"_" + str(query), MESSAGE_CATEGORY, Qgis.Info)
        if "?rel" not in query and "?val" not in query:
            return query
        selectpart=query[0:query.find("WHERE")]
        optionals="?item ?rel ?val . "
        if amount>1:
            for i in range(1,amount+1):
                selectpart+=" ?rel"+str(i)+" ?val"+str(i)+" "
                if i==1:
                    optionals += "OPTIONAL { ?val ?rel" + str(i) + " ?val" + str(i) + " . "
                else:
                    optionals+="OPTIONAL { ?val"+str(i-1)+" ?rel"+str(i)+" ?val"+str(i)+" . "
            for i in range(1,amount+1):
                optionals+="}"
        query=query.replace(query[0:query.find("WHERE")],selectpart).replace("?item ?rel ?val . ",optionals)
        QgsMessageLog.logMessage('ExpandQuery '+str(query), MESSAGE_CATEGORY, Qgis.Info)
        return query

    @staticmethod
    def loadAdditionalGraphResources(existinggraph,graphuri):
        if graphuri==None or graphuri=="":
            return None

    @staticmethod
    def loadGraph(graphuri,graph=None):
        if graphuri==None or graphuri=="":
            return None
        s = QSettings()  # getting proxy from qgis options settings
        proxyEnabled = s.value("proxy/proxyEnabled")
        proxyType = s.value("proxy/proxyType")
        proxyHost = s.value("proxy/proxyHost")
        proxyPort = s.value("proxy/proxyPort")
        proxyUser = s.value("proxy/proxyUser")
        proxyPassword = s.value("proxy/proxyPassword")
        if proxyHost != None and proxyHost != "" and proxyPort != None and proxyPort != "":
            #QgsMessageLog.logMessage('Proxy? ' + str(proxyHost), MESSAGE_CATEGORY, Qgis.Info)
            proxy = urllib.request.ProxyHandler({'http': proxyHost})
            opener = urllib.request.build_opener(proxy)
            urllib.request.install_opener(opener)
        #QgsMessageLog.logMessage('Started task "{}"'.format("Load Graph"), MESSAGE_CATEGORY, Qgis.Info)
        if graph==None:
            graph = Graph()
        try:
            if graphuri.startswith("http"):
                QgsMessageLog.logMessage(" Data: " + str(graphuri) + "", MESSAGE_CATEGORY, Qgis.Info)
                with urllib.request.urlopen(graphuri) as data:
                    readit=data.read().decode()
                    QgsMessageLog.logMessage(" Data: "+str(readit)+"", MESSAGE_CATEGORY, Qgis.Info)
                    filepath = graphuri.split(".")
                    graph.parse(data=readit,format=filepath[len(filepath) - 1])
            else:
                filepath = graphuri.split(".")
                result = graph.parse(graphuri, format=filepath[len(filepath) - 1])
        except Exception as e:
            QgsMessageLog.logMessage('Failed "{}"'.format(str(e)), MESSAGE_CATEGORY, Qgis.Info)
            #self.exception = str(e)
            return None
        return graph

    @staticmethod
    def detectLiteralTypeByURI(literal):
        return ""

    @staticmethod
    def detectGeoLiteralType(literal):
        try:
            geom = QgsGeometry.fromWkt(literal)
            return "wkt"
        except:
            print("no wkt")
        try:
            geom = QgsGeometry.fromWkb(bytes.fromhex(literal))
            return "wkb"
        except:
            print("no wkb")
        try:
            json.loads(literal)
            return "geojson"
        except:
            print("no geojson")
        return ""

    @staticmethod
    def handleURILiteral(uri):
        result = []
        if uri.startswith("http") and uri.endswith(".map"):
            try:
                f = urlopen(uri)
                myjson = json.loads(f.read())
                if "data" in myjson and "type" in myjson["data"] and myjson["data"]["type"] == "FeatureCollection":
                    features = myjson["data"]["features"]
                    for feat in features:
                        result.append(feat["geometry"])
                return result
            except:
                QgsMessageLog.logMessage("Error getting geoshape " + str(uri) + " - " + str(sys.exc_info()[0]))
        return None

    ## Executes a SPARQL endpoint specific query to find labels for given classes. The query may be configured in the configuration file.
    #  @param self The object pointer.
    #  @param classes array of classes to find labels for
    #  @param query the class label query
    @staticmethod
    def getLabelsForClasses(classes, query, triplestoreconf, triplestoreurl,preferredlang="en",typeindicator="class"):
        result = {}
        # url="https://www.wikidata.org/w/api.php?action=wbgetentities&props=labels&ids="
        if query==None:
            if typeindicator=="class":
                query="SELECT ?class ?label WHERE { %%concepts%% . OPTIONAL { ?class <"+str(triplestoreconf["labelproperty"])+"> ?label .\n FILTER langMatches(lang(?label), \""+str(preferredlang)+"\") } OPTIONAL { ?class <"+str(triplestoreconf["labelproperty"])+"> ?label . }}"
        if "SELECT" in query:
            vals = "VALUES ?class { "
            for qid in classes:
                vals += qid + " "
            vals += "}\n"
            query = query.replace("%%concepts%%", vals)
            results = SPARQLUtils.executeQuery(triplestoreurl, query)
            if results == False:
                return result
            for res in results["results"]["bindings"]:
                result[res["class"]["value"]] = res["label"]["value"]
        else:
            url = query
            i = 0
            qidquery = ""
            for qid in classes:
                #QgsMessageLog.logMessage(str(qid), MESSAGE_CATEGORY, Qgis.Info)
                if "wikidata" in triplestoreurl and "Q" in qid:
                    qidquery += "Q" + qid.split("Q")[1]
                elif "wikidata" in triplestoreurl and "P" in qid:
                    qidquery += "P" + qid.split("P")[1]
                elif "wikidata" in triplestoreurl:
                    result[qid] = qid
                    continue
                if (i % 50) == 0:
                    while qidquery.endswith("|"):
                        qidquery=qidquery[:-1]
                    #QgsMessageLog.logMessage(str(url.replace("%%concepts%%", qidquery)), MESSAGE_CATEGORY, Qgis.Info)
                    myResponse = json.loads(requests.get(url.replace("%%concepts%%", qidquery).replace("%%language%%",preferredlang)).text)
                    #QgsMessageLog.logMessage(str(myResponse), MESSAGE_CATEGORY, Qgis.Info)
                    #QgsMessageLog.logMessage("Entities: "+str(len(myResponse["entities"])), MESSAGE_CATEGORY, Qgis.Info)
                    if "entities" in myResponse:
                        for ent in myResponse["entities"]:
                            print(ent)
                            if preferredlang in myResponse["entities"][ent]["labels"]:
                                result[ent] = myResponse["entities"][ent]["labels"][preferredlang]["value"]
                            elif "en" in myResponse["entities"][ent]["labels"]:
                                result[ent] = myResponse["entities"][ent]["labels"]["en"]["value"]
                            else:
                                result[ent]=qid
                    qidquery = ""
                else:
                    qidquery += "|"
                i = i + 1
            if qidquery!="":
                while qidquery.endswith("|"):
                    qidquery = qidquery[:-1]
                #QgsMessageLog.logMessage(str(url.replace("%%concepts%%", qidquery)), MESSAGE_CATEGORY, Qgis.Info)
                myResponse = json.loads(requests.get(url.replace("%%concepts%%", qidquery)).text)
                #QgsMessageLog.logMessage(str(myResponse), MESSAGE_CATEGORY, Qgis.Info)
                # QgsMessageLog.logMessage("Entities: "+str(len(myResponse["entities"])), MESSAGE_CATEGORY, Qgis.Info)
                if "entities" in myResponse:
                    for ent in myResponse["entities"]:
                        print(ent)
                        if preferredlang in myResponse["entities"][ent]["labels"]:
                            result[ent] = myResponse["entities"][ent]["labels"][preferredlang]["value"]
                        elif "en" in myResponse["entities"][ent]["labels"]:
                            result[ent] = myResponse["entities"][ent]["labels"]["en"]["value"]
                        else:
                            result[ent] = ""
        return result
