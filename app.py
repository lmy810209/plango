import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)

# 세션키 (Render > Environment에서 SECRET_KEY 환경변수로 넣어두면 더 안전)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")

# ---- 데모용 계정 (요청하신 값) ----
USERS = {
    "lmy8129": {"password": "@@qwer0512", "role": "admin"},   # 관리자
    "my8129":  {"password": "@@qwer0512", "role": "worker"},  # 작업자
}

# ---- 로그인/권한 데코레이터 ----
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
                # 권한없음 -> 자신의 대시보드로 보내기
                return redirect(url_for("dashboard"))
            return view(*args, **kwargs)
        return wrapped
    return decorator

# ---- 라우트 ----
@app.route("/")
def index():
    # 로그인 상태면 역할에 맞게 이동, 아니면 로그인 페이지
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
