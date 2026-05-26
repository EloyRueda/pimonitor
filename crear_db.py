# Script rápido: crear_db.py
import sqlite3
import getpass
from werkzeug.security import generate_password_hash

def setup_db(db_path, user, password):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT)''')
    
    hash_pw = generate_password_hash(password)
    try:
	cursor.execute('''INSERT INTO users (username, password_hash)
                          VALUES (?, ?)
                          ON CONFLICT(username) DO UPDATE SET password_hash=excluded.password_hash''',
        conn.commit()
        print(f"Base de datos {db_path} actualizada con éxito.")
    except Exeption as e:
        print(f"Error en {db_path}: {e}")
    conn.close()

if __name__ == "__main__":
    print("--- Configuración de Seguridad ---")
    user_admin = "admin"

    # Pregunta las contraseñas sin mostrarlas en pantalla
    pw_monitor = getpass.getpass(f"Introduce contraseña para {user_admin} en PiMonitor: ")
    pw_share = getpass.getpass(f"Introduce contraseña para {user_admin} en PiShare: ")

    setup_db('/usb/pimonitor/pimonitor.db', user_admin, pw_monitor)
    setup_db('/usb/pishare/pishare.db', user_admin, pw_share)

    print("\nProceso finalizado. Las contraseñas han sido hasheadas y guardadas en la DB.")
