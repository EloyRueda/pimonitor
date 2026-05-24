# 📊 PiMonitor Dashboard

PiMonitor es un panel de control web ligero y reactivo desarrollado en **Python (Flask)** para monitorizar el estado de salud de una Raspberry Pi en tiempo real. 

El proyecto está diseñado de forma robusta bajo el **principio de menor privilegio**, ejecutándose de forma totalmente aislada bajo su propio usuario del sistema sin privilegios de administración (`sudo`).

---

## ⚡ Características Principales

* **Métricas en tiempo real:** Carga de CPU, uso de memoria RAM, temperatura del procesador y estado del almacenamiento.
* **Gestión de almacenamiento doble:** Lectura independiente de la tarjeta MicroSD principal y de unidades de almacenamiento externo (USB).
* **Monitorización de Servicios:** Supervisión de servicios locales (Docker, Nginx, Apache, Proxy, etc.).
* **Arquitectura Hardened:** El proceso corre aislado del usuario administrador (`admin1`) y de `root`.

---

## 🛡️ Arquitectura de Seguridad (Aislamiento)

Para evitar que una vulnerabilidad en la aplicación web comprometa la Raspberry Pi, el servicio se ejecuta bajo el demonio dedicado `pimonitor`, el cual solo tiene permisos de lectura/escritura en su propio directorio de trabajo dentro del almacenamiento externo.
