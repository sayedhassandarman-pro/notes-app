import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
import hashlib
from datetime import datetime


# ---------------- DATABASE ----------------
class Database:
    def __init__(self):
        self.conn = sqlite3.connect("app.db")
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT,
            created_at TEXT
        )
        """)
        self.conn.commit()

    def execute(self, query, params=()):
        self.cursor.execute(query, params)
        self.conn.commit()

    def fetch(self, query, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchall()


db = Database()


# ---------------- SECURITY ----------------
def hash_password(password):
    salt = "PRO_SALT_2026"
    return hashlib.sha256((password + salt).encode()).hexdigest()


# ---------------- APP ----------------
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Pro Notes App")
        self.root.geometry("700x650")
        self.root.config(bg="#1e1e1e")

        self.selected_id = None

        self.build_login()

    # ---------------- LOGIN UI ----------------
    def build_login(self):
        self.clear()

        tk.Label(self.root, text="LOGIN", font=("Arial", 20), fg="white", bg="#1e1e1e").pack(pady=20)

        self.username = tk.Entry(self.root, width=30)
        self.username.pack(pady=5)

        self.password = tk.Entry(self.root, width=30, show="*")
        self.password.pack(pady=5)

        tk.Button(self.root, text="Login", bg="blue", fg="white", command=self.login).pack(pady=5)
        tk.Button(self.root, text="Register", bg="purple", fg="white", command=self.register).pack(pady=5)

    def login(self):
        u = self.username.get()
        p = hash_password(self.password.get())

        user = db.fetch("SELECT * FROM users WHERE username=? AND password=?", (u, p))

        if user:
            self.build_dashboard()
        else:
            messagebox.showerror("Error", "Invalid login")

    def register(self):
        try:
            db.execute(
                "INSERT INTO users(username, password) VALUES (?, ?)",
                (self.username.get(), hash_password(self.password.get()))
            )
            messagebox.showinfo("OK", "User created")
        except:
            messagebox.showerror("Error", "User exists")

    # ---------------- DASHBOARD ----------------
    def build_dashboard(self):
        self.clear()

        tk.Label(self.root, text="NOTES DASHBOARD", font=("Arial", 18), fg="white", bg="#1e1e1e").pack(pady=10)

        self.note_text = tk.Text(self.root, height=5, width=60)
        self.note_text.pack(pady=10)

        self.search = tk.Entry(self.root, width=40)
        self.search.pack(pady=5)
        tk.Button(self.root, text="Search", command=self.load_notes).pack()

        self.tree = ttk.Treeview(self.root, columns=("ID", "Note", "Date"), show="headings")
        self.tree.heading("ID", text="ID")
        self.tree.heading("Note", text="Note")
        self.tree.heading("Date", text="Date")

        self.tree.column("ID", width=50)
        self.tree.column("Note", width=400)
        self.tree.column("Date", width=150)

        self.tree.pack(pady=10)

        self.tree.bind("<<TreeviewSelect>>", self.select_note)

        tk.Button(self.root, text="Save", bg="green", fg="white", command=self.save_note).pack(pady=2)
        tk.Button(self.root, text="Update", bg="orange", fg="white", command=self.update_note).pack(pady=2)
        tk.Button(self.root, text="Delete", bg="red", fg="white", command=self.delete_note).pack(pady=2)

        self.load_notes()

    # ---------------- NOTES ----------------
    def save_note(self):
        text = self.note_text.get("1.0", tk.END).strip()
        if not text:
            return

        db.execute(
            "INSERT INTO notes(content, created_at) VALUES (?, ?)",
            (text, datetime.now().strftime("%Y-%m-%d %H:%M"))
        )

        self.note_text.delete("1.0", tk.END)
        self.load_notes()

    def load_notes(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        keyword = self.search.get()

        if keyword:
            rows = db.fetch(
                "SELECT * FROM notes WHERE content LIKE ? ORDER BY id DESC",
                ('%' + keyword + '%',)
            )
        else:
            rows = db.fetch("SELECT * FROM notes ORDER BY id DESC")

        for r in rows:
            self.tree.insert("", tk.END, values=r)

    def select_note(self, event):
        selected = self.tree.focus()
        data = self.tree.item(selected, "values")

        if data and len(data) >= 3:
            self.selected_id = data[0]

            self.note_text.delete("1.0", tk.END)
            self.note_text.insert(tk.END, data[1])

    def update_note(self):
        if not self.selected_id:
            messagebox.showwarning("Select", "Please select a note first")
            return

        db.execute(
            "UPDATE notes SET content=? WHERE id=?",
            (self.note_text.get("1.0", tk.END).strip(), self.selected_id)
        )

        self.load_notes()

    def delete_note(self):
        if not self.selected_id:
            messagebox.showwarning("Select", "Please select a note first")
            return

        db.execute("DELETE FROM notes WHERE id=?", (self.selected_id,))

        self.note_text.delete("1.0", tk.END)
        self.selected_id = None

        self.load_notes()

    # ---------------- UTIL ----------------
    def clear(self):
        for w in self.root.winfo_children():
            w.destroy()


# ---------------- RUN ----------------
root = tk.Tk()
app = App(root)
root.mainloop()