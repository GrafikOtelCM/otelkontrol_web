from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import pandas as pd
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "supersecretkey"

# =====================
# Kullanıcılar
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
    if 'username' not in session or 'api_key' not in session:
        return redirect(url_for('login'))

    filename = request.args.get('filename')
    if not filename:
        return redirect(url_for('upload'))

    filepath = os.path.join('uploads', filename)
    if not os.path.exists(filepath):
        flash("Dosya bulunamadı.")
        return redirect(url_for('upload'))

    df = pd.read_excel(filepath)

    error_values = ["", "N/A", "None", 0]
    errors = []

    for i, row in df.iterrows():
        for col in df.columns:
            value = row[col]
            if pd.isna(value) or str(value).strip() in map(str, error_values):
                errors.append(f"Satır {i+2}, Sütun '{col}' → Geçersiz değer: {value}")

    data = df.fillna("").to_dict(orient='records')
    columns = df.columns.tolist()

    return render_template(
        "report.html",
        data=data,
        columns=columns,
        filename=filename,
        errors=errors,
        error_values=[str(e) for e in error_values],
        username=session.get('username')
    )

# =====================
# Çıkış
# =====================
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# =====================
# Sunucu Başlat
# =====================
if __name__ == '__main__':
    app.run(debug=True)
