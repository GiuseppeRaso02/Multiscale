import sqlite3
import pandas as pd
import matplotlib
matplotlib.use('TkAgg')  # Forza il backend TkAgg se necessario
import matplotlib.pyplot as plt
import seaborn as sns

# Imposta il percorso del database (modifica se necessario)
DB_NAME = "annotation_system.db"

# Esegui una query per ottenere per ogni utente la percentuale offensiva media
conn = sqlite3.connect(DB_NAME)
query = """
SELECT 
    u.id,
    u.username,
    u.age,
    u.gender,
    u.education,
    AVG( (a.worst*1.0) / (a.best + a.worst) * 100 ) AS avg_offensive_pct
FROM annotations a
JOIN users u ON a.user_id = u.id
GROUP BY u.id
"""
df_users = pd.read_sql_query(query, conn)
conn.close()

# Rimuovi eventuali righe con valori nulli
df_users = df_users.dropna(subset=["avg_offensive_pct"])

# Visualizza il grafico scatter: età vs percentuale offensiva media per utente
plt.figure(figsize=(10,6))
sns.scatterplot(data=df_users, x="age", y="avg_offensive_pct", hue="education", palette="viridis", s=80, alpha=0.8)
plt.title("Average Offensive Percentage by User")
plt.xlabel("Age")
plt.ylabel("Average Offensive Percentage (%)")
plt.legend(title="Education Level", bbox_to_anchor=(1.05, 1), loc="upper left")
plt.tight_layout()
plt.show()
