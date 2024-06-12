import tkinter as tk
from tkinter import messagebox
import queue
import logging
from widgets import create_treeview, create_buttons, create_add_transaction_widgets, add_transaction
from utils import load_investments_and_transactions, delete_selected, confirm_delete, update_form
from login import LoginWindow
from db import get_db_cursor, close_db
from db_utils import fetch_investments


class InvestmentApp:
    def add_transaction(self):
        return add_transaction(self)

    def update_form(self, *args):
        return update_form(self, *args)

    def __init__(self, root, email):
        logging.debug("Initializing InvestmentApp")
        self.root = root
        self.email = email
        self.queue = queue.Queue()
        self.root.title("Gestion d'Investissements")
        self.treeview = create_treeview(self.root)
        create_buttons(self)
        self.load_investments_and_transactions()
        self.check_queue()

    def load_investments_and_transactions(self):
        load_investments_and_transactions(self)

    def open_add_transaction_window(self):
        create_add_transaction_widgets(self)
        self.investment_type.trace_add("write", self.update_form)
        self.update_form()

    def update_investment_dropdown(self):
        logging.debug("Updating investment dropdown")
        mydb, cursor = get_db_cursor()
        investments = fetch_investments(cursor, self.email)
        self.nom_entreprise_dropdown['values'] = [investment[2] for investment in investments]
        close_db(mydb, cursor)

    def check_queue(self):
        while not self.queue.empty():
            msg_type, msg = self.queue.get()
            if msg_type == "success":
                logging.debug("Transaction added successfully message received")
                if self.root.winfo_exists():
                    messagebox.showinfo("Succès", msg)
                    self.new_window.destroy()
                    self.root.after(0, self.load_investments_and_transactions)
            elif msg_type == "error":
                logging.error(msg)
                messagebox.showerror("Erreur", msg)
        if self.root.winfo_exists():
            self.root.after(100, self.check_queue)

    def confirm_delete(self):
        confirm_delete(self)

    def delete_selected(self, selected_items):
        delete_selected(self, selected_items)

    def logout(self):
        logging.debug("Logging out")
        self.root.destroy()
        root = tk.Tk()
        app = LoginWindow(root)
        root.mainloop()

    def edit_selected(self):
        selected_items = self.treeview.selection()

        if not selected_items:
            messagebox.showwarning("Modification", "Aucun élément sélectionné pour la modification.")
            return

        for item in selected_items:
            item_tags = self.treeview.item(item, "tags")
            values = self.treeview.item(item, "values")
            if "investment" in item_tags:
                symbole_boursier = values[0]
                logging.debug(f"Symbole boursier Entreprise sélectionné: {symbole_boursier}")
                open_edit_investment_form(self, symbole_boursier)
            elif "transaction" in item_tags:
                id_transaction = values[0]
                logging.debug(f"ID Transaction sélectionné: {id_transaction}")
                open_edit_transaction_form(self, id_transaction)


def open_edit_investment_form(app, symbole_boursier):
    logging.debug(f"Tentative de modification de l'investissement avec nom: {symbole_boursier}")
    mydb, cursor = get_db_cursor()
    cursor.execute("SELECT * FROM Investissement WHERE symbole_boursier = %s", (symbole_boursier,))
    investment = cursor.fetchone()
    close_db(mydb, cursor)

    if investment is None:
        logging.error(f"Investissement avec nom {symbole_boursier} non trouvé.")
        messagebox.showerror("Erreur", "Investissement non trouvé.")
        return

    logging.debug(f"Investissement trouvé: {investment}")

    # Créer une nouvelle fenêtre pour la modification
    edit_window = tk.Toplevel(app.root)
    edit_window.title("Modifier Investissement")

    # Créer et placer les widgets d'entrée pour la modification
    tk.Label(edit_window, text="Nom Entreprise:").grid(row=0, column=0, padx=20, pady=10)
    app.nom_entreprise_entry = tk.Entry(edit_window)
    app.nom_entreprise_entry.grid(row=0, column=1, padx=20, pady=10)
    app.nom_entreprise_entry.insert(0, investment[2])

    tk.Label(edit_window, text="Symbole Boursier:").grid(row=1, column=0, padx=20, pady=10)
    app.symbole_boursier_entry = tk.Entry(edit_window)
    app.symbole_boursier_entry.grid(row=1, column=1, padx=20, pady=10)
    app.symbole_boursier_entry.insert(0, investment[3])

    tk.Label(edit_window, text="Secteur Activité:").grid(row=2, column=0, padx=20, pady=10)
    app.secteur_activite_entry = tk.Entry(edit_window)
    app.secteur_activite_entry.grid(row=2, column=1, padx=20, pady=10)
    app.secteur_activite_entry.insert(0, investment[4])

    tk.Button(edit_window, text="Sauvegarder les modifications", command=lambda: save_changes(app, id_investment=investment[0])).grid(row=3, columnspan=2, pady=20)


def open_edit_transaction_form(app, id_transaction):
    logging.debug(f"Tentative de modification de la transaction avec ID: {id_transaction}")
    mydb, cursor = get_db_cursor()
    cursor.execute("SELECT * FROM Transaction WHERE id_transaction = %s", (id_transaction,))
    transaction = cursor.fetchone()
    close_db(mydb, cursor)

    if transaction is None:
        logging.error(f"Transaction avec ID {id_transaction} non trouvée.")
        messagebox.showerror("Erreur", "Transaction non trouvée.")
        return

    logging.debug(f"Transaction trouvée: {transaction}")

    # Créer une nouvelle fenêtre pour la modification
    edit_window = tk.Toplevel(app.root)
    edit_window.title("Modifier Transaction")

    # Créer et placer les widgets d'entrée pour la modification
    tk.Label(edit_window, text="Date:").grid(row=0, column=0, padx=20, pady=10)
    app.date_entry = tk.Entry(edit_window)
    app.date_entry.grid(row=0, column=1, padx=20, pady=10)
    app.date_entry.insert(0, transaction[3])

    tk.Label(edit_window, text="Prix:").grid(row=1, column=0, padx=20, pady=10)
    app.prix_entry = tk.Entry(edit_window)
    app.prix_entry.grid(row=1, column=1, padx=20, pady=10)
    app.prix_entry.insert(0, transaction[4])

    tk.Label(edit_window, text="Quantité:").grid(row=2, column=0, padx=20, pady=10)
    app.quantite_entry = tk.Entry(edit_window)
    app.quantite_entry.grid(row=2, column=1, padx=20, pady=10)
    app.quantite_entry.insert(0, transaction[5])

    # Bouton pour sauvegarder les changements
    save_button = tk.Button(edit_window, text="Sauvegarder les modifications",
                            command=lambda: save_changes(app, id_transaction=id_transaction))
    save_button.grid(row=3, columnspan=2, pady=20)


def save_changes(app, id_investment=None, id_transaction=None):
    mydb, cursor = get_db_cursor()
    if id_investment:
        cursor.execute(
            "UPDATE Investissement SET nom_entreprise = %s, symbole_boursier = %s, secteur_activite = %s WHERE id_investissement = %s",
            (app.nom_entreprise_entry.get(), app.symbole_boursier_entry.get(), app.secteur_activite_entry.get(),
             id_investment))
    elif id_transaction:
        cursor.execute("UPDATE Transaction SET date = %s, prix_achat = %s, quantite = %s WHERE id_transaction = %s",
                       (app.date_entry.get(), app.prix_entry.get(), app.quantite_entry.get(), id_transaction))
    mydb.commit()
    close_db(mydb, cursor)
    app.load_investments_and_transactions()
    messagebox.showinfo("Succès", "Les modifications ont été enregistrées avec succès.")
