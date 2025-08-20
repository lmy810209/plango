# app.py (전체 완본)

import os
from datetime import date
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for, session, jsonify
)

app = Flask(__name__)

# 세션 키 (Render > Environment에 SECRET_KEY 넣어두면 그 값 사용)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")

# ---------------------------------------------------------------------
# 데모용 계정/데이터 (추후 DB로 교체 가능)
# ---------------------------------------------------------------------
# 로그인 계정 (아이디 → 비번/역할)
USERS = {
    "lmy8129": {"password": "@@qwer0512", "role": "admin"},   # 관리자
    "my8129":  {"password": "@@qwer0512", "role": "worker"},  # 작업자
}

# 사용자 관리 표 데이터 (화면용)
USER_ROWS = [
    # 샘플 데이터들 (원하면 비워도 됨)
    {
        "username": "test123",
        "name": "테스트사용자",
        "email": "test123@hmc.com",
        "phone": "010-1234-5678",
        "role": "worker",
        "joined": "-",
        "active": True
    },
    {
        "username": "worker1",
        "name": "김작업자",
        "email": "worker1@hmc.com",
        "phone": "",
        "role": "worker",
        "joined": "2025-08-12",
        "active": True
    },
    {
        "username": "my8129",
        "name": "작업자",
        "email": "worker@hmc.com",
        "phone": "",
        "role": "worker",
        "joined": "2025-08-12",
        "active": True
    },
    {
        "username": "hmcadmin",
        "name": "관리자",
        "email": "hmcadmin@hmc.com",
        "phone": "",
        "role": "admin",
        "joined": "2025-08-09",
        "active": True
    },
    {
        "username": "lmy8129",
        "name": "관리자",
        "email": "admin@hmc.com",
        "phone": "",
        "role": "admin",
        "joined": "2025-08-09",
        "active": True
    },
]

# ---------------------------------------------------------------------
# 공통 데코레이터 (로그인/권한)
# ---------------------------------------------------------------------
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped

def role_required(role):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = session.get("user")
            if not user:
                return redirect(url_for("login"))
            if USERS.get(user, {}).get("role") != role:
                # 권한 없으면 자신의 대시보드로
                return redirect(url_for("dashboard"))
            return view(*args, **kwargs)
        return wrapped
    return decorator

# ---------------------------------------------------------------------
# 라우트: 인증/대시보드
# ---------------------------------------------------------------------
@app.route("/")
def index():
    if session.get("user"):
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        user = USERS.get(username)
        if user and user["password"] == password:
            session["user"] = username
            return redirect(url_for("dashboard"))
        else:
            error = "아이디 또는 비밀번호가 올바르지 않습니다."
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    user = session.get("user")
    role = USERS[user]["role"]
    if role == "admin":
        return redirect(url_for("admin_page"))
    return redirect(url_for("worker_page"))

@app.route("/admin")
@login_required
@role_required("admin")
def admin_page():
    user = session.get("user")
    return render_template("admin.html", user=user)

@app.route("/worker")
@login_required
@role_required("worker")
def worker_page():
    user = session.get("user")
    return render_template("worker.html", user=user)

# ---------------------------------------------------------------------
# 라우트: 관리자 전용 - 사용자 관리 화면
# ---------------------------------------------------------------------
@app.route("/admin/users")
@login_required
@role_required("admin")
def admin_users():
    user = session.get("user")
    return render_template("admin_users.html", user=user, rows=USER_ROWS)

# ---------------------------------------------------------------------
# 유틸 함수 (USER_ROWS 검색 등)
# ---------------------------------------------------------------------
def _find_user(username):
    for u in USER_ROWS:
        if u["username"] == username:
            return u
    return None

def _serialize_rows():
    return USER_ROWS

# ---------------------------------------------------------------------
# 관리자 전용 API: 사용자 추가/수정/삭제
# (프론트: admin_users.html에서 fetch로 호출)
# ---------------------------------------------------------------------
@app.post("/admin/api/users/add")
@login_required
@role_required("admin")
def api_user_add():
    f = request.form
    username = f.get("username", "").strip()
    email    = f.get("email", "").strip()
    password = f.get("password", "").strip()
    role     = f.get("role", "worker").strip()
    name     = f.get("name", "").strip() or "-"
    phone    = f.get("phone", "").strip()

    if not username or not email or role not in ("admin", "worker"):
        return jsonify(ok=False, msg="필수값 누락 또는 잘못된 역할"), 400
    if _find_user(username):
        return jsonify(ok=False, msg="이미 존재하는 사용자명입니다."), 409

    USER_ROWS.append({
        "username": username,
        "name": name,
        "email": email,
        "phone": phone,
        "role": role,
        "joined": date.today().isoformat(),
        "active": True
    })
    # 로그인용 dict도 동기화(초기 비번이 있을 때만)
    if password:
        USERS[username] = {"password": password, "role": role}

    return jsonify(ok=True, rows=_serialize_rows())

@app.post("/admin/api/users/<username>/update")
@login_required
@role_required("admin")
def api_user_update(username):
    u = _find_user(username)
    if not u:
        return jsonify(ok=False, msg="사용자를 찾을 수 없습니다."), 404

    f = request.form
    new_email = f.get("email", "").strip()
    new_pwd   = f.get("password", "").strip()     # 변경 시에만 반영
    new_role  = f.get("role", "worker").strip()
    new_name  = f.get("name", "").strip() or "-"
    new_phone = f.get("phone", "").strip()
    active    = f.get("active", "true").lower() == "true"

    if not new_email or new_role not in ("admin", "worker"):
        return jsonify(ok=False, msg="필수값 누락 또는 잘못된 역할"), 400

    # 화면 데이터 수정
    u["email"]  = new_email
    u["name"]   = new_name
    u["phone"]  = new_phone
    u["role"]   = new_role
    u["active"] = active

    # 로그인 dict 수정
    if username in USERS:
        USERS[username]["role"] = new_role
        if new_pwd:
            USERS[username]["password"] = new_pwd
    else:
        if new_pwd:
            USERS[username] = {"password": new_pwd, "role": new_role}

    return jsonify(ok=True, rows=_serialize_rows())

@app.post("/admin/api/users/<username>/delete")
@login_required
@role_required("admin")
def api_user_delete(username):
    u = _find_user(username)
    if not u:
        return jsonify(ok=False, msg="사용자를 찾을 수 없습니다."), 404
    USER_ROWS.remove(u)
    if username in USERS:
        del USERS[username]
    return jsonify(ok=True, rows=_serialize_rows())

# ---------------------------------------------------------------------
# 로컬 개발용 실행 (Render에서는 gunicorn이 Procfile/Start Command로 실행)
# ---------------------------------------------------------------------
if __name__ == "__main__":
    # 로컬에서 테스트할 때만 사용. Render 배포는 gunicorn이 실행함.
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
