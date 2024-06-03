import tkinter as tk
from tkinter import messagebox, ttk
import threading
import queue
from datetime import datetime
from decimal import Decimal
from customtkinter import CTkEntry, CTkButton, CTkRadioButton
from db_utils import fetch_user_id, fetch_investments, fetch_transactions, get_db_cursor, close_db
from login import LoginWindow


def add_transaction_thread(id_investissement, date, prix_achat, quantite, queue, email):
    thread = threading.Thread(target=_add_transaction,
                              args=(id_investissement, date, prix_achat, quantite, queue, email))
    thread.daemon = True
    thread.start()


def _add_transaction(id_investissement, date, prix_achat, quantite, queue, email):
    mydb, cursor = get_db_cursor()
    id_utilisateur = fetch_user_id(cursor, email)
    sql = "INSERT INTO `Transaction` (`id_utilisateur`, `id_investissement`, `date`, `prix_achat`, `quantite`) VALUES (%s, %s, %s, %s, %s)"
    values = (id_utilisateur, id_investissement, date, prix_achat, quantite)
    cursor.execute(sql, values)
    mydb.commit()
    queue.put(("success", "Transaction ajoutée avec succès"))
    close_db(mydb, cursor)


class InvestmentApp:
    def __init__(self, root, email):
        self.root = root
        self.email = email
        self.queue = queue.Queue()
        self.root.title("Gestion d'Investissements")
        self.create_widgets()
        self.load_investments_and_transactions()
        self.check_queue()

    def create_widgets(self):
        self.treeview = ttk.Treeview(self.root,
                                     columns=("Type", "Valeur", "Date", "Prix d'achat de l'action", "Quantité"),
                                     show="tree headings")
        self.treeview.pack(pady=10, fill=tk.BOTH, expand=True)

        self.logout_button = CTkButton(self.root, text="Déconnexion", command=self.logout, corner_radius=10)
        self.logout_button.pack(pady=10)

        self.add_transaction_button = CTkButton(self.root, text="Ajouter une transaction",
                                                command=self.open_add_transaction_window, corner_radius=10)
        self.add_transaction_button.pack(pady=10)

    def load_investments_and_transactions(self):
        mydb, cursor = get_db_cursor()
        investments = fetch_investments(cursor, self.email)
        self.treeview.delete(*self.treeview.get_children())
        for investment in investments:
            inv_item = self.treeview.insert("", "end", text=investment[2], values=(investment[3], investment[4]),
                                            tags=("investment",))
            transactions = fetch_transactions(cursor, self.email)
            for transaction in transactions:
                if transaction[1] == investment[0]:
                    self.treeview.insert(inv_item, "end", text="Transaction", values=(
                        "", "", transaction[3], str(transaction[4]) + "\u20AC", transaction[5]), tags=("transaction",))
        close_db(mydb, cursor)

    def logout(self):
        self.root.destroy()
        root = tk.Tk()
        app = LoginWindow(root)
        root.mainloop()

    def open_add_transaction_window(self):
        self.new_window = tk.Toplevel(self.root)
        self.new_window.title("Ajouter une transaction")

        self.investment_type = tk.StringVar(value="existing")

        CTkRadioButton(self.new_window, text="Nouvel investissement", variable=self.investment_type, value="new").pack(
            padx=20, pady=10)
        CTkRadioButton(self.new_window, text="Investissement existant", variable=self.investment_type,
                       value="existing").pack(padx=20, pady=10)

        self.nom_entreprise_label = tk.Label(self.new_window, text="Nom de l'entreprise:")
        self.nom_entreprise_label.pack(padx=20, pady=10)
        self.nom_entreprise_entry = CTkEntry(self.new_window, border_width=2)
        self.nom_entreprise_entry.pack(padx=20, pady=10)

        self.nom_entreprise_dropdown = ttk.Combobox(self.new_window)
        self.nom_entreprise_dropdown.pack(padx=20, pady=10)
        self.update_investment_dropdown()
        self.nom_entreprise_dropdown.pack_forget()

        self.symbole_boursier_label = tk.Label(self.new_window, text="Symbole boursier:")
        self.symbole_boursier_entry = CTkEntry(self.new_window, border_width=2)
        self.symbole_boursier_entry.pack_forget()

        self.secteur_activite_label = tk.Label(self.new_window, text="Secteur d'activité:")
        self.secteur_activite_entry = CTkEntry(self.new_window, border_width=2)
        self.secteur_activite_entry.pack_forget()

        tk.Label(self.new_window, text="Date (YYYY-MM-DD):").pack(padx=20, pady=10)
        self.date_entry = CTkEntry(self.new_window, border_width=2)
        self.date_entry.pack(padx=20, pady=10)

        tk.Label(self.new_window, text="Prix:").pack(padx=20, pady=10)
        self.prix_entry = CTkEntry(self.new_window, border_width=2)
        self.prix_entry.pack(padx=20, pady=10)

        tk.Label(self.new_window, text="Quantité:").pack(padx=20, pady=10)
        self.quantite_entry = CTkEntry(self.new_window, border_width=2)
        self.quantite_entry.pack(padx=20, pady=10)

        self.add_transaction_button = CTkButton(self.new_window, text="Ajouter", command=self.add_transaction,
                                                corner_radius=10)
        self.add_transaction_button.pack(padx=20, pady=10)

        self.investment_type.trace_add("write", self.update_form)
        self.update_form()

    def update_form(self, *args):
        if self.investment_type.get() == "new":
            self.nom_entreprise_label.config(text="Nom de l'entreprise:")
            self.nom_entreprise_entry.pack(padx=20, pady=10)
            self.nom_entreprise_dropdown.pack_forget()
            self.symbole_boursier_label.pack(padx=20, pady=10)
            self.symbole_boursier_entry.pack(padx=20, pady=10)
            self.secteur_activite_label.pack(padx=20, pady=10)
            self.secteur_activite_entry.pack(padx=20, pady=10)
        else:
            self.nom_entreprise_label.config(text="Choisir l'entreprise:")
            self.nom_entreprise_entry.pack_forget()
            self.nom_entreprise_dropdown.pack(padx=20, pady=10)
            self.symbole_boursier_label.pack_forget()
            self.symbole_boursier_entry.pack_forget()
            self.secteur_activite_label.pack_forget()
            self.secteur_activite_entry.pack_forget()
            self.update_investment_dropdown()

    def update_investment_dropdown(self):
        mydb, cursor = get_db_cursor()
        investments = fetch_investments(cursor, self.email)
        self.nom_entreprise_dropdown['values'] = [investment[2] for investment in investments]
        close_db(mydb, cursor)

    def add_transaction(self):
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
        else:
            id_investissement = result[0]

        prix_achat = Decimal(prix_achat)
        quantite = int(quantite)
        date = datetime.strptime(date, "%Y-%m-%d").date()

        add_transaction_thread(id_investissement, date, prix_achat, quantite, self.queue, self.email)
        self.new_window.destroy()
        self.load_investments_and_transactions()
        close_db(mydb, cursor)

    def check_queue(self):
        while not self.queue.empty():
            msg_type, msg = self.queue.get()
            if msg_type == "success":
                messagebox.showinfo("Succès", msg)
                self.new_window.destroy()
                self.load_investments_and_transactions()
        self.root.after(100, self.check_queue)
