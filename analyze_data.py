import sqlite3
import pandas as pd
import numpy as np
import os

DB_NAME = "annotation_system.db"

# Assicurati che la directory 'analysis' esista
if not os.path.exists("analysis"):
    os.makedirs("analysis")

def analyze_data():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Chiedi la categoria da analizzare
    cursor.execute("SELECT id, name FROM categories")
    categories = cursor.fetchall()

    if not categories:
        print("No categories found in the database.")
        conn.close()
        return

    print("Available categories:")
    for category in categories:
        print(f"{category[0]}. {category[1]}")

    category_id = int(input("Choose a category ID to analyze: "))

    # Recupera i dati necessari dal database con un JOIN appropriato
    query = """
        SELECT u.id AS userId, u.age, u.gender, u.education, p.text AS phrase, 
               SUM(CASE WHEN a.best THEN 1 ELSE 0 END) AS bestVotes,
               SUM(CASE WHEN a.worst THEN 1 ELSE 0 END) AS worstVotes
        FROM annotations a
        JOIN users u ON a.user_id = u.id
        JOIN phrases p ON a.phrase_id = p.id
        WHERE p.category_id = ? 
        GROUP BY p.text, u.id, u.age, u.gender, u.education
    """
    cursor.execute(query, (category_id,))
    data = cursor.fetchall()

    if not data:
        print("No data found for the selected category.")
        conn.close()
        return

    # Trasforma i dati in un DataFrame
    columns = ["userId", "age", "gender", "education", "phrase", "bestVotes", "worstVotes"]
    df = pd.DataFrame(data, columns=columns)

    # Calcola i voti totali e filtra le frasi con voti
    df["totalVotes"] = df["bestVotes"] + df["worstVotes"]
    df = df[df["totalVotes"] > 0]  # Filtra le frasi senza voti

    # Calcolo dei punteggi lineare
    df["linearScore"] = (df["bestVotes"] - df["worstVotes"]) / df["totalVotes"]

    if df.empty:
        print("No phrases with sufficient votes for analysis.")
        conn.close()
        return

    # Trasforma il punteggio lineare in percentuale offensività usando la formula:
    # ((1 - linearScore) / 2) * 100
    # In questo modo, linearScore = -1 -> 100% offensivo, linearScore = 1 -> 0% offensivo.
    overall_mean_linear = ((1 - df["linearScore"].mean()) / 2) * 100

    if np.isnan(overall_mean_linear):
        print("Error: No valid scores to calculate means.")
        conn.close()
        return

    print(f"Overall mean offensive score: {overall_mean_linear:.2f}%")

    # Calcolo della deviazione standard binaria per frase
    # p_offensive = worstVotes / totalVotes, poiché worst rappresenta i voti offensivi
    df["p_offensive"] = df["worstVotes"] / df["totalVotes"]
    df["stdDevBinary"] = 2 * np.sqrt(df["p_offensive"] * (1 - df["p_offensive"]))

    phrase_std_dev = df.groupby("phrase").agg(
        stdDevBinary=("stdDevBinary", "mean")
    ).reset_index()

    # Ordina le frasi per deviazione standard binaria (decrescente)
    phrase_std_dev = phrase_std_dev.sort_values(by="stdDevBinary", ascending=False)

    # Salva i risultati delle frasi
    phrase_output_file = f"analysis/phraseStdDevCategory_{category_id}.csv"
    phrase_std_dev.to_csv(phrase_output_file, index=False, sep=';', encoding='utf-8-sig')
    print(f"Phrase-wise binary standard deviation saved to {phrase_output_file}.")

    # Menu per l'analisi di gruppo
    print("Data Analysis Menu")
    print("1. Analyze by age")
    print("2. Analyze by gender")
    print("3. Analyze by education level")
    print("4. Exit")

    choice = input("Choose an analysis option: ")

    if choice == "1":
        def age_group(age):
            if age < 20:
                return "<20"
            elif 20 <= age < 30:
                return "20-29"
            elif 30 <= age < 40:
                return "30-39"
            elif 40 <= age < 50:
                return "40-49"
            elif 50 <= age < 60:
                return "50-59"
            else:
                return "60+"
        df["ageGroup"] = df["age"].apply(age_group)
        group_column = "ageGroup"
    elif choice == "2":
        group_column = "gender"
    elif choice == "3":
        group_column = "education"
    elif choice == "4":
        conn.close()
        return
    else:
        print("Invalid choice!")
        conn.close()
        return

    # Calcolo della media dei punteggi per gruppo (senza aggregazione per annotatore)
    mean_scores = df.groupby(group_column).agg(
        meanLinearScore=("linearScore", "mean"),
        totalVotes=("totalVotes", "sum")
    ).reset_index()

    # Calcolo della proporzione offensiva pesata per ciascun utente
    user_grouped = df.groupby([group_column, "userId"]).agg(
        totalWorst=("worstVotes", "sum"),
        totalVotes=("totalVotes", "sum")
    ).reset_index()
    user_grouped["userOffensiveProportion"] = user_grouped["totalWorst"] / user_grouped["totalVotes"]

    # Calcolo della deviazione standard tra annotatori per ciascun gruppo
    std_dev = user_grouped.groupby(group_column).agg(
        stdDevLinear=("userOffensiveProportion", "std")
    ).reset_index()

    # Unisco i risultati della media e della deviazione standard
    grouped = pd.merge(mean_scores, std_dev, on=group_column)

    # Trasforma il punteggio medio in percentuale offensività
    grouped["meanLinearScore"] = ((1 - grouped["meanLinearScore"]) / 2) * 100

    # Identifica le frasi più offensive con accordo uniforme (bassa deviazione standard)
    most_offensive_phrases = df.groupby("phrase").agg(
        meanOffensivityScore=("linearScore", "mean"),
        stdDevOffensivity=("linearScore", "std")
    ).reset_index()

    # Trasforma il punteggio medio offensività in percentuale usando la formula invertita
    most_offensive_phrases["meanOffensivityScore"] = ((1 - most_offensive_phrases["meanOffensivityScore"]) / 2) * 100

    # Seleziona le frasi con la deviazione standard più bassa e le ordina in ordine decrescente di offensività
    uniformly_offensive = most_offensive_phrases[
        most_offensive_phrases["stdDevOffensivity"] == most_offensive_phrases["stdDevOffensivity"].min()
    ]
    uniformly_offensive = uniformly_offensive.sort_values(by="meanOffensivityScore", ascending=False).head(5)

    # Salva i risultati principali
    output_file = f"analysis/analysisBy{group_column.capitalize()}Category_{category_id}.csv"
    grouped.to_csv(output_file, index=False, sep=';', encoding='utf-8-sig')

    # Appendi le frasi più offensive al file
    with open(output_file, "a", encoding="utf-8-sig") as f:
        f.write("\n--- Most Offensive Phrases (Uniform Agreement) ---\n")
        for _, row in uniformly_offensive.iterrows():
            f.write(
                f"Phrase: {row['phrase']}, Offensivity Score: {row['meanOffensivityScore']:.2f}%, Std Dev: {row['stdDevOffensivity']:.2f}\n"
            )

    print(f"Group-wise analysis and offensive phrases saved to {output_file}.")

    conn.close()
    # Formatta l'output con due cifre decimali e colonne ben allineate
    pd.set_option('display.float_format', lambda x: f"{x:6.2f}%")

    header = '\033[38;5;214m' + '  '.join(grouped.columns) + '\033[0m'
    print(f"\nAnalysis by {group_column.capitalize()} for category ID {category_id}:")
    print(header)
    for index, row in grouped.iterrows():
        print(f"{row[group_column]:>10}  {row['meanLinearScore']:>10.2f}%  {row['totalVotes']:>10}  {row['stdDevLinear']:>10.2f}%")

if __name__ == "__main__":
    analyze_data()
