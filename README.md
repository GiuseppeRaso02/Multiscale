# Annotation System

Questo repository contiene un sistema per la gestione e l'annotazione dei dati, con funzionalità sia da linea di comando che tramite interfaccia grafica.

## Funzionalità

### Gestione Utenti e Categorie
- **Add User:** Aggiunge un nuovo utente al database.
- **Delete User:** Rimuove un utente e tutte le sue annotazioni.
- **List User:** Visualizza tutti gli utenti presenti nel database.
- **Add Category:** Aggiunge una nuova categoria nel sistema.

### Importazione Frasi
- **Import Phrases (from TSV):**  
  - Prende un file `.tsv` (con il nome specificato) e importa tutte le frasi nel database.
  - Una volta avviato il comando, se si preme **Start Annotation** appariranno le seguenti opzioni:
    - **Annotate a Category:** Permette di annotare le frasi appartenenti ad una categoria.
    - **View Annotations by User:** Mostra le annotazioni suddivise per utente.
    - **View Scores by Category:** Visualizza i punteggi delle annotazioni raggruppati per categoria.

### Analisi Dati
- **Analyze Data:**  
  Analizza i dati in base alle categorie disponibili. Durante l'analisi è possibile scegliere:
  1. **Analyze by Age:** Raggruppa e confronta i dati in base all'età degli utenti.
  2. **Analyze by Gender:** Raggruppa e confronta i dati in base al genere.
  3. **Analyze by Education Level:** Raggruppa e confronta i dati in base al livello di istruzione.

## Requisiti

- Python 3.6 o superiore
- SQLite3
- [Pandas](https://pandas.pydata.org/)
- [NumPy](https://numpy.org/)
- [Matplotlib](https://matplotlib.org/)
- [Seaborn](https://seaborn.pydata.org/)
- [SciPy](https://scipy.org/)
- [Questionary](https://github.com/tmbo/questionary)
- [Tabulate](https://pypi.org/project/tabulate/)

Le dipendenze possono essere installate eseguendo:

```bash
pip install -r requirements.txt
```
## Utilizzo
### Database
Se non si desidera utilizzare il database già popolato, è possibile ricrearlo semplicemente eliminando il file del database esistente (ad esempio annotation_system.db) prima di eseguire il sistema.

## Modalità a Linea di Comando
Per eseguire il sistema dalla linea di comando, lancia:
```bash
python main_system.py
```
Questo comando gestisce le operazioni di:

Aggiunta, rimozione e visualizzazione degli utenti e delle categorie.
Importazione delle frasi da file TSV.
Avvio del processo di annotazione, che offre le seguenti opzioni:
- **Annotate a Category**
- **View Annotations by User**
- **View Scores by Category**
Analisi dei dati, con opzioni di raggruppamento per età, genere e livello di istruzione.
## Modalità Interfaccia Grafica
Per effettuare l'annotazione tramite interfaccia grafica, vai nella cartella GUI ed esegui:
```bash
python main_window.py
```
Questo aprirà una finestra interattiva che ti permetterà di annotare le frasi.

## Struttura del Repository
- **main_system.py**: Script principale per la gestione a linea di comando e l'analisi dei dati.
- **analysis.py**: Script per generare grafici e analizzare i dati.
- **annotation_system.db**: Database SQLite (se presente). Può essere eliminato per ricreare un database nuovo.
- **requirements.txt**: Elenco delle librerie Python necessarie.
- **GUI/**: Cartella contenente il codice per l'interfaccia grafica (es. main_window.py).
- **README.md**: Questo file di documentazione.

Contributi
Se desideri contribuire al progetto, sentiti libero di aprire una issue o inviare una pull request. Le modifiche e i suggerimenti sono benvenuti!
