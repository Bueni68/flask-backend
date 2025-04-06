import { updateStatus } from './status.js';
import { showFullNameForm, deleteTempUser } from './tempUserForm.js';
import { sendLeaveTime } from './leaveTime.js';

window.addEventListener('DOMContentLoaded', () => {
    updateStatus(showFullNameForm);

    // Eventlistener für Button, falls vorhanden
    const sendButton = document.getElementById('sendLeaveTimeButton');
    if (sendButton) {
        sendButton.addEventListener('click', sendLeaveTime);
    }
    
    const deleteButton = document.getElementById('deleteTempUserButton');
    if (deleteButton) {
        deleteButton.addEventListener('click', deleteTempUser);
    }
});
