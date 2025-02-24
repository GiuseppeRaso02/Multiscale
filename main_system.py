import sqlite3
import csv
from setup_database import setup_database
from annotate_system import annotation_menu
from analyze_data import analyze_data
import questionary
from tabulate import tabulate  # pip install tabulate

DB_NAME = "annotation_system.db"


def add_user():
    username = questionary.text("Enter username:").ask().strip()
    age_str = questionary.text("Enter age:").ask().strip()
    try:
        age = int(age_str)
    except ValueError:
        print("Age must be a valid integer.")
        return
    gender = questionary.text("Enter gender (Male/Female/Non-Binary/Other):").ask().strip()
    education = questionary.select(
        "Enter education level:",
        choices=[
            "Elementary School",
            "Middle School",
            "High School Diploma",
            "Bachelor's Degree",
            "Master's Degree",
            "PhD"
        ]
    ).ask()

    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, age, gender, education) VALUES (?, ?, ?, ?)",
                (username, age, gender, education)
            )
            conn.commit()
        print(f"User '{username}' added successfully!")
    except sqlite3.Error as e:
        print("An error occurred while adding the user:", e)


def list_users():
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, age, gender, education FROM users")
            users = cursor.fetchall()
        if users:
            headers = ["ID", "Username", "Age", "Gender", "Education"]
            print(tabulate(users, headers=headers, tablefmt="pretty"))
        else:
            print("No users found.")
    except sqlite3.Error as e:
        print("Error retrieving users:", e)
    input("Press Enter to return to the main menu.")


def delete_user():
    username = questionary.text("Enter the username to delete:").ask().strip()
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            user = cursor.fetchone()
            if not user:
                print("User not found!")
            else:
                user_id = user[0]
                cursor.execute("DELETE FROM annotations WHERE user_id = ?", (user_id,))
                cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
                conn.commit()
                print(f"User '{username}' and all associated data have been deleted.")
    except sqlite3.Error as e:
        print("Error deleting user:", e)


def delete_all_annotations():
    confirm = questionary.confirm("Are you sure you want to delete all annotations?").ask()
    if confirm:
        try:
            with sqlite3.connect(DB_NAME) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM annotations")
                conn.commit()
            print("All annotations have been deleted.")
        except sqlite3.Error as e:
            print("Error deleting annotations:", e)
    else:
        print("Operation cancelled.")


def add_category():
    choice = questionary.select(
        "Add Category",
        choices=[
            "Enter category name",
            "Return to main menu"
        ]
    ).ask()
    if choice == "Return to main menu":
        return
    elif choice == "Enter category name":
        category_name = questionary.text("Enter category name:").ask().strip()
        try:
            with sqlite3.connect(DB_NAME) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO categories (name) VALUES (?)", (category_name,))
                conn.commit()
            print(f"Category '{category_name}' added successfully!")
        except sqlite3.Error as e:
            print("Error adding category:", e)


def import_phrases_from_tsv(category_id, filename):
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            with open(filename, 'r', encoding='utf-8') as file:
                reader = csv.reader(file, delimiter='\t')
                for row in reader:
                    if len(row) >= 2:
                        index, text = row[0], row[1]
                        cursor.execute("INSERT INTO phrases (text, category_id) VALUES (?, ?)", (text, category_id))
            conn.commit()
        print(f"Phrases from '{filename}' imported successfully!")
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found. Please check the file path and try again.")
    except Exception as e:
        print("An unexpected error occurred:", e)


def main():
    setup_database()
    while True:
        choice = questionary.select(
            "Main Menu",
            choices=[
                "Add User",
                "Delete User and Associated Data",
                "List Users",
                "Add Category",
                "Import Phrases (from TSV)",
                "Start Annotation",
                "Analyze Data",
                "Delete All Annotations",
                "Exit"
            ]
        ).ask()

        if choice == "Add User":
            add_user()
        elif choice == "Delete User and Associated Data":
            delete_user()
        elif choice == "List Users":
            list_users()
        elif choice == "Add Category":
            add_category()
        elif choice == "Import Phrases (from TSV)":
            category_name = questionary.text("Enter category name to import phrases into:").ask().strip()
            try:
                with sqlite3.connect(DB_NAME) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT id FROM categories WHERE name = ?", (category_name,))
                    category = cursor.fetchone()
                if not category:
                    print(f"Category '{category_name}' not found!")
                else:
                    category_id = category[0]
                    filename = questionary.text("Enter TSV filename (e.g., phrases.tsv):").ask().strip()
                    import_phrases_from_tsv(category_id, filename)
            except sqlite3.Error as e:
                print("Database error:", e)
        elif choice == "Start Annotation":
            annotation_menu()
        elif choice == "Analyze Data":
            analyze_data()
        elif choice == "Delete All Annotations":
            delete_all_annotations()
        elif choice == "Exit":
            print("Goodbye!")
            break


if __name__ == "__main__":
    main()
