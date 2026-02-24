# Subscription Detection Engine

This document outlines exactly how the backend engine works to separate the 10% of recurring subscription payments from the 90% of random daily noise. 

## The Core Philosophy
The algorithm is designed to be **Strict by Default**. It is much better to accidentally miss a subscription (which you can manually add later) than to accidentally flag your coffee habit as a monthly bill. 

The entire engine lives in `/backend/app/engine.py` and runs completely automatically every time you upload a CSV file.

---

## Step 1: Merchant Normalization (The `normalize_merchant_name` function)
Banks are notoriously terrible at formatting merchant names. They often append store numbers, dates, or weird punctuation. We need to clean these up so the engine realizes that "UBER EATS LOCAL" and "UBER RIDE" are different, but two different Starbucks locations are the same company.

**Here is exactly what the code does line-by-line:**
1. `name.lower()`: Converts everything to lowercase so "NETFLIX" matches "Netflix".
2. `re.sub(r'\d+', '', name)`: Uses Regex to delete any digits (0-9). This removes store numbers.
3. `re.sub(r'[*\/\\-]', ' ', name)`: Uses Regex to target specific special characters used by banks (asterisks, slashes) and turns them into spaces.
4. `for word in junk_words:`: It loops through a list of weak words like "inc", "llc", "store", "mktp" and purposefully deletes them so we can find the true root name of the company.
5. `" ".join(name.split())`: Finally, it squishes any weird double-spaces down into neat single spaces.

---

## Step 2: Detection Rules (The `detect_subscriptions` function)
Once all the merchant names in the CSV are cleaned up, the engine groups them into buckets (e.g., all Starbucks payments in one bucket, all Netflix payments in another). 

It then loops through each bucket and applies three extremely strict mathematical rules. If a bucket fails *any* of these rules, it is immediately thrown out and ignored.

### 🔴 Rule 1: The "At Least Twice" Rule
```python
if len(tx_list) < 2:
    continue
```
* **What it does:** If you only ever went to a specific merchant one single time in the entire CSV file, it cannot possibly be a recurring subscription. It throws it out.

### 🔴 Rule 2: The "30-Day Window" Rule
```python
if not (25 <= days_diff <= 35):
    is_subscription = False
    break
```
* **What it does:** The engine grabs the dates of two payments and calculates how many days apart they were. 
* **The Logic:** Monthly subscriptions usually hit exactly 30 days apart. However, we have to allow a tight "wiggle room" (25 to 35 days) to account for February (28 days), months with 31 days, and banks that delay weekend charges until Monday. If the gap between payments falls outside this window, it throws the merchant out.

### 🔴 Rule 3: The "Tolerance" Rule
```python
if amount_diff > Decimal('5.00'):
    is_subscription = False
    break
```
* **What it does:** It compares the dollar amount of this month's bill to last month's bill.
* **The Logic:** While our coffee runs fluctuate wildly depending on what we order, our Spotify bill is almost identically the same every month. We allow a maximum variance of $5.00 between bills (just in case local taxes changed by a few pennies or the subscription raised its price). If the price swings by more than $5, it throws the merchant out.

---

## Step 3: Saving to DynamoDB 
If a merchant successfully survives all three strict rules, the engine calculates the overall average cost, the average number of days between bills, and notes the most recent payment date. 

It passes this summarized "Subscription" profile back to `main.py`, which then automatically saves it to your brand new `Subscriptions` table in AWS DynamoDB!
