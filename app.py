from flask import Flask, render_template, request, session, redirect, url_for
import sqlite3
from datetime import datetime
import requests
import base64
import os

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "demo-secret-key-2026-change-later")

# ============== DARAJA CONFIG ==============
DARAJA_CONSUMER_KEY = os.environ.get("DARAJA_CONSUMER_KEY")
DARAJA_CONSUMER_SECRET = os.environ.get("DARAJA_CONSUMER_SECRET")
DARAJA_SHORTCODE = os.environ.get("DARAJA_SHORTCODE")
DARAJA_PASSKEY = os.environ.get("DARAJA_PASSKEY")
CALLBACK_URL = os.environ.get("CALLBACK_URL")

# ============== ADMIN PASSWORD ==============
ADMIN_PASSWORD = "admin2026"   # ← CHANGE THIS TO YOUR STRONG PASSWORD

# ============== WORD LISTS ==============
UNSUBSCRIBE_REQUIRED = ["unsubscribe", "un-subscribe", "opt out"]
ADDRESS_REQUIRED = ["address", "p.o.box", "po box", "physical address"]
HYPE_WORDS = ["100%", "guarantee", "best in", "number one", "instant", "free forever"]
CTA_WORDS = ["click", "reply", "book", "schedule", "download", "sign up", "get started", "shop now", "learn more", "contact us"]

def init_db():
    conn = sqlite3.connect('payments.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT NOT NULL,
        amount INTEGER NOT NULL,
        checkout_request_id TEXT,
        merchant_request_id TEXT,
        mpesa_receipt TEXT,
        status TEXT DEFAULT 'pending',
        timestamp TEXT NOT NULL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_emails (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT NOT NULL,
        subject TEXT,
        body TEXT NOT NULL,
        report TEXT,
        score INTEGER,
        created_at TEXT NOT NULL
    )''')
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
        "TransactionType": "CustomerBuyGoodsOnline",
        "Amount": amount,
        "PartyA": phone,
        "PartyB": DARAJA_SHORTCODE,
        "PhoneNumber": phone,
        "CallBackURL": CALLBACK_URL,
        "AccountReference": "EMAILANALYZER",
        "TransactionDesc": "Payment for Email Analysis Tool"
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
                result = initiate_stk_push(phone)
                if result.get("ResponseCode") == "0":
                    conn = sqlite3.connect('payments.db')
                    c = conn.cursor()
                    c.execute('''INSERT INTO transactions (phone, amount, checkout_request_id, timestamp, status)
                                 VALUES (?, ?, ?, ?, ?)''', 
                              (phone, 5000, result.get("CheckoutRequestID"), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "pending"))
                    conn.commit()
                    conn.close()
                    session["pending_phone"] = phone
                    message = f"✅ STK Push sent to {phone}. Check your phone!"
                else:
                    message = "Failed to initiate payment"
            else:
                message = "Invalid phone number"

        elif action == "logout":
            session.clear()
            return redirect(url_for("index"))

    return render_template("index.html", unlocked=unlocked, message=message)

@app.route("/load_template", methods=["POST"])
def load_template():
    template_id = int(request.form.get("template_id", 0))
    templates = [
        {"subject": "Special Offer: 20% Off This Week Only!", "body": "Hi there,\n\nWe’re excited to offer you 20% off our premium plan this week only!\n\nClick here to claim your discount: [Link]\n\nBest regards,\nYour Company"},
        {"subject": "Follow-up on Our Meeting", "body": "Hi [Name],\n\nThank you for the productive meeting yesterday. Just following up on the action points we discussed.\n\nLet me know if you need any further information.\n\nBest regards,\nYour Company"},
        {"subject": "Monthly Newsletter – March 2026", "body": "Dear valued customer,\n\nHere’s what’s new this month at our company...\n\n[Content]\n\nWe appreciate your continued support!\n\nBest regards,\nYour Company"},
        {"subject": "Thank You for Your Purchase!", "body": "Hi [Name],\n\nThank you so much for choosing us! Your order has been processed and is on the way.\n\nWe hope you love it!\n\nBest regards,\nYour Company"},
        {"subject": "Invoice #INV-2026-045 – Payment Due", "body": "Dear [Name],\n\nPlease find attached your invoice for March services.\n\nTotal due: KSh 12,500\nPayment due by: 15th April 2026\n\nThank you for your prompt payment!\n\nBest regards,\nYour Company"},
        {"subject": "Invitation: Let’s Schedule a Quick Call", "body": "Hi [Name],\n\nI’d love to schedule a quick 15-minute call to discuss how we can help your business grow.\n\nAre you free next week?\n\nBest regards,\nYour Company"}
    ]
    selected = templates[template_id % len(templates)]
    return render_template("index.html", unlocked=True, message=f"✅ Template loaded: {selected['subject']}")

@app.route('/analyze-email', methods=['POST'])
def analyze_email():
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict()

    subject = data.get('subject', '').strip()
    body = data.get('body', '').strip()
    org_name = data.get('org_name', 'Your Company')

    if not body:
        return jsonify({"error": "Email body is required"}), 400

    body_lower = body.lower()
    report = []
    score = 100   # Start with perfect score
    spam_risk = "Low"

    # === COMPLIANCE & SPAM CHECKS ===
    if not any(word in body_lower for word in ["unsubscribe", "opt out", "un-subscribe"]):
        report.append({"type": "warning", "msg": "Missing unsubscribe link (increases spam risk)"})
        score -= 15

    if not any(word in body_lower for word in ["address", "p.o.box", "po box", "physical address"]):
        report.append({"type": "warning", "msg": "Missing physical address (CAN-SPAM / DPA compliance)"})
        score -= 10

    if any(word in body_lower for word in ["100%", "guarantee", "best in world", "number one", "instant results"]):
        report.append({"type": "warning", "msg": "Avoid absolute claims - high spam trigger"})
        score -= 12
        spam_risk = "Medium"

    if any(word in body_lower for word in ["limited time", "only today", "hurry", "last chance", "act now"]):
        report.append({"type": "info", "msg": "Urgency words detected - use sparingly"})
        score -= 8

    if not any(word in body_lower for word in ["click", "reply", "book", "schedule", "download", "sign up", "get started", "shop now", "learn more", "contact us"]):
        report.append({"type": "warning", "msg": "Weak or missing Call-To-Action"})
        score -= 10

    # Tone penalties
    if any(word in body_lower for word in ["must", "immediately", "asap", "urgent", "now"]):
        score -= 5

    # Positive points
    if any(word in body_lower for word in ["please", "thank", "appreciate", "kindly", "hope you're well"]):
        score += 8

    # Length check
    if len(body) < 50:
        report.append({"type": "warning", "msg": "Email body is too short"})
        score -= 10
    elif len(body) > 800:
        report.append({"type": "info", "msg": "Email is quite long - consider shortening"})
        score -= 5

    # Final score bounds
    score = max(0, min(100, score))

    if score < 50:
        spam_risk = "High"
    elif score < 75:
        spam_risk = "Medium"

    # Preview
    signature = f"\n\nBest regards,\n{org_name}"
    preview = f"Subject: {subject or '(No subject)'}\n\n{body}{signature}"

    return jsonify({
        "preview": preview,
        "report": report,
        "email_score": score,
        "spam_risk": spam_risk,
        "tone": "neutral",   # you can enhance this later
        "status": "success"
    })

# ============== OWNER UNLOCK ==============
@app.route("/owner/unlock")
def owner_unlock():
    key = request.args.get("key")
    if key == "owner2026":   # Change this for better security
        session["unlocked"] = True
        session["pending_phone"] = "254700000000"
        return redirect(url_for("index"))
    return "Invalid owner key", 403

# ============== ADMIN LOGIN ==============
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect("/admin/dashboard")
        return "Incorrect password. Try again."
    
    return """
    <div style="max-width:400px;margin:100px auto;padding:40px;border:1px solid #ddd;border-radius:12px;text-align:center;">
        <h2>Admin Login</h2>
        <form method="POST">
            <input type="password" name="password" placeholder="Admin Password" style="width:100%;padding:12px;margin:15px 0;">
            <button type="submit" style="width:100%;padding:12px;background:#00A651;color:white;border:none;border-radius:8px;">Login</button>
        </form>
    </div>
    """

@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    conn = sqlite3.connect('payments.db')
    c = conn.cursor()
    c.execute("SELECT id, phone, checkout_request_id, status FROM transactions WHERE status = 'pending' ORDER BY timestamp DESC")
    pending = c.fetchall()
    conn.close()

    html = """
    <h2>Admin Dashboard - Manual Payment Approval</h2>
    <p><a href="/admin/add_user">➕ Manually Unlock a User</a></p><br>
    <h3>Pending Payments</h3>
    """
    if pending:
        html += "<table border='1' cellpadding='10' style='width:100%;border-collapse:collapse;'>"
        html += "<tr><th>ID</th><th>Phone</th><th>Checkout ID</th><th>Action</th></tr>"
        for p in pending:
            html += f"""
            <tr>
                <td>{p[0]}</td>
                <td>{p[1]}</td>
                <td>{p[2]}</td>
                <td>
                    <form method="POST" action="/admin/manual_confirm" style="display:inline;">
                        <input type="hidden" name="checkout_id" value="{p[2]}">
                        <input type="text" name="receipt" placeholder="M-Pesa Receipt Number" required>
                        <button type="submit" style="background:#00A651;color:white;padding:8px 16px;border:none;border-radius:6px;">Mark as Paid</button>
                    </form>
                </td>
            </tr>
            """
        html += "</table>"
    else:
        html += "<p>No pending payments at the moment.</p>"

    html += '<br><a href="/admin/logout">Logout</a>'
    return html

@app.route("/admin/manual_confirm", methods=["POST"])
def manual_confirm():
    if not session.get("admin_logged_in"):
        return "Unauthorized", 401

    checkout_id = request.form.get("checkout_id")
    receipt = request.form.get("receipt")

    conn = sqlite3.connect('payments.db')
    c = conn.cursor()
    c.execute("UPDATE transactions SET status='paid', mpesa_receipt=? WHERE checkout_request_id=?", (receipt, checkout_id))
    conn.commit()
    conn.close()

    return "✅ Payment confirmed manually! The user is now unlocked."

@app.route("/admin/add_user", methods=["GET", "POST"])
def admin_add_user():
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    if request.method == "POST":
        phone = request.form.get("phone", "").strip()
        if phone.startswith("0"):
            phone = "254" + phone[1:]
        elif len(phone) == 9:
            phone = "254" + phone

        if phone.startswith("254") and len(phone) == 12:
            conn = sqlite3.connect('payments.db')
            c = conn.cursor()
            c.execute('''INSERT INTO transactions (phone, amount, checkout_request_id, timestamp, status, mpesa_receipt)
                         VALUES (?, ?, ?, ?, ?, ?)''',
                      (phone, 5000, "MANUAL_" + datetime.now().strftime("%Y%m%d%H%M%S"), 
                       datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "paid", "MANUAL_ADD"))
            conn.commit()
            conn.close()
            return f"✅ User {phone} has been manually unlocked!"
        else:
            return "Invalid phone number"

    return """
    <div style="max-width:500px;margin:80px auto;padding:40px;border:1px solid #ddd;border-radius:12px;">
        <h2>Manually Unlock User</h2>
        <form method="POST">
            <label>Phone Number (e.g. 0712345678)</label><br>
            <input type="tel" name="phone" required style="width:100%;padding:12px;margin:15px 0;"><br><br>
            <button type="submit" style="width:100%;padding:12px;background:#00A651;color:white;border:none;border-radius:8px;">Unlock User</button>
        </form>
        <br><a href="/admin/dashboard">← Back to Dashboard</a>
    </div>
    """

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect("/admin/login")

if __name__ == "__main__":
    app.run(debug=True)
