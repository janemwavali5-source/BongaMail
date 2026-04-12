from flask import Flask, render_template, request, session, jsonify, redirect, url_for
import sqlite3
from datetime import datetime
import requests
import base64
import os
import random

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "demo-secret-key-2026-change-later")

# ============== DARAJA CONFIG (Production - Real Money) ==============
DARAJA_CONSUMER_KEY = os.environ.get("DARAJA_CONSUMER_KEY")
DARAJA_CONSUMER_SECRET = os.environ.get("DARAJA_CONSUMER_SECRET")
DARAJA_SHORTCODE = os.environ.get("DARAJA_SHORTCODE")          # Your Equity Till Number
DARAJA_PASSKEY = os.environ.get("DARAJA_PASSKEY")
CALLBACK_URL = os.environ.get("CALLBACK_URL")

# ============== ADMIN PASSWORD (CHANGE THIS TO YOUR STRONG PASSWORD) ==============
ADMIN_PASSWORD = "Bonga Mail 2030?"   # ← CHANGE THIS IMMEDIATELY!

# ============== WORD LISTS FOR EMAIL ANALYZER ==============
UNSUBSCRIBE_REQUIRED = ["unsubscribe", "un-subscribe", "opt out"]
ADDRESS_REQUIRED = ["address", "p.o.box", "po box", "physical address"]
HYPE_WORDS = ["100%", "guarantee", "best in", "number one", "instant", "free forever"]
URGENCY_WORDS = ["limited time", "only today", "hurry", "last chance", "act now"]
CTA_WORDS = ["click", "reply", "book", "schedule", "download", "sign up", "get started", "shop now", "learn more", "contact us"]
FRIENDLY_WORDS = ["please", "thank", "appreciate", "kindly", "hope", "great"]
URGENT_WORDS = ["must", "immediately", "asap", "urgent", "now"]
FORMAL_WORDS = ["regards", "sincerely", "best regards", "dear"]

# ============== DATABASE SETUP ==============
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
            mpesa_receipt TEXT,
            result_code INTEGER,
            result_desc TEXT,
            callback_received_at TEXT,
            timestamp TEXT NOT NULL,
            status TEXT DEFAULT 'pending'
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS created_emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT NOT NULL,
            subject TEXT,
            body TEXT NOT NULL,
            report TEXT,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

# ============== DARAJA HELPERS ==============
def get_access_token():
    url = "https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
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
        "TransactionType": "CustomerBuyGoodsOnline",     # For Equity Till Number
        "Amount": amount,
        "PartyA": phone,
        "PartyB": DARAJA_SHORTCODE,
        "PhoneNumber": phone,
        "CallBackURL": CALLBACK_URL,
        "AccountReference": "EMAILANALYZER",            # Platform name visible to payer
        "TransactionDesc": "Email Analyzer Platform Unlock"
    }

    headers = {"Authorization": f"Bearer {token}"}
    url = "https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    response = requests.post(url, json=payload, headers=headers)
    return response.json()

# ============== MAIN ROUTES ==============
@app.route("/", methods=["GET", "POST"])
def index():
    unlocked = session.get("unlocked", False)
    message = None
    payment_in_progress = bool(session.get("pending_phone"))

    if request.method == "POST":
        action = request.form.get("action")

        if action == "pay":
            raw_phone = request.form.get("phone", "").strip()
            phone = "".join(c for c in raw_phone if c.isdigit())
            if phone.startswith("0"):
                phone = "254" + phone[1:]
            elif len(phone) == 9:
                phone = "254" + phone

            if phone.startswith("254") and len(phone) == 12:
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
                        message = f"✅ STK Push sent to {phone}. Check your phone!"
                        payment_in_progress = True
                    else:
                        message = f"Daraja Error: {result.get('errorMessage', result)}"
                except Exception as e:
                    message = f"Failed to contact Daraja: {str(e)}"
            else:
                message = "Please enter a valid Kenyan phone number (e.g. 0712345678)"

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
        SELECT status, mpesa_receipt FROM transactions 
        WHERE phone = ? 
        ORDER BY timestamp DESC LIMIT 1
    ''', (phone,))
    row = c.fetchone()
    conn.close()

    if row:
        status, receipt = row
        if status == "paid":
            session["unlocked"] = True
            return jsonify({"status": "paid", "receipt": receipt or "N/A"})
        return jsonify({"status": status})
    return jsonify({"status": "pending"})

@app.route("/mpesa/callback", methods=["POST"])
def mpesa_callback():
    try:
        data = request.get_json()
        callback = data["Body"]["stkCallback"]
        
        checkout_id = callback.get("CheckoutRequestID")
        result_code = callback.get("ResultCode")
        result_desc = callback.get("ResultDesc", "")
        status = "paid" if result_code == 0 else "failed"

        mpesa_receipt = None
        phone_from_callback = None

        if result_code == 0 and "CallbackMetadata" in callback:
            items = callback["CallbackMetadata"].get("Item", [])
            for item in items:
                name = item.get("Name")
                value = item.get("Value")
                if name == "MpesaReceiptNumber":
                    mpesa_receipt = value
                elif name == "PhoneNumber":
                    phone_from_callback = value

        conn = sqlite3.connect('payments.db')
        c = conn.cursor()

        # Idempotency check
        c.execute("SELECT mpesa_receipt FROM transactions WHERE checkout_request_id = ?", (checkout_id,))
        existing = c.fetchone()
        if existing and existing[0]:
            conn.close()
            return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"}), 200

        c.execute('''
            UPDATE transactions 
            SET status = ?,
                merchant_request_id = ?,
                mpesa_receipt = ?,
                result_code = ?,
                result_desc = ?,
                callback_received_at = ?
            WHERE checkout_request_id = ?
        ''', (status, callback.get("MerchantRequestID"), mpesa_receipt,
              result_code, result_desc, datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
              checkout_id))

        conn.commit()
        conn.close()

        if status == "paid" and session.get("pending_phone") == (phone_from_callback or session.get("pending_phone")):
            session["unlocked"] = True

    except Exception as e:
        print("Callback error:", str(e))

    return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"}), 200

# ============== ADMIN LOGIN ==============
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        entered_password = request.form.get("password")
        
        if entered_password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        else:
            return render_template("admin_login.html", error="Incorrect password. Please try again.")
    
    return render_template("admin_login.html")


@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
    return render_template("admin.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_login"))


# ============== MANUAL DATABASE UPDATE (Protected) ==============
@app.route("/admin/manual_confirm", methods=["POST"])
def manual_confirm():
    if not session.get("admin_logged_in"):
        return "Unauthorized. Please log in as admin first.", 401

    checkout_id = request.form.get("checkout_id")
    mpesa_receipt = request.form.get("mpesa_receipt")
    phone = request.form.get("phone")

    if not checkout_id or not mpesa_receipt:
        return "Missing required fields (checkout_id or mpesa_receipt)", 400

    conn = sqlite3.connect('payments.db')
    c = conn.cursor()
    c.execute('''
        UPDATE transactions 
        SET status = 'paid',
            mpesa_receipt = ?,
            callback_received_at = ?
        WHERE checkout_request_id = ?
    ''', (mpesa_receipt, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), checkout_id))
    conn.commit()
    conn.close()

    # Auto-unlock current user session if phone matches
    if session.get("pending_phone") == phone:
        session["unlocked"] = True

    return "✅ Payment manually confirmed and database updated successfully!"


# ============== EMAIL ANALYZER ==============
@app.route('/analyze-email', methods=['POST'])
def analyze_email():
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict()

    subject = data.get('subject', '').strip()
    body = data.get('body', '').strip()
    org_name = data.get('org_name', 'Your Company')
    absent_mode = data.get('absent_mode', False)
    team_mode = data.get('team_mode', False)
    comments = data.get('comments', '')

    if not body:
        return jsonify({"error": "Email body is required"}), 400

    body_lower = body.lower()
    report = []

    if not any(word in body_lower for word in UNSUBSCRIBE_REQUIRED):
        report.append({"type": "warning", "msg": "Add physical unsubscribe link or phrase"})
    if not any(word in body_lower for word in ADDRESS_REQUIRED):
        report.append({"type": "warning", "msg": "Add physical address (CAN-SPAM requirement)"})
    if any(word in body_lower for word in HYPE_WORDS):
        report.append({"type": "warning", "msg": "Avoid absolute hype words"})
    if any(word in body_lower for word in URGENCY_WORDS):
        report.append({"type": "info", "msg": "Urgency words detected — use sparingly"})
    if not any(word in body_lower for word in CTA_WORDS):
        report.append({"type": "warning", "msg": "Weak or missing Call-To-Action"})

    triggered_words = []
    if any(word in body_lower for word in FRIENDLY_WORDS):
        tone = "friendly"
        triggered_words = [w for w in FRIENDLY_WORDS if w in body_lower]
    elif any(word in body_lower for word in URGENT_WORDS):
        tone = "urgent"
        triggered_words = [w for w in URGENT_WORDS if w in body_lower]
    elif any(word in body_lower for word in FORMAL_WORDS):
        tone = "formal"
        triggered_words = [w for w in FORMAL_WORDS if w in body_lower]
    else:
        tone = "neutral"

    tone_options = {
        "friendly": [f"Tone is friendly and approachable — you used words like {', '.join(triggered_words[:3])} which makes it warm!"],
        "urgent": ["Tone feels a bit pushy — consider softening it"],
        "formal": ["Tone is professional and clear — excellent for B2B"],
        "neutral": ["Tone is neutral — add a few polite words to make it warmer"]
    }
    tone_suggestion = random.choice(tone_options.get(tone, ["Good tone!"]))

    signature = f"\n\nBest regards,\n{org_name}"
    preview = f"Subject: {subject or '(No subject)'}\n\n{body}{signature}"

    return jsonify({
        "preview": preview,
        "report": report,
        "tone": tone,
        "tone_suggestion": tone_suggestion,
        "absent_active": bool(absent_mode),
        "team_active": bool(team_mode),
        "comments": comments,
        "status": "success"
    })

if __name__ == "__main__":
    app.run(debug=True)
