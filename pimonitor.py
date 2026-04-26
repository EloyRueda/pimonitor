import psutil
import subprocess
import sqlite3
import os
from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash
from dotenv import load_dotenv

# 1. Carga de variables de entorno (Corregido con comillas)
load_dotenv("/usb/pimonitor/.env")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "una_clave_por_defecto_muy_segura")

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=False,   # Cambiar a True solo cuando tengas HTTPS
    SESSION_COOKIE_SAMESITE='Lax',
)

# Decorador para proteger rutas
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_service_status(service_name):
    try:
        res = subprocess.run(['systemctl', 'is-active', service_name], capture_output=True, text=True)
        return res.stdout.strip()
    except:
        return "error"

def check_db_login(user, password):
    conn = sqlite3.connect('/usb/pimonitor/pimonitor.db')
    cursor = conn.cursor()
    cursor.execute('SELECT password_hash FROM users WHERE username = ?', (user,))
    result = cursor.fetchone()
    conn.close()
    if result and check_password_hash(result[0], password):
        return True
    return False

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['username']
        pw = request.form['password']
        if check_db_login(user, pw):
            session['logged_in'] = True
            return redirect(url_for('index'))
        return "Acceso denegado", 401
    return render_template('login.html')

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/stats')
@login_required
def stats():
    return jsonify({
        "cpu_usage": psutil.cpu_percent(),
        "cpu_temp": psutil.sensors_temperatures()['cpu_thermal'][0].current if 'cpu_thermal' in psutil.sensors_temperatures() else 0,
        "ram": psutil.virtual_memory().percent,
        "swap": psutil.swap_memory().percent,
        "services": {
            "pishare": get_service_status("pishare"),
            "nginx": get_service_status("nginx"),
            "ssh": get_service_status("ssh"),
            "dnsmasq": get_service_status("dnsmasq-server")
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)