/* ============================================================
   APP.JS — Auth & Onboarding Logic
   
   FLOW:
   1. If user already has a token → redirect to dashboard.html
   2. Login → get token → redirect to dashboard.html
   3. Register → auto-login → show one-time CSV upload → dashboard.html
   4. Upload is ONLY shown once after registration (onboarding)
   ============================================================ */

// Automatically use local backend if testing locally, or the EC2 Public IP if hosted online!
const API_URL = (window.location.protocol === 'file:' || window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
    ? 'http://127.0.0.1:8000'
    : `http://${window.location.hostname}:8000`;

// ── DOM References ──────────────────────────────────────
const authLayout        = document.getElementById('auth-layout');
const onboardingPanel   = document.getElementById('onboarding-panel');
const loginForm         = document.getElementById('login-form');
const registerForm      = document.getElementById('register-form');
const uploadForm        = document.getElementById('upload-form');
const notification      = document.getElementById('notification');
const fileInput         = document.getElementById('csv-file');
const fileMsg           = document.querySelector('.file-msg');
const uploadStatus      = document.getElementById('upload-status');


// ── Auth Guard ──────────────────────────────────────────
// If user is already logged in, send them straight to the dashboard.
document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('token');
    if (token) {
        window.location.href = 'dashboard.html';
    }
});


// ══════════════════════════════════════════════════════════
//  UI HELPERS
// ══════════════════════════════════════════════════════════

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

// Transition from auth screen → onboarding upload screen
function showOnboarding() {
    authLayout.classList.add('hidden');
    onboardingPanel.classList.remove('hidden');
}

// Skip onboarding and go straight to dashboard
function skipOnboarding() {
    window.location.href = 'dashboard.html';
}

// Update file name display when a file is selected
fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        fileMsg.textContent = e.target.files[0].name;
        fileMsg.style.color = 'var(--accent-blue-light)';
    } else {
        fileMsg.textContent = 'Choose a CSV file or drag it here';
        fileMsg.style.color = '';
    }
});


// ══════════════════════════════════════════════════════════
//  API: REGISTER
//  On success: auto-login the user, then show the
//  one-time onboarding CSV upload panel.
// ══════════════════════════════════════════════════════════

registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    hideNotification();

    const btn = document.getElementById('register-btn');
    btn.textContent = 'Creating account...';
    btn.disabled = true;

    const username = document.getElementById('reg-username').value;
    const email = document.getElementById('reg-email').value;
    const password = document.getElementById('reg-password').value;

    try {
        // Step 1: Register the user
        const regResponse = await fetch(`${API_URL}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password })
        });

        const regData = await regResponse.json();

        if (!regResponse.ok) {
            showNotification(regData.error || 'Registration failed');
            return;
        }

        // Step 2: Auto-login immediately after registration
        const loginData = new URLSearchParams();
        loginData.append('username', username);
        loginData.append('password', password);

        const loginResponse = await fetch(`${API_URL}/token`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: loginData
        });

        const tokenData = await loginResponse.json();

        if (loginResponse.ok) {
            // Save the JWT token
            localStorage.setItem('token', tokenData.access_token);
            // Show the one-time onboarding upload screen
            showOnboarding();
        } else {
            // Registration succeeded but auto-login failed — fall back to login tab
            showNotification('Account created! Please sign in.', 'success');
            setTimeout(() => switchTab('login'), 1500);
        }

    } catch (err) {
        showNotification('Failed to connect to server');
    } finally {
        btn.textContent = 'Create Account';
        btn.disabled = false;
    }
});


// ══════════════════════════════════════════════════════════
//  API: LOGIN
//  On success: store token and redirect straight to dashboard.
//  NO upload prompt for returning users.
// ══════════════════════════════════════════════════════════

loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    hideNotification();

    const btn = document.getElementById('login-btn');
    btn.textContent = 'Signing in...';
    btn.disabled = true;

    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;

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
            localStorage.setItem('token', data.access_token);
            // Returning users go directly to the dashboard — no upload
            window.location.href = 'dashboard.html';
        } else {
            showNotification(data.detail || data.error || 'Incorrect username or password');
        }
    } catch (err) {
        showNotification('Failed to connect to server');
    } finally {
        btn.textContent = 'Sign In';
        btn.disabled = false;
    }
});


// ══════════════════════════════════════════════════════════
//  API: UPLOAD CSV (Onboarding — One-Time)
//  This form only appears after a fresh registration.
// ══════════════════════════════════════════════════════════

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
            uploadStatus.textContent = `Done — ${data.subscriptions_detected || 0} subscriptions detected. Redirecting...`;
            uploadStatus.className = 'status-msg status-success';

            // Head to dashboard after a brief success message
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
        btn.textContent = 'Upload & Analyze';
        btn.disabled = false;
    }
});
