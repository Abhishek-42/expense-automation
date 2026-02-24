const API_URL = 'http://127.0.0.1:8000';

const subsList = document.getElementById('subs-list');
const loadingMsg = document.getElementById('subs-loading');
const errorMsg = document.getElementById('subs-error');
const monthlyTotalEl = document.getElementById('monthly-total');

// Ensure the user is still logged in before trying to fetch sensitive data
document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('token');
    if (!token) {
        // Kick them back to login if they have no token
        window.location.href = 'index.html';
        return;
    }

    fetchSubscriptions(token);
});

function logout() {
    localStorage.removeItem('token');
    window.location.href = 'index.html';
}

async function fetchSubscriptions(token) {
    try {
        const response = await fetch(`${API_URL}/subscriptions`, {
            method: 'GET',
            headers: { 'Authorization': `Bearer ${token}` }
        });

        const data = await response.json();

        // Hide loading text
        loadingMsg.classList.add('hidden');

        if (response.ok) {
            populateTable(data.subscriptions);
        } else {
            showError("Failed to load your subscriptions. Your session may have expired.");
            if (response.status === 401) {
                setTimeout(logout, 2500);
            }
        }
    } catch (err) {
        loadingMsg.classList.add('hidden');
        showError("Unable to connect to the backend server. Is API running?");
    }
}

function populateTable(subscriptions) {
    if (!subscriptions || subscriptions.length === 0) {
        subsList.innerHTML = `
            <tr>
                <td colspan="5" style="text-align:center; padding: 2rem; color: var(--text-secondary);">
                    We haven't detected any recurring subscriptions yet.<br>
                    Try uploading more bank transactions!
                </td>
            </tr>
        `;
        return;
    }

    let monthlyTotal = 0;

    subscriptions.forEach(sub => {
        // Calculate estimated monthly impact
        // If billing cycle is ~30 days, we add the full amount. 
        // If it's weekly (~7 days), we multiply by 4 to get the monthly impact.
        let monthlyImpact = parseFloat(sub.average_amount);
        if (sub.billing_cycle_days < 20) {
            monthlyImpact = monthlyImpact * (30 / sub.billing_cycle_days);
        }
        monthlyTotal += monthlyImpact;

        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td style="font-weight: 600;">${sub.merchant_name}</td>
            <td style="color: var(--success-color);">$${parseFloat(sub.average_amount).toFixed(2)}</td>
            <td>Every ${sub.billing_cycle_days} days</td>
            <td>${sub.last_payment_date}</td>
            <td>
                <button class="secondary-btn" style="padding: 5px 10px; font-size: 12px; border-color: var(--error-color); color: var(--error-color);">
                    Remove
                </button>
            </td>
        `;
        subsList.appendChild(tr);
    });

    // Update the total at the top of the dashboard
    monthlyTotalEl.textContent = `$${monthlyTotal.toFixed(2)}`;
}

function showError(msg) {
    errorMsg.textContent = msg;
    errorMsg.classList.remove('hidden');
}
