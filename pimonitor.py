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
    SESSION_COOKIE_SECURE=True,   # Cambiar a True solo cuando tengas HTTPS
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

@app.route('/data')
@login_required # Para que nadie vea datos sin iniciar sesión
def get_data():
    services = ['nginx', 'docker', 'ssh', 'pishare']
    status_map = {}
    
    for srv in services:
        try:
            # Ejecuta 'systemctl is-active' para cada servicio
            res = subprocess.run(['systemctl', 'is-active', srv], capture_output=True, text=True)
            status_map[srv] = res.stdout.strip() # Devolverá 'active', 'inactive' o 'failed'
        except:
            status_map[srv] = 'error'
            
    # Lógica especial para el contenedor DNSMASQ
    try:
        # Consultar a docker si el contenedor está corriendo
        docker_res = subprocess.run(['docker', 'inspect', '-f', '{{.State.Status}}', 'dnsmasq-server'], 
                                    capture_output=True, text=True)
        # Si devuelve 'running', marcar como 'active' para que el JS lo muestre verde
        status_map['dnsmasq-docker'] = 'active' if docker_res.stdout.strip() == 'running' else 'failed'
    except:
        status_map['dnsmasq-docker'] = 'error'
        
    try:
        import psutil
        cpu_usage = psutil.cpu_percent(interval=None) 
        ram_usage = psutil.virtual_memory().percent
        # Temperatura
        temp = "N/A"
        temps = psutil.sensors_temperatures()
        if 'cpu_thermal' in temps:
            temp = f"{temps['cpu_thermal'][0].current:.1f}"
    except Exception as e:
        cpu_usage = ram_usage = "Error"
        temp = "N/A"
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    # 4. Devolver JSON único
    return jsonify({
        "temperature": temp,
        "cpu": cpu_usage,
        "ram": ram_usage,
        "services": status_map
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)