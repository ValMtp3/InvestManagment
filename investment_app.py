import tkinter as tk
from tkinter import messagebox, ttk
import threading
import queue
from datetime import datetime
from decimal import Decimal
from customtkinter import CTkEntry, CTkButton, CTkRadioButton
from db_utils import fetch_user_id, fetch_investments, fetch_transactions, get_db_cursor, close_db
from login import LoginWindow
import logging

# Configurer le logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def add_transaction_thread(id_investissement, date, prix_achat, quantite, queue, email):
    logging.debug(f"Starting thread to add transaction: {id_investissement}, {date}, {prix_achat}, {quantite}, {email}")
    thread = threading.Thread(target=_add_transaction,
                              args=(id_investissement, date, prix_achat, quantite, queue, email))
    thread.daemon = True
    thread.start()


def _add_transaction(id_investissement, date, prix_achat, quantite, queue, email):
    try:
        mydb, cursor = get_db_cursor()
        id_utilisateur = fetch_user_id(cursor, email)
        sql = "INSERT INTO `Transaction` (`id_utilisateur`, `id_investissement`, `date`, `prix_achat`, `quantite`) VALUES (%s, %s, %s, %s, %s)"
        values = (id_utilisateur, id_investissement, date, prix_achat, quantite)
        cursor.execute(sql, values)
        mydb.commit()
        queue.put(("success", "Transaction ajoutée avec succès"))
        logging.debug(f"Transaction added successfully: {values}")
        close_db(mydb, cursor)
    except Exception as e:
        logging.error(f"An error occurred in the thread: {e}")
        print(f"Une erreur s'est produite dans le thread : {e}")


class InvestmentApp:
    def __init__(self, root, email):
        logging.debug("Initializing InvestmentApp")
        self.root = root
        self.email = email
        self.queue = queue.Queue()
        self.root.title("Gestion d'Investissements")
        self.create_widgets()
        self.load_investments_and_transactions()
        self.check_queue()

    def create_widgets(self):
        logging.debug("Creating widgets")
        self.treeview = ttk.Treeview(self.root,
                                     columns=("Type", "Valeur", "Date", "Prix d'achat de l'action", "Quantité", "Total", "Gain/Perte"),
                                     show="tree headings")

        self.treeview.pack(pady=10, fill=tk.BOTH, expand=True)

        # Style for treeview headings
        style = ttk.Style()
        style.configure("Treeview.Heading", font=('Helvetica', 10, 'bold'), foreground="black", background="white")

        self.treeview.heading("#0", text="Nom / Transaction")
        self.treeview.column("#0", width=200, anchor='center')
        self.treeview.heading("Type", text="Symbole")
        self.treeview.column("Type", width=100, anchor='center')
        self.treeview.heading("Valeur", text="Secteur")
        self.treeview.column("Valeur", width=100, anchor='center')
        self.treeview.heading("Date", text="Date")
        self.treeview.column("Date", width=100, anchor='center')
        self.treeview.heading("Prix d'achat de l'action", text="Prix d'achat de l'action")
        self.treeview.column("Prix d'achat de l'action", width=150, anchor='center')
        self.treeview.heading("Quantité", text="Quantité")
        self.treeview.column("Quantité", width=100, anchor='center')
        self.treeview.heading("Total", text="Total")
        self.treeview.column("Total", width=100, anchor='center')
        self.treeview.heading("Gain/Perte", text="Gain/Perte")
        self.treeview.column("Gain/Perte", width=100, anchor='center')
        self.treeview.tag_configure("gain", foreground="green")
        self.treeview.tag_configure("perte", foreground="red")

        self.logout_button = CTkButton(self.root, text="Déconnexion", command=self.logout, corner_radius=10, fg_color="red")
        self.logout_button.pack(pady=10)

        self.add_transaction_button = CTkButton(self.root, text="Ajouter une transaction",
                                                command=self.open_add_transaction_window, corner_radius=10, fg_color="green")
        self.add_transaction_button.pack(pady=10)

    def load_investments_and_transactions(self):
        logging.debug("Loading investments and transactions")
        mydb, cursor = get_db_cursor()
        investments = fetch_investments(cursor, self.email)
        self.treeview.delete(*self.treeview.get_children())
        for investment in investments:
            total_investment = 0  # Initialize the total for this investment

            # Fetch the current price for the investment
            cursor.execute("SELECT cours_actuel FROM Cours_actuel WHERE id_investissement = %s", (investment[0],))
            cours_actuel = cursor.fetchone()[0]

            inv_item = self.treeview.insert("", "end", text=investment[2] + " (" + str(cours_actuel) + "\u20AC)",
                                            values=(investment[3], investment[4], "", "", "", "", ""),
                                            tags=("investment",))
            transactions = fetch_transactions(cursor, self.email)
            for transaction in transactions:
                if transaction[1] == investment[0]:
                    total = transaction[4] * transaction[5]  # Calculate the total for this transaction
                    total_investment += total  # Add the total of this transaction to the total for the investment

                    # Calculate the gain or loss percentage
                    gain_perte_percentage = ((cours_actuel - transaction[4]) / transaction[4]) * 100

                    # Determine the tag for the gain or loss percentage
                    gain_perte_tag = "gain" if gain_perte_percentage >= 0 else "perte"

                    self.treeview.insert(inv_item, "end", text="Transaction", values=(
                        "", "", transaction[3], str(transaction[4]) + "\u20AC", transaction[5], str(total) + "\u20AC", "{:.2f}%".format(gain_perte_percentage)),
                                         tags=("transaction", gain_perte_tag))

            self.treeview.set(inv_item, "Total", str(total_investment) + "\u20AC")

        close_db(mydb, cursor)

    def logout(self):
        logging.debug("Logging out")
        self.root.destroy()
        root = tk.Tk()
        app = LoginWindow(root)
        root.mainloop()

    def open_add_transaction_window(self):
        logging.debug("Opening add transaction window")
        self.new_window = tk.Toplevel(self.root)
        self.new_window.title("Ajouter une transaction")

        self.investment_type = tk.StringVar(value="existing")

        CTkRadioButton(self.new_window, text="Nouvel investissement", variable=self.investment_type, value="new").grid(
            row=0, column=0, padx=20, pady=10)
        CTkRadioButton(self.new_window, text="Investissement existant", variable=self.investment_type,
                       value="existing").grid(row=1, column=0, padx=20, pady=10)

        self.nom_entreprise_label = tk.Label(self.new_window, text="Nom de l'entreprise:", bg="#f0f0f0", font=('Helvetica', 10, 'bold'))
        self.nom_entreprise_label.grid(row=2, column=0, padx=20, pady=10)
        self.nom_entreprise_entry = CTkEntry(self.new_window, border_width=2)
        self.nom_entreprise_entry.grid(row=3, column=0, padx=20, pady=10)

        self.nom_entreprise_dropdown = ttk.Combobox(self.new_window)
        self.nom_entreprise_dropdown.grid(row=4, column=0, padx=20, pady=10)
        self.update_investment_dropdown()
        self.nom_entreprise_dropdown.grid_remove()

        self.symbole_boursier_label = tk.Label(self.new_window, text="Symbole boursier:", bg="#f0f0f0", font=('Helvetica', 10, 'bold'))
        self.symbole_boursier_label.grid(row=5, column=0, padx=20, pady=10)
        self.symbole_boursier_entry = CTkEntry(self.new_window, border_width=2)
        self.symbole_boursier_entry.grid(row=6, column=0, padx=20, pady=10)

        self.secteur_activite_label = tk.Label(self.new_window, text="Secteur d'activité:", bg="#f0f0f0", font=('Helvetica', 10, 'bold'))
        self.secteur_activite_label.grid(row=7, column=0, padx=20, pady=10)
        self.secteur_activite_entry = CTkEntry(self.new_window, border_width=2)
        self.secteur_activite_entry.grid(row=8, column=0, padx=20, pady=10)

        self.date_label = tk.Label(self.new_window, text="Date au format DD/MM/YYYY:", bg="#f0f0f0", font=('Helvetica', 10, 'bold'))
        self.date_label.grid(row=9, column=0, padx=20, pady=10)
        self.date_entry = CTkEntry(self.new_window, border_width=2)
        self.date_entry.grid(row=10, column=0, padx=20, pady=10)

        self.prix_label = tk.Label(self.new_window, text="Prix d'achat:", bg="#f0f0f0", font=('Helvetica', 10, 'bold'))
        self.prix_label.grid(row=11, column=0, padx=20, pady=10)
        self.prix_entry = CTkEntry(self.new_window, border_width=2)
        self.prix_entry.grid(row=12, column=0, padx=20, pady=10)

        self.quantite_label = tk.Label(self.new_window, text="Quantité:", bg="#f0f0f0", font=('Helvetica', 10, 'bold'))
        self.quantite_label.grid(row=13, column=0, padx=20, pady=10)
        self.quantite_entry = CTkEntry(self.new_window, border_width=2)
        self.quantite_entry.grid(row=14, column=0, padx=20, pady=10)

        self.confirm_button = CTkButton(self.new_window, text="Confirmer", command=self.add_transaction,
                                        corner_radius=10, fg_color="blue")
        self.confirm_button.grid(row=15, column=0, padx=20, pady=10)

        self.investment_type.trace_add("write", self.update_form)
        self.update_form()

    def update_form(self, *args):
        logging.debug("Updating form based on investment type")
        if self.investment_type.get() == "new":
            self.nom_entreprise_label.config(text="Nom de l'entreprise:", bg="#f0f0f0", font=('Helvetica', 10, 'bold'))
            self.nom_entreprise_entry.grid(row=3, column=0, padx=20, pady=10)
            self.nom_entreprise_dropdown.grid_remove()

            self.symbole_boursier_label.grid(row=5, column=0, padx=20, pady=10)
            self.symbole_boursier_entry.grid(row=6, column=0, padx=20, pady=10)

            self.secteur_activite_label.grid(row=7, column=0, padx=20, pady=10)
            self.secteur_activite_entry.grid(row=8, column=0, padx=20, pady=10)
        else:
            self.nom_entreprise_label.config(text="Choisir l'entreprise:", bg="#f0f0f0", font=('Helvetica', 10, 'bold'))
            self.nom_entreprise_entry.grid_remove()
            self.nom_entreprise_dropdown.grid(row=4, column=0, padx=20, pady=10)

            self.symbole_boursier_label.grid_remove()
            self.symbole_boursier_entry.grid_remove()

            self.secteur_activite_label.grid_remove()
            self.secteur_activite_entry.grid_remove()

        self.update_investment_dropdown()

    def update_investment_dropdown(self):
        logging.debug("Updating investment dropdown")
        mydb, cursor = get_db_cursor()
        investments = fetch_investments(cursor, self.email)
        self.nom_entreprise_dropdown['values'] = [investment[2] for investment in investments]
        close_db(mydb, cursor)

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

            prix_achat = Decimal(prix_achat)
            quantite = int(quantite)
            date = datetime.strptime(date, "%d/%m/%Y").date()

            add_transaction_thread(id_investissement, date, prix_achat, quantite, self.queue, self.email)
            self.new_window.destroy()
            self.load_investments_and_transactions()
            close_db(mydb, cursor)
        except Exception as e:
            logging.error(f"An error occurred while adding the transaction: {e}")
            messagebox.showerror("Erreur", f"Une erreur s'est produite lors de l'ajout de la transaction : {e}")

    def check_queue(self):
        while not self.queue.empty():
            msg_type, msg = self.queue.get()
            if msg_type == "success":
                logging.debug("Transaction added successfully message received")
                if self.root.winfo_exists():  # Check if the window is still open
                    messagebox.showinfo("Succès", msg)
                    self.new_window.destroy()
                    self.root.after(0, self.load_investments_and_transactions)  # Refresh the data in the main thread
        if self.root.winfo_exists():  # Check if the window is still open
            self.root.after(100, self.check_queue)
