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
