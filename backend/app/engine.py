import re
from datetime import datetime

# words to ignore in merchant names
JUNK_WORDS = ['store', 'payment', 'inc', 'llc', 'com', 'mktp', 'market', 'local']

KNOWN_SUBS = ['netflix', 'spotify', 'amazon prime', 'gym', 'adobe', 'aws', 'cloud', 'internet', 'broadband']
KNOWN_HABITS = ['starbucks', 'shell', 'mcdonalds', 'uber', 'lyft', 'grocery', 'cafe', 'restaurant']

def clean_name(desc):
    name = desc.lower()
    name = re.sub(r'\d+', '', name)
    name = re.sub(r'[*\/\\-]', ' ', name)

    for word in JUNK_WORDS:
        name = re.sub(r'\b' + word + r'\b', '', name)

    return " ".join(name.split())


def detect_subscriptions(transactions):
    grouped_txns = {}
    
    for txn in transactions:
        merchant_name = clean_name(txn['description'])
        
        if merchant_name not in grouped_txns:
            grouped_txns[merchant_name] = []
            
        grouped_txns[merchant_name].append(txn)

    final_results = []

    for name, txn_list in grouped_txns.items():
        if len(txn_list) < 2:
            continue

        # check if it's just a regular habit
        is_habit = False
        for habit in KNOWN_HABITS:
            if habit in name:
                is_habit = True
                break
        
        if is_habit:
            print(f"Skipping habit: {name}")
            continue

        # sort chronologically
        txn_list.sort(key=lambda t: datetime.fromisoformat(t['date']))

        is_sub = True
        total_amount = 0.0
        total_days = 0
        number_of_gaps = 0
        
        is_known_sub = any(known in name for known in KNOWN_SUBS)

        # calculate gaps and amount diffs
        for i in range(1, len(txn_list)):
            prev_txn = txn_list[i - 1]
            current_txn = txn_list[i]

            date1 = datetime.fromisoformat(prev_txn['date'])
            date2 = datetime.fromisoformat(current_txn['date'])
            diff_days = (date2 - date1).days

            # Check if the gap matches a known frequency
            valid_gap = False
            if 6 <= diff_days <= 8:
                valid_gap = True
            elif 13 <= diff_days <= 15:
                valid_gap = True
            elif 20 <= diff_days <= 40:
                valid_gap = True
            elif 360 <= diff_days <= 370:
                valid_gap = True
                
            if not valid_gap and not is_known_sub:
                is_sub = False
                break

            # Calculate amount difference
            amount_diff = abs(current_txn['amount'] - prev_txn['amount'])
            avg_amount = (current_txn['amount'] + prev_txn['amount']) / 2
            
            # check if difference is > 30% of average
            if avg_amount > 0:
                percent_change = amount_diff / avg_amount
                if percent_change > 0.30 and not is_known_sub:
                    is_sub = False
                    break

            total_days += diff_days
            number_of_gaps += 1
            total_amount += current_txn['amount']

        if is_sub and number_of_gaps > 0:
            total_amount += txn_list[0]['amount']
            avg_a = total_amount / len(txn_list)
            avg_d = total_days / number_of_gaps

            # simple confidence score
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
