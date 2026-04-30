import psutil
import subprocess
import sqlite3
import os
import sys
import pyotp
import qrcode
import base64
import io
from flask import Flask, render_template, jsonify, request, session, redirect, url_for, flash
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

#Obtener información del proxy
def get_proxy_stats():
    try:
        # El comando 'squidclient' da info detallada
        result = subprocess.check_output(["squidclient", "mgr:info"]).decode()
        # Extraer el "Cache Hit Ratio" (Eficiencia de la caché)
        hits = [line for line in result.split('\n') if 'Request Hit Ratios' in line]
        return hits[0] if hits else "Caché activa"
    except Exception:
        return "Squid no responde"

def check_proxy_health():
    services = {
        "Squid (Caché)": "squid",
        "Privoxy (Privacidad)": "privoxy"
    }
    proxy_status = []
    
    for svc_name, display_name in services.items():
        try:
            # Usamos el comando que añadiste a sudoers previamente
            result = subprocess.run(
                ["sudo", "systemctl", "is-active", svc_name], 
                capture_output=True, 
                text=True, 
                timeout=2
            )
            status = result.stdout.strip() # Devolverá 'active', 'inactive', 'failed', etc.
        except Exception as e:
            status = "error"
            
        proxy_status.append({
            "name": display_name,
            "status": status
        })
        
    return proxy_status

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
        username = request.form['username']
        password = request.form['password']
        
        if check_db_login(username, password):
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            # Capturamos la IP real para Fail2Ban
            ip_real = request.headers.get('X-Real-IP', request.remote_addr)
            
            # Forzamos la escritura en stderr para que systemd lo capture
            try:
                print(f"ALERTA_SEGURIDAD: Login fallido desde {ip_real}", file=sys.stderr, flush=True)
            except Exception:
                pass # Que no se rompa la web si el log falla
            
            
            flash('Usuario o contraseña incorrectos')
            return render_template('login.html'), 401 # Cargar el template con el error
            
    return render_template('login.html')

# FUNCIONES PARA 2FA
@app.route('/setup-2fa')
def setup_2fa():
    try: 
        # En producción, recupera esto de tu base de datos
        secret = "RQS24HCG3E5C2AGK4F5555E3GIOVHIX4" 
        
        totp = pyotp.TOTP(secret)
        # name: el usuario, issuer_name: el nombre que sale en la App
        uri = totp.provisioning_uri(name="admin1", issuer_name="PiMonitor")
        
        # Crear imagen QR
        img = qrcode.make(uri)
        buf = io.BytesIO()
        img.save(buf)
        qr_b64 = base64.b64encode(buf.getvalue()).decode()
        
        return f'<h2>Escanea este código con Google Authenticator</h2><img src="data:image/png;base64,{qr_b64}">'
    except Exception as e:
        return f"Error al generar QR: {str(e)}", 500

@app.route('/verify-2fa', methods=['GET', 'POST'])
def verify_2fa():
    if request.method == 'POST':
        user_code = request.form.get('otp_code')
        secret = "RQS24HCG3E5C2AGK4F5555E3GIOVHIX4"
        totp = pyotp.TOTP(secret)
        
        if totp.verify(user_code):
            session['2fa_authenticated'] = True
            return redirect(url_for('index'))
        else:
            # INTEGRACIÓN CON FAIL2BAN
            ip_real = request.headers.get('X-Real-IP', request.remote_addr)
            print(f"ALERTA_SEGURIDAD: Fallo 2FA desde {ip_real}", file=sys.stderr, flush=True)
            flash("Código incorrecto o expirado")
            
    return render_template('2fa_verify.html')

@app.route('/login-2fa', methods=['POST'])
def login_2fa():
    if request.method == 'POST':
        # Recuperamos al usuario que está "en espera"
        user_id = session.get('temp_user_id')
        if not user_id:
            return redirect(url_for('login'))

        user = db.session.get(user_id)
        token = request.form.get('otp_token')
        
        totp = pyotp.totp.TOTP(user.mfa_secret)
        
        if totp.verify(token):
            # ¡Código correcto! Limpiamos la sesión temporal e iniciamos sesión real
            session.pop('temp_user_id')
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash("Código incorrecto")
            return redirect(url_for('verify_2fa_page'))
    
    # Si es GET, tiene que devolver el HTML
    return render_template('2fa_input.html')

# Enviar cookies sólo si la conexión es segura
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

# Ruta de prueba para verificar que la aplicación se está ejecutando correctamente
@app.route('/testview')
def testview():
    return "La ruta de prueba funciona perfectamente"

@app.route('/')
@login_required
def index():    
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if not session.get('2fa_authenticated'):
        return redirect(url_for('verify_2fa'))
    
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
    try:
        # 1. Lista de servicios a chequear
        services_to_check = ['nginx', 'docker', 'ssh', 'pishare', 'squid', 'privoxy']
        status_map = {}
        
        for srv in services_to_check:
            try:
                # IMPORTANTE: Añadimos 'sudo' para tener permisos
                res = subprocess.run(['sudo', 'systemctl', 'is-active', srv], 
                                     capture_output=True, text=True, timeout=2)
                status_map[srv] = res.stdout.strip()
            except Exception:
                status_map[srv] = 'error'

        # 2. Lógica para Docker (dnsmasq)
        try:
            docker_res = subprocess.run(['sudo', 'docker', 'inspect', '-f', '{{.State.Status}}', 'dnsmasq-server'], 
                                        capture_output=True, text=True, timeout=2)
            status_raw = docker_res.stdout.strip()
            status_map['dnsmasq'] = 'active' if status_raw == 'running' else 'failed'

        except Exception:
            print(f"Error Docker: {e}")
            status_map['dnsmasq'] = 'error'
            
        # 3. Métricas de Sistema
        cpu_usage = psutil.cpu_percent(interval=None) 
        ram_usage = psutil.virtual_memory().percent
        temp = "N/A"
        temps = psutil.sensors_temperatures()
        if 'cpu_thermal' in temps:
            temp = f"{temps['cpu_thermal'][0].current:.1f}"

        # 4. Retorno de JSON (Todo dentro de un solo try)
        return jsonify({
            "temperature": temp,
            "cpu": cpu_usage,
            "ram": ram_usage,
            "services": status_map
        })

    except Exception as e:
        # Si algo falla arriba, esto evita que la web se quede en "Cargando..."
        print(f"Error en /data: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/logout')
def logout():
    # Limpiar todas las variables de sesión
    session.clear() 
    flash('Has cerrado sesión correctamente')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
