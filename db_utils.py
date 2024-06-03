import logging
from db import get_db_cursor, close_db, Error

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


def fetch_user_id(cursor, email):
    try:
        cursor.execute("SELECT id_utilisateur FROM utilisateur WHERE email = %s", (email,))
        return cursor.fetchone()[0]
    except Exception as e:
        logging.error(f"Error fetching user id: {e}")
        return None


def fetch_investments(cursor, email):
    try:
        user_id = fetch_user_id(cursor, email)
        cursor.execute("SELECT * FROM Investissement WHERE id_utilisateur = %s", (user_id,))
        return cursor.fetchall()
    except Error as e:
        logging.error(f"Error fetching investments: {e}")
        return []


def fetch_transactions(cursor, email):
    try:
        user_id = fetch_user_id(cursor, email)
        cursor.execute("SELECT * FROM Transaction WHERE id_utilisateur = %s ORDER BY date", (user_id,))
        return cursor.fetchall()
    except Error as e:
        logging.error(f"Error fetching transactions: {e}")
        return []
