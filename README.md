# UV-Safe: Radiazione Ultravioletta e Mitigazione Arborea nei Capoluoghi Italiani

Piattaforma analitica e Knowledge Graph RDF per valutare il rischio da radiazione solare e la protezione offerta dal verde urbano nei 110 comuni capoluogo italiani.

---

## 1. Obiettivi e Domanda di Ricerca

### 1.1 Contesto
Nei mesi estivi le aree urbane affrontano una forte pressione termica e radiativa dovuta alla combinazione di irraggiamento solare e superfici edificate. L'esposizione non protetta ai raggi ultravioletti rappresenta una delle principali cause di danni ai tessuti cutanei, favorendo scottature nel breve periodo e patologie croniche nel lungo termine.

In questo ambito la vegetazione cittadina agisce come una barriera naturale: le chiome degli alberi intercettano tra il 70% e il 90% della radiazione solare incidente, garantendo percorsi protetti e zone di sosta all'ombra.

### 1.2 Domanda di Ricerca
In che misura i capoluoghi italiani esposti a livelli critici di raggi UV durante l'estate dispongono di una percentuale di verde urbano sufficiente a mitigare l'esposizione diretta al suolo?

Lo studio confronta i valori massimi estivi dell'Indice UV registrati nel 2024 con la percentuale di verde urbano censita da ISTAT, classificando i comuni secondo i criteri sanitari internazionali definiti da OMS ed EPA.

---

## 2. Fonti Dati e Licenze

Il progetto utilizza esclusivamente dati aperti istituzionali che consentono la redistribuzione e il riutilizzo per qualsiasi finalità, inclusa quella commerciale.

### 2.1 Matrice delle Fonti Primarie

| Dataset | Fonte | Formato | Licenza | Accesso alla Sorgente | Ruolo nel Progetto |
| Dati ambientali nelle città: Verde Urbano 2024 | ISTAT | CSV (3 stelle) | CC BY 4.0 | [ISTAT DataBrowser](https://esploradati.istat.it/databrowser/#/it/dw/categories/IT1,Z0920ENV,1.0/ENV_CITIES/DCCV_URBANENV_URBGRE/IT1,609_1_DF_DCCV_URBANENV_18,1.0) | Percentuale di verde urbano comunale |
| Air Quality and Solar Radiation Archive 2024 | Open-Meteo Copernicus CAMS | CSV e JSON (3 stelle) | CC BY 4.0 | [Open-Meteo API](https://open-meteo.com/en/docs/air-quality-api) | Rilevazioni orarie e massimi estivi UVI |
| Wikidata Knowledge Base | Wikimedia Foundation | SPARQL e RDF (5 stelle) | CC0 1.0 | [Wikidata SPARQL Service](https://query.wikidata.org/) | Coordinate geografiche e interlinking LOD |

### 2.2 Compatibilità Giuridica
Le licenze CC BY 4.0 e CC0 1.0 consentono l'integrazione e la creazione di opere derivate senza clausole limitative. L'intero Knowledge Graph e il dataset consolidato sono rilasciati con licenza Creative Commons Attribuzione 4.0 (CC BY 4.0).

---

## 3. Elaborazione e Bonifica dei Dati

La pipeline di trasformazione è sviluppata all'interno del notebook progetto.ipynb secondo i passaggi seguenti:

1. Acquisizione e pulizia dei dati ISTAT
   I codici territoriali sono stati normalizzati a sei cifre con zeri iniziali e sono state eliminate le righe di aggregazione regionale o provinciale.
2. Riconciliazione geografica e arricchimento con Wikidata
   Tramite query SPARQL ogni codice ISTAT è stato associato al rispettivo identificatore stabile in Wikidata e alle coordinate geografiche ufficiali, raggiungendo una copertura del 100% sui 110 capoluoghi censiti.
3. Acquisizione radiometrica Open-Meteo
   Sulle coordinate dei comuni sono state estratte le serie orarie relative al trimestre compreso tra il primo giugno e il 31 agosto 2024, calcolando il valore massimo stagionale dell'indice UV.
4. Classificazione operativa OMS ed EPA
   I valori fisici dell'indice UV sono stati raggruppati nelle classi di allerta sanitaria standard:
   * UVI da 0.0 a 2.9: Rischio Basso
   * UVI da 3.0 a 5.9: Rischio Moderato
   * UVI da 6.0 a 7.9: Rischio Alto
   * UVI da 8.0 a 10.9: Rischio Molto Alto
   * UVI ≥ 11.0: Rischio Estremo
5. Generazione del dataset consolidato
   I dati armonizzati sono stati esportati nella tabella dataset/processed/uv_verde_unificato_2024.csv.

Nota territoriale: I capoluoghi italiani sono formalmente 112 per via delle province a sede condivisa, ma la rilevazione statistica annuale ISTAT seleziona storicamente 110 unità campionarie. Il dataset include la totalità dei comuni monitorati dalla fonte.

---

## 4. Modellazione Semantica e Knowledge Graph RDF

### 4.1 Ontologia di Dominio
Il modello concettuale è formalizzato nel file ontology/uv_safe_ontology.ttl riutilizzando vocabolari standard come schema.org, RDFS e OWL:
* Classe onto:City: sottoclasse di schema:City
* Proprietà di raccordo onto:sameAsWikidata: sottoproprietà di owl:sameAs
* Proprietà numeriche e descrittive:
  * onto:istatCode: codice identificativo del comune
  * schema:latitude e schema:longitude: coordinate territoriali
  * onto:greenDensity: incidenza percentuale del verde urbano
  * onto:uvMax: picco massimo di indice UV registrato
  * onto:uvClearSkyMax: indice teorico a cielo sereno
  * onto:riskCategoryOMS: categoria di rischio sanitario

### 4.2 Knowledge Graph
Il grafo generato con la libreria rdflib è serializzato in formato Turtle nel file output/uv_safe_graph.ttl:
* URI delle risorse: https://w3id.org/uvsafe/resource/city/{codice_istat}
* Collegamento esterno: ciascuna città è collegata alla corrispondente entità Wikidata tramite predicato owl:sameAs
* Consistenza del grafo: 110 risorse modellate per oltre 1100 triple semantiche validate

---

## 5. Query SPARQL di Esempio

I file delle query analitiche sono memorizzati nella cartella sparql/.

### 5.1 Comuni ad Alta Vulnerabilità
Individua le città caratterizzate da sollecitazione radiativa molto alta (UVI ≥ 8.0) e percentuale di verde inferiore al 5%:

```sparql
PREFIX ex: [https://w3id.org/uvsafe/ontology/](https://w3id.org/uvsafe/ontology/)
PREFIX rdfs: [http://www.w3.org/2000/01/rdf-schema#](http://www.w3.org/2000/01/rdf-schema#)

SELECT ?comune ?uvMax ?verde ?rischio
WHERE {
    ?city a ex:City ;
          rdfs:label ?comune ;
          ex:uvMax ?uvMax ;
          ex:greenDensity ?verde ;
          ex:riskCategoryOMS ?rischio .
    FILTER (?uvMax >= 8.0 && ?verde < 5.0)
}
ORDER BY DESC(?uvMax)