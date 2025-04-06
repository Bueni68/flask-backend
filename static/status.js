let statusUpdateTimeout = null;
let isFullNameFormVisible = false;

export function setFormVisible(state) {
    isFullNameFormVisible = state;
}
export function getFormVisible() {
    return isFullNameFormVisible;
}
export function getStatusTimeout() {
    return statusUpdateTimeout;
}
export function setStatusTimeout(timeout) {
    statusUpdateTimeout = timeout;
}

export function updateStatus(showFullNameForm) {
    fetch("/status")
        .then(response => response.json())
        .then(data => {
            const statusDiv = document.getElementById("status");
            statusDiv.innerHTML = "";
            const stations = data.stations || [];

            if (stations.length === 0) {
                statusDiv.innerHTML = "<div class='station unknown'>Keine Stationen gefunden</div>";
                return;
            }

            stations.forEach(station => {
                const div = document.createElement("div");
                const status = station.status || "unbekannt";
                div.className = `station ${status}`;
                div.textContent = `${station.station}: ${status}`;
                statusDiv.appendChild(div);
            });

            document.getElementById("occupied_stations_count").textContent = data.occupied_stations;

            const historyList = document.getElementById("history");
            historyList.innerHTML = "";
            const lastFive = (data.history || []);
            if (lastFive.length === 0) {
                historyList.innerHTML = "<li>- Keine Einträge vorhanden -</li>";
            }
            lastFive.forEach(entry => {
                const li = document.createElement("li");
                let text = `${entry.userFullName} - ${entry.station} (${entry.action}) um ${entry.timestamp}`;
                if (entry.action === "verlassen" && entry.duration) {
                    text += ` – Genutzte Zeit: ${entry.duration}`;
                }
                li.textContent = text;
                li.style.color = entry.action === "betreten" ? "red" :
                                 entry.action === "verlassen" ? "green" : "gray";
                historyList.appendChild(li);
            });

            const estimatedList = document.getElementById("estimated_times");
            
            estimatedList.innerHTML = data.estimated_times.length > 0 ? "" : "<li>- Keine Einträge vorhanden -</li>";
            (data.estimated_times || []).forEach(time => {
                const li = document.createElement("li");
                li.textContent = `${time.station}: ${time.leave_time} Uhr`;
                estimatedList.insertBefore(li, estimatedList.firstChild);
            });
        })
        .catch(console.error);

    fetch('/temp_user_status')
        .then(res => res.json())
        .then(data => {
            if (data.temp_user_created) {
                showFullNameForm(data.temp_user_id);
            }
        })
        .catch(console.error)
        .finally(() => {
            if (!isFullNameFormVisible) {
                statusUpdateTimeout = setTimeout(() => updateStatus(showFullNameForm), 2000);
            }
        });
}
