import re
from datetime import datetime

# Words to completely ignore from merchant names
JUNK_WORDS = ['store', 'payment', 'inc', 'llc', 'com', 'mktp', 'market', 'local']

# Hybrid approach dictionaries
KNOWN_SUBS = ['netflix', 'spotify', 'amazon prime', 'gym', 'hulu', 'adobe', 'aws', 'cloud', 'internet', 'broadband', 'apple']
KNOWN_HABITS = ['starbucks', 'shell', 'mcdonalds', 'uber', 'lyft', 'grocery', 'cafe', 'restaurant']

def clean_name(desc):
    # make it lowercase
    name = desc.lower()
    # remove numbers and special characters
    name = re.sub(r'\d+', '', name)
    name = re.sub(r'[*\/\\-]', ' ', name)

    # remove the junk words
    for word in JUNK_WORDS:
        name = re.sub(r'\b' + word + r'\b', '', name)

    # clean up extra spaces
    return " ".join(name.split())

def detect_subscriptions(transactions):
    grouped_txns = {}
    
    # 1. Group all transactions by their clean merchant name
    for txn in transactions:
        merchant_name = clean_name(txn['description'])
        
        # if not in dictionary, add it
        if merchant_name not in grouped_txns:
            grouped_txns[merchant_name] = []
            
        grouped_txns[merchant_name].append(txn)

    final_results = []

    # 2. Loop through each group to see if it's a subscription
    for name, txn_list in grouped_txns.items():
        # we need at least 2 transactions to find a pattern
        if len(txn_list) < 2:
            continue

        # Check blacklist first (is it a habit?)
        is_habit = False
        for habit in KNOWN_HABITS:
            if habit in name:
                is_habit = True
                break
        
        if is_habit:
            print("Skipping habit:", name)
            continue # Reject immediately, it's just a habit

        # Sort the transactions chronologically by date
        txn_list.sort(key=lambda t: datetime.fromisoformat(t['date']))

        is_sub = True
        total_amount = 0.0
        total_days = 0
        number_of_gaps = 0
        
        # Check if it's a globally known subscription
        is_known_sub = False
        for known in KNOWN_SUBS:
            if known in name:
                is_known_sub = True
                break

        # 3. Calculate gaps and amount differences
        for i in range(1, len(txn_list)):
            prev_txn = txn_list[i - 1]
            current_txn = txn_list[i]

            date1 = datetime.fromisoformat(prev_txn['date'])
            date2 = datetime.fromisoformat(current_txn['date'])
            diff_days = (date2 - date1).days

            # Check if the gap matches a known frequency
            valid_gap = False
            if 6 <= diff_days <= 8:
                valid_gap = True # Weekly
            elif 13 <= diff_days <= 15:
                valid_gap = True # Bi-weekly
            elif 20 <= diff_days <= 40:
                valid_gap = True # Monthly (forgiving)
            elif 360 <= diff_days <= 370:
                valid_gap = True # Yearly
                
            if valid_gap == False and is_known_sub == False:
                is_sub = False
                break

            # Calculate amount difference
            amount_diff = abs(current_txn['amount'] - prev_txn['amount'])
            avg_amount = (current_txn['amount'] + prev_txn['amount']) / 2
            
            # If the difference is > 30% of the average, and it's not a known sub, flag it
            if avg_amount > 0:
                percent_change = amount_diff / avg_amount
                if percent_change > 0.30 and is_known_sub == False:
                    is_sub = False
                    break

            total_days += diff_days
            number_of_gaps += 1
            total_amount += current_txn['amount']

        # 4. If it survived all checks, add to results
        if is_sub == True and number_of_gaps > 0:
            total_amount += txn_list[0]['amount']
            avg_a = total_amount / len(txn_list)
            avg_d = total_days / number_of_gaps

            # Calculate a basic confidence score
            confidence = 50
            if is_known_sub: 
                confidence += 40
            if len(txn_list) > 3: 
                confidence += 10
                
            if confidence > 100:
                confidence = 100

            print("Found subscription:", name)

            final_results.append({
                "merchant_name": name.title(),
                "average_amount": round(avg_a, 2),
                "billing_cycle_days": round(avg_d, 0),
                "last_payment_date": txn_list[-1]['date'],
                "original_transactions_count": len(txn_list),
                "confidence_score": confidence
            })

    return final_results
