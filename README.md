# MediTwin Lab

MediTwin Lab e un laboratorio virtuale in silico basato su AI per simulare ipotesi terapeutiche, confrontare rischi e benefici, e apprendere da esperimenti biomedici digitali.

## Missione

MediTwin Lab nasce per supportare ricerca, formazione e ragionamento sperimentale in ambito biomedico.
L'obiettivo non e sostituire medici, trial clinici o terapie reali, ma offrire un ambiente sicuro dove:

- testare scenari teorici su pazienti virtuali;
- confrontare combinazioni farmacologiche e protocolli;
- analizzare possibili trade-off tra efficacia e tollerabilita;
- generare nuove ipotesi da validare con metodi scientifici reali.

## Posizionamento del prodotto

MediTwin Lab e progettato come:

- research simulator;
- educational tool;
- decision-support prototype per studio preclinico e accademico.

Non e una piattaforma di prescrizione, diagnosi o decisione clinica autonoma.

## Cosa simula

Il sistema costruisce un paziente virtuale con caratteristiche personalizzabili:

- demografia: eta, sesso, peso;
- quadro clinico: patologie, comorbidita, storia clinica;
- fisiologia: parametri vitali, biomarcatori, funzione epatica e renale;
- contesto terapeutico: farmaci in corso, dose, tempistiche, aderenza;
- fattori di rischio e stile di vita.

Su questa base, l'utente puo selezionare uno o piu principi attivi e avviare simulazioni che stimano:

- assorbimento, distribuzione, metabolismo, eliminazione (ADME);
- concentrazione nel tempo (profili teorici PK/PD);
- interazioni tra farmaci e vulnerabilita patient-specific;
- probabilita teorica di effetti avversi e benefici attesi;
- limiti del modello e aree ad alta incertezza.

## Output del motore AI

Ogni esperimento virtuale restituisce un report strutturato in cinque blocchi:

1. Benefici potenziali
2. Rischi e controindicazioni
3. Scenario evolutivo nel tempo
4. Parametri da monitorare
5. Grado di incertezza

Questo formato aiuta a distinguere chiaramente tra segnali robusti e ipotesi deboli.

## Ciclo operativo

1. Creazione del paziente virtuale.
2. Selezione della patologia (es. epilessia, oncologia, infiammazione cronica, rischio cardiovascolare).
3. Inserimento di farmaco singolo o combinazione terapeutica.
4. Esecuzione della simulazione.
5. Analisi di pro/contro, eventi avversi e parametri critici.
6. Modifica iterativa di dose, timing, combinazioni o caratteristiche del paziente.
7. Confronto tra esperimenti e aggiornamento della memoria scientifica interna.

## Modulo di apprendimento

Il sistema confronta gli esiti virtuali tra esperimenti multipli per:

- identificare pattern di successo o fallimento;
- evidenziare trade-off ricorrenti;
- aggiornare i modelli in modo incrementale;
- suggerire nuove ipotesi da testare.

L'AI e quindi un assistente di laboratorio digitale: osserva, confronta, apprende, corregge.

## Esempi d'uso

### Epilessia (scenario virtuale)

Simulazione di terapia combinata antiepilettica con valutazione di:

- controllo delle crisi;
- sedazione, sonnolenza, irritabilita, impatto cognitivo;
- variazioni di peso;
- interazioni metaboliche;
- effetto sulla qualita di vita e necessita di monitoraggio piu stretto.

### Oncologia (scenario virtuale)

Simulazione di scenari realistici, ad esempio:

- risposta parziale;
- resistenza terapeutica;
- tossicita cumulativa;
- impatto su biomarcatori;
- combinazioni con immunoterapia;
- rischio di progressione in base al profilo molecolare.

## Frase di progetto

**EN**: MediTwin Lab is an AI-powered in silico research environment to simulate therapeutic hypotheses, compare risks and benefits, and learn from virtual biomedical experiments.

**IT**: MediTwin Lab e un laboratorio virtuale basato su AI per simulare ipotesi terapeutiche, valutare benefici e rischi, e apprendere dagli esperimenti biomedici digitali.

## Safety, etica e limiti

MediTwin Lab deve includere in ogni ambiente, report e interfaccia i seguenti principi:

- Nessun consiglio medico reale.
- Nessuna prescrizione terapeutica.
- Nessuna sostituzione di professionisti sanitari o trial clinici.
- Obbligo di dichiarare incertezza e limiti del modello.
- Uso destinato a ricerca, formazione e prototipazione decision-support.

---

## Disclaimer

MediTwin Lab e un simulatore di ricerca in silico e uno strumento educativo.
I risultati sono ipotesi computazionali e non devono essere usati per diagnosi, prescrizione o decisioni cliniche reali.
Ogni valutazione sanitaria deve essere effettuata da professionisti qualificati e validata attraverso evidenze cliniche appropriate.

## Sito pubblico (GitHub Pages)

Il repository include una landing pubblica in [docs/index.html](docs/index.html) con:

- visione del progetto;
- workflow di simulazione;
- catalogo iniziale di fonti dati medicali, chimiche e alimentari;
- disclaimer safety sempre visibile.

Deploy automatico configurato con GitHub Actions in [.github/workflows/pages.yml](.github/workflows/pages.yml).

### Abilitazione Pages

1. Apri Settings > Pages nel repository GitHub.
2. In Build and deployment seleziona Source: GitHub Actions.
3. Esegui un push su main: il workflow pubblichera il contenuto della cartella docs.

## Fonti dati integrate (catalogo iniziale)

Le fonti sono elencate in [docs/data/sources.json](docs/data/sources.json) e comprendono esempi ad alta priorita come:

- medicali: PubMed, ClinicalTrials.gov, openFDA, Open Targets;
- chimiche: PubChem, ChEMBL, UniProt, KEGG;
- alimentari: USDA FoodData Central, EFSA OpenFoodTox, FooDB.

Nota: ogni fonte mantiene la propria licenza e termini d'uso; prima di un uso produttivo serve verificare compliance legale e scientifica per ciascun dataset.

## Piano tecnico minimo per diventare un riferimento

Per ottenere un impatto concreto, la versione pubblica deve evolvere in 4 moduli:

1. Data ingestion verificabile
2. Modello simulativo trasparente
3. Valutazione incertezza e rischio
4. Benchmark e validazione metodologica

Un possibile stack iniziale:

- data layer: PostgreSQL + estensioni analitiche + object storage;
- compute layer: pipeline ETL schedulate + versioning dataset;
- AI layer: modelli PK/PD ibridi (meccanicistici + probabilistici);
- serving layer: API con audit trail, report riproducibili e controllo versioni.

## Implementazione MVP inclusa nel repository

Questa versione include gia tre componenti operative:

1. Ingestione automatica API (openFDA, PubChem, USDA) con snapshot versionati.
2. Motore simulativo MVP rule-based con score di beneficio/rischio/incertezza.
3. Dashboard laboratorio su GitHub Pages con confronto esperimenti e storico paziente virtuale.

### 1) Ingestione API versionata

Script: [scripts/ingest_apis.py](scripts/ingest_apis.py)

Comando locale:

```bash
python3 scripts/ingest_apis.py
```

Output principali:

- snapshot timestamped in [data/ingestion](data/ingestion)
- manifest ultimo run in [data/ingestion/LATEST.json](data/ingestion/LATEST.json)
- feed live per dashboard in [docs/data/live/manifest.json](docs/data/live/manifest.json)
- knowledge base aggregata in [docs/data/live/knowledge_base.json](docs/data/live/knowledge_base.json)

Automazione CI: workflow schedulato in [.github/workflows/ingest.yml](.github/workflows/ingest.yml).

### 2) Motore simulativo MVP

Script: [scripts/simulate_mvp.py](scripts/simulate_mvp.py)

Input esempio: [data/experiments/sample_input.json](data/experiments/sample_input.json)

Comando locale:

```bash
python3 scripts/simulate_mvp.py --input data/experiments/sample_input.json
```

Output:

- report JSON strutturati in [data/experiments](data/experiments)
- indice storico in [data/experiments/index.json](data/experiments/index.json)

### 3) Dashboard laboratorio completa

Pagina principale: [docs/index.html](docs/index.html)

Feature incluse:

- catalogo fonti mediche/chimiche/alimentari con filtri;
- monitor ingestione API e stato dataset live;
- form Simulation Lab per creare esperimenti virtuali;
- report JSON visualizzato in tempo reale;
- storico esperimenti e confronto metriche;
- persistenza locale browser (localStorage) + seed iniziale.

Codice dashboard:

- logica applicativa in [docs/app.js](docs/app.js)
- stile in [docs/styles.css](docs/styles.css)
- dataset seed in [docs/data/seed_experiments.json](docs/data/seed_experiments.json)

## Backend API + Database

E stata aggiunta una API FastAPI con persistenza SQLite e autenticazione base via API key.

Struttura principale:

- applicazione API in [backend/app/main.py](backend/app/main.py)
- router endpoint in [backend/app/api/routes.py](backend/app/api/routes.py)
- modello DB in [backend/app/db/models.py](backend/app/db/models.py)
- motore simulativo API in [backend/app/services/simulation_engine.py](backend/app/services/simulation_engine.py)

### Installazione

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### Avvio API

```bash
source .venv/bin/activate
export PYTHONPATH=backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Swagger UI disponibile su `http://localhost:8000/docs`.

### Endpoint principali

- `GET /v1/health`
- `POST /v1/experiments/run` (richiede header `x-api-key`)
- `GET /v1/experiments`
- `GET /v1/experiments/{report_id}`
- `POST /v1/ingestion/run` (richiede header `x-api-key`)
- `GET /v1/terminologies/search?q=...`

## Terminologie e codifiche

Catalogo terminologico iniziale in [data/terminologies/catalog.json](data/terminologies/catalog.json) con mapping di base tra:

- RxNorm (farmaci);
- ATC (classificazione terapeutica);
- ICD-10 (patologie).

Il motore API normalizza i nomi delle terapie selezionate e include la sezione `normalized_therapies` nel report.

## Benchmark e validazione sintetica

Script benchmark in [scripts/run_validation_benchmark.py](scripts/run_validation_benchmark.py).

Esecuzione:

```bash
source .venv/bin/activate
python3 scripts/run_validation_benchmark.py
```

Output:

- storico benchmark in [data/validation](data/validation)
- ultimo risultato in [data/validation/LATEST.json](data/validation/LATEST.json)

## Test e CI

Test API in [backend/tests/test_api.py](backend/tests/test_api.py).

Esecuzione locale:

```bash
source .venv/bin/activate
export PYTHONPATH=backend
pytest backend/tests -q
```

Workflow CI backend: [.github/workflows/backend-ci.yml](.github/workflows/backend-ci.yml).