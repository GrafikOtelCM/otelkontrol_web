import re

def normalize_phone_number(phone):
    """
    Telefon numarasındaki boşluk, parantez, tire gibi karakterleri temizler,
    sadece sayıları bırakır.
    """
    if not phone:
        return ""
    cleaned = re.sub(r"[^\d]", "", phone)
    return cleaned[-10:] if len(cleaned) >= 10 else cleaned

def sanitize_place_id(place_id):
    """
    Place ID'deki baştaki ve sondaki boşlukları temizler, geçersiz olanları boş döner.
    """
    if not place_id or place_id.lower() in ['nan', 'none']:
        return None
    return place_id.strip()
