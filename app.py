from flask import Flask, render_template, request, redirect, url_for, session
from functools import wraps
import os

app = Flask(__name__)
# 세션 키 (Render > Environment에 SECRET_KEY 환경변수로 넣어두면 더 안전)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")

# 임시 사용자 (나중에 DB로 바꿀 예정)
USERS = {
    "admin": "1234",   # 예시: 아이디 admin / 비번 1234
}

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped

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
        if USERS.get(username) == password:
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
    return render_template("dashboard.html", user=session.get("user"))
