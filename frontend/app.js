// Configuration
const API_URL = 'http://127.0.0.1:8000';

// DOM Elements
const authContainer = document.getElementById('auth-container');
const dashboardContainer = document.getElementById('dashboard-container');
const loginForm = document.getElementById('login-form');
const registerForm = document.getElementById('register-form');
const uploadForm = document.getElementById('upload-form');
const notification = document.getElementById('notification');
const fileInput = document.getElementById('csv-file');
const fileMsg = document.querySelector('.file-msg');
const uploadStatus = document.getElementById('upload-status');

// Check Initial Auth State
document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('token');
    if (token) {
        showDashboard();
    }
});

// UI Helpers
function switchTab(tab) {
    document.getElementById('tab-login').classList.remove('active');
    document.getElementById('tab-register').classList.remove('active');
    loginForm.classList.add('hidden');
    registerForm.classList.add('hidden');
    hideNotification();

    if (tab === 'login') {
        document.getElementById('tab-login').classList.add('active');
        loginForm.classList.remove('hidden');
    } else {
        document.getElementById('tab-register').classList.add('active');
        registerForm.classList.remove('hidden');
    }
}

function showNotification(msg, type = 'error') {
    notification.textContent = msg;
    notification.className = `notification ${type}`;
    notification.classList.remove('hidden');
}

function hideNotification() {
    notification.classList.add('hidden');
}

function showDashboard() {
    authContainer.classList.add('hidden');
    dashboardContainer.classList.remove('hidden');
    hideNotification();
}

function logout() {
    localStorage.removeItem('token');
    dashboardContainer.classList.add('hidden');
    authContainer.classList.remove('hidden');
    switchTab('login');
}

// Update file input text when a file is selected
fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        fileMsg.textContent = e.target.files[0].name;
    } else {
        fileMsg.textContent = 'Choose a CSV file or drag it here';
    }
});

// --- API Calls ---

// Register
registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    hideNotification();

    const username = document.getElementById('reg-username').value;
    const password = document.getElementById('reg-password').value;

    try {
        const response = await fetch(`${API_URL}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (response.ok) {
            showNotification('Registration successful! Please log in.', 'success');
            setTimeout(() => switchTab('login'), 2000);
        } else {
            showNotification(data.error || 'Registration failed');
        }
    } catch (err) {
        showNotification('Failed to connect to server');
    }
});

// Login
loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    hideNotification();

    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;

    // FastAPI's OAuth2 expects x-www-form-urlencoded data
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    try {
        const response = await fetch(`${API_URL}/token`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            // Save the JWT token exactly where the browser can find it later
            localStorage.setItem('token', data.access_token);
            showDashboard();
        } else {
            // FastAPI's OAuth2PasswordRequestForm throws a 400 with a "detail" key for bad passwords.
            showNotification(data.detail || data.error || 'Incorrect username or password');
        }
    } catch (err) {
        showNotification('Failed to connect to server');
    }
});

// Upload CSV File
uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    uploadStatus.textContent = "Uploading...";
    uploadStatus.className = 'status-msg';

    const file = fileInput.files[0];
    if (!file) return;

    // Prepare the file as multipart/form-data
    const formData = new FormData();
    formData.append('file', file);

    // Retrieve our secure keycard
    const token = localStorage.getItem('token');

    try {
        const response = await fetch(`${API_URL}/upload/transactions`, {
            method: 'POST',
            headers: {
                // Attach the JWT Token in the Authorization header
                'Authorization': `Bearer ${token}`
                // Do NOT set Content-Type manually when using FormData, 
                // the browser calculates the boundary automatically.
            },
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            uploadStatus.textContent = "Processing complete! Redirecting to dashboard...";
            uploadStatus.className = 'status-msg status-success';

            // Redirect to the dedicated dashboard page after 1.5 seconds
            setTimeout(() => {
                window.location.href = 'dashboard.html';
            }, 1500);
        } else {
            uploadStatus.textContent = data.error || data.detail || 'Upload failed.';
            uploadStatus.className = 'status-msg status-error';
            // If the token expired or is invalid, force a logout
            if (response.status === 401) {
                setTimeout(() => logout(), 2000);
            }
        }
    } catch (err) {
        uploadStatus.textContent = 'Failed to communicate with the server.';
        uploadStatus.className = 'status-msg status-error';
    }
});

