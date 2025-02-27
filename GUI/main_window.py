import sys, os

# Aggiunge la cartella padre al PYTHONPATH
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
# print("sys.path:", sys.path)  # Rimuovere dopo il debug

import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import sqlite3
import random

# Imposta il percorso del database nella cartella padre
DB_NAME = os.path.join(parent_dir, "annotation_system.db")


#########################################
# Finestra per Aggiungere un Nuovo Utente #
#########################################
def add_user_window(parent):
    win = tk.Toplevel(parent)
    win.title("Add User")
    win.geometry("400x350")
    win.configure(bg="#f0f8ff")

    label_font = ("Helvetica", 12)
    entry_font = ("Helvetica", 12)

    tk.Label(win, text="Username:", font=label_font, bg="#f0f8ff").pack(pady=5)
    username_entry = tk.Entry(win, font=entry_font)
    username_entry.pack(pady=5)

    tk.Label(win, text="Age:", font=label_font, bg="#f0f8ff").pack(pady=5)
    age_entry = tk.Entry(win, font=entry_font)
    age_entry.pack(pady=5)

    tk.Label(win, text="Gender (Male/Female/Non-Binary/Other):", font=label_font, bg="#f0f8ff").pack(pady=5)
    gender_entry = tk.Entry(win, font=entry_font)
    gender_entry.pack(pady=5)

    tk.Label(win, text="Education Level:", font=label_font, bg="#f0f8ff").pack(pady=5)
    education_options = [
        "Elementary School",
        "Middle School",
        "High School Diploma",
        "Bachelor's Degree",
        "Master's Degree",
        "PhD"
    ]
    education_var = tk.StringVar(win)
    education_combo = ttk.Combobox(win, textvariable=education_var, state="readonly", values=education_options,
                                   font=entry_font)
    education_combo.pack(pady=5)
    education_combo.current(0)

    def submit_user():
        username = username_entry.get().strip()
        age_str = age_entry.get().strip()
        gender = gender_entry.get().strip()
        education = education_var.get().strip()

        if not username or not age_str or not gender or not education:
            messagebox.showerror("Error", "Please fill in all fields.")
            return

        try:
            age = int(age_str)
        except ValueError:
            messagebox.showerror("Error", "Age must be a valid integer.")
            return

        try:
            with sqlite3.connect(DB_NAME) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (username, age, gender, education) VALUES (?, ?, ?, ?)",
                    (username, age, gender, education)
                )
                conn.commit()
            messagebox.showinfo("Success", f"User '{username}' added successfully!")
            win.destroy()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", str(e))

    tk.Button(win, text="Submit", command=submit_user, font=label_font, bg="#add8e6").pack(pady=20)

    win.transient(parent)
    win.grab_set()
    parent.wait_window(win)


#########################################
# Finestra per Annotare una Categoria (votazione a gruppi, random e ripetizioni) #
#########################################
def annotate_category_window(parent):
    win = tk.Toplevel(parent)
    win.title("Annotate Category")
    win.geometry("900x650")
    win.configure(bg="#f0f8ff")

    label_font = ("Helvetica", 12)

    tk.Label(win, text="Enter your username:", font=label_font, bg="#f0f8ff").pack(pady=5)
    user_entry = tk.Entry(win, font=label_font)
    user_entry.pack(pady=5)

    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM categories")
            categories = cursor.fetchall()
    except sqlite3.Error as e:
        messagebox.showerror("Database Error", str(e))
        win.destroy()
        return

    if not categories:
        messagebox.showinfo("Info", "No categories available. Please add a category first.")
        win.destroy()
        return

    tk.Label(win, text="Select Category:", font=label_font, bg="#f0f8ff").pack(pady=5)
    category_var = tk.StringVar(win)
    category_options = [f"{cat[0]}: {cat[1]}" for cat in categories]
    category_combo = ttk.Combobox(win, textvariable=category_var, state="readonly", values=category_options,
                                  font=label_font)
    category_combo.pack(pady=5)
    category_combo.current(0)

    tk.Label(win, text="Number of phrases per group:", font=label_font, bg="#f0f8ff").pack(pady=5)
    group_size_entry = tk.Entry(win, font=label_font)
    group_size_entry.pack(pady=5)
    group_size_entry.insert(0, "5")

    tk.Label(win, text="Number of rounds:", font=label_font, bg="#f0f8ff").pack(pady=5)
    rounds_entry = tk.Entry(win, font=label_font)
    rounds_entry.pack(pady=5)
    rounds_entry.insert(0, "1")

    phrases_frame = tk.Frame(win, bg="#f0f8ff")
    phrases_frame.pack(pady=10, fill="both", expand=True)

    progress_label = tk.Label(win, text="", font=("Helvetica", 10), bg="#f0f8ff")
    progress_label.pack(pady=5)

    phrases = []  # Lista di tuple (phrase_id, text)
    groups = []  # Lista dei gruppi (lista di frasi)
    group_vote_vars = []  # Lista parallela a 'groups': per ogni gruppo, una lista di (phrase_id, StringVar)
    current_group_index = [0]
    rounds_total = [1]
    rounds_completed = [0]

    btn_load = tk.Button(win, text="Load Phrases", command=lambda: load_phrases(), font=label_font, bg="#add8e6")
    btn_load.pack(pady=5)

    nav_frame = tk.Frame(win, bg="#f0f8ff")
    btn_prev = tk.Button(nav_frame, text="Previous Group", command=lambda: previous_group(), font=label_font,
                         bg="#add8e6")
    btn_next = tk.Button(nav_frame, text="Next Group", command=lambda: next_group(), font=label_font, bg="#add8e6")
    btn_prev.pack(side="left", padx=10)
    btn_next.pack(side="left", padx=10)

    btn_submit_round = tk.Button(win, text="Submit Round", command=lambda: submit_round(), font=label_font,
                                 bg="#add8e6")

    def init_round():
        selected = category_var.get()
        try:
            cat_id = int(selected.split(":")[0])
        except ValueError:
            messagebox.showerror("Error", "Invalid category selection.")
            return
        try:
            with sqlite3.connect(DB_NAME) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, text FROM phrases WHERE category_id = ?", (cat_id,))
                all_phrases = cursor.fetchall()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", str(e))
            win.destroy()
            return
        if not all_phrases:
            messagebox.showinfo("Info", "No phrases found in this category.")
            win.destroy()
            return
        random.shuffle(all_phrases)
        try:
            group_size = int(group_size_entry.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Group size must be a valid integer.")
            return
        groups.clear()
        for i in range(0, len(all_phrases), group_size):
            groups.append(all_phrases[i:i + group_size])
        group_vote_vars.clear()
        for grp in groups:
            vars_grp = []
            for phrase in grp:
                var = tk.StringVar(win, value="no_vote")
                vars_grp.append((phrase[0], var))
            group_vote_vars.append(vars_grp)
        current_group_index[0] = 0
        load_group(0)

    def load_phrases():
        try:
            rounds_total[0] = int(rounds_entry.get().strip())
        except ValueError:
            messagebox.showerror("Error", "Number of rounds must be a valid integer.")
            return
        init_round()
        user_entry.config(state="disabled")
        group_size_entry.config(state="disabled")
        rounds_entry.config(state="disabled")
        btn_load.pack_forget()
        nav_frame.pack(pady=5)
        btn_submit_round.pack(pady=5)
        load_group(current_group_index[0])

    def load_group(index):
        for widget in phrases_frame.winfo_children():
            widget.destroy()
        if index < 0 or index >= len(groups):
            return
        current_grp = groups[index]
        current_vars = group_vote_vars[index]
        for j, (phrase_id, text) in enumerate(current_grp):
            row = tk.Frame(phrases_frame, bg="#f0f8ff")
            row.grid(row=j, column=0, sticky="w", pady=2)
            label = tk.Label(row, text=text, wraplength=500, justify="left", bg="#f0f8ff")
            label.grid(row=0, column=0, sticky="w")
            rb_frame = tk.Frame(row, bg="#f0f8ff")
            rb_frame.grid(row=0, column=1, padx=10)
            rb_offensive = tk.Radiobutton(rb_frame, text="Offensive", variable=current_vars[j][1], value="offensive",
                                          bg="#f0f8ff")
            rb_not_offensive = tk.Radiobutton(rb_frame, text="Not Offensive", variable=current_vars[j][1],
                                              value="not_offensive", bg="#f0f8ff")
            rb_skip = tk.Radiobutton(rb_frame, text="Skip", variable=current_vars[j][1], value="no_vote", bg="#f0f8ff")
            rb_offensive.pack(side="left", padx=5)
            rb_not_offensive.pack(side="left", padx=5)
            rb_skip.pack(side="left", padx=5)
        progress_label.config(
            text=f"Group {index + 1} of {len(groups)} (Round {rounds_completed[0] + 1} of {rounds_total[0]})")

    def next_group():
        if current_group_index[0] < len(groups) - 1:
            current_group_index[0] += 1
            load_group(current_group_index[0])
        else:
            messagebox.showinfo("End of Round", "You have reached the last group of this round.")

    def previous_group():
        if current_group_index[0] > 0:
            current_group_index[0] -= 1
            load_group(current_group_index[0])
        else:
            messagebox.showinfo("Info", "This is the first group.")

    def submit_round():
        username = user_entry.get().strip()
        if not username:
            messagebox.showerror("Error", "Please enter your username.")
            return
        try:
            with sqlite3.connect(DB_NAME) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
                result = cursor.fetchone()
                if not result:
                    messagebox.showerror("Error", f"User '{username}' not found.")
                    return
                user_id = result[0]
                for grp_vars in group_vote_vars:
                    for phrase_id, var in grp_vars:
                        vote = var.get()
                        if vote == "no_vote":
                            continue
                        elif vote == "offensive":
                            best_flag = False
                            worst_flag = True
                        elif vote == "not_offensive":
                            best_flag = True
                            worst_flag = False
                        else:
                            continue
                        cursor.execute("""
                            INSERT INTO annotations (user_id, phrase_id, best, worst)
                            VALUES (?, ?, ?, ?)
                        """, (user_id, phrase_id, best_flag, worst_flag))
                conn.commit()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", str(e))
            return

        rounds_completed[0] += 1
        if rounds_completed[0] < rounds_total[0]:
            messagebox.showinfo("Round Submitted",
                                f"Round {rounds_completed[0]} submitted successfully! Starting next round.")
            init_round()
        else:
            messagebox.showinfo("Success", "All rounds submitted successfully!")
            win.destroy()

    btn_submit_round.config(command=submit_round)

    win.transient(parent)
    win.grab_set()
    parent.wait_window(win)


#########################################
# Finestra Principale (Main Window)      #
#########################################
def main_window():
    style = ttk.Style()
    style.theme_use('clam')
    root = tk.Tk()
    root.title("Annotation System")
    root.geometry("600x400")
    root.configure(bg="#e6f2ff")

    btn_font = ("Helvetica", 12)

    btn_add_user = tk.Button(root, text="Add User", width=25, command=lambda: add_user_window(root), font=btn_font,
                             bg="#add8e6")
    btn_start_annotation = tk.Button(root, text="Start Annotation", width=25,
                                     command=lambda: annotate_category_window(root), font=btn_font, bg="#add8e6")
    btn_exit = tk.Button(root, text="Exit", width=25, command=root.quit, font=btn_font, bg="#add8e6")

    btn_add_user.pack(pady=10)
    btn_start_annotation.pack(pady=10)
    btn_exit.pack(pady=10)

    root.mainloop()


if __name__ == "__main__":
    main_window()
