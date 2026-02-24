# The Dedicated Subscriptions Dashboard
This document explains the architecture and logic of the standalone frontend dashboard (`dashboard.html`) designed to view processed subscription data securely.

## 1. Separation of Concerns
Instead of cluttering the main upload page (`index.html`) with a massive layout and dense data tables, we isolated the subscription analytics into their own dedicated ecosystem:
- `dashboard.html`: Contains the structural layout and empty table.
- `dashboard.css`: Contains CSS rules that override the narrow 450px login constraints of `style.css` so the dashboard can stretch elegantly across wide desktop monitors.
- `dashboard.js`: The "brain" that securely handles API calls and mathematical estimation algorithms independent from the file upload logic.

## 2. Secure Route Protection
The very first thing `dashboard.js` does when it loads into the browser is check for the `token`:
```javascript
const token = localStorage.getItem('token');
if (!token) {
    window.location.href = 'index.html';
    return;
}
```
If a user tries to bookmark the dashboard or type the URL directly without logging in first, the JavaScript immediately ejects them and forces them back to the login page.

## 3. The Retrieval Process (GET /subscriptions)
When the user successfully uploads a CSV file on the `index.html` page, `app.js` automatically tells the browser to redirect to `dashboard.html`.

As soon as `dashboard.html` opens, the `fetchSubscriptions(token)` function fires.
1. It builds a secure `GET` request.
2. It explicitly attaches the `Authorization: Bearer <TOKEN>` header.
3. It hits our FastAPI backend `GET /subscriptions` endpoint to retrieve *only* the subscriptions belonging to the specific user who owns that token.

## 4. The Monthly Impact Calculator
Because users want to know how much cash they are burning each month, the frontend doesn't just blindly print the data—it performs active calculations before rendering the HTML table.
```javascript
let monthlyImpact = parseFloat(sub.average_amount);
if (sub.billing_cycle_days < 20) {
    monthlyImpact = monthlyImpact * (30 / sub.billing_cycle_days);
}
monthlyTotal += monthlyImpact;
```
**How it works:**
- It looks at the mathematical `billing_cycle_days` that the backend Engine generated.
- If a subscription bills every ~7 days (weekly), the frontend algorithm realizes that `$5.00` weekly actually has a `$20.00` monthly impact!
- It calculates `(30 / 7) = ~4.2`, and multiplies that by the `$5.00` cost to accurately predict the user's monthly burn rate.

## 5. Dynamic HTML Injection
Finally, it uses `document.createElement('tr')` to build secure HTML rows for each subscription and appends them into the empty `<tbody>` tag. By injecting HTML mathematically like this instead of hard-coding it, the dashboard can seamlessly support 1 subscription or 1,000 subscriptions without the UI breaking.
