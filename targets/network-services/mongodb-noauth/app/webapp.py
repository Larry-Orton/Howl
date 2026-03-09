#!/usr/bin/env python3
"""DataPulse Analytics - Web application with MongoDB backend."""

from flask import Flask, render_template, request, redirect, session, url_for
from pymongo import MongoClient
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

client = MongoClient("mongodb://127.0.0.1:27017/")
db = client["datapulse"]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/robots.txt")
def robots():
    return "User-agent: *\nDisallow: /.internal/\nDisallow: /admin/\n", 200, {"Content-Type": "text/plain"}

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form.get("email", "")
        password = request.form.get("password", "")
        user = db.users.find_one({"email": email})
        if user and user.get("plaintext_backup") == password:
            session["user"] = email
            session["role"] = user.get("role", "user")
            return redirect("/admin/system" if user.get("role") == "admin" else "/dashboard")
        error = "Invalid credentials"
    return render_template("login.html", error=error)

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")
    return render_template("dashboard.html", user=session["user"])

@app.route("/admin/system")
def admin_system():
    if "user" not in session or session.get("role") != "admin":
        return redirect("/login")
    try:
        flag = open("/opt/datapulse/admin_flag/root.txt").read().strip()
    except FileNotFoundError:
        flag = "FLAG_NOT_FOUND"
    return render_template("admin.html", flag=flag)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
