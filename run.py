import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")
    print(f"\n[+] Smart Expense Tracker & AI Advisor is running!")
    print(f"[*] Local Access:   http://127.0.0.1:{port}")
    print(f"[*] Network/Mobile: http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=debug)
