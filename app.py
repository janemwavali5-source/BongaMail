
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




