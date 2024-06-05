import tkinter as tk
from login import LoginWindow
from db_utils import get_db_cursor, close_db
from investment_app import InvestmentApp

def run_main(email):
    mydb, cursor = get_db_cursor()
    root = tk.Tk()
    app = InvestmentApp(root, email)
    root.mainloop()
    close_db(mydb, cursor)

if __name__ == "__main__":
    root = tk.Tk()
    app = LoginWindow(root)
    root.mainloop()