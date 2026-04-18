from flask import Flask, render_template, request, session, redirect, url_for
import sqlite3
from datetime import datetime
import requests
import base64
import os

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "demo-secret-key-2026-change-later")

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
    score = 100
    spam_risk = "Low"

    # === COMPLIANCE CHECKS ===
    if not any(word in body_lower for word in UNSUBSCRIBE_REQUIRED):
        report.append({"type": "warning", "msg": "Missing unsubscribe link (high spam risk)"})
        score -= 25

    if not any(word in body_lower for word in ADDRESS_REQUIRED):
        report.append({"type": "warning", "msg": "Missing physical address (CAN-SPAM / legal requirement)"})
        score -= 15

    # === SPAM & HYPE CHECKS ===
    hype_count = sum(1 for word in HYPE_WORDS if word in body_lower)
    if hype_count > 0:
        report.append({"type": "warning", "msg": f"Contains {hype_count} hype word(s)"})
        score -= hype_count * 10
        if hype_count >= 2:
            spam_risk = "High"

    # Urgency words (use sparingly)
    urgency_count = sum(1 for word in URGENCY_WORDS if word in body_lower)
    if urgency_count > 2:
        report.append({"type": "info", "msg": "Too many urgency words - can trigger spam filters"})
        score -= 12

    # Call-To-Action
    if not any(word in body_lower for word in CTA_WORDS):
        report.append({"type": "warning", "msg": "Weak or missing Call-To-Action"})
        score -= 15

    # === ADDITIONAL SPAM SIGNALS ===
    if body.count('!') > 6:
        report.append({"type": "warning", "msg": "Too many exclamation marks (!)" })
        score -= 10

    if len([c for c in body if c.isupper()]) > len(body) * 0.25:
        report.append({"type": "warning", "msg": "Too much uppercase text"})
        score -= 12

    # Link count
    link_count = body_lower.count("http")
    if link_count > 5:
        report.append({"type": "warning", "msg": f"Too many links ({link_count})"})
        score -= 10

    # Length checks
    if len(body) < 60:
        report.append({"type": "warning", "msg": "Email body is too short"})
        score -= 8
    elif len(body) > 900:
        report.append({"type": "info", "msg": "Email is very long - consider shortening"})
        score -= 5

    # Tone detection
    tone = "neutral"
    if any(word in body_lower for word in FRIENDLY_WORDS):
        tone = "friendly"
    elif any(word in body_lower for word in URGENT_WORDS):
        tone = "urgent"

    # Final score bounds
    score = max(30, min(100, score))

    # Adjust spam risk based on final score
    if score < 55:
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
        "tone": tone,
        "status": "success"
    })

# ============== OWNER UNLOCK ==============
@app.route("/owner/unlock")
def owner_unlock():
    key = request.args.get("key")
    if key == "BongaMail2030?":   # Change this for better security
        session["unlocked"] = True
        session["pending_phone"] = "254700000000"
        return redirect(url_for("index"))
    return "Invalid owner key", 403

# ============== ADMIN PASSWORD ==============
ADMIN_PASSWORD = "BongaMail2030?"

# ============== ADMIN LOGIN ==============
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect("/admin/dashboard")
        else:
            error = "Incorrect password. Please try again."
    
    return render_template('admin/login.html')
    

# ============== ADMIN DASHBOARD ==============
@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect("/admin/login")

    conn = sqlite3.connect('payments.db')
    c = conn.cursor()
    c.execute("SELECT id, phone, checkout_request_id, status FROM transactions WHERE status = 'pending' ORDER BY timestamp DESC")
    pending = c.fetchall()
    conn.close()

    return render_template('admin/dashboard.html')
    

# ============== MANUAL CONFIRM ==============
@app.route("/admin/manual_confirm", methods=["POST"])
def manual_confirm():
    if not session.get("admin_logged_in"):
        return "Unauthorized", 401

    checkout_id = request.form.get("checkout_id")
    receipt = request.form.get("receipt")

    if not checkout_id:
        return "Missing checkout_id", 400

    conn = sqlite3.connect('payments.db')
    c = conn.cursor()
    c.execute("UPDATE transactions SET status='paid', mpesa_receipt=? WHERE checkout_request_id=?", (receipt, checkout_id))
    conn.commit()
    conn.close()

    return redirect("/admin/dashboard.html")


# ============== ADMIN ADD USER ==============
@app.route("/admin/add_user", methods=["GET", "POST"])
def admin_add_user():
    if not session.get("admin_logged_in"):
        return redirect("/admin/login.html")

    message = None
    error = None

    if request.method == "POST":
        phone = request.form.get("phone", "").strip()
        if phone.startswith("0"):
            phone = "254" + phone[1:]
        elif len(phone) == 9:
            phone = "254" + phone

        if phone.startswith("254") and len(phone) == 12:
            try:
                conn = sqlite3.connect('payments.db')
                c = conn.cursor()
                c.execute('''INSERT INTO transactions 
                             (phone, amount, checkout_request_id, timestamp, status, mpesa_receipt)
                             VALUES (?, ?, ?, ?, ?, ?)''',
                          (phone, 5000, 
                           "MANUAL_" + datetime.now().strftime("%Y%m%d%H%M%S"), 
                           datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                           "paid", 
                           "MANUAL_ADD"))
                conn.commit()
                conn.close()
                message = f"✅ User {phone} has been manually unlocked!"
            except Exception as e:
                error = f"Database error: {str(e)}"
        else:
            error = "Invalid phone number. Please use format like 0712345678"

    return render_template('admin/add_user.html')
boar

# ============== ADMIN LOGOUT ==============
@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect("/admin/login")

if __name__ == "__main__":
    app.run(debug=True)
