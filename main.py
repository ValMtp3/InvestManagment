import tkinter as tk
from tkinter import messagebox, ttk
from db import get_db_cursor, close_db, Error
import threading
import queue
import logging
from Login import LoginWindow
from decimal import Decimal
from datetime import datetime
from customtkinter import CTkEntry, CTkButton

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


def fetch_user_id(cursor, email):
    try:
        logging.debug(f"Fetching user id for email: {email}")
        cursor.execute("SELECT id_utilisateur FROM utilisateur WHERE email = %s", (email,))
        user_id = cursor.fetchone()[0]
        logging.debug(f"Fetched user id: {user_id}")
        return user_id
    except Exception as e:
        logging.error(f"Error fetching user id: {e}")
        return None


def fetch_investments(cursor, email):
    try:
        logging.debug(f"Fetching investments for email: {email}")
        user_id = fetch_user_id(cursor, email)
        if user_id is None:
            return []
        cursor.execute("SELECT * FROM Investissement WHERE id_utilisateur = %s", (user_id,))
        investments = cursor.fetchall()
        logging.debug(f"Fetched investments: {investments}")
        return investments
    except Error as e:
        logging.error(f"Error fetching investments: {e}")
        return []


def fetch_transactions(cursor, email):
    try:
        logging.debug(f"Fetching transactions for email: {email}")
        user_id = fetch_user_id(cursor, email)
        if user_id is None:
            return []
        cursor.execute("SELECT * FROM Transaction WHERE id_utilisateur = %s ORDER BY date", (user_id,))
        transactions = cursor.fetchall()
        logging.debug(f"Fetched transactions: {transactions}")
        return transactions
    except Error as e:
        logging.error(f"Error fetching transactions: {e}")
        return []


def add_transaction_thread(id_investissement, date, prix_achat, quantite, queue, email):
    logging.debug(f"Starting thread to add transaction: {id_investissement}, {date}, {prix_achat}, {quantite}")
    thread = threading.Thread(target=_add_transaction,
                              args=(id_investissement, date, prix_achat, quantite, queue, email))
    thread.daemon = True  # Permet de tuer le thread si le programme se termine
    thread.start()


def _add_transaction(id_investissement, date, prix_achat, quantite, queue, email):
    mydb, cursor = get_db_cursor()
    if mydb is None or cursor is None:
        logging.error("Database connection failed in thread")
        queue.put(("error", "Erreur de connexion à la base de données"))
        return

    try:
        id_utilisateur = fetch_user_id(cursor, email)
        logging.debug(f"Inserting transaction: {id_investissement, date, prix_achat, quantite}")

        # Insère la transaction
        sql = "INSERT INTO `Transaction` (`id_utilisateur`, `id_investissement`, `date`, `prix_achat`, `quantite`) VALUES (%s, %s, %s, %s, %s)"
        values = (id_utilisateur, id_investissement, date, prix_achat, quantite)
        cursor.execute(sql, values)
        mydb.commit()
        logging.debug("Transaction inserted successfully")
        queue.put(("success", "Transaction ajoutée avec succès"))
    except Error as e:
        logging.error(f"Erreur lors de l'ajout de la transaction: {e}")
        queue.put(("error", f"Erreur lors de l'ajout de la transaction: {e}"))
    finally:
        close_db(mydb, cursor)  # Fermer la connexion à la base de données


class InvestmentApp:
    def __init__(self, root, email):
        logging.debug("Initializing InvestmentApp")
        self.root = root
        self.email = email
        self.queue = queue.Queue()
        self.root.title("Gestion d'Investissements")
        self.create_styles()
        self.create_widgets()
        self.load_investments_and_transactions()
        self.check_queue()

    def create_styles(self):
        logging.debug("Creating styles")
        self.style = ttk.Style()
        self.style.configure("Investment.TLabel", background="lightblue", foreground="black",
                             font=('Arial', 10, 'bold'))
        self.style.configure("Transaction.TLabel", background="lightgreen", foreground="black", font=('Arial', 9))

    def create_widgets(self):
        logging.debug("Creating widgets")
        self.treeview = ttk.Treeview(self.root,
                                     columns=("Type", "Valeur", "Date", "Prix d'achat de l'action", "Quantité"),
                                     show="tree headings")
        self.treeview.pack(pady=10, fill=tk.BOTH, expand=True)

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

        self.logout_button = CTkButton(self.root, text="Déconnexion", command=self.logout, corner_radius=10)
        self.logout_button.pack(pady=10)

        self.add_transaction_button = CTkButton(self.root, text="Ajouter une transaction",
                                                command=self.open_add_transaction_window, corner_radius=10)
        self.add_transaction_button.pack(pady=10)

    def load_investments_and_transactions(self):
        mydb, cursor = get_db_cursor()
        if mydb is None or cursor is None:
            return
        logging.debug("Loading investments and transactions")
        try:
            investments = fetch_investments(cursor, self.email)
            self.treeview.delete(*self.treeview.get_children())
            for investment in investments:
                inv_item = self.treeview.insert("", "end", text=investment[2], values=(investment[3], investment[4]),
                                                tags=("investment",))
                transactions = fetch_transactions(cursor, self.email)
                for transaction in transactions:
                    if transaction[1] == investment[0]:  # Check if transaction belongs to this investment
                        self.treeview.insert(inv_item, "end", text=f"Transaction ", values=(
                            "", "", transaction[3], str(transaction[4]) + "\u20AC", transaction[5]),
                                             tags=("transaction",))
        except Exception as e:
            logging.error(f"Error loading investments and transactions: {e}")
            messagebox.showerror("Erreur", f"Erreur lors du chargement des investissements et transactions: {e}")
        finally:
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

        tk.Radiobutton(self.new_window, text="Nouvel investissement", variable=self.investment_type, value="new").pack()
        tk.Radiobutton(self.new_window, text="Investissement existant", variable=self.investment_type,
                       value="existing").pack()

        tk.Label(self.new_window, text="Nom de l'entreprise:").pack()
        self.nom_entreprise_entry = CTkEntry(self.new_window, border_width=2)
        self.nom_entreprise_entry.pack(pady=5)

        self.symbole_boursier_label = tk.Label(self.new_window, text="Symbole boursier:")
        self.symbole_boursier_entry = CTkEntry(self.new_window, border_width=2)

        self.secteur_activite_label = tk.Label(self.new_window, text="Secteur d'activité:")
        self.secteur_activite_entry = CTkEntry(self.new_window, border_width=2)

        tk.Label(self.new_window, text="Date (YYYY-MM-DD):").pack()
        self.date_entry = CTkEntry(self.new_window, border_width=2)
        self.date_entry.pack(pady=5)

        tk.Label(self.new_window, text="Prix:").pack()
        self.prix_entry = CTkEntry(self.new_window, border_width=2)
        self.prix_entry.pack(pady=5)

        tk.Label(self.new_window, text="Quantité:").pack()
        self.quantite_entry = CTkEntry(self.new_window, border_width=2)
        self.quantite_entry.pack(pady=5)

        self.add_transaction_button = CTkButton(self.new_window, text="Ajouter", command=self.add_transaction,
                                                corner_radius=10)
        self.add_transaction_button.pack(pady=10)

        self.investment_type.trace_add("write", self.update_form)

    def update_form(self, *args):
        if self.investment_type.get() == "new":
            self.symbole_boursier_label.pack()
            self.symbole_boursier_entry.pack(pady=5)
            self.secteur_activite_label.pack()
            self.secteur_activite_entry.pack(pady=5)
        else:
            self.symbole_boursier_label.pack_forget()
            self.symbole_boursier_entry.pack_forget()
            self.secteur_activite_label.pack_forget()
            self.secteur_activite_entry.pack_forget()

    def add_transaction(self):
        try:
            logging.debug("Adding transaction")
            nom_entreprise = self.nom_entreprise_entry.get()
            date = self.date_entry.get()
            prix_achat = self.prix_entry.get()
            quantite = self.quantite_entry.get()

            if not nom_entreprise or not date or not prix_achat or not quantite:
                messagebox.showerror("Erreur", "Tous les champs doivent être remplis.")
                return

            mydb, cursor = get_db_cursor()
            if mydb is None or cursor is None:
                return

            id_utilisateur = fetch_user_id(cursor, self.email)
            cursor.execute(
                "SELECT id_investissement FROM Investissement WHERE id_utilisateur = %s AND nom_entreprise = %s",
                (id_utilisateur, nom_entreprise))
            result = cursor.fetchone()
            if result is None:
                # Créer un nouvel investissement
                sql = "INSERT INTO `Investissement` (`id_utilisateur`, `nom_entreprise`) VALUES (%s, %s)"
                values = (id_utilisateur, nom_entreprise)
                cursor.execute(sql, values)
                mydb.commit()
                id_investissement = cursor.lastrowid
            else:
                id_investissement = result[0]  # Extract the integer from the tuple

            prix_achat = Decimal(prix_achat)
            quantite = int(quantite)
            date = datetime.strptime(date, "%Y-%m-%d").date()

            add_transaction_thread(id_investissement, date, prix_achat, quantite, self.queue, self.email)
        except ValueError:
            messagebox.showerror("Erreur", "Veuillez entrer des valeurs valides.")
        except Exception as e:
            logging.error(f"Erreur lors de l'ajout de la transaction : {e}")
            messagebox.showerror("Erreur", f"Erreur lors de l'ajout de la transaction : {e}")

    def create_investment(self, id_investissement):
        logging.debug("Creating investment")
        nom_entreprise = self.nom_entreprise_entry.get()
        symbole_boursier = self.symbole_boursier_entry.get()
        secteur_activite = self.secteur_activite_entry.get()

        if not nom_entreprise or not symbole_boursier or not secteur_activite:
            messagebox.showerror("Erreur", "Tous les champs doivent être remplis.")
            return

        try:
            mydb, cursor = get_db_cursor()
            if mydb is None or cursor is None:
                return

            id_utilisateur = fetch_user_id(cursor, self.email)
            sql = "INSERT INTO `Investissement` (`id_utilisateur`, `nom_entreprise`, `symbole_boursier`, `secteur_activite`) VALUES (%s, %s, %s, %s)"
            values = (id_utilisateur, nom_entreprise, symbole_boursier, secteur_activite)
            cursor.execute(sql, values)
            mydb.commit()
            logging.debug("Investment created successfully")
            messagebox.showinfo("Succès", "Investissement créé avec succès")
        except Error as e:
            logging.error(f"Erreur lors de la création de l'investissement: {e}")
            messagebox.showerror("Erreur", f"Erreur lors de la création de l'investissement: {e}")
        finally:
            close_db(mydb, cursor)  # Fermer la connexion à la base de données
            self.new_window.destroy()  # Fermer la fenêtre de création d'investissement
            self.load_investments_and_transactions()  # Rafraîchir la fenêtre principale

    def check_queue(self):
        try:
            while not self.queue.empty():
                msg_type, msg = self.queue.get()
                if msg_type == "success":
                    messagebox.showinfo("Succès", msg)
                    logging.info(f"Success: {msg}")
                    self.new_window.destroy()  # Close the add transaction window
                    self.load_investments_and_transactions()  # Refresh the main window
                elif msg_type == "error":
                    messagebox.showerror("Erreur", msg)
                    logging.error(f"Error: {msg}")
                elif msg_type == "create_investment":
                    logging.info(f"Opening investment creation window for id: {msg}")
                    self.open_create_investment_window(msg)
        except Exception as e:
            logging.error(f"Error in check_queue: {e}")
        finally:
            self.root.after(100, self.check_queue)

    def open_create_investment_window(self, id_investissement):
        logging.debug("Opening create investment window")
        self.new_window = tk.Toplevel(self.root)
        self.new_window.title("Créer un investissement")

        tk.Label(self.new_window, text="Nom de l'entreprise:").pack()
        self.nom_entreprise_entry = CTkEntry(self.new_window, border_width=2)
        self.nom_entreprise_entry.pack(pady=5)

        tk.Label(self.new_window, text="Symbole boursier:").pack()
        self.symbole_boursier_entry = CTkEntry(self.new_window, border_width=2)
        self.symbole_boursier_entry.pack(pady=5)

        tk.Label(self.new_window, text="Secteur d'activité:").pack()
        self.secteur_activite_entry = CTkEntry(self.new_window, border_width=2)
        self.secteur_activite_entry.pack(pady=5)

        self.create_investment_button = CTkButton(self.new_window, text="Créer",
                                                  command=lambda: self.create_investment(id_investissement),
                                                  corner_radius=10)
        self.create_investment_button.pack(pady=10)


def run_main(email):
    logging.debug("Running main application")
    mydb, cursor = get_db_cursor()
    if mydb is None or cursor is None:
        return
    try:
        root = tk.Tk()
        app = InvestmentApp(root, email)
        root.mainloop()
    except Exception as e:
        logging.error(f"Error in run_main: {e}")
    finally:
        # Pass the required arguments to close_db()
        close_db(mydb, cursor)


if __name__ == "__main__":
    logging.debug("Starting application")
    try:
        root = tk.Tk()
        app = LoginWindow(root)
        root.mainloop()
    except Exception as e:
        logging.error(f"Error in __main__: {e}")
