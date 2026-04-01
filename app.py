from flask import Flask, render_template, request, session, jsonify, redirect, url_for
import sqlite3
from datetime import datetime
import requests
import base64

app = Flask(__name__)
app.secret_key = "demo-secret-key-2026-change-later"

# ============== DARAJA CONFIG (SANDBOX) ==============
DARAJA_CONSUMER_KEY = "your_consumer_key_here"
DARAJA_CONSUMER_SECRET = "your_consumer_secret_here"
DARAJA_SHORTCODE = "174379"
DARAJA_PASSKEY = "your_passkey_here"
CALLBACK_URL = "https://your-ngrok-url.ngrok.io/mpesa/callback"
# ====================================================

def init_db():
    conn = sqlite3.connect('payments.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT NOT NULL,
            amount INTEGER NOT NULL,
            checkout_request_id TEXT,
            merchant_request_id TEXT,
            timestamp TEXT NOT NULL,
            status TEXT DEFAULT 'pending'
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_access_token():
    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
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
        "TransactionType": "CustomerPayBillOnline",
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

@app.route("/", methods=["GET", "POST"])
def index():
    unlocked = session.get("unlocked", False)
    message = None
    payment_in_progress = bool(session.get("pending_phone"))

    if request.method == "POST":
        action = request.form.get("action")

        if action == "pay":
            phone = request.form.get("phone", "").strip()
            if phone.startswith("0"):
                phone = "254" + phone[1:]
            elif not phone.startswith("254"):
                phone = "254" + phone

            if phone and len(phone) == 12:
                try:
                    result = initiate_stk_push(phone)
                    if result.get("ResponseCode") == "0":
                        conn = sqlite3.connect('payments.db')
                        c = conn.cursor()
                        c.execute('''
                            INSERT INTO transactions 
                            (phone, amount, checkout_request_id, timestamp, status)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (phone, 5000, result.get("CheckoutRequestID"),
                              datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "pending"))
                        conn.commit()
                        conn.close()

                        session["pending_phone"] = phone
                        message = "✅ STK Push sent! Check your phone."
                        payment_in_progress = True
                    else:
                        message = f"Daraja Error: {result.get('errorMessage', result)}"
                except Exception as e:
                    message = f"Failed to contact Daraja: {str(e)}"
            else:
from flask import Flask, render_template, request, session, jsonify, redirect, url_for
import sqlite3
from datetime import datetime
import requests
import base64

app = Flask(__name__)
app.secret_key = "demo-secret-key-2026-change-later"

# ============== DARAJA CONFIG (SANDBOX) ==============
DARAJA_CONSUMER_KEY = "your_consumer_key_here"
DARAJA_CONSUMER_SECRET = "your_consumer_secret_here"
DARAJA_SHORTCODE = "174379"
DARAJA_PASSKEY = "your_passkey_here"
CALLBACK_URL = "https://your-ngrok-url.ngrok.io/mpesa/callback"
# ====================================================

def init_db():
    conn = sqlite3.connect('payments.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT NOT NULL,
            amount INTEGER NOT NULL,
            checkout_request_id TEXT,
            merchant_request_id TEXT,
            timestamp TEXT NOT NULL,
            status TEXT DEFAULT 'pending'
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_access_token():
    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
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
        "TransactionType": "CustomerPayBillOnline",
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

@app.route("/", methods=["GET", "POST"])
def index():
    unlocked = session.get("unlocked", False)
    message = None
    payment_in_progress = bool(session.get("pending_phone"))

    if request.method == "POST":
        action = request.form.get("action")

        if action == "pay":
            phone = request.form.get("phone", "").strip()
            if phone.startswith("0"):
                phone = "254" + phone[1:]
            elif not phone.startswith("254"):
                phone = "254" + phone

            if phone and len(phone) == 12:
                try:
                    result = initiate_stk_push(phone)
                    if result.get("ResponseCode") == "0":
                        conn = sqlite3.connect('payments.db')
                        c = conn.cursor()
                        c.execute('''
                            INSERT INTO transactions 
                            (phone, amount, checkout_request_id, timestamp, status)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (phone, 5000, result.get("CheckoutRequestID"),
                              datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "pending"))
                        conn.commit()
                        conn.close()

                        session["pending_phone"] = phone
                        message = "✅ STK Push sent! Check your phone."
                        payment_in_progress = True
                    else:
                        message = f"Daraja Error: {result.get('errorMessage', result)}"
                except Exception as e:
                    message = f"Failed to contact Daraja: {str(e)}"
            else:
                message = "Please enter a valid Kenyan phone (e.g. 0712345678)"

        elif action == "logout":
            session.clear()
            return redirect(url_for("index"))

    return render_template("index.html", 
                         unlocked=unlocked, 
                         message=message,
                         payment_in_progress=payment_in_progress)

@app.route("/api/check_status", methods=["GET"])
def check_status():
    phone = session.get("pending_phone")
    if not phone:
        return jsonify({"status": "none"})

    conn = sqlite3.connect('payments.db')
    c = conn.cursor()
    c.execute('''
        SELECT status FROM transactions 
        WHERE phone = ? AND status IN ('paid', 'failed')
        ORDER BY timestamp DESC LIMIT 1
    ''', (phone,))
    row = c.fetchone()
    conn.close()

    if row:
        status = row[0]
        if status == "paid":
            session["unlocked"] = True
        return jsonify({"status": status})
    return jsonify({"status": "pending"})

@app.route("/mpesa/callback", methods=["POST"])
def mpesa_callback():
    # (unchanged - keeps your callback working)
    data = request.json
    try:
        callback = data["Body"]["stkCallback"]
        checkout_id = callback.get("CheckoutRequestID")
        result_code = callback.get("ResultCode")
        status = "paid" if result_code == 0 else "failed"

        conn = sqlite3.connect('payments.db')
        c = conn.cursor()
        c.execute('''
            UPDATE transactions 
            SET status = ?, merchant_request_id = ?
            WHERE checkout_request_id = ?
        ''', (status, callback.get("MerchantRequestID"), checkout_id))
        conn.commit()
        conn.close()
    except:
        pass
    return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"}), 200

# === YOUR ORIGINAL ANALYZE ROUTE (unchanged) ===
@app.route("/api/analyze", methods=["POST"])
def analyze():
    if not session.get("unlocked", False):
        return jsonify({"error": "Please complete payment to unlock the tool"}), 403

    data = request.json
    body = data.get("body", "")
    comments = data.get("comments", "")
    absent_mode = data.get("absentMode", False)
    team_mode = data.get("teamMode", False)
    subject = data.get("subject", "")
    org_name = data.get("orgName", "[Your Organization]")
    org_phone = data.get("orgPhone", "[Your Phone]")
    org_email = data.get("orgEmail", "[Your Email]")

    body_lower = body.lower()
    report = []
    
    if "unsubscribe" not in body_lower:
        report.append({"msg": "Consider adding an unsubscribe link (CAN-SPAM/GDPR requirement)", "severity": "warn"})
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
    elif any(w in body_lower for w in ["regards", "sincerely", "best regards"]):
        tone = "formal"
    
    tone_suggestion = {
        "friendly": "Tone is friendly and approachable ✓",
        "urgent": "Tone feels pushy – consider softening for better relationships",
        "formal": "Tone is professional ✓ Consider adding warmth if targeting customers",
        "neutral": "Add polite words (please/thank you) to improve connection"
    }[tone]

    signature = f"\nBest regards,\n{org_name}\nPhone: {org_phone}\nEmail: {org_email}"
    preview = f"Subject: {subject or '(No subject)'}\n\n{body}\n{signature}"

    return jsonify({
        "preview": preview,
        "report": report,
        "tone": tone,
        "tone_suggestion": tone_suggestion,
        "absent_active": absent_mode,
        "team_active": team_mode,
        "comments": comments
    })

if __name__ == "__main__":
    app.run(debug=True)Enter                message = "Please enter a valid Kenyan phone (e.g. 0712345678)"

        elif action == "logout":
            session.clear()
            return redirect(url_for("index"))

    return render_template("index.html", 
                         unlocked=unlocked, 
                         message=message,
                         payment_in_progress=payment_in_progress)

@app.route("/api/check_status", methods=["GET"])
def check_status():
    phone = session.get("pending_phone")
    if not phone:
        return jsonify({"status": "none"})

    conn = sqlite3.connect('payments.db')
    c = conn.cursor()
    c.execute('''
        SELECT status FROM transactions 
        WHERE phone = ? AND status IN ('paid', 'failed')
        ORDER BY timestamp DESC LIMIT 1
    ''', (phone,))
    row = c.fetchone()
    conn.close()

    if row:
        status = row[0]
        if status == "paid":
            session["unlocked"] = True
        return jsonify({"status": status})
    return jsonify({"status": "pending"})

@app.route("/mpesa/callback", methods=["POST"])
def mpesa_callback():
    # (unchanged - keeps your callback working)
    data = request.json
    try:
        callback = data["Body"]["stkCallback"]
        checkout_id = callback.get("CheckoutRequestID")
        result_code = callback.get("ResultCode")
        status = "paid" if result_code == 0 else "failed"

        conn = sqlite3.connect('payments.db')
        c = conn.cursor()
        c.execute('''
            UPDATE transactions 
            SET status = ?, merchant_request_id = ?
            WHERE checkout_request_id = ?
        ''', (status, callback.get("MerchantRequestID"), checkout_id))
        conn.commit()
        conn.close()
    except:
        pass
    return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"}), 200

# === YOUR ORIGINAL ANALYZE ROUTE (unchanged) ===
@app.route("/api/analyze", methods=["POST"])
def analyze():
    if not session.get("unlocked", False):
        return jsonify({"error": "Please complete payment to unlock the tool"}), 403

    data = request.json
    body = data.get("body", "")
    comments = data.get("comments", "")
    absent_mode = data.get("absentMode", False)
    team_mode = data.get("teamMode", False)
    subject = data.get("subject", "")
    org_name = data.get("orgName", "[Your Organization]")
    org_phone = data.get("orgPhone", "[Your Phone]")
    org_email = data.get("orgEmail", "[Your Email]")

