import googlemaps

def normalize_phone(phone: str) -> str:
    return (
        phone.replace(" ", "")
        .replace("-", "")
        .replace("(", "")
        .replace(")", "")
        .replace("+90", "")
        .replace("0090", "")
        .lstrip("0")
    )

def analyze_hotels(df, api_key):
    gmaps = googlemaps.Client(key=api_key)

    dogru_kayitlar = []
    telefon_hatalilar = []
    websitesizler = []

    print(f"[INFO] İşlenecek otel sayısı: {len(df)}")

    for index, row in df.iterrows():
        otel_adi = str(row.get("Otel Adı")).strip()
        place_id = str(row.get("Place ID")).strip()
        excel_phone = str(row.get("Telefon")).strip()

        if not otel_adi or not place_id:
            print(f"[SKIP] {index}. satır - Eksik otel adı veya Place ID")
            continue

        try:
            details = gmaps.place(place_id=place_id, fields=["formatted_phone_number", "website"])
            result = details.get("result", {})

            if not result:
                print(f"[WARN] {otel_adi}: Google'dan bilgi alınamadı.")
                continue

            google_phone = normalize_phone(result.get("formatted_phone_number", ""))
            excel_phone_clean = normalize_phone(excel_phone)
            has_website = bool(result.get("website"))

            if not has_website:
                websitesizler.append({
                    "name": otel_adi,
                    "tel": excel_phone
                })
                print(f"[WEB YOK] {otel_adi}")
            elif google_phone and google_phone != excel_phone_clean:
                telefon_hatalilar.append({
                    "name": otel_adi,
                    "expected_tel": excel_phone,
                    "actual_tel": result.get("formatted_phone_number"),
                    "website": result.get("website", "Yok")
                })
                print(f"[TEL HATA] {otel_adi} | Beklenen: {excel_phone} - Google: {result.get('formatted_phone_number')}")
            else:
                dogru_kayitlar.append({
                    "name": otel_adi,
                    "tel": result.get("formatted_phone_number", "Belirtilmemiş"),
                    "website": result.get("website", "Yok")
                })
                print(f"[DOĞRU] {otel_adi}")

        except Exception as e:
            print(f"[HATA] {otel_adi}: Google API hatası -> {e}")
            continue

    print(f"\n[ÖZET] Doğru: {len(dogru_kayitlar)} | Telefon Sorunu: {len(telefon_hatalilar)} | Web Sitesi Eksik: {len(websitesizler)}\n")

    stats = {
        "total": len(df),
        "dogru": len(dogru_kayitlar),
        "telefon": len(telefon_hatalilar),
        "web": len(websitesizler)
    }

    return dogru_kayitlar, telefon_hatalilar, websitesizler, stats
