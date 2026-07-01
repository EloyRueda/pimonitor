📊 PiMonitor Dashboard
PiMonitor es un panel de control web ligero y reactivo desarrollado en Python (Flask) para monitorizar el estado de salud de una Raspberry Pi en tiempo real.

El proyecto está diseñado de forma robusta bajo el principio de menor privilegio, ejecutándose de forma totalmente aislada bajo su propio usuario del sistema sin privilegios de administración (sudo).

⚡ Características Principales
Métricas en tiempo real: Carga de CPU, uso de memoria RAM, temperatura del procesador y estado del almacenamiento.
Gestión de almacenamiento doble: Lectura independiente de la tarjeta MicroSD principal y de unidades de almacenamiento externo (USB).
Monitorización de Servicios: Supervisión de servicios locales (Docker, Nginx, Apache, Proxy, etc.).
Arquitectura Hardened: El proceso corre aislado del usuario administrador (admin1) y de root.
🛡️ Arquitectura de Seguridad (Aislamiento)
Para evitar que una vulnerabilidad en la aplicación web comprometa la Raspberry Pi, el servicio se ejecuta bajo el demonio dedicado pimonitor, el cual solo tiene permisos de lectura/escritura en su propio directorio de trabajo dentro del almacenamiento externo.

[ Sistema Operativo ] ──> Ejecuta Systemd │ └──> [ Usuario: pimonitor ] (Sin Shell / No-Sudo) │ └──> Trabaja exclusivamente en: ├── /pimonitor/ (Código y BD) └── /var/log/pimonitor/ (Logs)

🧰 Requisitos de Despliegue
1. Crear el usuario del sistema aislado
Por seguridad, el demonio no debe tener acceso a una shell interactiva:

sudo useradd -r -s /bin/false pimonitor
🧰 Configuración del directorio principal del servicio
sudo mkdir -p /etc/pimonitor sudo chown -R pimonitor:pimonitor /etc/pimonitor

🚀 Instalación y Puesta en Marcha Clonar el repositorio dentro de la carpeta del USB:

cd /usb
git clone [https://github.com/TU_USUARIO/pimonitor.git](https://github.com/TU_USUARIO/pimonitor.git)
cd pimonitor
Crear el Entorno Virtual (venv) e instalar dependencias:

python3 -m venv venv
venv/bin/pip install -r requirements.txt
Configurar el entorno: Crea un archivo .env en la raíz (ignorado en Git por seguridad) con tus claves:

FLASK_ENV=production
SECRET_KEY=tu_clave_secreta_aqui
⚙️ Configuración del Servicio (Systemd) Crea el archivo de configuración del demonio:

sudo nano /etc/systemd/system/pimonitor.service
Pega el siguiente contenido:

[Unit]
Description=Servicio PiMonitor
After=network.target local-fs.target

[Service]
User=pimonitor
Group=pimonitor
WorkingDirectory=/usb/pimonitor
ExecStart=/usb/pimonitor/venv/bin/python3 /usb/pimonitor/pimonitor.py
StandardOutput=append:/var/log/pimonitor/access.log
StandardError=append:/var/log/pimonitor/error.log
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
Habilitación definitiva:

# Directorio de logs con permisos para el usuario
sudo mkdir -p /var/log/pimonitor
sudo chown -R pimonitor:pimonitor /var/log/pimonitor

# Recarga y arranque de la aplicación
sudo systemctl daemon-reload
sudo systemctl enable pimonitor.service
sudo systemctl start pimonitor.service
Puedes verificar que el panel está corriendo seguro en segundo plano ejecutando service pimonitor status.

## ⚙️ Personalización de Servicios (Backend)

⚠️ **¡AVISO IMPORTANTE PARA CONTRIBUIDORES Y FORKS!** El backend de esta aplicación (`pimonitor.py`) está configurado para comprobar de forma específica los servicios activos en mi servidor local. Si clonas este repositorio o vas a realizar un despliegue (`push`), **debes editar el archivo de backend en Python** para adaptar la lista de servicios a los que tengas configurados en tu propia máquina.

Busca en el código `pimonitor.py` el array o la función encargada de supervisar los demonios del sistema y modifica los nombres (ej. `nginx`, `docker`, `smbd`) por los tuyos:

```python
# Ejemplo de la sección a modificar en pimonitor.py
SERVICIOS_A_MONITORIZAR = ['docker', 'squid', 'ssh', 'tu_servicio_aqui']
```
