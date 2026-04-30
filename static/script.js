function getStatusClass(status) {
    const s = status.toLowerCase();
    if (s === 'active' || s === 'running') return 'status-active';
    if (s === 'inactive' || s === 'dead') return 'status-stop';
    if (s === 'failed' || s === 'error') return 'status-error';
    return 'status-stop'; // Por si acaso
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
            document.getElementById('temp').innerText = (data.temperature || "N/A") + "°C";
            document.getElementById('cpu').innerText = (data.cpu || "0") + "%";
            document.getElementById('ram').innerText = (data.ram || "0") + "%";

            // 2. Render de Servicios (Unificado)
            const sContainer = document.getElementById('services-container');
            if (!sContainer) return;

            let sHtml = '<h3 style="grid-column: 1/-1; text-align: left; color: #888; margin-bottom: 10px;">Estado de los Servicios</h3>';
            
            // Verificamos que 'services' exista para evitar el error de 'undefined'
            if (data.services) {
                for (const [name, status] of Object.entries(data.services)) {
                    const sClass = getStatusClass(status);
                    sHtml += `
                        <div class="service-item ${sClass}">
                            <span>${name.toUpperCase()}</span>
                            <span class="status-dot">${status.toUpperCase()}</span>
                        </div>
                    `;
                }
            } else {
                sHtml += '<p>No se encontraron servicios.</p>';
            }
            
            sContainer.innerHTML = sHtml;
        })
        .catch(err => console.error("Error al obtener datos:", err));
}

setInterval(updateDashboard, 5000);
updateDashboard();