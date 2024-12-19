import sqlite3
import csv
from setup_database import setup_database
from PyInquirer import prompt
from annotate_system import annotation_menu

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

    for user in users:
        print(user)

def add_category():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    category_name = input("Enter category name: ")
    cursor.execute("INSERT INTO categories (name) VALUES (?)", (category_name,))
    conn.commit()
    conn.close()
    print(f"Category '{category_name}' added successfully!")

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
        print("2. List Users")
        print("3. Add Category")
        print("4. Import Phrases (from TSV)")
        print("5. Start Annotation")
        print("6. Exit")

        choice = input("Choose an option: ")
        if choice == "1":
            add_user()
        elif choice == "2":
            list_users()
        elif choice == "3":
            add_category()
        elif choice == "4":
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            category_name = input("Enter category name to import phrases into: ")
            cursor.execute("SELECT id FROM categories WHERE name = ?", (category_name,))
            category = cursor.fetchone()

            if not category:
                print(f"Category '{category_name}' not found!")
            else:
                category_id = category[0]
                filename = input("Enter TSV filename (e.g., culo.tsv): ")
                import_phrases_from_tsv(category_id, filename)

            conn.close()
        elif choice == "5":
            annotation_menu()
        elif choice == "6":
            break
        else:
            print("Invalid choice!")

if __name__ == "__main__":
    main()
