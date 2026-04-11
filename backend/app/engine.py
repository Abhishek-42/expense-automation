import re
from datetime import datetime
from collections import defaultdict


JUNK_WORDS = ['store', 'payment', 'inc', 'llc', 'com', 'mktp', 'market', 'local']

AMOUNT_TOLERANCE = 50.00
MIN_CYCLE_DAYS = 25
MAX_CYCLE_DAYS = 35
MIN_OCCURRENCES = 2


def normalize_merchant_name(description: str) -> str:
    name = description.lower()
    name = re.sub(r'\d+', '', name)
    name = re.sub(r'[*\/\\-]', ' ', name)

    for word in JUNK_WORDS:
        name = re.sub(r'\b' + word + r'\b', '', name)

    name = " ".join(name.split())
    return name


def detect_subscriptions(transactions: list) -> list:
    grouped = defaultdict(list)

    for tx in transactions:
        merchant = normalize_merchant_name(tx['description'])
        grouped[merchant].append(tx)

    results = []

    for merchant, tx_list in grouped.items():
        if len(tx_list) < MIN_OCCURRENCES:
            continue

        tx_list.sort(key=lambda x: datetime.strptime(x['date'], "%Y-%m-%d"))

        is_recurring = True
        total_amount = 0.0
        total_days = 0
        intervals = 0

        for i in range(1, len(tx_list)):
            prev = tx_list[i - 1]
            curr = tx_list[i]

            prev_date = datetime.strptime(prev['date'], "%Y-%m-%d")
            curr_date = datetime.strptime(curr['date'], "%Y-%m-%d")
            days_apart = (curr_date - prev_date).days

            if not (MIN_CYCLE_DAYS <= days_apart <= MAX_CYCLE_DAYS):
                is_recurring = False
                break

            amount_diff = abs(curr['amount'] - prev['amount'])
            if amount_diff > AMOUNT_TOLERANCE:
                is_recurring = False
                break

            total_days += days_apart
            intervals += 1
            total_amount += curr['amount']

        if is_recurring and intervals > 0:
            total_amount += tx_list[0]['amount']
            avg_amount = total_amount / len(tx_list)
            avg_cycle = total_days / intervals

            results.append({
                "merchant_name": merchant.title(),
                "average_amount": round(avg_amount, 2),
                "billing_cycle_days": round(avg_cycle, 0),
                "last_payment_date": tx_list[-1]['date'],
                "original_transactions_count": len(tx_list)
            })

    return results
