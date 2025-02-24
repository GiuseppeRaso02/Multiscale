import sqlite3

DB_NAME = "annotation_system.db"
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# Esegui lo swap: in SQLite gli aggiornamenti vengono effettuati utilizzando i valori originali per ogni riga
cursor.execute("UPDATE annotations SET best = worst, worst = best")
conn.commit()
conn.close()
