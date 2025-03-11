function updateStatus() {
    fetch("/status")
        .then(response => response.json())
        .then(data => {
            let statusDiv = document.getElementById("status");
            statusDiv.innerHTML = "";

            let stations = Object.keys(data.stations);
            stations.forEach(station => {
                let div = document.createElement("div");

                // Station-Status holen oder "unbekannt" setzen
                let status = data.stations[station] || "unbekannt";

                // CSS-Klasse setzen (falls unbekannt, neutral lassen)
                div.className = `station ${status}`;

                // Textinhalt setzen
                div.textContent = `${station}: ${status}`;

                // Div zur Webseite hinzufügen
                statusDiv.appendChild(div);
            });

            document.getElementById("people_count").textContent = data.people_count;

            let historyList = document.getElementById("history");
            historyList.innerHTML = "";

            if (Array.isArray(data.history)) {
                data.history.forEach(entry => {
                    let li = document.createElement("li");
                    li.textContent = `${entry.name} - ${entry.station} (${entry.action}) um ${entry.timestamp}`;
                    historyList.appendChild(li);
                });
            } else {
                historyList.innerHTML = "<li>Keine Historie vorhanden</li>";
            }

            // 🔴 Aktualisiert die Liste der geplanten Verlassenszeiten
            let estimatedList = document.getElementById("estimated_times");
            estimatedList.innerHTML = "";

            if (Array.isArray(data.estimated_times)) {
                data.estimated_times.forEach(time => {
                    let li = document.createElement("li");
                    li.textContent = `Station wird frei um ca. ${time}`;
                    estimatedList.appendChild(li);
                });
            } else {
                estimatedList.innerHTML = "<li>Keine geplanten Zeiten</li>";
            }
        })
        .catch(error => console.error("Fehler beim Abrufen der Daten:", error))
        .finally(() => {
            setTimeout(updateStatus, 5000); // Warte 5 Sekunden, bevor das nächste Update kommt
        });
}

// 🔹 Funktion zum Speichern der geplanten Verlassenszeit
function sendLeaveTime() {
    let station = document.getElementById("station_select").value;
    let leaveTime = document.getElementById("leave_time").value;

    if (!station) {
        alert("Bitte eine Station auswählen!");
        return;
    }
    if (!leaveTime) {
        alert("Bitte eine Uhrzeit eingeben!");
        return;
    }

    console.log("Sende Daten:", { station: station, leave_time: leaveTime });  // Ausgabe der zu sendenden Daten

    fetch("/set_leave_time", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ station: station, leave_time: leaveTime })
    })
    .then(response => response.json())
    .then(data => {
        console.log("Server-Antwort:", data);  // Antwort des Servers anzeigen
        if (data.error) {
            alert(data.error);  // Fehler anzeigen, falls die Station nicht belegt ist
        } else {
            alert("Verlassenszeit gespeichert!");
        }
    })
    .catch(error => {
        console.error("Fehler:", error);
        alert("Es gab einen Fehler bei der Anfrage!");
    });
}

updateStatus(); // Erstes Update sofort ausführen





