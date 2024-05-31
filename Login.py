import tkinter as tk
from tkinter import messagebox
from db import get_db_cursor, close_db, Error
import logging

class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Connexion")
        self.create_widgets()
        self.root.bind('<Return>', self.login)

    def create_widgets(self):
        tk.Label(self.root, text="Email").grid(row=0, column=0)
        self.email_entry = tk.Entry(self.root)
        self.email_entry.grid(row=0, column=1)

        tk.Label(self.root, text="Mot de passe").grid(row=1, column=0)
        self.password_entry = tk.Entry(self.root, show="*")
        self.password_entry.grid(row=1, column=1)

        tk.Button(self.root, text="Se connecter", command=self.login).grid(row=2, column=0, columnspan=2)

    def login(self, event=None):
        email = self.email_entry.get()
        password = self.password_entry.get()
        if self.check_login(email, password):
            self.root.destroy()
            from main import run_main
            run_main(email)
        else:
            messagebox.showerror("Erreur", "Email ou mot de passe incorrect")

    def check_login(self, email, password):
        mydb, cursor = get_db_cursor()
        if mydb is None or cursor is None:
            return False
        try:
            cursor.execute("SELECT * FROM utilisateur WHERE email = %s AND password = %s", (email, password))
            return cursor.fetchone() is not None
        except Error as e:
            logging.error(f"Erreur lors de la vérification des identifiants: {e}")
            return False
        finally:
            close_db(mydb, cursor)

if __name__ == "__main__":
    root = tk.Tk()
    app = LoginWindow(root)
    root.mainloop()
