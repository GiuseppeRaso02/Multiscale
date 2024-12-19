import sqlite3
from math import exp, log
from PyInquirer import prompt

DB_NAME = "annotation_system.db"

def annotate_category(user_id, category_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.id, p.text
        FROM phrases p
        LEFT JOIN annotations a ON p.id = a.phrase_id AND a.user_id = ?
        WHERE p.category_id = ? AND a.id IS NULL
    """, (user_id, category_id))
    phrases = cursor.fetchall()

    if not phrases:
        print("No more phrases to annotate in this category.")
        conn.close()
        return

    question_best = [
        {
            'type': 'checkbox',
            'name': 'best_phrases',
            'message': 'Select the BEST phrases:',
            'choices': [{'name': phrase[1], 'value': phrase[0]} for phrase in phrases]
        }
    ]
    best_phrases = prompt(question_best)['best_phrases']

    question_worst = [
        {
            'type': 'checkbox',
            'name': 'worst_phrases',
            'message': 'Select the WORST phrases:',
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

    for phrase in phrases:
        phrase_id, text, best_votes, worst_votes = phrase
        best_votes = best_votes or 0
        worst_votes = worst_votes or 0
        total_votes = best_votes + worst_votes

        if total_votes > 0:
            raw_score = (exp(best_votes) - exp(worst_votes)) / total_votes

            # Evita valori negativi per il logaritmo
            if raw_score < 0:
                normalized_score = 0.0
            else:
                normalized_score = (log(1 + raw_score) - log(1)) / (log(2) - log(1))
        else:
            normalized_score = 0.0

        scores[phrase_id] = (text, normalized_score)

    conn.close()

    print("Scores:")
    for phrase_id, (text, score) in scores.items():
        print(f"Phrase: {text}, Score: {score:.2f}")

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

    category_id = int(input("Choose a category ID to annotate: "))
    annotate_category(user_id, category_id)

    calculate_scores()

if __name__ == "__main__":
    annotation_menu()
