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
            const sContainer = document.getElementById('services-container');
            if (!sContainer) return;

            let sHtml = '<h3 style="grid-column: 1/-1; text-align: left; color: #888; margin-bottom: 10px; text-align: center"></h3>';

            // Verificamos que 'services' exista para evitar el error de 'undefined'
            if (data.services && Object.keys(data.services).length > 0) {
                for (const [name, status] of Object.entries(data.services)) {
                    const sClass = getStatusClass(status);
                    sHtml += `
                        <div class="service-item ${sClass}">
                            <span>${name.toUpperCase()}</span>
                            <span class="status-dot">${status.toUpperCase()}</span>
                        </div>
                    `;
                 }
            }
    	    else {
                sHtml += '<p>No se encontraron servicios.</p>';
            }

            document.getElementById('red-descarga').innerText = formatearVelocidad(data.red_descarga);
            document.getElementById('red-subida').innerText = formatearVelocidad(data.red_subida);

            sContainer.innerHTML = sHtml;
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

setInterval(updateDashboard, 5000);
updateDashboard();
