import re

def normalize_phone(phone: str) -> str:
    """
    Telefon numaralarını sadeleştirip yalnızca rakamlarla döndürür.
    Örnek: "(0242) 123 45 67" -> "02421234567"
    """
    if not phone:
        return ""
    # Sadece rakamları al
    digits = re.sub(r'\D', '', phone)
    # Başında 90 varsa kaldır
    if digits.startswith("90") and len(digits) > 10:
        digits = digits[2:]
    return digits

def sanitize_place_id(raw_id: str) -> str:
    """
    Place ID değerlerinden boşluk, yeni satır, tab gibi karakterleri temizler.
    """
    return raw_id.strip().replace('\n', '').replace('\r', '').replace(' ', '')
