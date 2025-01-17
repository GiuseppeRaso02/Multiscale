import sqlite3
import csv
from setup_database import setup_database
from annotate_system import annotation_menu
from analyze_data import analyze_data
from PyInquirer import prompt

DB_NAME = "annotation_system.db"

def add_user():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    username = input("Enter username: ")
    age = int(input("Enter age: "))
    gender = input("Enter gender (Male/Female/Non-Binary/Other): ")

    question_education = [
        {
            'type': 'list',
            'name': 'education',
            'message': 'Enter education level:',
            'choices': [
                "Elementary School",
                "Middle School",
                "High School Diploma",
                "Bachelor's Degree",
                "Master's Degree",
                "PhD"
            ]
        }
    ]

    education = prompt(question_education)['education']

    cursor.execute("""
        INSERT INTO users (username, age, gender, education)
        VALUES (?, ?, ?, ?)
    """, (username, age, gender, education))

    conn.commit()
    conn.close()
    print(f"User {username} added successfully!")

def list_users():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    conn.close()

    print("Users List:")
    for user in users:
        print(user)

    input("Press Enter to return to the main menu.")

def delete_user():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    username = input("Enter the username to delete: ")
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

    conn.close()

def delete_all_annotations():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    confirm = input("Are you sure you want to delete all annotations? (yes/no): ").lower()
    if confirm == "yes":
        cursor.execute("DELETE FROM annotations")
        conn.commit()
        print("All annotations have been deleted.")
    else:
        print("Operation cancelled.")

    conn.close()

def add_category():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    while True:
        print("Add Category")
        print("1. Enter category name")
        print("2. Return to main menu")

        choice = input("Choose an option: ")
        if choice == "2":
            return

        if choice == "1":
            category_name = input("Enter category name: ")
            cursor.execute("INSERT INTO categories (name) VALUES (?)", (category_name,))
            conn.commit()
            conn.close()
            print(f"Category '{category_name}' added successfully!")
            return

def import_phrases_from_tsv(category_id, filename):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        with open(filename, 'r', encoding='utf-8') as file:
            reader = csv.reader(file, delimiter='\t')
            for row in reader:
                index, text = row
                cursor.execute("INSERT INTO phrases (text, category_id) VALUES (?, ?)", (text, category_id))
        conn.commit()
        print(f"Phrases from {filename} imported successfully!")
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found. Please check the file path and try again.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        conn.close()

def main():
    setup_database()

    while True:
        print("1. Add User")
        print("2. Delete User and Associated Data")
        print("3. List Users")
        print("4. Add Category")
        print("5. Import Phrases (from TSV)")
        print("6. Start Annotation")
        print("7. Analyze Data")
        print("8. Delete All Annotations")
        print("9. Exit")

        choice = input("Choose an option: ")

        if choice == "1":
            add_user()
        elif choice == "2":
            delete_user()
        elif choice == "3":
            list_users()
        elif choice == "4":
            add_category()
        elif choice == "5":
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            category_name = input("Enter category name to import phrases into: ")

            cursor.execute("SELECT id FROM categories WHERE name = ?", (category_name,))
            category = cursor.fetchone()

            if not category:
                print(f"Category '{category_name}' not found!")
            else:
                category_id = category[0]
                filename = input("Enter TSV filename (e.g., phrases.tsv): ")
                import_phrases_from_tsv(category_id, filename)

            conn.close()
        elif choice == "6":
            annotation_menu()
        elif choice == "7":
            analyze_data()
        elif choice == "8":
            delete_all_annotations()
        elif choice == "9":
            print("Goodbye!")
            break
        else:
            print("Invalid choice! Please try again.")

if __name__ == "__main__":
    main()