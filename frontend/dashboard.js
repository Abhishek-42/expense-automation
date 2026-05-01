/* ============================================================
   DASHBOARD — Client Logic
   Handles: Auth guard, API fetch, table rendering, stats
   ============================================================ */

// Automatically use local backend if testing locally, or the EC2 Public IP if hosted online!
const API_URL = (window.location.protocol === 'file:' || window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
    ? 'http://127.0.0.1:8000'
    : `http://${window.location.hostname}:8000`;

// ── DOM References ──────────────────────────────────────
const subsList      = document.getElementById('subs-list');
const loadingMsg    = document.getElementById('subs-loading');
const errorMsg      = document.getElementById('subs-error');
const monthlyTotalEl = document.getElementById('monthly-total');
const subCountEl    = document.getElementById('sub-count');
const avgAmountEl   = document.getElementById('avg-amount');
const yearlyTotalEl = document.getElementById('yearly-total');


// ── Sanitize text before injecting into HTML ────────────
function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = String(str);
    return div.innerHTML;
}


// ── Currency Formatter (Indian Standard) ────────────────
// Formats numbers in the Indian numbering system:
//   1234567.89 → "12,34,567.89"
// Uses the built-in Intl API with 'en-IN' locale.
function formatINR(amount) {
    return amount.toLocaleString('en-IN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}


// ── Auth Guard ──────────────────────────────────────────
// If no JWT token exists, redirect to login immediately.
document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = 'index.html';
        return;
    }
    fetchSubscriptions(token);
});


// ── Logout ──────────────────────────────────────────────
function logout() {
    localStorage.removeItem('token');
    window.location.href = 'index.html';
}


// ── API: Fetch Subscriptions ────────────────────────────
async function fetchSubscriptions(token) {
    try {
        const response = await fetch(`${API_URL}/subscriptions`, {
            method: 'GET',
            headers: { 'Authorization': `Bearer ${token}` }
        });

        const data = await response.json();

        // Hide loading spinner
        loadingMsg.classList.add('hidden');

        if (response.ok) {
            renderTable(data.subscriptions);
        } else {
            showError('Failed to load subscriptions. Session may have expired.');
            if (response.status === 401) {
                setTimeout(logout, 2500);
            }
        }
    } catch (err) {
        loadingMsg.classList.add('hidden');
        showError('Unable to connect to the backend. Is the API running?');
    }
}


// ── Render: Confidence Dots ─────────────────────────────
// Visualizes detection confidence as a row of dots:
//   2 transactions  = 2 amber dots (low confidence)
//   3-4 transactions = 3 green dots (medium)
//   5+ transactions  = 5 green dots (high)
function renderConfidenceDots(txCount) {
    const level   = txCount >= 5 ? 5 : txCount >= 3 ? 3 : 2;
    const maxDots = 5;
    let html = '<div class="confidence-dots">';

    for (let i = 0; i < maxDots; i++) {
        if (i < level) {
            const cls = level <= 2 ? 'filled medium' : 'filled';
            html += `<span class="${cls}"></span>`;
        } else {
            html += '<span></span>';
        }
    }

    html += '</div>';
    return html;
}


// ── Render: Cycle Label ─────────────────────────────────
// Converts raw day-count into a human-readable frequency label.
function getCycleLabel(cycleDays) {
    const days = parseInt(cycleDays);
    if (days >= 28 && days <= 31) return 'Monthly';
    if (days >= 13 && days <= 15) return 'Bi-weekly';
    if (days >= 6  && days <= 8)  return 'Weekly';
    return `${days}d`;
}


// ── Render: Full Table ──────────────────────────────────
function renderTable(subscriptions) {

    // Handle empty state
    if (!subscriptions || subscriptions.length === 0) {
        subsList.innerHTML = `
            <tr>
                <td colspan="6">
                    <div class="empty-state">
                        <svg class="empty-state-icon" viewBox="0 0 24 24" fill="none"
                             stroke="currentColor" stroke-width="1.5">
                            <path stroke-linecap="round" stroke-linejoin="round"
                                d="M2.25 13.5h3.86a2.25 2.25 0 0 1 2.012 1.244l.256.512a2.25 2.25 0 0 0 2.013 1.244h3.218a2.25 2.25 0 0 0 2.013-1.244l.256-.512a2.25 2.25 0 0 1 2.013-1.244h3.859m-19.5.338V18a2.25 2.25 0 0 0 2.25 2.25h15A2.25 2.25 0 0 0 21.75 18v-4.162c0-.224-.034-.447-.1-.661L19.24 5.338a2.25 2.25 0 0 0-2.15-1.588H6.911a2.25 2.25 0 0 0-2.15 1.588L2.35 13.177a2.25 2.25 0 0 0-.1.661Z"/>
                        </svg>
                        <p>No recurring subscriptions detected yet.<br>
                        <a href="index.html">Upload more bank transactions</a> to improve detection.</p>
                    </div>
                </td>
            </tr>
        `;
        return;
    }

    // ── Calculate Stats ─────────────────────────────────
    let monthlyTotal = 0;

    subscriptions.forEach(sub => {
        let monthlyImpact = parseFloat(sub.average_amount);

        // Normalize non-monthly cycles to a monthly projection
        if (sub.billing_cycle_days < 20) {
            monthlyImpact = monthlyImpact * (30 / sub.billing_cycle_days);
        }
        monthlyTotal += monthlyImpact;

        // Build the table row
        const txCount = sub.confidence_based_on_tx_count || sub.original_transactions_count || 2;
        const tr = document.createElement('tr');

        tr.innerHTML = `
            <td><span class="merchant-name">${escapeHtml(sub.merchant_name)}</span></td>
            <td><span class="amount-cell">₹${formatINR(parseFloat(sub.average_amount))}</span></td>
            <td><span class="cycle-badge">${getCycleLabel(sub.billing_cycle_days)}</span></td>
            <td>${escapeHtml(sub.last_payment_date)}</td>
            <td>
                <div class="confidence-bar">
                    ${renderConfidenceDots(txCount)}
                </div>
            </td>
            <td>
                <button class="remove-btn">Remove</button>
            </td>
        `;

        subsList.appendChild(tr);
    });

    // ── Update Stat Cards ───────────────────────────────
    const subCount = subscriptions.length;
    const avgPerSub = subCount > 0 ? monthlyTotal / subCount : 0;
    const yearlyProjection = monthlyTotal * 12;

    monthlyTotalEl.textContent = `₹${formatINR(monthlyTotal)}`;
    subCountEl.textContent     = subCount;
    avgAmountEl.textContent    = `₹${formatINR(avgPerSub)}`;
    yearlyTotalEl.textContent  = `₹${formatINR(yearlyProjection)}`;
}


// ── Error Display ───────────────────────────────────────
function showError(msg) {
    errorMsg.textContent = msg;
    errorMsg.classList.remove('hidden');
}
