import { updateStatus, setFormVisible, setStatusTimeout, getStatusTimeout } from './status.js';

let countdownInterval;
let tempUserTimeout = null;

export function showFullNameForm(tempUserId) {
    setFormVisible(true);
    if (getStatusTimeout()) {
        clearTimeout(getStatusTimeout());
        setStatusTimeout(null);
    }

    const formContainer = document.getElementById('fullNameFormContainer');
    formContainer.style.display = 'flex';

    startCountdown(120);

    tempUserTimeout = setTimeout(() => deleteTempUser(), 120000);

    const form = document.getElementById('fullNameForm');
    form.onsubmit = function (event) {
        event.preventDefault();
        clearTimeout(tempUserTimeout);

        const fullName = document.getElementById('fullName').value;
        fetch('/save_user', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ temp_user_id: tempUserId, full_name: fullName })
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === 'user_saved') {
                alert('User gespeichert!');
                hideFullNameForm();
            }
        })
        .catch(console.error);
    }
}

function startCountdown(seconds) {
    let remaining = seconds;
    document.getElementById('counter').textContent = remaining;
    if (countdownInterval) clearInterval(countdownInterval);

    countdownInterval = setInterval(() => {
        remaining--;
        document.getElementById('counter').textContent = remaining;
        if (remaining <= 0) {
            clearInterval(countdownInterval);
            hideFullNameForm();
        }
    }, 1000);
}

export function hideFullNameForm() {
    document.getElementById('fullNameFormContainer').style.display = 'none';
    setFormVisible(false);
    clearInterval(countdownInterval);
    updateStatus()
}

export function deleteTempUser() {
    fetch('/delete_temp_user', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(res => res.json())
    .then(data => console.log("TempUser gelöscht:", data));
    hideFullNameForm();
}
