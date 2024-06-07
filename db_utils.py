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

def calculate_roi(cursor, id_investissement):
    try:
        cursor.execute("SELECT prix_achat FROM Transaction WHERE id_investissement = %s", (id_investissement,))
        transactions = cursor.fetchall()
        cursor.execute("SELECT cours_actuel FROM Cours_actuel WHERE id_investissement = %s", (id_investissement,))
        cours_actuel = cursor.fetchone()[0]
        roi_percentages = []
        for transaction in transactions:
            prix_achat = transaction[0]
            if prix_achat is not None and cours_actuel is not None:  # Ensure both prices are not None
                roi = (cours_actuel - prix_achat) / prix_achat * 100
                roi_percentages.append(roi)
        return round(sum(roi_percentages) / len(roi_percentages), 2) if roi_percentages else None
    except Exception as e:
        logging.error(f"Error calculating ROI: {e}")
        return None