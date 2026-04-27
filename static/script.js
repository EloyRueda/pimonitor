async function updateStatus() {
    const container = document.getElementById('services-container');
    const tempElement = document.getElementById('temp');

    // Si el HTML aún no está listo, salir silenciosamente
    if (!container || !tempElement){
        return;
    }

    try {
        const response = await fetch('/data');
        const data = await response.json();
        document.getElementById('temp').innerText = data.temperature + "°C";
        document.getElementById('cpu').innerText = data.cpu + "%";
        document.getElementById('ram').innerText = data.ram + "%";

        // Actualizar temperatura
        tempElement.innerText = data.temperature + "°C";
        tempElement.innerText = data.temperature + "°C";
        tempElement.innerText = data.temperature + "°C";

        // Cambiar color si el uso es muy alto (>80%)
        document.getElementById('cpu').style.color = data.cpu > 80 ? '#ff6666' : '#fff';
        document.getElementById('ram').style.color = data.ram > 80 ? '#ff6666' : '#fff';

        // Limpiar y rellenar servicios
        container.innerHTML = ""; 

        for (const [name, status] of Object.entries(data.services)) {
            const card = document.createElement('div');
            // Usamos las clases que definimos en el CSS
            card.className = `status-card ${status === 'active' ? 'online' : 'offline'}`;
            card.style.padding = "10px";
            card.style.margin = "10px auto";
            card.style.width = "80%";
            card.style.borderRadius = "5px";
            
            card.innerHTML = `<strong>${name.toUpperCase()}</strong>: ${status}`;
            container.appendChild(card);
        }
    } catch (e) { 
        console.error("Error en la actualización:", e); 
    }
}

// Ejecutar cuando el DOM esté totalmente cargado
document.addEventListener('DOMContentLoaded', () => {
    setInterval(updateStatus, 5000);
    updateStatus();
});