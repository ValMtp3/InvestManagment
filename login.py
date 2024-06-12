import tkinter as tk
from tkinter import messagebox
from customtkinter import CTkEntry, CTkButton
from db_utils import get_db_cursor, close_db
import re
import bcrypt

class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Connexion")
        self.create_widgets()
        self.root.bind('<Return>', self.login)

    def create_widgets(self):
        tk.Label(self.root, text="Email", font=('Helvetica', 12, 'bold')).grid(row=0, column=0, padx=10, pady=10)
        self.email_entry = CTkEntry(self.root, border_width=2)
        self.email_entry.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(self.root, text="Mot de passe", font=('Helvetica', 12, 'bold')).grid(row=1, column=0, padx=10, pady=10)
        self.password_entry = CTkEntry(self.root, show="*", border_width=2)
        self.password_entry.grid(row=1, column=1, padx=10, pady=10)

        self.login_button = CTkButton(self.root, text="Se connecter", command=self.login, corner_radius=10)
        self.login_button.grid(row=2, column=0, columnspan=2, pady=10)

        self.create_account_button = CTkButton(self.root, text="Créer un compte", command=self.create_account, corner_radius=10)
        self.create_account_button.grid(row=3, column=0, columnspan=2, pady=10)

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
            cursor.execute("SELECT password FROM utilisateur WHERE email = %s", (email,))
            result = cursor.fetchone()
            if result and bcrypt.checkpw(password.encode('utf-8'), result[0].encode('utf-8')):
                return True
            else:
                return False
        except Exception as e:
            return False
        finally:
            close_db(mydb, cursor)

    def is_valid_email(self, email):
        email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return re.match(email_regex, email) is not None

    def create_account(self):
        email = self.email_entry.get()
        password = self.password_entry.get()

        if email == "" or password == "":
            messagebox.showwarning("Attention", "Veuillez remplir tous les champs")
            return

        if not self.is_valid_email(email):
            messagebox.showwarning("Attention", "Adresse email invalide")
            return

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        mydb, cursor = get_db_cursor()
        if mydb is None or cursor is None:
            messagebox.showerror("Erreur", "Erreur de connexion à la base de données")
            return

        try:
            cursor.execute("INSERT INTO utilisateur (email, password) VALUES (%s, %s)", (email, hashed_password))
            mydb.commit()
            messagebox.showinfo("Succès", "Compte créé avec succès")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la création du compte : {e}")
        finally:
            close_db(mydb, cursor)