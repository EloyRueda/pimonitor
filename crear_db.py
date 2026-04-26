# Script rápido: crear_db.py
import sqlite3
from werkzeug.security import generate_password_hash

def setup_db(db_path, user, password):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT)''')
    
    hash_pw = generate_password_hash(password)
    try:
        cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (user, hash_pw))
        conn.commit()
        print(f"Base de datos {db_path} creada con éxito.")
    except sqlite3.IntegrityError:
        print(f"El usuario en {db_path} ya existe.")
    conn.close()

# Crear ambas
setup_db('/usb/pimonitor/pimonitor.db', 'admin', 'clave_monitor')
setup_db('/usb/pishare/pishare.db', 'admin', 'clave_share')
