from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import pandas as pd
from werkzeug.utils import secure_filename
from utils import analyze_hotels

app = Flask(__name__)
app.secret_key = "supersecretkey"

USERS = {
    "otelcm": "OtelCM741952",
    "ecem": "e741952",
    "grafik": "g741952"
}

@app.route("/", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username in USERS and USERS[username] == password:
            session["username"] = username
            return redirect(url_for("apikey"))
        else:
            error = "Kullanıcı adı veya şifre hatalı"
    return render_template("login.html", error=error)

@app.route("/apikey", methods=["GET", "POST"])
def apikey():
    if "username" not in session:
        return redirect(url_for("login"))
    error = None
    if request.method == "POST":
        api_key = request.form.get("api_key")
        if not api_key or len(api_key.strip()) < 10:
            error = "Geçerli bir API anahtarı girin."
        else:
            session["api_key"] = api_key.strip()
            return redirect(url_for("upload"))
    return render_template("apikey.html", error=error)

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if "api_key" not in session:
        return redirect(url_for("apikey"))
    error = None
    if request.method == "POST":
        file = request.files.get("file")
        if file and file.filename.endswith((".xls", ".xlsx")):
            filename = secure_filename(file.filename)
            os.makedirs("uploads", exist_ok=True)
            filepath = os.path.join("uploads", filename)
            file.save(filepath)
            return redirect(url_for("report", filename=filename))
        else:
            error = "Lütfen geçerli bir Excel dosyası yükleyin (.xls veya .xlsx)."
    return render_template("upload.html", error=error)

@app.route("/report")
def report():
    filename = request.args.get("filename")
    if not filename:
        return redirect(url_for("upload"))
    filepath = os.path.join("uploads", filename)
    if not os.path.exists(filepath):
        flash("Dosya bulunamadı.")
        return redirect(url_for("upload"))

    df = pd.read_excel(filepath)
    print(f"[INFO] Excel'den okunan satır sayısı: {len(df)}")
    dogru_kayitlar, telefon_hatalilar, websitesizler, stats = analyze_hotels(df, session["api_key"])

    return render_template(
        "report.html",
        dogru_kayitlar=dogru_kayitlar,
        telefon_hatalilar=telefon_hatalilar,
        websitesizler=websitesizler,
        stats=stats
    )

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
