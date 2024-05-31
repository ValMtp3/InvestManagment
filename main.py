import tkinter as tk
from tkinter import messagebox, ttk
from db import get_db_cursor, close_db, Error
import threading
import queue
import logging
from Login import LoginWindow
from decimal import Decimal
from datetime import datetime

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
        cursor.execute("SELECT * FROM Transaction WHERE id_utilisateur = %s", (user_id,))
        transactions = cursor.fetchall()
        logging.debug(f"Fetched transactions: {transactions}")
        return transactions
    except Error as e:
        logging.error(f"Error fetching transactions: {e}")
        return []

def add_transaction_thread(id_investissement, date, prix, quantite, queue):
    logging.debug(f"Starting thread to add transaction: {id_investissement}, {date}, {prix}, {quantite}")
    thread = threading.Thread(target=_add_transaction, args=(id_investissement, date, prix, quantite, queue))
    thread.daemon = True  # Permet de tuer le thread si le programme se termine
    thread.start()

def _add_transaction(id_investissement, date, prix, quantite, queue):
    mydb, cursor = get_db_cursor()
    if mydb is None or cursor is None:
        logging.error("Database connection failed in thread")
        queue.put(("error", "Erreur de connexion à la base de données"))
        return

    try:
        logging.debug(f"Inserting transaction: {id_investissement, date, prix, quantite}")
        sql = "INSERT INTO `Transaction` (`id_investissement`, `date`, `prix`, `quantite`) VALUES (%s, %s, %s, %s)"
        values = (id_investissement, date, prix, quantite)
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
        self.create_widgets()
        self.load_investments()
        self.load_transactions()
        self.check_queue()

    def create_widgets(self):
        logging.debug("Creating widgets")
        self.investment_treeview = ttk.Treeview(self.root, columns=("Nom", "Type", "Valeur"), show="headings")
        self.investment_treeview.pack(pady=10)
        self.investment_treeview.heading("Nom", text="Nom")
        self.investment_treeview.column("Nom", width=200)
        self.investment_treeview.heading("Type", text="Symbole")
        self.investment_treeview.column("Type", width=100)
        self.investment_treeview.heading("Valeur", text="Secteur")
        self.investment_treeview.column("Valeur", width=100)

        self.transaction_treeview = ttk.Treeview(self.root, columns=("Date", "Prix", "Quantité"), show="headings")
        self.transaction_treeview.pack(pady=10)
        self.transaction_treeview.heading("Date", text="Date")
        self.transaction_treeview.column("Date", width=200)
        self.transaction_treeview.heading("Prix", text="Prix")
        self.transaction_treeview.column("Prix", width=100)
        self.transaction_treeview.heading("Quantité", text="Quantité")
        self.transaction_treeview.column("Quantité", width=100)

        self.logout_button = tk.Button(self.root, text="Déconnexion", command=self.logout)
        self.logout_button.pack()

        self.add_transaction_button = tk.Button(self.root, text="Ajouter une transaction", command=self.open_add_transaction_window)
        self.add_transaction_button.pack()


    def load_transactions(self):
        logging.debug("Loading transactions")
        try:
            mydb, cursor = get_db_cursor()
            if mydb is None or cursor is None:
                return
            transactions = fetch_transactions(cursor, self.email)
            self.transaction_treeview.delete(*self.transaction_treeview.get_children())
            for transaction in transactions:
                self.transaction_treeview.insert("", "end", values=transaction[3:])
        except Exception as e:
            logging.error(f"Error loading transactions: {e}")
            messagebox.showerror("Erreur", f"Erreur lors du chargement des transactions: {e}")
        finally:
            close_db(mydb, cursor)

    def logout(self):
        logging.debug("Logging out")
        self.root.destroy()  # Fermer la fenêtre principale

    def load_investments(self):
        logging.debug("Loading investments")
        try:
            mydb, cursor = get_db_cursor()
            if mydb is None or cursor is None:
                return
            investments = fetch_investments(cursor, self.email)
            self.investment_treeview.delete(*self.investment_treeview.get_children())
            for investment in investments:
                self.investment_treeview.insert("", "end", values=investment[2:])
        except Exception as e:
            logging.error(f"Error loading investments: {e}")
            messagebox.showerror("Erreur", f"Erreur lors du chargement des investissements: {e}")
        finally:
            close_db(mydb, cursor)

    def open_add_transaction_window(self):
        logging.debug("Opening add transaction window")
        self.new_window = tk.Toplevel(self.root)
        self.new_window.title("Ajouter une transaction")

        tk.Label(self.new_window, text="ID Investissement:").pack()
        self.id_investissement_entry = tk.Entry(self.new_window)
        self.id_investissement_entry.pack()

        tk.Label(self.new_window, text="Date (YYYY-MM-DD):").pack()
        self.date_entry = tk.Entry(self.new_window)
        self.date_entry.pack()

        tk.Label(self.new_window, text="Prix:").pack()
        self.prix_entry = tk.Entry(self.new_window)
        self.prix_entry.pack()

        tk.Label(self.new_window, text="Quantité:").pack()
        self.quantite_entry = tk.Entry(self.new_window)
        self.quantite_entry.pack()

        tk.Button(self.new_window, text="Ajouter", command=self.add_transaction).pack()

    def add_transaction(self):
        logging.debug("Adding transaction")
        try:
            id_investissement = self.id_investissement_entry.get()
            date = self.date_entry.get()
            prix = self.prix_entry.get()
            quantite = self.quantite_entry.get()

            if not id_investissement or not date or not prix or not quantite:
                messagebox.showerror("Erreur", "Tous les champs doivent être remplis.")
                return

            try:
                id_investissement = int(id_investissement)
                prix = Decimal(prix)
                quantite = int(quantite)
                date = datetime.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                messagebox.showerror("Erreur", "Veuillez entrer des valeurs valides.")
                return

            add_transaction_thread(id_investissement, date, prix, quantite, self.queue)
            self.new_window.destroy()  # Fermer la fenêtre de dialogue
        except Exception as e:
            logging.error(f"Erreur lors de l'ajout de la transaction : {e}")
            messagebox.showerror("Erreur", f"Erreur lors de l'ajout de la transaction : {e}")

    def check_queue(self):
        try:
            while not self.queue.empty():
                msg_type, msg = self.queue.get()
                if msg_type == "success":
                    messagebox.showinfo("Succès", msg)
                    logging.info(f"Success: {msg}")
                elif msg_type == "error":
                    messagebox.showerror("Erreur", msg)
                    logging.error(f"Error: {msg}")
        except Exception as e:
            logging.error(f"Error in check_queue: {e}")
        finally:
            self.root.after(100, self.check_queue)

def run_main(email):
    logging.debug("Running main application")
    try:
        root = tk.Tk()
        app = InvestmentApp(root, email)
        root.mainloop()
    except Exception as e:
        logging.error(f"Error in run_main: {e}")
    finally:
        close_db()

if __name__ == "__main__":
    logging.debug("Starting application")
    try:
        root = tk.Tk()
        app = LoginWindow(root)
        root.mainloop()
    except Exception as e:
        logging.error(f"Error in __main__: {e}")

