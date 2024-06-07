import logging
from tkinter import messagebox
from db_utils import get_db_cursor, close_db, fetch_investments, fetch_transactions, calculate_roi


def load_investments_and_transactions(app):
    logging.debug("Loading investments and transactions")
    mydb, cursor = get_db_cursor()
    investments = fetch_investments(cursor, app.email)
    app.treeview.delete(*app.treeview.get_children())
    app.treeview.tag_configure("oddrow", background="white")
    app.treeview.tag_configure("evenrow", background="lightgrey")
    for i, investment in enumerate(investments):
        total_investment = 0
        cursor.execute("SELECT cours_actuel FROM Cours_actuel WHERE id_investissement = %s", (investment[0],))
        result = cursor.fetchone()
        if result:
            cours_actuel = result[0]
        else:
            logging.error(f"Could not find current price for investment {investment[0]}")
            cours_actuel = 0
        roi = calculate_roi(cursor, investment[0])
        if roi is not None:
            roi_tag = "gain" if roi >= 0 else "perte"
        else:
            roi_tag = "unknown"
        color_tag = "oddrow" if i % 2 else "evenrow"
        inv_item = app.treeview.insert("", "end", text=investment[2] + " (" + str(cours_actuel) + "\u20AC)",
                                       values=(investment[3], investment[4], "", "", "", "", "{:.2f}%".format(roi) if roi is not None else "N/A"),
                                       tags=(color_tag, "investment", roi_tag, investment[0]))
        transactions = fetch_transactions(cursor, app.email)
        for transaction in transactions:
            if transaction[1] == investment[0]:
                total = transaction[4] * transaction[5]
                total_investment += total
                gain_perte_percentage = ((cours_actuel - transaction[4]) / transaction[4]) * 100
                gain_perte_tag = "gain" if gain_perte_percentage >= 0 else "perte"
                app.treeview.insert(inv_item, "end", text="Transaction",
                                    values=("", transaction[3], "", str(transaction[4]) + "\u20AC", transaction[5],
                                            str(total) + "\u20AC", "{:.2f}%".format(gain_perte_percentage)),
                                    tags=(color_tag, "transaction", gain_perte_tag, transaction[0]))
        app.treeview.set(inv_item, "Total", str(total_investment) + "\u20AC")
    close_db(mydb, cursor)


def confirm_delete(app):
    selected_items = app.treeview.selection()
    if not selected_items:
        messagebox.showwarning("Suppression", "Aucun élément sélectionné pour la suppression.")
        return
    confirm = messagebox.askyesno("Confirmation", "Voulez-vous vraiment supprimer les éléments sélectionnés ?")
    if confirm:
        app.delete_selected(selected_items)


def delete_selected(app, selected_items):
    mydb, cursor = get_db_cursor()
    for item in selected_items:
        item_tags = app.treeview.item(item, "tags")
        if "investment" in item_tags:
            id_investissement = app.treeview.item(item, "tags")[-1]
            cursor.execute("DELETE FROM Investissement WHERE id_investissement = %s", (id_investissement,))
        elif "transaction" in item_tags:
            id_transaction = app.treeview.item(item, "tags")[-1]
            cursor.execute("DELETE FROM Transaction WHERE id_transaction = %s", (id_transaction,))
        app.treeview.delete(item)
    mydb.commit()
    close_db(mydb, cursor)


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
