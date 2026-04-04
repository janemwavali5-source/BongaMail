from flask import Flask, render_template,
import sqlite3
from datetime import datetime
import requests
import base64
import is

app = Flask(__name__)
app.secret_key = is.environ.get("FLASK_SEC

# ============== DARAJA CONFIG (with fallback
DARAJA_CONSUMER_KEY = os.environ.get("DARAJA
DARAJA_CONSUMER_SECRET = os.environ.get
DARAJA_SHORTCODE = "174379"
DARAJA_PASSKEY = os.environ.get
CALLBACK_URL = os.environ.get

if "your_consumer_key_here" in DARAJA_CONSUMER_KEY
    print("Using placeholder Daraja
# =======================================

def init_db():
    Conn = sqlite3.connect('payments.db')
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS transaction
            id INTEGER PRIMARY KEY AUTOINCREMENT
            phone TEXT NOT NULL,
            amount INTEGER NOT NULL,
            checkout_request_id TEXT,
            merchant_request_id TEXT,
            timestamp TEXT NOT NULL,
            status TEXT DEFAULT 'pending'
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_access_token():
    url = "https://sandbox.safaricom.co.ke
    credentials = base64.b64encode(f"{DARAJA
    headers = {"Authorization": f"Basic {
    response = requests.get(url, headers=headers
    return response.json().get("access

def initiate_stk_push(phone, amount=5000):
    token = get_access_token()
    timestamp = datetime.now().strftime("%
    password = base64.b64encode(f"{DARAJA

    payload = {
        "BusinessShortCode": DARAJA_SHORTCODE
        "Password": password,
        "Timestamp": timestamp,
        "Transaction type": transactiontype,
        "Amount": amount
        "PartyA": phone,
        "PartyB": DARAJA_SHORTCODE,
        "PhoneNumber": phone,
        "CallBackURL": CALLBACK_URL,
        "AccountReference": "ToolUnlock202
        "TransactionDesc": "Payment for
    }
    headers = {"Authorization": f"Bearer
    url = "https://sandbox.safaricom.co.ke
    response = requests.post(url, json
    return response.json()
    result = initiate_stk_push(phone)
    if result.get("ResponseCode") == "0":
        conn.sqlite3.connect('payments.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO transactions
            (phone, amount, checkout_request_id
            VALUES (?,?,?,?,?)
        ''',(phone, 5000, result.get("Checkout
             datetime.now().strftime("%Y
        conn.commit()
        conn.close()

        session["pending_phone"] = phone
        message = "STK Push sent! Check your
        payment_in_progress = True
    else:
        message = "Daraja Error: {}".format(res

                                            

    
         
      if "address" not in body_lower and "p.o.box" not in body_lower:
        report.append({"msg": "Add physical address for commercial emails", "severity": "warn"})
    if any(x in body_lower for x in ["100%", "guarantee", "best in", "number one"]):
        report.append({"msg": "Avoid absolute claims like '100% guarantee' or 'best in world'", "severity": "issue"})
    if any(x in body_lower for x in ["limited time", "only today", "hurry", "last chance"]):
        report.append({"msg": "Urgency claims must be truthful", "severity": "warn"})
    
    if not any(x in body_lower for x in ["click", "reply", "book", "schedule", "download", "sign up", "get started", "shop now", "learn more", "contact us", "book now"]):
        report.append({"msg": "Weak or missing Call-to-Action", "severity": "issue"})
    
    tone = "neutral"
    if any(w in body_lower for w in ["please", "thank", "appreciate", "kindly"]):
        tone = "friendly"
    elif any(w in body_lower for w in ["must", "immediately", "asap", "urgent", "now"]):
        tone = "urgent"
    encerely", "be
        tone = "formal"
    
    tone_suggestion = {
        "friendly": "Tone is friendly and approachable ✓",
        "urgent": "Tone feels pushy – consider softening for better relationships",
        "formal": "Tone is professional ✓ Consider adding warmth if targeting customers",
        "neutral": "Add polite words (please/thank you) to improve connection"
    }[tone]

    signature = f"\nBest regards,\n{org_name}\nPhone: {org_phone}\nEmail: {org_email}"
    preview = f"Subject: {subject or '(No subject)'}\n\n{body}\nsignature}"   

    return jsonify({
        preview": preview,
        "report": report,
        "tone": tone,
        "tone_suggestion": tone_suggestion,
        "absent_active": absent_mode,
        "team_active": team_mode,
        "comments": comments
    })

if __name__ == "__main__":
    app.run(debug=True)Enter message = "Please enter a valid Kenyan phone (e.g. 0712345678)

        elif action == "logout":
            session.clear()
            return redirect(url_for("index"))

    return render_template("index.html", 
                         unlocked=unlocked, 
                         message=message,
                         payment_in_progress=payment_in_progress)




