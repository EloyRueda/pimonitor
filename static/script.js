function getStatusClass(status) {
    const s = status.toLowerCase();
    if (s === 'active' || s === 'running') return 'status-active';
    if (s === 'inactive' || s === 'dead') return 'status-stop';
    if (s === 'failed' || s === 'error') return 'status-error';
    return 'status-stop';
}

function getStatusClass(status) {
    if (!status) return 'status-stop';
    const s = status.toLowerCase();
    if (s === 'active' || s === 'running') return 'status-active';
    if (s === 'inactive' || s === 'dead') return 'status-stop';
    if (s === 'failed' || s === 'error') return 'status-error';
    return 'status-stop';
}

function updateDashboard() {
    fetch('/data')
        .then(res => {
            if (!res.ok) throw new Error("Error en la respuesta del servidor");
            return res.json();
        })
        .then(data => {
            // 1. Actualizar Métricas
            const elTemp = document.getElementById('temp');
            const elCpu = document.getElementById('cpu');
            const elRam = document.getElementById('ram');
            const elSwap = document.getElementById('swap');
            const elDisk = document.getElementById('disk');
            const elUsb = document.getElementById('usb');

            if(elTemp) elTemp.innerText = (data.temperature || "N/A") + "°C";
            if(elCpu) elCpu.innerText = (data.cpu || "0") + "%";
            if(elRam) elRam.innerText = (data.ram || "0") + "%";
            if(elSwap) elSwap.innerText = (data.swap_usage || "0") + "%";
            if(elDisk) elDisk.innerText = (data.disk_usage || "0") + "%";
            if(elUsb) elUsb.innerText = (data.usb_usage || "0") + "%";

            // 2. Render de Servicios
            const tablaServicios = document.getElementById('lista-servicios');

            if (tablaServicios) {
                let sHtml = '';

                // Verificar que 'services' exista y tenga datos
                if (data.services && Object.keys(data.services).length > 0) {
                    for (const [name, status] of Object.entries(data.services)) {
                        const sClass = getStatusClass(status); // Obtiene status-active, status-stop, etc.

                        sHtml += `
                            <tr style="border-bottom: 1px solid #2d3748; height: 45px;">
                                <td style="font-weight: bold; color: #fff; text-transform: uppercase;">${name}</td>
                                <td>
                                    <span class="status-dot ${sClass}" style="padding: 4px 10px; border-radius: 6px; font-size: 0.8em; color: #fff; display: inline-block;">
                                        ${status.toUpperCase()}
                                    </span>
                                </td>
                                <td style="text-align: right; color: #a6adc8; font-size: 0.85em;">
                                    systemd
                                </td>
                            </tr>
                        `;
                    }
                }
		else {
                    sHtml = '<tr><td colspan="3" style="padding: 15px 0; text-align: center; color: #718096;">No se encontraron servicios.</td></tr>';
                }
                tablaServicios.innerHTML = sHtml;
            }

            // 3. Actualizar velocidades de Red (Fuera del bloque anterior para asegurar que siempre corra)
            const elDescarga = document.getElementById('red-descarga');
            const elSubida = document.getElementById('red-subida');
            if (elDescarga) elDescarga.innerText = formatearVelocidad(data.red_descarga);
            if (elSubida) elSubida.innerText = formatearVelocidad(data.red_subida);
        })
        .catch(err => console.error("Error al obtener datos:", err));
}

// Función auxiliar para que la interfaz pase automáticamente de KB/s a MB/s
function formatearVelocidad(kbps) {
    if (kbps >= 1024) {
        return (kbps / 1024).toFixed(2) + ' MB/s';
    }
    return kbps.toFixed(2) + ' KB/s';
}

function actualizarDispositivosRed() {
    fetch('/api/network-hosts')
    .then(response => {
        if (!response.ok) throw new Error('Error al escanear');
        return response.json();
    })
    .then(data => {
        const tbody = document.getElementById('lista-hosts');
        tbody.innerHTML = '';

        if (!data.hosts || data.hosts.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" style="padding: 15px 0; text-align: center;">No se detectaron otros equipos activos.</td></tr>';
            return;
        }
        data.hosts.sort((a, b) => a.ip.localeCompare(b.ip, undefined, { numeric: true }));

        data.hosts.forEach(host => {
            tbody.innerHTML += `
                <tr style="border-bottom: 1px solid #2d3748; height: 45px;">
                    <td style="font-weight: bold; color: #fff;">${host.ip}</td>
                    <td style="color: #63b3ed; font-size: 0.9em;">${host.vendor}</td> <td style="font-family: monospace; color: #cbd5e1; letter-spacing: 0.5px;">${host.mac}</td>
                    <td style="text-align: right;">
                        <span class="status-dot status-active" style="padding: 4px 10px; border-radius: 6px; font-size: 0.8em; color: #fff;">ONLINE</span>
                    </td>
                </tr>
                `;
        });
    })
    .catch(error => {
        console.error('Error de red:', error);
        document.getElementById('lista-hosts').innerHTML = `<tr><td colspan="4" style="padding: 15px 0; text-align: center; color: #e53e3e;">Error al compilar la tabla ARP del sistema</td></tr>`;
    });
}

// Ejecutar el escáner al cargar la página por primera vez
actualizarDispositivosRed();

setInterval(updateDashboard, 5000);
// Refrescar de forma pasiva cada 10 minutos (600000 ms) para no sobrecargar el servidor
setInterval(actualizarDispositivosRed, 600000);
updateDashboard();
