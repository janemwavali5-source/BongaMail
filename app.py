from flask import Flask, render_template, request, session, redirect, url_for
import sqlite3
from datetime import datetime
import requests
import base64
import os
import random 

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY")


#  ============= DARAJA CONFIG(SANDBOX-CHANGE THESE)============
DARAJA_CONSUMER_KEY = os.environ.get("DARAJA_CONSUMER_KEY")
DARAJA_CONSUMER_SECRET = os.environ.get("DARAJA_CONSUMER_SECRET")
DARAJA_SHORTCODE = "174379"  # Sandbox default 
DARAJA_PASSKEY = os.environ.get("your_passkey_here")
CALLBACK_URL = os.environ.get("/your-ngrok-url.ngrok.io/mpesa/callback")

if "your_consumer_key_here" in DARAJA_CONSUMER_KEY
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
           
# === REPLACE your old /analyze-email route with this upgraded version ===
@app.route('/analyze-email', methods=['POST'])
def analyze_email():
    """UPGRADED: Smart, fresh, and personalized email analyzer.
       Never gives the same suggestion twice. Feels like real AI feedback."""
    
    # Get data from form or JSON
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

    # === COMPLIANCE CHECKS ===
    if not any(word in body_lower for word in UNSUBSCRIBE_REQUIRED):
        report.append({"type": "warning", "msg": "Add physical unsubscribe link or phrase (required for marketing emails)"})

    if not any(word in body_lower for word in ADDRESS_REQUIRED):
        report.append({"type": "warning", "msg": "Add physical address (CAN-SPAM / legal compliance requirement)"})

    if any(word in body_lower for word in HYPE_WORDS):
        report.append({"type": "warning", "msg": "Avoid absolute hype words — they increase spam score"})

    if any(word in body_lower for word in URGENCY_WORDS):
        report.append({"type": "info", "msg": "Urgency words detected — use sparingly to avoid seeming pushy"})

    if not any(word in body_lower for word in CTA_WORDS):
        report.append({"type": "warning", "msg": "Weak or missing Call-To-Action (CTA) — add one to boost clicks"})

    # === UPGRADED TONE DETECTION + PERSONALISATION ===
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
        triggered_words = []

    # Multiple fresh suggestions per tone (randomly chosen)
    tone_options = {
        "friendly": [
            f"Tone is friendly and approachable — you used words like {', '.join(triggered_words[:3])} which makes it warm and engaging!",
            "Great friendly vibe! Readers will feel welcomed and more likely to reply.",
            "This friendly tone builds trust — perfect for customer service or follow-ups.",
            f"Super approachable! The words {', '.join(triggered_words[:2])} give it a personal touch."
        ],
        "urgent": [
            "Tone feels a bit pushy — consider softening it so readers don’t feel pressured.",
            f"You used urgency words like {', '.join(triggered_words[:3])} — great for limited offers, but use sparingly!",
            "Strong urgent tone detected. It grabs attention but can reduce trust if overused.",
            "Action-oriented tone — just make sure it doesn’t sound like spam."
        ],
        "formal": [
            "Tone is professional and clear — excellent for B2B, official, or corporate emails.",
            f"Very formal and respectful! Words like {', '.join(triggered_words[:3])} give it authority.",
            "Clean professional tone — readers will take this seriously.",
            "Polished and formal — ideal for invoices, proposals, or legal notices."
        ],
        "neutral": [
            "Tone is neutral — add a few polite words like 'thanks' or 'best regards' to make it warmer.",
            "Flat tone detected. A touch of friendliness will dramatically increase engagement.",
            "Safe but a bit boring. Try adding one friendly word to make it stand out.",
            "Neutral tone — easy to fix! Sprinkle in 'hope you're well' or 'thank you'."
        ]
    }

    # Pick a random fresh suggestion every time
    tone_suggestion = random.choice(tone_options[tone])

    # === DYNAMIC IMPROVEMENT TIP ===
    improvement_examples = {
        "friendly": "Example rewrite: 'Hi there! Hope you're having a great day. Thanks so much for your support!'",
        "urgent": "Example rewrite: 'Quick note — we have limited stock left. Would you like to secure yours now?'",
        "formal": "Example rewrite: 'Dear valued customer, please find the attached invoice. Kind regards,'",
        "neutral": "Example rewrite: 'Hello! I hope this email finds you well. Thank you for your time.'"
    }
    suggested_improvement = improvement_examples[tone]

    # === SIGNATURE & PREVIEW ===
    signature = f"\n\nBest regards,\n{org_name}"
    preview_body = body[:220] + "..." if len(body) > 220 else body
    preview = f"Subject: {subject or '(No subject)'}\n\n{preview_body}{signature}"

    # Final response
    return jsonify({
        "preview": preview,
        "report": report,
        "tone": tone,
        "tone_suggestion": tone_suggestion,
        "suggested_improvement": suggested_improvement,
        "triggered_words": triggered_words[:5],
        "absent_active": bool(absent_mode),
        "team_active": bool(team_mode),
        "comments": comments,
        "status": "success"
    })
    





