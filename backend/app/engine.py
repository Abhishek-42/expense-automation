import re
from datetime import datetime
from collections import defaultdict
from decimal import Decimal

# Helper function to clean up messy bank names 
# Example: "STARBUCKS STORE 0812" -> "starbucks"
def normalize_merchant_name(description: str) -> str:
    """
    Strips numbers, special characters, and common weak words from a merchant string
    to find the true 'root' name of the company.
    """
    # 1. Convert to lowercase
    name = description.lower()
    
    # 2. Remove any numbers (store numbers, dates, etc)
    name = re.sub(r'\d+', '', name)
    
    # 3. Remove weird bank punctuation (asterisks, slashes, dashes)
    name = re.sub(r'[*\/\\-]', ' ', name)
    
    # 4. Remove common junk words that hide the real company name
    junk_words = ['store', 'payment', 'inc', 'llc', 'com', 'mktp', 'market', 'local']
    for word in junk_words:
        # \b means "word boundary" so we only delete whole words, not parts of words
        name = re.sub(r'\b' + word + r'\b', '', name)
    
    # 5. Clean up extra spaces
    name = " ".join(name.split())
    
    return name

def detect_subscriptions(transactions: list) -> list:
    """
    Scans a list of raw transaction dictionaries.
    Returns a list of detected subscriptions based on STRICT rules:
    - Must happen at least 2 times
    - Payments must be between 25 and 35 days apart (monthly)
    - Dollar amounts must be roughly the same (within $5 tolerance)
    """
    # Group transactions by our cleaned-up merchant names
    # Structure: {"netflix": [ {tx1}, {tx2} ], "starbucks": [ {tx1}, {tx2}, {tx3} ]}
    grouped_txs = defaultdict(list)
    
    for tx in transactions:
        merchant = normalize_merchant_name(tx['description'])
        grouped_txs[merchant].append(tx)
        
    detected_subscriptions = []
    
    for merchant, tx_list in grouped_txs.items():
        # Rule 1: We only care if we've seen them bill you at least twice
        if len(tx_list) < 2:
            continue
            
        # Sort their payments by date so we can calculate the days between them
        tx_list.sort(key=lambda x: datetime.strptime(x['date'], "%Y-%m-%d"))
        
        is_subscription = True
        total_amount = 0.0
        total_days_between = 0
        valid_intervals = 0
        
        # Look at each payment side-by-side with the payment that came before it
        for i in range(1, len(tx_list)):
            prev_tx = tx_list[i-1]
            curr_tx = tx_list[i]
            
            # Math: How many days apart were these two charges?
            prev_date = datetime.strptime(prev_tx['date'], "%Y-%m-%d")
            curr_date = datetime.strptime(curr_tx['date'], "%Y-%m-%d")
            days_diff = (curr_date - prev_date).days
            
            # Rule 2: Strict Month check (allow some wiggle room for weekends/leap years)
            if not (25 <= days_diff <= 35):
                is_subscription = False
                break
                
            # Rule 3: Amount tolerance (is this month's bill wildly different than last month?)
            # We allow a very strict $5 difference (in case taxes changed by a few pennies)
            amount_diff = abs(curr_tx['amount'] - prev_tx['amount'])
            if amount_diff > 5.00:
                is_subscription = False
                break
                
            total_days_between += days_diff
            valid_intervals += 1
            total_amount += curr_tx['amount']
            
        # If it survived all the strict rules above, it's a real subscription!
        if is_subscription and valid_intervals > 0:
            # Calculate the final averages
            avg_interval = total_days_between / valid_intervals
            # Add the very first payment to our total before dividing
            total_amount += tx_list[0]['amount']
            avg_amount = total_amount / len(tx_list)
            
            last_date = tx_list[-1]['date']
            
            detected_subscriptions.append({
                "merchant_name": merchant.title(), # Capitalize it nicely again
                "average_amount": round(avg_amount, 2),
                "billing_cycle_days": round(avg_interval, 0),
                "last_payment_date": last_date,
                "original_transactions_count": len(tx_list)
            })
            
    return detected_subscriptions
