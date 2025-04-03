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

            // Anzeige der belegten Stationen:
            document.getElementById("occupied_stations_count").textContent = data.occupied_stations;

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

            // Aktualisiert die Liste der geplanten Verlassenszeiten
            let estimatedList = document.getElementById("estimated_times");
            estimatedList.innerHTML = "";

            if (Array.isArray(data.estimated_times)) {
                data.estimated_times.forEach(time => {
                    let li = document.createElement("li");
                    li.textContent = time + " Uhr";
                    estimatedList.insertBefore(li, estimatedList.firstChild);
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

    console.log("Sende Daten:", { station: station, leave_time: leaveTime });

    fetch("/set_leave_time", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ station: station, leave_time: leaveTime })
    })
    .then(response => response.json())
    .then(data => {
        console.log("Server-Antwort:", data);  // Antwort des Servers anzeigen
        if (data.error) {
            alert(data.error);  // Fehler anzeigen, falls Station nicht belegt
        } else {
            alert("Verlassenszeit gespeichert!");
        }
    })
    .catch(error => {
        console.error("Fehler:", error);
        alert("Es gab einen Fehler bei der Anfrage!");
    });
}

function personalizeRFID() {
    let rfid = document.getElementById("rfid_input").value;
    let name = document.getElementById("name_input").value;

    if (!rfid || !name) {
        alert("Bitte sowohl RFID als auch Name eingeben!");
        return;
    }

    fetch("/personalize_rfid", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rfid: rfid, name: name })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
        } else {
            alert(data.message);
        }
    })
    .catch(error => {
        console.error("Fehler:", error);
        alert("Es gab einen Fehler bei der Anfrage!");
    });
}

function checkUID(uid) {
    fetch("/check_uid", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ uid: uid })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === "unknown") {
            // Zeige Eingabefeld für unbekannte UID
            document.getElementById("personalize_section").style.display = "block";
            document.getElementById("unknown_uid").textContent = data.uid;
        } else if (data.status === "known") {
            alert(`UID ${data.uid} gehört zu ${data.name}`);
        }
    })
    .catch(error => {
        console.error("Fehler beim Überprüfen der UID:", error);
    });
}

function saveName() {
    let uid = document.getElementById("unknown_uid").textContent;
    let name = document.getElementById("name_input").value;

    if (!name) {
        alert("Bitte einen Namen eingeben!");
        return;
    }

    fetch("/save_name", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ uid: uid, name: name })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
        } else {
            alert(data.message);
            document.getElementById("personalize_section").style.display = "none";
        }
    })
    .catch(error => {
        console.error("Fehler beim Speichern des Namens:", error);
    });
}

updateStatus(); // Erstes Update sofort ausführen
