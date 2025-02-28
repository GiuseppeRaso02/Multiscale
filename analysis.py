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

# Imposta l'ordine desiderato per le opzioni di istruzione
edu_order = ["Elementary School","Middle School","High School Diploma","Bachelor's Degree","Master's Degree","PhD"]
df_users["education"] = pd.Categorical(df_users["education"], categories=edu_order, ordered=True)

# Grafico 1: Scatter plot - Età vs Percentuale Offensiva Media per utente
plt.figure(figsize=(10,6))
custom_palette = sns.color_palette("tab10", n_colors=len(edu_order))
sns.scatterplot(data=df_users, x="age", y="avg_offensive_pct", hue="education",
                hue_order=edu_order, palette=custom_palette, s=80, alpha=0.8)
plt.title("Average Offensive Percentage by User")
plt.xlabel("Age")
plt.ylabel("Average Offensive Percentage (%)")
plt.legend(title="Education Level", bbox_to_anchor=(1.05, 1), loc="upper left")
plt.tight_layout()
plt.show()


# Grafico 2: Box plot - Distribuzione della Percentuale Offensiva per Genere
plt.figure(figsize=(8,6))
sns.boxplot(data=df_users, x="gender", y="avg_offensive_pct", palette="viridis")
plt.title("Distribution of Offensive Percentage by Gender")
plt.xlabel("Gender")
plt.ylabel("Average Offensive Percentage (%)")
plt.tight_layout()
plt.show()

# Grafico 3: Violin Plot - Distribuzione della Percentuale Offensiva per Livello di Istruzione
plt.figure(figsize=(10,6))
sns.violinplot(data=df_users, x="education", y="avg_offensive_pct", order=edu_order, palette="tab10")
plt.title("Violin Plot of Offensive Percentage by Education Level")
plt.xlabel("Education Level")
plt.ylabel("Average Offensive Percentage (%)")
plt.tight_layout()
plt.show()

# Grafico 4: Histogram/KDE Plot - Distribuzione della Percentuale Offensiva per Genere
plt.figure(figsize=(10,6))
sns.histplot(data=df_users, x="avg_offensive_pct", hue="gender", kde=True, palette="Set2",
             element="step", stat="density", common_norm=False)
plt.title("Distribution of Offensive Percentage by Gender")
plt.xlabel("Average Offensive Percentage (%)")
plt.ylabel("Density")
plt.tight_layout()
plt.show()

