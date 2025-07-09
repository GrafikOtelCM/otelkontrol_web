from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import pandas as pd
import googlemaps
from werkzeug.utils import secure_filename
from utils import normalize_phone_number  # ← normalize fonksiyonu eklendi

app = Flask(__name__)
app.secret_key = 'supersecretkey'

USERS = {
    'otelcm': 'OtelCM741952',
    'ecem': 'e741952',
    'grafik': 'g741952'
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
    filename = request.args.get('filename')
    if not filename:
        return redirect(url_for('upload'))

    filepath = os.path.join('uploads', filename)
    if not os.path.exists(filepath):
        flash("Dosya bulunamadı.")
        return redirect(url_for('upload'))

    df = pd.read_excel(filepath)
    gmaps = googlemaps.Client(key=session['api_key'])

    dogru_kayitlar = []
    telefon_hatalilar = []
    websitesizler = []

    for index, row in df.iterrows():
        otel_adi = str(row.get('Otel Adı')).strip()
        excel_phone = str(row.get('Telefon')).strip()
        place_id = str(row.get('Place ID')).strip()

        try:
            details = gmaps.place(place_id=place_id, fields=['formatted_phone_number', 'website'])
            result = details.get('result', {})

            google_phone = normalize_phone_number(result.get('formatted_phone_number', ''))
            excel_phone_clean = normalize_phone_number(excel_phone)
            website = result.get('website', None)

            if not website:
                websitesizler.append({'name': otel_adi, 'tel': excel_phone})
            elif google_phone and google_phone != excel_phone_clean:
                telefon_hatalilar.append({
                    'name': otel_adi,
                    'expected_tel': excel_phone,
                    'actual_tel': result.get('formatted_phone_number', ''),
                    'website': website
                })
            else:
                dogru_kayitlar.append({
                    'name': otel_adi,
                    'tel': excel_phone,
                    'website': website
                })
        except Exception as e:
            print(f"Hata oluştu ({otel_adi}): {e}")

    stats = {
        'total': len(df),
        'dogru': len(dogru_kayitlar),
        'telefon': len(telefon_hatalilar),
        'web': len(websitesizler)
    }

    return render_template('report.html',
                           dogru_kayitlar=dogru_kayitlar,
                           telefon_hatalilar=telefon_hatalilar,
                           websitesizler=websitesizler,
                           stats=stats)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
