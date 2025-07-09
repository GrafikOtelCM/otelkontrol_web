from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import pandas as pd
from werkzeug.utils import secure_filename
import googlemaps
from utils import normalize_phone_number, sanitize_place_id

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
    hatali_place_ids = []

    if request.method == 'POST':
        file = request.files.get('file')
        if file and file.filename.endswith(('.xls', '.xlsx')):
            filename = secure_filename(file.filename)
            os.makedirs('uploads', exist_ok=True)
            filepath = os.path.join('uploads', filename)
            file.save(filepath)

            try:
                df = pd.read_excel(filepath)
                if 'Place ID' not in df.columns:
                    flash("Excel dosyasında 'Place ID' sütunu bulunamadı.", "danger")
                    return redirect(url_for('upload'))

                gmaps = googlemaps.Client(key=session['api_key'])

                for index, row in df.iterrows():
                    place_id = sanitize_place_id(row.get('Place ID', ''))
                    otel_adi = str(row.get('Otel Adı', '')).strip()

                    if not place_id:
                        hatali_place_ids.append((otel_adi, "Boş Place ID"))
                        continue

                    try:
                        gmaps.place(place_id=place_id, fields=['name'])
                    except Exception as e:
                        hata_mesaji = str(e)
                        if "INVALID_REQUEST" in hata_mesaji or "NOT_FOUND" in hata_mesaji:
                            hatali_place_ids.append((otel_adi, hata_mesaji))
                if hatali_place_ids:
                    return render_template('upload.html', error=None, hatalar=hatali_place_ids)
                else:
                    return redirect(url_for('report', filename=filename))

            except Exception as e:
                error = f"Excel okunurken hata oluştu: {str(e)}"
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
        flash("Dosya bulunamadı.", "danger")
        return redirect(url_for('upload'))

    df = pd.read_excel(filepath)
    gmaps = googlemaps.Client(key=session['api_key'])

    dogru_kayitlar = []
    telefon_hatalilar = []
    websitesizler = []

    for index, row in df.iterrows():
        otel_adi = str(row.get('Otel Adı', '')).strip()
        excel_phone = normalize_phone_number(str(row.get('Telefon', '')))
        place_id = sanitize_place_id(row.get('Place ID', ''))

        if not place_id:
            continue

        try:
            details = gmaps.place(place_id=place_id, fields=['formatted_phone_number', 'website'])
            result = details.get('result', {})
            google_phone = normalize_phone_number(result.get('formatted_phone_number', ''))
            website = result.get('website', '')

            if not website:
                websitesizler.append({'name': otel_adi, 'tel': excel_phone})
            elif google_phone and google_phone != excel_phone:
                telefon_hatalilar.append({
                    'name': otel_adi,
                    'expected_tel': excel_phone,
                    'actual_tel': google_phone,
                    'website': website
                })
            else:
                dogru_kayitlar.append({'name': otel_adi, 'tel': excel_phone, 'website': website})

        except Exception as e:
            print(f"[HATA] {otel_adi}: {str(e)}")

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

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
