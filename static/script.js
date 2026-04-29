function updateDashboard() {
    fetch('/data')
        .then(res => res.json())
        .then(data => {
            // Métricas superiores
            document.getElementById('temp').innerText = data.temperature + "°C";
            document.getElementById('cpu').innerText = data.cpu + "%";
            document.getElementById('ram').innerText = data.ram + "%";

            // Render de Proxies
            const pContainer = document.getElementById('proxy-container');
            pContainer.innerHTML = data.proxies.map(p => `
                <div class="service-item ${p.status === 'active' ? 'status-active' : 'status-inactive'}">
                    <span>${p.name}</span>
                    <span class="status-dot">${p.status.toUpperCase()}</span>
                </div>
            `).join('');

            // Render de Servidores del Sistema
            const sContainer = document.getElementById('services-container');
            let sHtml = '<h3 style="grid-column: 1/-1; margin-bottom: 10px;">Servidores del Sistema</h3>';
            for (const [name, status] of Object.entries(data.services)) {
                const sClass = status === 'active' ? 'status-active' : 'status-inactive';
                sHtml += `
                    <div class="service-item ${sClass}">
                        <span>${name.toUpperCase()}</span>
                        <span class="status-dot">${status.toUpperCase()}</span>
                    </div>
                `;
            }
            sContainer.innerHTML = sHtml;
        });
}

setInterval(updateDashboard, 5000);
updateDashboard();