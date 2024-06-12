from tkinter import ttk, messagebox
import tkinter as tk
from customtkinter import CTkButton, CTkRadioButton, CTkEntry
import logging
from db import get_db_cursor, close_db
from db_utils import fetch_user_id
from transaction_threads import add_transaction_thread
import decimal
import datetime


def create_treeview(root):
    treeview = ttk.Treeview(root,
                            columns=(
                                "Type", "Valeur", "Date", "Prix d'achat de l'action", "Quantité", "Total",
                                "Gain/Perte"),
                            show="tree headings")

    treeview.pack(pady=10, fill=tk.BOTH, expand=True)
    style = ttk.Style()
    style.configure("Treeview.Heading", font=('Helvetica', 10, 'bold'), foreground="black", background="white")
    treeview.heading("#0", text="Nom / Transaction")
    treeview.column("#0", width=200, anchor='center')
    treeview.heading("Type", text="Symbole")
    treeview.column("Type", width=100, anchor='center')
    treeview.heading("Valeur", text="Secteur")
    treeview.column("Valeur", width=100, anchor='center')
    treeview.heading("Date", text="Date")
    treeview.column("Date", width=100, anchor='center')
    treeview.heading("Prix d'achat de l'action", text="Prix d'achat de l'action")
    treeview.column("Prix d'achat de l'action", width=150, anchor='center')
    treeview.heading("Quantité", text="Quantité")
    treeview.column("Quantité", width=100, anchor='center')
    treeview.heading("Total", text="Total")
    treeview.column("Total", width=100, anchor='center')
    treeview.heading("Gain/Perte", text="Gain/Perte")
    treeview.column("Gain/Perte", width=100, anchor='center')
    treeview.tag_configure("gain", foreground="green")
    treeview.tag_configure("perte", foreground="red")
    return treeview


def create_buttons(app):
    app.logout_button = CTkButton(app.root, text="Déconnexion", command=app.logout, corner_radius=10, fg_color="red")
    app.logout_button.pack(pady=10)
    app.add_transaction_button = CTkButton(app.root, text="Ajouter une transaction",
                                           command=app.open_add_transaction_window, corner_radius=10, fg_color="green")
    app.add_transaction_button.pack(pady=10)
    app.refresh_button = CTkButton(app.root, text="Rafraîchir", command=app.load_investments_and_transactions,
                                   corner_radius=10)
    app.refresh_button.pack(side='top', pady=10)
    app.delete_button = CTkButton(app.root, text="Supprimer", command=app.confirm_delete, corner_radius=10,
                                  fg_color="red")
    app.delete_button.pack(pady=10)
    # Ajout du bouton Modifier
    app.edit_button = CTkButton(app.root, text="Modifier", command=app.edit_selected, corner_radius=10, fg_color="blue")
    app.edit_button.pack(pady=10)


def create_add_transaction_widgets(app):
    app.new_window = tk.Toplevel(app.root)
    app.new_window.title("Ajouter une transaction")

    app.investment_type = tk.StringVar(value="existing")

    CTkRadioButton(app.new_window, text="Nouvel investissement", variable=app.investment_type, value="new").grid(
        row=0, column=0, padx=20, pady=10)
    CTkRadioButton(app.new_window, text="Investissement existant", variable=app.investment_type,
                   value="existing").grid(row=1, column=0, padx=20, pady=10)

    app.nom_entreprise_label = tk.Label(app.new_window, text="Nom de l'entreprise:", bg="#f0f0f0",
                                        font=('Helvetica', 10, 'bold'))
    app.nom_entreprise_label.grid(row=2, column=0, padx=20, pady=10)
    app.nom_entreprise_entry = CTkEntry(app.new_window, border_width=2)
    app.nom_entreprise_entry.grid(row=3, column=0, padx=20, pady=10)

    app.nom_entreprise_dropdown = ttk.Combobox(app.new_window)
    app.nom_entreprise_dropdown.grid(row=4, column=0, padx=20, pady=10)
    app.nom_entreprise_dropdown.grid_remove()

    app.symbole_boursier_label = tk.Label(app.new_window, text="Symbole boursier:", bg="#f0f0f0",
                                          font=('Helvetica', 10, 'bold'))
    app.symbole_boursier_label.grid(row=5, column=0, padx=20, pady=10)
    app.symbole_boursier_entry = CTkEntry(app.new_window, border_width=2)
    app.symbole_boursier_entry.grid(row=6, column=0, padx=20, pady=10)

    app.secteur_activite_label = tk.Label(app.new_window, text="Secteur d'activité:", bg="#f0f0f0",
                                          font=('Helvetica', 10, 'bold'))
    app.secteur_activite_label.grid(row=7, column=0, padx=20, pady=10)
    app.secteur_activite_entry = CTkEntry(app.new_window, border_width=2)
    app.secteur_activite_entry.grid(row=8, column=0, padx=20, pady=10)

    app.date_label = tk.Label(app.new_window, text="Date au format DD/MM/YYYY:", bg="#f0f0f0",
                              font=('Helvetica', 10, 'bold'))
    app.date_label.grid(row=9, column=0, padx=20, pady=10)
    app.date_entry = CTkEntry(app.new_window, border_width=2)
    app.date_entry.grid(row=10, column=0, padx=20, pady=10)

    app.prix_label = tk.Label(app.new_window, text="Prix d'achat:", bg="#f0f0f0", font=('Helvetica', 10, 'bold'))
    app.prix_label.grid(row=11, column=0, padx=20, pady=10)
    app.prix_entry = CTkEntry(app.new_window, border_width=2)
    app.prix_entry.grid(row=12, column=0, padx=20, pady=10)

    app.quantite_label = tk.Label(app.new_window, text="Quantité:", bg="#f0f0f0", font=('Helvetica', 10, 'bold'))
    app.quantite_label.grid(row=13, column=0, padx=20, pady=10)
    app.quantite_entry = CTkEntry(app.new_window, border_width=2)
    app.quantite_entry.grid(row=14, column=0, padx=20, pady=10)

    app.confirm_button = CTkButton(app.new_window, text="Confirmer", command=app.add_transaction, corner_radius=10,
                                   fg_color="blue")
    app.confirm_button.grid(row=15, column=0, padx=20, pady=10)

    app.investment_type.trace_add("write", app.update_form)
    app.update_form()


def add_transaction(self):
    try:
        logging.debug("Adding transaction")
        mydb, cursor = get_db_cursor()
        if self.investment_type.get() == "new":
            nom_entreprise = self.nom_entreprise_entry.get()
            symbole_boursier = self.symbole_boursier_entry.get()
            secteur_activite = self.secteur_activite_entry.get()
        else:
            nom_entreprise = self.nom_entreprise_dropdown.get()
            symbole_boursier = ""
            secteur_activite = ""

        date = self.date_entry.get()
        prix_achat = self.prix_entry.get()
        quantite = self.quantite_entry.get()

        if not nom_entreprise or not date or not prix_achat or not quantite:
            logging.warning("Tous les champs doivent être remplis.")
            messagebox.showerror("Erreur", "Tous les champs doivent être remplis.")
            return

        id_utilisateur = fetch_user_id(cursor, self.email)
        cursor.execute(
            "SELECT id_investissement FROM Investissement WHERE id_utilisateur = %s AND nom_entreprise = %s",
            (id_utilisateur, nom_entreprise))
        result = cursor.fetchone()
        if result is None:
            sql = "INSERT INTO `Investissement` (`id_utilisateur`, `nom_entreprise`, `symbole_boursier`, `secteur_activite`) VALUES (%s, %s, %s, %s)"
            values = (id_utilisateur, nom_entreprise, symbole_boursier, secteur_activite)
            cursor.execute(sql, values)
            mydb.commit()
            id_investissement = cursor.lastrowid
            logging.debug(f"New investment added: {values}")
        else:
            id_investissement = result[0]
            logging.debug(f"Existing investment found: {id_investissement}")

        prix_achat = decimal.Decimal(self.prix_entry.get())
        quantite = int(quantite)
        date = datetime.datetime.strptime(date, "%d/%m/%Y").date()

        add_transaction_thread(id_investissement, date, prix_achat, quantite, self.queue, self.email)
        self.new_window.destroy()
        self.load_investments_and_transactions()
        close_db(mydb, cursor)
    except Exception as e:
        logging.error(f"An error occurred while adding the transaction: {e}")
        messagebox.showerror("Erreur", f"Une erreur s'est produite lors de l'ajout de la transaction : {e}")