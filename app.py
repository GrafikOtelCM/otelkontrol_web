
from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import pandas as pd
import googlemaps
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "supersecretkey"

USERS = {
    "otelcm": "OtelCM741952",
    "ecem": "e741952",
    "grafik": "g741952"
}

def normalize_phone(phone):
    return phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "").replace("+90", "").strip()

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if USERS.get(username) == password:
            session["username"] = username
            return redirect(url_for("apikey"))
        flash("Kullanıcı adı veya şifre hatalı")
    return render_template("login.html")

@app.route("/apikey", methods=["GET", "POST"])
def apikey():
    if "username" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        api_key = request.form.get("api_key")
        if api_key and len(api_key.strip()) > 10:
            session["api_key"] = api_key.strip()
            return redirect(url_for("upload"))
        flash("Geçerli bir API anahtarı girin.")
    return render_template("apikey.html")

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if "api_key" not in session:
        return redirect(url_for("apikey"))
    if request.method == "POST":
        file = request.files.get("file")
        if file and file.filename.endswith((".xls", ".xlsx")):
            filename = secure_filename(file.filename)
            os.makedirs("uploads", exist_ok=True)
            filepath = os.path.join("uploads", filename)
            file.save(filepath)
            return redirect(url_for("report", filename=filename))
        flash("Lütfen geçerli bir Excel dosyası (.xls, .xlsx) yükleyin.")
    return render_template("upload.html")

@app.route("/report")
def report():
    if "api_key" not in session:
        return redirect(url_for("login"))
    filename = request.args.get("filename")
    if not filename:
        return redirect(url_for("upload"))
    filepath = os.path.join("uploads", filename)
    if not os.path.exists(filepath):
        flash("Dosya bulunamadı.")
        return redirect(url_for("upload"))
    df = pd.read_excel(filepath)
    gmaps = googlemaps.Client(key=session["api_key"])

    dogru_kayitlar = []
    telefon_hatalilar = []
    websitesizler = []

    for _, row in df.iterrows():
        otel_adi = str(row.get("Otel Adı")).strip()
        excel_tel = normalize_phone(str(row.get("Telefon")))
        place_id = str(row.get("Place ID")).strip()

        try:
            response = gmaps.place(place_id=place_id, fields=["formatted_phone_number", "website"])
            result = response.get("result", {})
            google_tel = normalize_phone(result.get("formatted_phone_number", ""))
            website = result.get("website", "")

            if not website:
                websitesizler.append({"name": otel_adi, "tel": row.get("Telefon")})
            elif google_tel and google_tel != excel_tel:
                telefon_hatalilar.append({
                    "name": otel_adi,
                    "expected_tel": row.get("Telefon"),
                    "actual_tel": result.get("formatted_phone_number", ""),
                    "website": website
                })
            else:
                dogru_kayitlar.append({
                    "name": otel_adi,
                    "tel": row.get("Telefon"),
                    "website": website
                })
        except Exception:
            continue

    stats = {
        "total": len(df),
        "dogru": len(dogru_kayitlar),
        "telefon": len(telefon_hatalilar),
        "web": len(websitesizler)
    }

    return render_template("report.html",
                           dogru_kayitlar=dogru_kayitlar,
                           telefon_hatalilar=telefon_hatalilar,
                           websitesizler=websitesizler,
                           stats=stats)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
