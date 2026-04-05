from flask import Flask, render_template, request, session, redirect, url_for
import sqlite3
from datetime import datetime
import requests
import base64
import os

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY")


#  ============= DARAJA CONFIG(SANDBOX-CHANGE THESE)============
DARAJA_CONSUMER_KEY = os.environ.get("DARAJA_CONSUMER_KEY")
DARAJA_CONSUMER_SECRET = os.environ.get("DARAJA_CONSUMER_SECRET")
DARAJA_SHORTCODE = "174379"  # Sandbox default 
DARAJA_PASSKEY = os.environ.get("your_passkey_here")
CALLBACK_URL = os.environ.get("/your-ngrok-url.ngrok.io/mpesa/callback")

if "your_consumer_key_here" in DARAJA_CONSUMER_KEY
    print("Using placeholder Daraja
# =======================================

def init_db():
    Conn = sqlite3.connect('payments.db')
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS transaction
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT NOT NULL,
            amount INTEGER NOT NULL,
            checkout_request_id TEXT,
            merchant_request_id TEXT,
            timestamp TEXT NOT NULL,
            status TEXT DEFAULT 'pending'
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS created_emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT NOT NULL,
            subject TEXT,
            body TEXT NOT NULL,
            report TEXT,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL 
        ):
    conn.commit()
    conn.close()

init_db()

def get_access_token():
    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_types=client_credentials"
    credentials = base64.b64encode(f"{DARAJA_CONSUMER_KEY}:{DARAJA_CONSUMER_SECRET}".encode()).decode()
    headers = {"Authorization": f"Basic {credentials}"}
    response = requests.get(url, headers=headers)
    return response.json().get("access_token")

def initiate_stk_push(phone, amount=5000):
    token = get_access_token()
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password = base64.b64encode(f"{DARAJA_SHORTCODE}{DARAJA_PASSKEY}{timestamp}".encode()).decode()

    payload = {
        "BusinessShortCode": DARAJA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "Transaction type": transactiontype,
        "Amount": amount,
        "PartyA": phone,
        "PartyB": DARAJA_SHORTCODE,
        "PhoneNumber": phone,
        "CallBackURL": CALLBACK_URL,
        "AccountReference": "ToolUnlock2026",
        "TransactionDesc": "Payment for Email Analysis Tool"
    }
    headers = {"Authorization": f"Bearer {token}"}
    url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    response = requests.post(url, json=payload, headers=headers)
    return response.json()
    result = initiate_stk_push(phone)
    if result.get("ResponseCode") == "0":
        conn.sqlite3.connect('payments.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO transactions
            (phone, amount, checkout_request_id, timestamp,status)
            VALUES (?,?,?,?,?)
        ''',(phone, 5000, result.get("CheckoutRequestID"),
             datetime.now().strftime("%Y%m%d%H%M%S"),"pending"))
        conn.commit()
        conn.close()

        session["pending_phone"] = phone
        message = f"STK Push sent to {phone}.Open your and enter PIN,"
        payment_in_progress = True:
    else:
        message = "Daraja Error: {}".format(res

@app.route("/api/check_status", methods=["GET", "POST"])
def check_status():
    phone = session.get("pending_phone")
    if not phone:
        return jsonify({"status": "none"})

    Conn = sqlite3.connect('payments.db')
    c = conn.cursor()
    c.execute('''
        SELECT status FROM transactions
        WHERE phone = ? AND status IN ('payment
        ORDER BY timestamp DESC LIMIT 1
    ''', (phone,))
    row = c.fetchone()
    conn.close()

    if row:
        status = row[0]
        if status == "paid":
            session ["unlocked"] = True
        return jsonify({"status": status})
    return jsonify({"status": "pending"})
       
@app.route("/mpesa/callback", methods["POST","GET"]
def mpesa_callback():
    """Simple M-Pesa callback - exactly as you asked"""
    try:
        payload = request.get_json()
        print("M-PESA CALLBACK RECEIVED:")
        print(payload)

        # TODO: You can add DB update here later (mark subscription as paid)

        return {
            "ResultCode": 0,
            "ResultDesc": "Success"
        }
    except Exception as e:
        print("Callback error:",str
        return {
            "ResultCode": 0,
            "ResultDesc": "Accepted"
           
@app.route("/api/analyze", methods=["POST", "GET"])
def analyze ():
    if not session.get("unlocked", False):
        return jsonify({"error": "Please

    data = request.get_json(silent=True)
    body = data.get("body", "")
    comments = data.get("comments", "")
    absent_mode data.get("absentMode",)
    team_mode = data.get("teamMode", False)
    subject = data.get("subject", "")
    org_name = data.get("orgName", "[Your Organization]")
    org_phone = data.get("orgPhone", "[Your Phone]")
    org_email = data.get("orgEmail", "[Your Email]")

    body_lower = body.lower().strip()

    # === CONFIGURABLE KEYWORD LISTS (easy
    UNSUBSCRIBE_REQUIRED
    ADDRESS_REQUIRED
    HYPE_WORDS
    URGENCY_WORDS
    CTA_WORDS 

    FRIENDLY_WORDS
    URGENT_WORDS
    FORMAL_WORDS

    report = []

    # Compliance checks
    if not any(word in body_lower for word
        report.append({"msg": "Add physical 

    if not any(word in body_lower for word
        report.append({"msg": "Avoid absolute 

    if any(word in body_lower for word in
        report.append({"msg": "Urgency else

    if not any(word in body_lower for word
        report.append({"msg": "Weak or

    # Tone detection (priority: friendly
    if any(word in body_lower for
        tone = "friendly"
    elif any(word in body_lower for word
        tone = "urgent"
    elif any(word in body_lower for word
        tone = "formal"
    else:
        tone = "neutral"

    tone suggestions = {
        "friendly": "Tone is friendly and
        "urgent": "Tone feels pushy - 
        "formal": "Tone is professional
        "neutral": "Add polite words
    }[tone]

    # Signature & preview
    signature = f"\nBest regards, \n{org_name
    preview = f"Subject: {subject or '(No

    return jsonify({
        "preview": preview,
        "report": report,
        "tone": tone,
        "tone_suggestion": tone_suggestions,
        "absent_active": absent_mode,
        "team_active": team_mode,
        "comments": comments
    })

    





