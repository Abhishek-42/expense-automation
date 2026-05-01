import boto3
import os
from datetime import datetime, timedelta
from app.db import subscriptions_table, user_ids, ses_client
from dotenv import load_dotenv

load_dotenv()

# my verified email here
MY_EMAIL = os.environ.get("SES_SENDER_EMAIL", "anila9823@gmail.com") 

def get_next_date(last_date, cycle):
    # calculate the next payment date
    d1 = datetime.fromisoformat(last_date)
    return d1 + timedelta(days=cycle)

def send_email(to_email, merchant_name, amt, expected_date):
    # subject of the email
    sub = "Upcoming Subscription: " + merchant_name
    
    # basic html body
    html_body = """
    <html>
    <body>
        <h2>ExpenseIQ Alert</h2>
        <p>Hi,</p>
        <p>You have a subscription coming up!</p>
        <p><b>Merchant:</b> """ + merchant_name + """</p>
        <p><b>Amount:</b> """ + str(amt) + """</p>
        <p><b>Date:</b> """ + str(expected_date) + """</p>
        <br>
        <p>Cancel it if you don't want to pay.</p>
    </body>
    </html>
    """
    
    txt_body = "Hi, you have a sub coming up for " + merchant_name

    try:
        # call aws ses to send
        resp = ses_client.send_email(
            Destination={'ToAddresses': [to_email]},
            Message={
                'Body': {
                    'Html': {'Charset': "UTF-8", 'Data': html_body},
                    'Text': {'Charset': "UTF-8", 'Data': txt_body},
                },
                'Subject': {'Charset': "UTF-8", 'Data': sub},
            },
            Source=MY_EMAIL,
        )
        print("Sent email to " + to_email)
        return True
    except Exception as e:
        print("Error sending email:", e)
        return False

def check_subs_and_email():
    today = datetime.now()
    
    # get all subs from db
    res = subscriptions_table.scan()
    all_subs = res.get('Items', [])
    
    count = 0
    
    # loop through them
    for s in all_subs:
        last_d = s.get('last_payment_date')
        cycle = int(s.get('billing_cycle_days', 30))
        
        if last_d is None:
            continue
            
        next_d = get_next_date(last_d, cycle)
        
        # calculate diff
        diff = (next_d.date() - today.date()).days
        
        # if diff is between 0 and 3 days, send email
        if diff >= 0 and diff <= 3:
            uid = s.get('user_id')
            
            # get user email from other table
            u_res = user_ids.get_item(Key={'user_id': uid})
            u_data = u_res.get('Item')
            
            if u_data and 'email' in u_data:
                u_email = u_data['email']
                m_name = s.get('merchant_name')
                amt = float(s.get('average_amount'))
                date_str = next_d.strftime('%Y-%m-%d')
                
                print("Found a match! sending email...")
                
                sent = send_email(u_email, m_name, amt, date_str)
                if sent:
                    count += 1
                    
    return {"msg": "done", "emails_sent": count}
