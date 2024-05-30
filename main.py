import tkinter as tk
from tkinter import messagebox, ttk
from mysql.connector import connect, Error
from db import mydb, cursor, close_db
from Login import LoginWindow


def fetch_investments(email):
    try:
        cursor.execute("SELECT id_utilisateur FROM utilisateur WHERE email = %s", (email,))
        user_id = cursor.fetchone()[0]
        cursor.execute("SELECT * FROM Investissement WHERE id_utilisateur = %s", (user_id,))
        investments = cursor.fetchall()
        return investments
    except Error as e:
        print(f"Error: {e}")
        return []


def fetch_transactions(email):
    try:
        cursor.execute("SELECT id_utilisateur FROM utilisateur WHERE email = %s", (email,))
        user_id = cursor.fetchone()[0]
        cursor.execute("SELECT * FROM Transaction WHERE id_utilisateur = %s", (user_id,))
        transactions = cursor.fetchall()
        return transactions
    except Error as e:
        print(f"Error: {e}")
        return []


def add_transaction(id_investissement, date, prix, quantite):
    try:
        sql = "INSERT INTO `Transaction` (`id_investissement`, `date`, `prix`, `quantite`) VALUES (%s, %s, %s, %s)"
        values = (id_investissement, date, prix, quantite)
        cursor.execute(sql, values)
        mydb.commit()
        messagebox.showinfo("Succès", "Transaction ajoutée avec succès")
    except Error as e:
        messagebox.showerror("Erreur", f"Erreur lors de l'ajout de la transaction: {e}")


class InvestmentApp:
    def __init__(self, root, email):
        self.root = root
        self.email = email
        self.root.title("Gestion d'Investissements")
        self.create_widgets()
        self.load_investments()
        self.load_transactions()

    def create_widgets(self):
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

        self.add_transaction_button = tk.Button(self.root, text="Ajouter une transaction",
                                                command=self.open_add_transaction_window)
        self.add_transaction_button.pack()

    def load_transactions(self):
        transactions = fetch_transactions(self.email)
        self.transaction_treeview.delete(*self.transaction_treeview.get_children())
        for transaction in transactions:
            self.transaction_treeview.insert("", "end", values=transaction[3:])

    def logout(self):
        try:
            self.root.destroy()
            root = tk.Tk()
            app = LoginWindow(root)
            root.mainloop()
        except Exception as e:
            print(f"Error in logout: {e}")

    def load_investments(self):
        investments = fetch_investments(self.email)
        self.investment_treeview.delete(*self.investment_treeview.get_children())
        for investment in investments:
            self.investment_treeview.insert("", "end", values=investment[2:])

    def open_add_transaction_window(self):
        try:
            self.new_window = tk.Toplevel(self.root)
            self.new_window.title("Ajouter une transaction")

            tk.Label(self.new_window, text="ID Investissement").grid(row=0, column=0)
            self.id_investissement_entry = tk.Entry(self.new_window)
            self.id_investissement_entry.grid(row=0, column=1)

            tk.Label(self.new_window, text="Date (YYYY-MM-DD)").grid(row=1, column=0)
            self.date_entry = tk.Entry(self.new_window)
            self.date_entry.grid(row=1, column=1)

            tk.Label(self.new_window, text="Prix").grid(row=2, column=0)
            self.prix_entry = tk.Entry(self.new_window)
            self.prix_entry.grid(row=2, column=1)

            tk.Label(self.new_window, text="Quantité").grid(row=3, column=0)
            self.quantite_entry = tk.Entry(self.new_window)
            self.quantite_entry.grid(row=3, column=1)

            tk.Button(self.new_window, text="Ajouter", command=self.add_transaction).grid(row=4, column=0, columnspan=2)
        except Exception as e:
            print(f"Error in open_add_transaction_window: {e}")

    def add_transaction(self):
        try:
            id_investissement = self.id_investissement_entry.get()
            date = self.date_entry.get()
            prix = self.prix_entry.get()
            quantite = self.quantite_entry.get()

            # Check that all fields are filled
            if not id_investissement or not date or not prix or not quantite:
                messagebox.showerror("Erreur", "Veuillez remplir tous les champs.")
                return

            # Check that id_investissement, prix and quantite are numbers
            if not id_investissement.isdigit() or not prix.replace('.', '', 1).isdigit() or not quantite.replace('.', '', 1).isdigit():
                messagebox.showerror("Erreur", "L'ID d'investissement, le prix et la quantité doivent être des nombres.")
                return

            add_transaction(id_investissement, date, prix, quantite)
            self.new_window.destroy()
        except Exception as e:
            print(f"Error in add_transaction: {e}")
            messagebox.showerror("Erreur", f"Erreur lors de l'ajout de la transaction: {e}")


def run_main(email):
    root = tk.Tk()
    app = InvestmentApp(root, email)
    root.mainloop()
    close_db()


if __name__ == "__main__":
    root = tk.Tk()
    app = LoginWindow(root)
    root.mainloop()