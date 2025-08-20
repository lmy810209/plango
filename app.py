from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from functools import wraps

app = Flask(__name__)
app.secret_key = "your_secret_key"  # 세션용

# ---------------------------
# DB 연결 함수
# ---------------------------
def get_db_connection():
    conn = sqlite3.connect("users.db")
    conn.row_factory = sqlite3.Row
    return conn

# ---------------------------
# 로그인 필요 데코레이터
# ---------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("로그인이 필요합니다.")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# ---------------------------
# 관리자 권한 필요 데코레이터
# ---------------------------
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "role" not in session or session["role"] != "관리자":
            flash("관리자 권한이 필요합니다.")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated_function

# ---------------------------
# 라우트
# ---------------------------

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE username = ? AND password = ?", 
                            (username, password)).fetchone()
        conn.close()

        if user:
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            flash("로그인 성공")
            return redirect(url_for("index"))
        else:
            flash("로그인 실패")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("로그아웃 완료")
    return redirect(url_for("index"))

# ---------------------------
# 사용자 관리 (관리자 전용)
# ---------------------------

@app.route("/users")
@admin_required
def user_list():
    conn = get_db_connection()
    users = conn.execute("SELECT * FROM users").fetchall()
    conn.close()
    return render_template("users.html", users=users)

@app.route("/users/add", methods=["GET", "POST"])
@admin_required
def user_add():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]
        name = request.form["name"]
        contact = request.form["contact"]

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO users (username, email, password, role, name, contact) VALUES (?, ?, ?, ?, ?, ?)",
            (username, email, password, role, name, contact),
        )
        conn.commit()
        conn.close()
        flash("사용자 추가 완료")
        return redirect(url_for("user_list"))
    return render_template("user_add.html")

@app.route("/users/edit/<int:user_id>", methods=["GET", "POST"])
@admin_required
def user_edit(user_id):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]
        name = request.form["name"]
        contact = request.form["contact"]

        if password:  # 비번 변경 시만 업데이트
            conn.execute(
                "UPDATE users SET email=?, password=?, role=?, name=?, contact=? WHERE id=?",
                (email, password, role, name, contact, user_id),
            )
        else:
            conn.execute(
                "UPDATE users SET email=?, role=?, name=?, contact=? WHERE id=?",
                (email, role, name, contact, user_id),
            )

        conn.commit()
        conn.close()
        flash("사용자 수정 완료")
        return redirect(url_for("user_list"))

    conn.close()
    return render_template("user_edit.html", user=user)

@app.route("/users/delete/<int:user_id>")
@admin_required
def user_delete(user_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
    flash("사용자 삭제 완료")
    return redirect(url_for("user_list"))

# ---------------------------
# 앱 실행
# ---------------------------
if __name__ == "__main__":
    # 최초 실행 시 DB 테이블 생성
    conn = get_db_connection()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        name TEXT,
        contact TEXT
    )
    """)
    conn.commit()
    conn.close()

    app.run(debug=True)
