import sqlite3
import pandas as pd
import numpy as np

DB_NAME = "annotation_system.db"

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

    # Calcola il punteggio normalizzato per ogni frase
    df["total_votes"] = df["best_votes"] + df["worst_votes"]
    df["score"] = np.where(
        df["total_votes"] > 0,
        (df["best_votes"] - df["worst_votes"]) / df["total_votes"],
        0
    )

    # Calcola statistiche individuali per ogni utente
    user_stats = df.groupby("user_id").agg(
        mean_score=("score", "mean"),
        std_dev=("score", "std"),
        total_votes=("total_votes", "sum")
    ).reset_index()

    # Aggiungi metadati degli utenti
    user_stats = user_stats.merge(df[["user_id", "age", "gender", "education"]].drop_duplicates(), on="user_id")

    # Filtra i dati per categorie di interesse e calcola statistiche aggregate
    print("Data Analysis Menu")
    print("1. Analyze by age")
    print("2. Analyze by gender")
    print("3. Analyze by education level")
    print("4. Exit")

    choice = input("Choose an analysis option: ")

    if choice == "1":
        group_column = "age"
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
    grouped = user_stats.groupby(group_column).agg(
        mean_score=("mean_score", "mean"),
        std_dev=("mean_score", "std"),
        total_votes=("total_votes", "sum")
    ).reset_index()

    print(f"\nAnalysis by {group_column.capitalize()} for category ID {category_id}:")
    print(grouped)

    # Salva i risultati in un file CSV
    output_file = f"analysis_by_{group_column}_category_{category_id}.csv"
    grouped.to_csv(output_file, index=False)
    print(f"Analysis saved to {output_file}.")

    conn.close()

if __name__ == "__main__":
    analyze_data()
