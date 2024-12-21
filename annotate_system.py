import sqlite3
from math import exp, log
from PyInquirer import prompt
import random

DB_NAME = "annotation_system.db"


def annotate_category(user_id, category_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Recupera tutte le frasi della categoria
    cursor.execute("SELECT id, text FROM phrases WHERE category_id = ?", (category_id,))
    all_phrases = cursor.fetchall()

    if not all_phrases:
        print("No phrases available in this category.")
        conn.close()
        return

    # Shuffle phrases to ensure randomness
    random.shuffle(all_phrases)

    # Chiedi quante frasi votare per volta
    num_phrases = int(input("How many phrases do you want to vote on at a time? "))

    # Chiedi quante ripetizioni fare
    repetitions = int(input("How many repetitions do you want? "))

    seen_phrases = set()

    for _ in range(repetitions):
        for i in range(0, len(all_phrases), num_phrases):
            phrases = all_phrases[i:i + num_phrases]

            # Ensure all phrases are seen at least once
            for phrase in phrases:
                seen_phrases.add(phrase[0])

            question_best = [
                {
                    'type': 'checkbox',
                    'name': 'best_phrases',
                    'message': 'Select the Offensive phrases:',
                    'choices': [{'name': phrase[1], 'value': phrase[0]} for phrase in phrases]
                }
            ]
            best_phrases = prompt(question_best)['best_phrases']

            question_worst = [
                {
                    'type': 'checkbox',
                    'name': 'worst_phrases',
                    'message': 'Select the not Offensive phrases:',
                    'choices': [{'name': phrase[1], 'value': phrase[0]} for phrase in phrases]
                }
            ]
            worst_phrases = prompt(question_worst)['worst_phrases']

            for phrase_id in best_phrases:
                cursor.execute("""
                    INSERT INTO annotations (user_id, phrase_id, best, worst)
                    VALUES (?, ?, ?, ?)
                """, (user_id, phrase_id, True, False))

            for phrase_id in worst_phrases:
                cursor.execute("""
                    INSERT INTO annotations (user_id, phrase_id, best, worst)
                    VALUES (?, ?, ?, ?)
                """, (user_id, phrase_id, False, True))

    # Ensure all phrases are seen at least once
    unseen_phrases = [phrase for phrase in all_phrases if phrase[0] not in seen_phrases]
    if unseen_phrases:
        print("The following phrases were not seen and will be presented now:")
        for phrase_id, text in unseen_phrases:
            print(text)

    conn.commit()
    conn.close()
    print("Annotations saved successfully!")


def calculate_scores():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.id, p.text, 
               SUM(CASE WHEN a.best THEN 1 ELSE 0 END) AS best_votes,
               SUM(CASE WHEN a.worst THEN 1 ELSE 0 END) AS worst_votes
        FROM phrases p
        LEFT JOIN annotations a ON p.id = a.phrase_id
        GROUP BY p.id
    """)

    phrases = cursor.fetchall()
    scores = {}

    max_raw_score = 0

    # Calcola i punteggi grezzi e trova il massimo
    for phrase in phrases:
        phrase_id, text, best_votes, worst_votes = phrase
        best_votes = best_votes or 0
        worst_votes = worst_votes or 0
        total_votes = best_votes + worst_votes

        if total_votes > 0:
            raw_score = max(0, (exp(best_votes) - exp(worst_votes)) / total_votes)  # Avoid negative raw_score
            max_raw_score = max(max_raw_score, raw_score)
            scores[phrase_id] = (text, raw_score)
        else:
            scores[phrase_id] = (text, 0.0)

    # Normalizza i punteggi in base al massimo valore calcolato
    for phrase_id, (text, raw_score) in scores.items():
        normalized_score = raw_score / max_raw_score if max_raw_score > 0 else 0.0
        scores[phrase_id] = (text, normalized_score)

    conn.close()

    print("Scores:")
    for phrase_id, (text, score) in scores.items():
        print(f"Phrase: {text}, Score: {score:.2f}")


def view_annotations_by_user():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    username = input("Enter the username to view annotations: ")
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    if not user:
        print("User not found!")
        conn.close()
        return
    user_id = user[0]

    cursor.execute("""
        SELECT p.text, a.best, a.worst
        FROM annotations a
        JOIN phrases p ON a.phrase_id = p.id
        WHERE a.user_id = ?
    """, (user_id,))

    annotations = cursor.fetchall()

    if not annotations:
        print(f"No annotations found for user '{username}'.")
    else:
        print(f"Annotations for user '{username}':")
        for text, best, worst in annotations:
            print(f"Phrase: {text}, Best: {bool(best)}, Worst: {bool(worst)}")

    conn.close()


def view_scores_by_category():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT id, name FROM categories")
    categories = cursor.fetchall()

    print("Available categories:")
    for category in categories:
        print(f"{category[0]}. {category[1]}")

    category_id = int(input("Choose a category ID to view scores: "))

    cursor.execute("""
        SELECT p.text, 
               SUM(CASE WHEN a.best THEN 1 ELSE 0 END) AS best_votes,
               SUM(CASE WHEN a.worst THEN 1 ELSE 0 END) AS worst_votes
        FROM phrases p
        LEFT JOIN annotations a ON p.id = a.phrase_id
        WHERE p.category_id = ?
        GROUP BY p.id
    """, (category_id,))

    phrases = cursor.fetchall()

    print(f"Scores for category {category_id}:")
    for text, best_votes, worst_votes in phrases:
        best_votes = best_votes or 0
        worst_votes = worst_votes or 0
        total_votes = best_votes + worst_votes

        if total_votes > 0:
            raw_score = max(0, (exp(best_votes) - exp(worst_votes)) / total_votes)
            normalized_score = raw_score / max(raw_score, 1)
        else:
            normalized_score = 0.0

        print(f"Phrase: {text}, Score: {normalized_score:.2f}")

    conn.close()


def annotation_menu():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    username = input("Enter your username: ")
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    if not user:
        print("User not found!")
        conn.close()
        return
    user_id = user[0]

    cursor.execute("SELECT id, name FROM categories")
    categories = cursor.fetchall()
    print("Available categories:")
    for category in categories:
        print(f"{category[0]}. {category[1]}")

    print("\nOptions:")
    print("1. Annotate a category")
    print("2. View annotations by user")
    print("3. View scores by category")
    choice = input("Choose an option: ")

    if choice == "1":
        category_id = int(input("Choose a category ID to annotate: "))
        annotate_category(user_id, category_id)
        calculate_scores()
    elif choice == "2":
        view_annotations_by_user()
    elif choice == "3":
        view_scores_by_category()
    else:
        print("Invalid option.")


if __name__ == "__main__":
    annotation_menu()