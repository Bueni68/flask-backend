export function sendLeaveTime() {
    const station = document.getElementById("station_select").value;
    const leaveTime = document.getElementById("leave_time").value;

    if (!station || !leaveTime) {
        alert("Bitte Station und Uhrzeit auswählen!");
        return;
    }

    fetch("/set_leave_time", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ station, leave_time: leaveTime })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
        } else {
            alert("Verlassenszeit gespeichert!");
        }
    })
    .catch(err => {
        console.error("Fehler:", err);
        alert("Fehler bei der Anfrage!");
    });
}
