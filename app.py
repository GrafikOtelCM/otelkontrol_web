from flask import Flask, render_template, request, redirect, url_for, session, flash
import googlemaps
import pandas as pd
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'supersecretkey'
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

AUTHORIZED_USERS = {
    "otelcm": "OtelCM741952",
    "muhammed": "muhammed2025",
    "can": "otelkontrol"
}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if AUTHORIZED_USERS.get(username) == password:
            session['username'] = username
            return redirect(url_for('apikey'))
        else:
            flash('Kullanıcı adı veya şifre hatalı.')
    return render_template('login.html')

@app.route('/apikey', methods=['GET', 'POST'])
def apikey():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        key = request.form['apikey'].strip()
        if key:
            session['apikey'] = key
            return redirect(url_for('upload'))
        else:
            flash('Lütfen geçerli bir API anahtarı girin.')
    return render_template('apikey.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'apikey' not in session:
        return redirect(url_for('apikey'))

    if request.method == 'POST':
        file = request.files.get('file')
        if file and file.filename.endswith(('.xls', '.xlsx')):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            return redirect(url_for('report', filename=filename))
        else:
            flash("Lütfen geçerli bir Excel dosyası yükleyin.")
    return render_template('upload.html')

@app.route('/report/<filename>')
def report(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    key = session.get('apikey')
    gmaps = googlemaps.Client(key=key)

    try:
        df = pd.read_excel(filepath)
    except Exception as e:
        flash(f"Excel dosyası okunamadı: {str(e)}")
        return redirect(url_for('upload'))

    if not {'place_id', 'telefon'}.issubset(df.columns):
        flash("Excel dosyasında 'place_id' ve 'telefon' sütunları olmalıdır.")
        return redirect(url_for('upload'))

    hatalar = []
    for index, row in df.iterrows():
        try:
            place = gmaps.place(place_id=row['place_id'])
            result = place['result']
            actual_phone = result.get('formatted_phone_number', 'YOK')
            website = 'VAR' if 'website' in result else 'YOK'
            if str(row['telefon']) != actual_phone:
                hatalar.append({
                    'satir': index + 2,
                    'otel': result.get('name', 'İsim yok'),
                    'adres': result.get('formatted_address', 'Adres yok'),
                    'beklenen': row['telefon'],
                    'gelen': actual_phone,
                    'website': website
                })
        except Exception as e:
            hatalar.append({
                'satir': index + 2,
                'otel': 'BİLİNEMEDİ',
                'adres': 'BİLİNEMEDİ',
                'beklenen': row['telefon'],
                'gelen': f"HATA: {str(e)}",
                'website': 'BİLİNEMEDİ'
            })
    return render_template('report.html', hatalar=hatalar)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    from waitress import serve
    serve(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
