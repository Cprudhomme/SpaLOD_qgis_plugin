## B1 - Plugin-Icon
> Für das Plugin ist das Icon einzubinden. Die nötige Grafik-Datei ist vorhanden.

This bug is fixed. The problem was in the icon path


## B2 - Bounding Box
> Betrifft die Funktion F1. Für Abfragen wurde die Möglichkeit einer räumlichen Einschränkung über eine Bounding Box (frei wählbar oder über Layer-Ausdehnung) implementiert. Bei der Ausführung der Abfrage wird eine Fehlermeldung zurückgemeldet. Die Fehler bzgl. der bestehenden Implementierung sind zu lösen.

This bug is fixed for wikidata and dbpedia triple store. For the 4 others, the query does not work, the result is always empty


## B3 - Query Box
> Betrifft die Funktion F1. Für Abfragen wurde in der Ober-fl äche ein Eingabefenster implementiert. Dieses ist so anzupassen, dass es dynamisch mit der Fenstergröße skaliert.

This bug is fixed using an horizontal layout with expanding strategy


## B4 - Schaltfl ächen
> Die Beschriftungen der Schaltflächen sind auf Englisch zu ändern.

This bug is fixed. By default, QGIS translates all texts if they are parts of their translation database


## B5 - Stabilität Enrichment: Columns
> Betrifft die Funktion F3. Beim Einladen von Layern mit vie-len Spalten stürzt das Plugin ab.

This bug is not reproducible. This functionnality always work well but sometimes, it can take some times for datasets with 500+ columns


## B6 - Escaping
> Betrifft die Funktion F3. Enthält das Schlüsselattribut Anfüh-rungszeichen wird die Query unterbrochen. Die Abfragen müssen entsprechend angepasst werden um problema-tische Zeichen zu entfernen oder zu escapen.

This bug is fixed escaping quotes in property string


## B7 - Attribut fehlt
> Betrifft die Funktion F3. Wenn der angereicherte Layer hin-zugefügt wird, fehlt die angereicherte Spalte in den Daten.

This bug is not reproducible. This functionality always work well, the column is always present in the enriched layer


## R1 - Sprache des anzureichernden Attributs
> Betrifft die Enrichment-Funktion (F3). Aktuell wird das zu ergänzende Attribut in einer beliebigen Sprache hinzugefügt. Hier sollte die Sprache festgelegt werden können.

This bug is fixed, the query with [AUTO_LANGUAGE] was not working


## R2 - Weitere Triplestores
> Betrifft die Funktion F1 und F3. Für die Funktionen sollen weitere Triplestore eingebunden werden, die abgefragt wer-den können, mindestens Wikidata, DBPedia, LinkedGeoData, Geonames.

Fixed. All triple stores are now available. The sparql queries are fixed and https requests now work well


## R3 - Weitere Schlüsselwerte
> Betrifft die Enrichment-Funktion (F3). Für die Zuordnung der Objekte aus dem Bestandsdatensatz zu den Objekten aus dem Anreicherungsdatensatz sollten mehrere Schlüs- selattribute möglich sein. Aktuell kann das Schlüsselattribut des Bestandsdatensatzes ausgewählt werden. Dieses wird mit dem Label-Attribut des Anreicherungsdatensatzes er-gleichen. Hier ist eine Zuordnung anhand weiterer Attribute umzusetzen, mindestens räumliche Nähe und Wikidata ID.

This feature has been implemented using a combobox with multiple choices for the key attribute


## R4 - Vergleichsoperatoren
> Betrifft die Funktionen F1 und F3. Für die Funktionen sollen unscharfe Vergleichsoperatoren mittels "contains" oder reguläre Ausdrücke eingebunden werden. Dies betrifft die SPARQL Abfragen der Konzepte sowie der Objekte.

This feature seems difficult to implement. Each time the filter function is added, the request timed out.

For example, [this query](https://query.wikidata.org/#SELECT%20distinct%20%3Fitem%20%3Fval%20%3FvalLabel%20%3Fvals%20WHERE%20%7B%0A%20%20%20%20VALUES%20%3Fvals%20%7B%20%22Georg-Schlesinger-Schule%22%20%7D%20.%20%0A%20%20%20%20%3Fitem%20%3Frel%20%3Fval%20.%0A%0A%20%20%20%20filter%28regex%28%3Fval%2C%20%3Fvals%29%29.%0A%0A%20%20%20%20SERVICE%20wikibase%3Alabel%20%7B%20bd%3AserviceParam%20wikibase%3Alanguage%20%22%5BAUTO_LANGUAGE%5D%2Cen%22.%20%7D%0A%7D) will never work:

```sql
SELECT distinct ?item ?val ?valLabel ?vals WHERE {
    VALUES ?vals { "Georg-Schlesinger-Schule" } .
    ?item ?rel ?val .

    filter(regex(?val, ?vals)).

    SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
}
```

It seems that the request execution tree is not optimized for such a query.


## R5 – Semantische Suche
> Betrifft die Funktionen F1 und F3. Für die Funktionen soll die Suche auf eine semantische Suchfunktion erweitert werden. Ziel ist, dass bei der Suche nach beispielsweise Schulen auf Wunsch auch Unterkategorien wie Grundschulen in die Ergebnismenge inkludiert werden.

This feature has been implemented using a union in the sparql request. It lets us choose all the concepts we want to include in the dataset. So we can easily choose either the elementary school and the primary school in one request.

In the HMI, a new checkbox "Concept union" is added in the geoconcepts list


## R6 - Objektverbindungen
> Betrifft die Funktionen F1 und F3. Es soll eine Möglichkeit zur explorativen Recherche anhand von Suchergebnissen ermöglicht werden. Dadurch soll es ermöglicht werden nach verbundenen Objekten zu suchen, beispielsweise anhand der Relation "part of".

This feature has been implemented using a specific query part for the 2 triple stores wikidata and dbpedia that add the partof.

In the HMI, a new checkbox "Part of" is added in the geoconcepts list