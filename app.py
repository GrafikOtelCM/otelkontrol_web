from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import pandas as pd
from werkzeug.utils import secure_filename
import googlemaps

app = Flask(__name__)
app.secret_key = "supersecretkey"

# =====================
# Çoklu Kullanıcı Bilgisi
# =====================
USERS = {
    "otelcm": "OtelCM741952",
    "ecem": "e741952",
    "grafik": "g741952"
}

# =====================
# Giriş Sayfası
# =====================
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

# =====================
# API Key Sayfası
# =====================
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

# =====================
# Dosya Yükleme Sayfası
# =====================
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

# =====================
# Rapor Sayfası
# =====================
@app.route('/report')
def report():
    if 'api_key' not in session or 'username' not in session:
        return redirect(url_for('login'))

    filename = request.args.get('filename')
    if not filename:
        flash("Yüklenecek dosya bulunamadı.", "danger")
        return redirect(url_for('upload'))

    filepath = os.path.join('uploads', filename)
    if not os.path.exists(filepath):
        flash("Dosya bulunamadı.", "danger")
        return redirect(url_for('upload'))

    df = pd.read_excel(filepath)
    df.fillna('', inplace=True)

    matched_records = []
    mismatched_phones = []
    no_website_hotels = []

    gmaps = googlemaps.Client(key=session['api_key'])

    for index, row in df.iterrows():
        otel_adi = str(row.get("Otel Adı", "")).strip()
        excel_telefon = str(row.get("Telefon", "")).strip().replace(" ", "")
        place_id = str(row.get("Place ID", "")).strip()

        if not place_id:
            continue

        try:
            place = gmaps.place(place_id=place_id, fields=['formatted_phone_number', 'website'])
            g_phone = place.get('result', {}).get('formatted_phone_number', '')
            g_website = place.get('result', {}).get('website', '')

            clean_gphone = g_phone.replace(" ", "").replace("(", "").replace(")", "").replace("-", "")

            if g_phone and excel_telefon not in clean_gphone:
                mismatched_phones.append({
                    "name": otel_adi,
                    "excel": excel_telefon,
                    "google": g_phone
                })
            elif not g_website:
                no_website_hotels.append({
                    "name": otel_adi,
                    "phone": excel_telefon
                })
            else:
                matched_records.append({
                    "name": otel_adi,
                    "phone": excel_telefon,
                    "place_id": place_id
                })

        except Exception as e:
            print(f"[HATA] {otel_adi}: {str(e)}")
            continue

    return render_template(
        'report.html',
        matched_records=matched_records,
        mismatched_phones=mismatched_phones,
        no_website_hotels=no_website_hotels
    )

# =====================
# Oturum Sonlandırma
# =====================
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# =====================
# Uygulama Başlat
# =====================
if __name__ == '__main__':
    app.run(debug=True)
