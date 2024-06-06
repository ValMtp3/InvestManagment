import threading
import logging
from db_utils import get_db_cursor, fetch_user_id, close_db

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
        queue.put(("error", f"Une erreur s'est produite dans le thread : {e}"))
        print(f"Une erreur s'est produite dans le thread : {e}")