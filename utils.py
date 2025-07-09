import re

def normalize_phone_number(phone):
    """
    Telefon numarasını normalize eder:
    - Parantez, boşluk, tire ve '+' gibi karakterleri kaldırır
    - Sadece rakamlar kalır
    """
    if not phone:
        return ''
    return re.sub(r'\D', '', phone)
