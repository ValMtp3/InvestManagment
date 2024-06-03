import tkinter as tk
from tkinter import messagebox
from db import get_db_cursor, close_db, Error
import logging
from customtkinter import CTkEntry, CTkButton


class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Connexion")
        self.create_widgets()
        self.root.bind('<Return>', self.login)  # Lie la touche Entrée à la fonction de connexion

    def create_widgets(self):
        # Crée les widgets pour l'email et le mot de passe
        tk.Label(self.root, text="Email").grid(row=0, column=0)
        self.email_entry = CTkEntry(self.root, border_width=2)
        self.email_entry.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(self.root, text="Mot de passe").grid(row=1, column=0)
        self.password_entry = CTkEntry(self.root, show="*", border_width=2)
        self.password_entry.grid(row=1, column=1, padx=10, pady=10)

        # Crée le bouton de connexion
        self.login_button = CTkButton(self.root, text="Se connecter", command=self.login, corner_radius=10)
        self.login_button.grid(row=2, column=0, columnspan=2, pady=10)

    def login(self, event=None):
        # Récupère l'email et le mot de passe
        email = self.email_entry.get()
        password = self.password_entry.get()

        # Vérifie les identifiants de connexion
        if self.check_login(email, password):
            # Si les identifiants sont corrects, détruit la fenêtre de connexion et lance l'application principale
            self.root.destroy()
            from main import run_main
            run_main(email)
        else:
            # Si les identifiants sont incorrects, affiche un message d'erreur
            messagebox.showerror("Erreur", "Email ou mot de passe incorrect")

    def check_login(self, email, password):
        # Récupère la connexion à la base de données
        mydb, cursor = get_db_cursor()

        # Si la connexion à la base de données a échoué, retourne False
        if mydb is None or cursor is None:
            return False

        try:
            # Exécute la requête SQL pour vérifier les identifiants
            cursor.execute("SELECT * FROM utilisateur WHERE email = %s AND password = %s", (email, password))

            # Retourne True si un utilisateur correspond aux identifiants, False sinon
            return cursor.fetchone() is not None
        except Error as e:
            logging.error(f"Erreur lors de la vérification des identifiants: {e}")
            return False
        finally:
            # Ferme la connexion à la base de données
            close_db(mydb, cursor)
