import os
import sqlite3
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret")

# --- DB 경로 (환경변수 DB_PATH가 있으면 그걸 사용: Render 디스크 권장) ---
default_db_dir = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(default_db_dir, exist_ok=True)
DB_PATH = os.environ.get("DB_PATH", os.path.join(default_db_dir, "hmc.db"))

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        name TEXT,
        email TEXT,
        phone TEXT,
        role TEXT CHECK(role IN ('admin','worker')) NOT NULL DEFAULT 'worker',
        active INTEGER NOT NULL DEFAULT 1,
        joined_at TEXT
    )""")
    conn.commit()
    cur.execute("SELECT COUNT(*) AS c FROM users")
    if cur.fetchone()["c"] == 0:
        seed = [
            ("lmy8129", "@@qwer0512", "관리자", "lmy8129@hmc.com", None, "admin", 1),
            ("my8129", "@@qwer0512", "김명규", "worker1@hmc.com", None, "worker", 1),
            ("hmcadmin", "@@qwer0512", "관리자", "hmcadmin@hmc.com", None, "admin", 1),
        ]
        for u, p, n, e, ph, r, a in seed:
            cur.execute("""
                INSERT INTO users (username,password,name,email,phone,role,active,joined_at)
                VALUES (?,?,?,?,?,?,?,?)
            """, (u, p, n, e, ph, r, a, datetime.now().strftime("%Y-%m-%d")))
        conn.commit()
    conn.close()

# --- 인증 데코레이터 ---
def login_required(f):
    @wraps(f)
    def _w(*a, **kw):
        if "user_id" not in session:
            return redirect(url_for("login", next=request.path))
        return f(*a, **kw)
    return _w

def admin_required(f):
    @wraps(f)
    def _w(*a, **kw):
        if "user_id" not in session:
            return redirect(url_for("login", next=request.path))
        if session.get("role") != "admin":
            flash("관리자만 접근 가능합니다.", "warning")
            return redirect(url_for("dashboard"))
        return f(*a, **kw)
    return _w

# --- 로그인/로그아웃 ---
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username","").strip()
        password = request.form.get("password","").strip()
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cur.fetchone()
        conn.close()
        if user and user["password"] == password and user["active"] == 1:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["name"] = user["name"] or user["username"]
            session["role"] = user["role"]
            flash("로그인되었습니다.", "success")
            return redirect(request.args.get("next") or url_for("dashboard"))
        flash("로그인 실패(아이디/비번/비활성 확인).", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("로그아웃되었습니다.", "info")
    return redirect(url_for("login"))

# --- 페이지 ---
@app.route("/")
@login_required
def dashboard():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM users WHERE role='worker'")
    workers = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) AS c FROM users")
    total_users = cur.fetchone()["c"]
    conn.close()
    return render_template("dashboard.html", workers=workers, total_users=total_users)

# --- 관리 ▸ 사용자 관리 ---
@app.route("/admin/users")
@admin_required
def admin_users():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users ORDER BY id DESC")
    users = cur.fetchall()
    conn.close()
    return render_template("users.html", users=users)

@app.route("/admin/users/create", methods=["POST"])
@admin_required
def create_user():
    f = request.form
    username = f.get("username","").strip()
    password = f.get("password","").strip()
    email = f.get("email","").strip()
    role = f.get("role","worker")
    name = f.get("name","").strip() or None
    phone = f.get("phone","").strip() or None
    if not username or not password or not email:
        flash("사용자명/비밀번호/이메일은 필수입니다.", "warning")
        return redirect(url_for("admin_users"))
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO users (username,password,name,email,phone,role,active,joined_at)
            VALUES (?,?,?,?,?,?,1,?)
        """, (username, password, name, email, phone, role, datetime.now().strftime("%Y-%m-%d")))
        conn.commit()
        conn.close()
        flash("사용자를 추가했습니다.", "success")
    except sqlite3.IntegrityError:
        flash("이미 존재하는 사용자명입니다.", "danger")
    return redirect(url_for("admin_users"))

@app.route("/admin/users/<int:user_id>/update", methods=["POST"])
@admin_required
def update_user(user_id):
    f = request.form
    username = f.get("username","").strip()
    email = f.get("email","").strip()
    role = f.get("role","worker")
    name = f.get("name","").strip() or None
    phone = f.get("phone","").strip() or None
    new_pw = f.get("new_password","").strip()
    active = 1 if f.get("active") == "on" else 0
    if not username or not email:
        flash("사용자명/이메일은 필수입니다.", "warning")
        return redirect(url_for("admin_users"))
    conn = get_db()
    cur = conn.cursor()
    if new_pw:
        cur.execute("""
            UPDATE users SET username=?, email=?, role=?, name=?, phone=?, active=?, password=?
            WHERE id=?
        """, (username, email, role, name, phone, active, new_pw, user_id))
    else:
        cur.execute("""
            UPDATE users SET username=?, email=?, role=?, name=?, phone=?, active=?
            WHERE id=?
        """, (username, email, role, name, phone, active, user_id))
    conn.commit()
    conn.close()
    flash("사용자 정보를 수정했습니다.", "success")
    return redirect(url_for("admin_users"))

@app.route("/admin/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def delete_user(user_id):
    if session.get("user_id") == user_id:
        flash("본인 계정은 삭제할 수 없습니다.", "warning")
        return redirect(url_for("admin_users"))
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
    flash("사용자를 삭제했습니다.", "success")
    return redirect(url_for("admin_users"))

# --- 로컬 실행용 (Render에서는 gunicorn이 app:app을 사용) ---
if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
