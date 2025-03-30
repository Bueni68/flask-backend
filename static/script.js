function updateStatus() {
    fetch("/status")
        .then(response => response.json())
        .then(data => {
            console.log("Empfangene Daten:", data); // Debugging

            let statusDiv = document.getElementById("status");
            statusDiv.innerHTML = "";

            if (!data.stations) {
                console.error("Fehler: 'stations' ist undefined!");
                statusDiv.innerHTML = "<p>Fehler: Keine Stationsdaten vorhanden.</p>";
                return;
            }

            Object.entries(data.stations).forEach(([station, info]) => {
                let div = document.createElement("div");
                div.className = `${station} ${info.status}`;
                div.textContent = info.status === "belegt"
                    ? `${station}: ${info.status} - Benutzer: ${info.name}`
                    : `${station}: ${info.status}`;
                statusDiv.appendChild(div);
            });

            if (data.lastDetectedCard) {
                document.getElementById("card_uid").value = data.lastDetectedCard; // Setze die UID im readonly-Feld
            }
            
            document.getElementById("occupied_stations_count").textContent = data.occupied_stations || 0;

            let historyList = document.getElementById("history");
            historyList.innerHTML = "";
            if (Array.isArray(data.history)) {
                data.history.forEach(entry => {
                    let li = document.createElement("li");
                    li.textContent = `${entry.station} (${entry.action}) um ${entry.timestamp || "???"}`;
                    historyList.appendChild(li);
                });
            } else {
                historyList.innerHTML = "<li>Keine Historie vorhanden</li>";
            }

            let estimatedList = document.getElementById("estimated_times");
            estimatedList.innerHTML = "";
            if (Array.isArray(data.estimated_times)) {
                data.estimated_times.forEach(time => {
                    let li = document.createElement("li");
                    li.textContent = time;
                    estimatedList.appendChild(li);
                });
            } else {
                estimatedList.innerHTML = "<li>Keine geplanten Zeiten</li>";
            }
        })
        .catch(error => console.error("Fehler beim Abrufen der Daten:", error))
        .finally(() => {
            setTimeout(updateStatus, 5000); // Automatische Aktualisierung alle 5 Sekunden
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

    console.log("Sende Daten:", { station, leave_time: leaveTime });

    fetch("/set_leave_time", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ station, leave_time: leaveTime })
    })
    .then(response => response.json())
    .then(data => {
        alert(data.success || data.error);
    })
    .catch(error => {
        console.error("Fehler:", error);
        alert("Es gab einen Fehler bei der Anfrage!");
    });
}

// 🔹 Funktion zum Setzen des Kartennamens
function setCardName() {
    let cardUid = document.getElementById("card_uid").value;
    let cardName = document.getElementById("card_name").value;

    if (!cardUid || !cardName) {
        alert("Bitte UID und Name der Karte eingeben!");
        return;
    }

    console.log("Sende Kartennamen:", { card_uid: cardUid, name: cardName });

    fetch("/set_card_name", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ card_uid: cardUid, name: cardName })
    })
    .then(response => response.json())
    .then(data => {
        alert(data.success || data.error);
    })
    .catch(error => {
        console.error("Fehler:", error);
        alert("Es gab einen Fehler bei der Anfrage!");
    });
}

// Erstes Update sofort ausführen
updateStatus();





