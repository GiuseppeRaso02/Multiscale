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

    # Recupera i dati necessari dal database
    query = """
        SELECT u.id AS user_id, u.age, u.gender, u.education, p.text, 
               SUM(CASE WHEN a.best THEN 1 ELSE 0 END) AS best_votes,
               SUM(CASE WHEN a.worst THEN 1 ELSE 0 END) AS worst_votes
        FROM annotations a
        JOIN users u ON a.user_id = u.id
        JOIN phrases p ON a.phrase_id = p.id
        WHERE p.category_id = ?
        GROUP BY u.id, u.age, u.gender, u.education, p.text
    """
    cursor.execute(query, (category_id,))
    data = cursor.fetchall()

    if not data:
        print("No data found for the selected category.")
        conn.close()
        return

    # Trasforma i dati in un DataFrame
    columns = ["user_id", "age", "gender", "education", "phrase", "best_votes", "worst_votes"]
    df = pd.DataFrame(data, columns=columns)

    # Calcola il punteggio lineare per ogni frase
    df["total_votes"] = df["best_votes"] + df["worst_votes"]
    df["linear_score"] = np.where(
        df["total_votes"] > 0,
        (df["best_votes"] - df["worst_votes"]) / df["total_votes"],
        0
    )

    # Calcola il punteggio esponenziale per ogni frase
    df["exponential_score"] = np.where(
        df["total_votes"] > 0,
        (np.exp(df["best_votes"]) - np.exp(df["worst_votes"])) /
        (np.exp(df["best_votes"]) + np.exp(df["worst_votes"])),
        0
    )

    # Filtra le frasi con almeno un minimo di voti (ad esempio 3 voti totali)
    min_votes = 3
    df = df[df["total_votes"] >= min_votes]

    # Calcola il punteggio medio generale
    overall_mean_linear = df["linear_score"].mean()
    overall_mean_exponential = df["exponential_score"].mean()

    print(f"Overall mean linear score: {overall_mean_linear:.2f}")
    print(f"Overall mean exponential score: {overall_mean_exponential:.2f}")

    # Calcolo deviazione standard frase per frase
    phrase_std_dev = df.groupby("phrase").agg(
        std_dev_linear=("linear_score", "std"),
        std_dev_exponential=("exponential_score", "std")
    ).reset_index()

    # Ordina le frasi per la deviazione standard lineare (decrescente)
    phrase_std_dev = phrase_std_dev.sort_values(by="std_dev_linear", ascending=False)

    # Salva i risultati delle frasi in un CSV
    phrase_output_file = f"analysis/phrase_std_dev_category_{category_id}.csv"
    phrase_std_dev.to_csv(phrase_output_file, index=False, sep=';', encoding='utf-8-sig')
    print(f"Phrase-wise standard deviation saved to {phrase_output_file}.")

    # Raggruppa i dati per categorie di interesse e calcola statistiche
    print("Data Analysis Menu")
    print("1. Analyze by age")
    print("2. Analyze by gender")
    print("3. Analyze by education level")
    print("4. Exit")

    choice = input("Choose an analysis option: ")

    if choice == "1":
        # Raggruppa le età in fasce
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

        df["age_group"] = df["age"].apply(age_group)
        group_column = "age_group"
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

    # Raggruppa i dati per la categoria scelta
    grouped = df.groupby(group_column).agg(
        mean_linear_score=("linear_score", "mean"),
        mean_exponential_score=("exponential_score", "mean"),
        total_votes=("total_votes", "sum")
    ).reset_index()

    # Calcola anche la deviazione assoluta rispetto alla media generale
    grouped["linear_mean_deviation"] = grouped["mean_linear_score"].apply(
        lambda group_mean: abs(group_mean - overall_mean_linear)
    )
    grouped["exponential_mean_deviation"] = grouped["mean_exponential_score"].apply(
        lambda group_mean: abs(group_mean - overall_mean_exponential)
    )

    # Salva i risultati delle analisi di gruppo in un CSV
    output_file = f"analysis/analysis_by_{group_column}_category_{category_id}.csv"
    grouped.to_csv(output_file, index=False, sep=';', encoding='utf-8-sig')
    print(f"Group-wise analysis saved to {output_file}.")

    print(f"\nAnalysis by {group_column.capitalize()} for category ID {category_id}:")
    print(grouped)

    conn.close()

if __name__ == "__main__":
    analyze_data()
