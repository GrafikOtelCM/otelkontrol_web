import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import googlemaps
import pandas as pd
import os
import datetime

# Kullanıcı girişi kontrolü
AUTHORIZED_USERS = {
    "admin": "sifre123",
    "muhammed": "muhammed2025",
    "efendim": "otelkontrol"
}

def start_app():
    def validate_login():
        username = user_entry.get()
        password = pass_entry.get()

        if AUTHORIZED_USERS.get(username) == password:
            login_window.destroy()
            run_main_app()
        else:
            messagebox.showerror("Giriş Hatası", "Kullanıcı adı veya şifre hatalı.")

    login_window = tk.Tk()
    login_window.title("🔐 Kullanıcı Girişi")
    login_window.geometry("400x220")
    login_window.configure(bg="#f0f4ff")

    label_title = tk.Label(login_window, text="Otel Kontrol Sistemi Girişi", font=("Helvetica", 14, "bold"), bg="#f0f4ff", fg="#002b80")
    label_title.pack(pady=10)

    tk.Label(login_window, text="Kullanıcı Adı:", bg="#f0f4ff").pack()
    user_entry = tk.Entry(login_window, width=30)
    user_entry.pack(pady=5)

    tk.Label(login_window, text="Şifre:", bg="#f0f4ff").pack()
    pass_entry = tk.Entry(login_window, show="*", width=30)
    pass_entry.pack(pady=5)

    login_btn = tk.Button(login_window, text="Giriş Yap", bg="#004080", fg="white", font=("Arial", 10, "bold"), command=validate_login)
    login_btn.pack(pady=15)

    login_window.mainloop()

def get_api_key():
    def on_submit():
        key = api_entry.get().strip()
        if not key:
            messagebox.showerror("API Hatası", "Lütfen geçerli bir Google API anahtarı girin.")
        else:
            api_window.destroy()
            run_verification(key)

    api_window = tk.Tk()
    api_window.title("🔐 Google Maps API Anahtarı")
    api_window.geometry("500x220")
    api_window.configure(bg="#e6f2ff")

    header = tk.Label(api_window, text="Otel Telefon Kontrol Sistemi", font=("Helvetica", 14, "bold"), bg="#e6f2ff", fg="#003366")
    header.pack(pady=10)

    label = tk.Label(api_window, text="Lütfen Google Maps API anahtarınızı girin:", font=("Arial", 11), bg="#e6f2ff")
    label.pack(pady=5)

    api_entry = tk.Entry(api_window, width=50, font=("Arial", 11), show="*")
    api_entry.pack(pady=5)

    button = tk.Button(api_window, text="Devam Et", width=20, font=("Arial", 10, "bold"), bg="#0066cc", fg="white", command=on_submit)
    button.pack(pady=15)

    api_window.mainloop()

def run_main_app():
    get_api_key()

def run_verification(api_key):
    try:
        gmaps = googlemaps.Client(key=api_key)
    except Exception as e:
        messagebox.showerror("API Hatası", f"API istemcisi başlatılamadı:\n{e}")
        return

    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])

    if not file_path:
        messagebox.showinfo("İptal", "Herhangi bir dosya seçilmedi.")
        return

    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        messagebox.showerror("Dosya Hatası", f"Excel dosyası okunamadı:\n{e}")
        return

    if not {'place_id', 'telefon'}.issubset(df.columns):
        messagebox.showerror("Format Hatası", "Excel dosyasında 'place_id' ve 'telefon' sütunları olmalıdır.")
        return

    hatalar = []
    log_kayitlari = []
    for index, row in df.iterrows():
        place_id = row['place_id']
        beklenen_telefon = str(row['telefon'])

        try:
            place = gmaps.place(place_id=place_id)
            result = place['result']
            otel_adi = result.get('name', 'İsim bulunamadı')
            adres = result.get('formatted_address', 'Adres bulunamadı')
            actual_telefon = result.get('formatted_phone_number', 'YOK')
            website_var = 'website' in result

            if actual_telefon != beklenen_telefon:
                hatalar.append((index + 2, otel_adi, adres, beklenen_telefon, actual_telefon, "VAR" if website_var else "YOK"))
                log_kayitlari.append(f"HATA | Satır {index + 2} | {otel_adi} | {adres} | Beklenen: {beklenen_telefon} | Gelen: {actual_telefon} | Website: {'VAR' if website_var else 'YOK'}")
            else:
                log_kayitlari.append(f"DOĞRU | Satır {index + 2} | {otel_adi} | {adres} | Telefon: {beklenen_telefon} | Website: {'VAR' if website_var else 'YOK'}")
        except Exception as e:
            hatalar.append((index + 2, 'BİLİNEMEDİ', 'BİLİNEMEDİ', beklenen_telefon, f"HATA: {str(e)}", "BİLİNEMEDİ"))
            log_kayitlari.append(f"HATA | Satır {index + 2} | Bilinmeyen Otel | HATA: {str(e)}")

    result_window = tk.Tk()
    result_window.title("📋 Eşleşme Sonuçları")
    result_window.geometry("1100x600")
    result_window.configure(bg="#ffffff")

    style = ttk.Style()
    style.configure("Treeview", font=("Arial", 10), rowheight=25)
    style.configure("Treeview.Heading", font=("Arial", 11, "bold"))

    header = tk.Label(result_window, text="📊 Kontrol Raporu", font=("Helvetica", 13, "bold"), bg="#ffffff", fg="#333333")
    header.pack(pady=(10, 0))

    tree = ttk.Treeview(result_window, columns=("Satır", "Otel Adı", "Adres", "Beklenen", "Gelen", "Website"), show="headings")
    tree.heading("Satır", text="Satır")
    tree.heading("Otel Adı", text="Otel Adı")
    tree.heading("Adres", text="Adres")
    tree.heading("Beklenen", text="Beklenen Telefon")
    tree.heading("Gelen", text="Gelen Telefon")
    tree.heading("Website", text="Website Butonu")

    tree.column("Satır", width=60)
    tree.column("Otel Adı", width=200)
    tree.column("Adres", width=250)
    tree.column("Beklenen", width=120)
    tree.column("Gelen", width=120)
    tree.column("Website", width=120)

    tree.pack(padx=15, pady=10, fill=tk.BOTH, expand=True)

    for hata in hatalar:
        tree.insert("", "end", values=hata)

    frame_buttons = tk.Frame(result_window, bg="#ffffff")
    frame_buttons.pack(pady=10)

    if hatalar:
        txt_content = "Otel Telefon Eşleşme Hataları:\n\n"
        for satir, otel_adi, adres, beklenen, gelen, website in hatalar:
            txt_content += f"Satır {satir}\nOtel Adı: {otel_adi}\nAdres: {adres}\nBeklenen: {beklenen}\nGelen: {gelen}\nWebsite Butonu: {website}\n\n"

        text_frame = tk.Frame(result_window, bg="#ffffff")
        text_frame.pack(pady=5, padx=15, fill=tk.BOTH, expand=True)

        text_widget = tk.Text(text_frame, wrap="word", height=10, font=("Arial", 10))
        text_widget.insert("1.0", txt_content)
        text_widget.configure(state="disabled")
        text_widget.pack(fill=tk.BOTH, expand=True)

    else:
        messagebox.showinfo("Başarılı", "Tüm otel telefonları doğru eşleşti.")

    result_window.mainloop()


if __name__ == "__main__":
    start_app()
