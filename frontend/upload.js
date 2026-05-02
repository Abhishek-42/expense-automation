// Automatically use local backend if testing locally, or the EC2 Public IP if hosted online!
const API_URL = (window.location.protocol === 'file:' || window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
    ? 'http://127.0.0.1:8000'
    : `http://${window.location.hostname}:8000`;

// auth check
document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = 'index.html';
    }
});

// logout logic
function logout() {
    localStorage.removeItem('token');
    window.location.href = 'index.html';
}

// DOM elements
const uploadForm = document.getElementById('upload-form');
const fileInput = document.getElementById('csv-file');
const fileMsg = document.querySelector('.file-msg');
const uploadStatus = document.getElementById('upload-status');

// Update file name display when a file is selected
fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        fileMsg.textContent = e.target.files[0].name;
        fileMsg.style.color = 'var(--accent-blue)';
    } else {
        fileMsg.textContent = 'Choose a CSV file or drag it here';
        fileMsg.style.color = '';
    }
});

// upload csv
uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const btn = document.getElementById('upload-btn');
    btn.textContent = 'Analyzing...';
    btn.disabled = true;
    uploadStatus.textContent = 'Uploading your transactions...';
    uploadStatus.className = 'status-msg';

    const file = fileInput.files[0];
    if (!file) {
        btn.textContent = 'Upload & Analyze';
        btn.disabled = false;
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    const token = localStorage.getItem('token');

    try {
        const response = await fetch(`${API_URL}/upload/transactions`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            uploadStatus.textContent = `Done! Successfully processed ${data.processed || 0} transactions. Redirecting...`;
            uploadStatus.className = 'status-msg status-success';

            // Head back to dashboard
            setTimeout(() => {
                window.location.href = 'dashboard.html';
            }, 1500);
        } else {
            uploadStatus.textContent = data.error || data.detail || 'Upload failed.';
            uploadStatus.className = 'status-msg status-error';
        }
    } catch (err) {
        uploadStatus.textContent = 'Failed to communicate with the server.';
        uploadStatus.className = 'status-msg status-error';
    } finally {
        if (btn) {
            btn.textContent = 'Upload & Analyze';
            btn.disabled = false;
        }
    }
});
