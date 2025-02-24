import sqlite3
import random
import textwrap
import questionary
from tabulate import tabulate


DB_NAME = "annotation_system.db"


def format_phrase(phrase, width=80):
    """Formatta la frase per adattarla alla larghezza del terminale"""
    return "\n".join(textwrap.wrap(phrase, width))


def annotate_category(user_id, category_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()

        # Recupera tutte le frasi della categoria
        cursor.execute("SELECT id, text FROM phrases WHERE category_id = ?", (category_id,))
        all_phrases = cursor.fetchall()

        if not all_phrases:
            print("No phrases available in this category.")
            return

        # Shuffle phrases per randomizzare l'ordine
        random.shuffle(all_phrases)

        # Chiedi quante frasi votare per volta
        num_phrases_str = questionary.text("How many phrases do you want to vote on at a time?").ask()
        try:
            num_phrases = int(num_phrases_str)
        except ValueError:
            print("Invalid number, defaulting to 5.")
            num_phrases = 5

        # Chiedi quante ripetizioni fare
        repetitions_str = questionary.text("How many repetitions do you want?").ask()
        try:
            repetitions = int(repetitions_str)
        except ValueError:
            print("Invalid number, defaulting to 1.")
            repetitions = 1

        seen_phrases = set()

        # Funzione di salvataggio comune per "exit"
        def save_and_exit(selected_ids, best_flag):
            for phrase_id in selected_ids:
                # Se best_flag è True, inserisce come non offensive (best=True, worst=False)
                cursor.execute("""
                    INSERT INTO annotations (user_id, phrase_id, best, worst)
                    VALUES (?, ?, ?, ?)
                """, (user_id, phrase_id, best_flag, not best_flag))
            conn.commit()
            print("Annotations saved successfully! Exiting early.")

        for _ in range(repetitions):
            random.shuffle(all_phrases)  # Rimescola ad ogni ripetizione
            for i in range(0, len(all_phrases), num_phrases):
                phrases = all_phrases[i:i + num_phrases]

                # Registra l'ID di tutte le frasi visualizzate
                for phrase in phrases:
                    seen_phrases.add(phrase[0])

                formatted_choices = [{'name': format_phrase(phrase[1]), 'value': phrase[0]} for phrase in phrases]
                # Aggiunge l'opzione di uscita
                formatted_choices.append({'name': 'Exit and Save', 'value': 'exit'})

                # Seleziona le frasi offensive (ovvero, quelle per cui l’utente indica "offensive")
                offensive_ids = questionary.checkbox(
                    'Select the Offensive phrases (or choose Exit to save):',
                    choices=formatted_choices
                ).ask()

                if 'exit' in offensive_ids:
                    offensive_ids.remove('exit')
                    save_and_exit(offensive_ids, best_flag=False)
                    return

                # Seleziona le frasi NON offensive
                non_offensive_ids = questionary.checkbox(
                    'Select the Non-Offensive phrases (or choose Exit to save):',
                    choices=formatted_choices
                ).ask()

                if 'exit' in non_offensive_ids:
                    non_offensive_ids.remove('exit')
                    save_and_exit(non_offensive_ids, best_flag=True)
                    return

                # Salva le annotazioni per le due scelte
                for phrase_id in offensive_ids:
                    cursor.execute("""
                        INSERT INTO annotations (user_id, phrase_id, best, worst)
                        VALUES (?, ?, ?, ?)
                    """, (user_id, phrase_id, False, True))
                for phrase_id in non_offensive_ids:
                    cursor.execute("""
                        INSERT INTO annotations (user_id, phrase_id, best, worst)
                        VALUES (?, ?, ?, ?)
                    """, (user_id, phrase_id, True, False))
        # Dopo le ripetizioni, controlla se ci sono frasi non viste
        unseen_phrases = [phrase for phrase in all_phrases if phrase[0] not in seen_phrases]
        if unseen_phrases:
            print("The following phrases were not seen and will be presented now:")
            for phrase_id, text in unseen_phrases:
                print(format_phrase(text))
        conn.commit()
        print("Annotations saved successfully!")


def calculate_scores_for_user(user_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.id, p.text, 
                   SUM(CASE WHEN a.best THEN 1 ELSE 0 END) AS best_votes,
                   SUM(CASE WHEN a.worst THEN 1 ELSE 0 END) AS worst_votes
            FROM phrases p
            LEFT JOIN annotations a ON p.id = a.phrase_id
            WHERE a.user_id = ?
            GROUP BY p.id
        """, (user_id,))
        phrases = cursor.fetchall()

    scores = {}
    for phrase in phrases:
        phrase_id, text, best_votes, worst_votes = phrase
        best_votes = best_votes or 0
        worst_votes = worst_votes or 0
        total_votes = best_votes + worst_votes

        if total_votes > 0:
            raw_score = (worst_votes - best_votes) / total_votes
            normalized_score = (raw_score + 1) / 2  # Mappa da [-1, 1] a [0, 1]
            scores[phrase_id] = (text, normalized_score)
        else:
            scores[phrase_id] = (text, 0.5)

    print("Scores for user:")
    for phrase_id, (text, score) in scores.items():
        print(f"Phrase: {text}, Score: {score:.2f}")


def view_annotations_by_user(existing_username=None):

    # Usa il nome utente esistente se fornito, altrimenti chiedilo
    if existing_username:
        username = existing_username
    else:
        username = questionary.text("Enter the username to view annotations:").ask().strip()

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        if not user:
            print("User not found!")
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
        table = []
        for text, best, worst in annotations:
            # Tronca il testo per una visualizzazione più ordinata (max 80 caratteri)
            short_text = textwrap.shorten(text, width=80, placeholder="...")
            table.append([short_text, bool(best), bool(worst)])
        headers = ["Phrase", "Best", "Worst"]
        print(f"Annotations for user '{username}':")
        print(tabulate(table, headers=headers, tablefmt="pretty"))


def view_scores_by_category():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM categories")
        categories = cursor.fetchall()
    if not categories:
        print("No categories found.")
        return
    print("Available categories:")
    for category in categories:
        print(f"{category[0]}. {category[1]}")

    category_id_str = questionary.text("Choose a category ID to view scores:").ask().strip()
    try:
        category_id = int(category_id_str)
    except ValueError:
        print("Invalid category ID.")
        return

    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
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

    table = []
    # Calcolo lineare del punteggio:
    # raw_score = (worst_votes - best_votes) / total_votes
    # normalized_score = (raw_score + 1) / 2
    for text, best_votes, worst_votes in phrases:
        best_votes = best_votes or 0
        worst_votes = worst_votes or 0
        total_votes = best_votes + worst_votes
        if total_votes > 0:
            raw_score = (worst_votes - best_votes) / total_votes
            normalized_score = (raw_score + 1) / 2
        else:
            normalized_score = 0.5
        short_text = textwrap.shorten(text, width=80, placeholder="...")
        table.append([short_text, best_votes, worst_votes, total_votes, f"{normalized_score:.2f}"])
    headers = ["Phrase", "Best Votes", "Worst Votes", "Total Votes", "Score"]
    print(f"Scores for category {category_id}:")
    print(tabulate(table, headers=headers, tablefmt="pretty"))


def annotation_menu():
    username = questionary.text("Enter your username:").ask().strip()
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        if not user:
            print("User not found!")
            return
        user_id = user[0]
        cursor.execute("SELECT id, name FROM categories")
        categories = cursor.fetchall()

    print("Available categories:")
    for category in categories:
        print(f"{category[0]}. {category[1]}")

    option = questionary.select(
        "Options:",
        choices=[
            "Annotate a category",
            "View annotations by user",
            "View scores by category"
        ]
    ).ask()

    if option == "Annotate a category":
        category_id_str = questionary.text("Choose a category ID to annotate:").ask().strip()
        try:
            category_id = int(category_id_str)
        except ValueError:
            print("Invalid category ID.")
            return
        annotate_category(user_id, category_id)
        # Nel sottomenu di annotation_menu, dopo aver già ottenuto 'username'
    elif option == "View annotations by user":
        view_annotations_by_user(username)
    elif option == "View scores by category":
        view_scores_by_category()
    else:
        print("Invalid option.")


if __name__ == "__main__":
    annotation_menu()
