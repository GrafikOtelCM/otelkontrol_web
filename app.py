from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import pandas as pd
from werkzeug.utils import secure_filename
import googlemaps
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"

USERS = {
    "otelcm": "OtelCM741952",
    "ecem": "e741952",
    "grafik": "g741952"
}

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in USERS and USERS[username] == password:
            session['username'] = username
            return redirect(url_for('apikey'))
        else:
            error = "Kullanıcı adı veya şifre hatalı"
    return render_template('login.html', error=error)

@app.route('/apikey', methods=['GET', 'POST'])
def apikey():
    if 'username' not in session:
        return redirect(url_for('login'))

    error = None
    if request.method == 'POST':
        api_key = request.form.get('api_key')
        if not api_key or len(api_key.strip()) < 10:
            error = "Geçerli bir API anahtarı girin."
        else:
            session['api_key'] = api_key.strip()
            return redirect(url_for('upload'))

    return render_template('apikey.html', error=error)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'api_key' not in session:
        return redirect(url_for('apikey'))

    error = None
    if request.method == 'POST':
        file = request.files.get('file')
        if file and file.filename.endswith(('.xls', '.xlsx')):
            filename = secure_filename(file.filename)
            os.makedirs('uploads', exist_ok=True)
            filepath = os.path.join('uploads', filename)
            file.save(filepath)
            return redirect(url_for('report', filename=filename))
        else:
            error = "Lütfen geçerli bir Excel dosyası (.xls, .xlsx) yükleyin."
    return render_template('upload.html', error=error)

@app.route('/report')
def report():
    if 'api_key' not in session:
        return redirect(url_for('apikey'))

    filename = request.args.get('filename')
    if not filename:
        return redirect(url_for('upload'))

    filepath = os.path.join('uploads', filename)
    if not os.path.exists(filepath):
        flash("Dosya bulunamadı.")
        return redirect(url_for('upload'))

    df = pd.read_excel(filepath)
    df.fillna('', inplace=True)

    correct = []
    website_missing = []
    phone_mismatch = []

    gmaps = googlemaps.Client(key=session['api_key'])

    for index, row in df.iterrows():
        otel_adi = str(row.get('Otel Adı')).strip()
        excel_phone = str(row.get('Telefon')).strip()
        place_id = str(row.get('Place ID')).strip()

        try:
            details = gmaps.place(place_id=place_id, fields=['formatted_phone_number', 'website'])
            result = details.get('result', {})

            google_phone = str(result.get('formatted_phone_number', '')).replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
            excel_phone_clean = excel_phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")

            has_website = bool(result.get('website'))

            if not has_website:
                website_missing.append({'otel_adi': otel_adi, 'telefon': excel_phone})
            elif google_phone and excel_phone_clean != google_phone:
                phone_mismatch.append({
                    'otel_adi': otel_adi,
                    'beklenen': excel_phone,
                    'googledaki': google_phone
                })
            else:
                correct.append({
                    'otel_adi': otel_adi,
                    'telefon': excel_phone,
                    'place_id': place_id
                })
        except Exception as e:
            print(f"Hata: {otel_adi} - {e}")
            continue

    stats = {
        'total': len(df),
        'correct': len(correct),
        'website_missing': len(website_missing),
        'phone_mismatch': len(phone_mismatch)
    }

    return render_template('report.html',
                           correct=correct,
                           website_missing=website_missing,
                           phone_mismatch=phone_mismatch,
                           stats=stats)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
