function updateStatus() {
    fetch("/status")
        .then(response => response.json())
        .then(data => {
            let statusDiv = document.getElementById("status");
            statusDiv.innerHTML = ""; 

            let stations = ["Station 1", "Station 2", "Station 3", "Station 4"];
            stations.forEach(station => {
                let div = document.createElement("div");
                
                // Station-Status holen oder "unbekannt" setzen
                let status = data.stations[station] || "unbekannt";
                
                // CSS-Klasse setzen (falls unbekannt, neutral lassen)
                div.className = `station ${status === "belegt" || status === "frei" ? status : ""}`;
                
                // Textinhalt setzen
                div.textContent = `${station}: ${status}`;
                
                // Div zur Webseite hinzufügen
                statusDiv.appendChild(div);
            });

            document.getElementById("people_count").textContent = data.people_count;

            let historyList = document.getElementById("history");
            historyList.innerHTML = ""; 

            data.history.forEach(entry => {
                let li = document.createElement("li");
                li.textContent = `${entry.name} - ${entry.station} (${entry.action}) um ${entry.timestamp}`;
                historyList.appendChild(li);
            });
        });
}

setInterval(updateStatus, 5004);
updateStatus();


