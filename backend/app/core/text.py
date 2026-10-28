import unicodedata


def normalize_tr(value: str) -> str:
    """Karşılaştırma/arama için Türkçe harf duyarsız anahtar üretir (saklanan değer değişmez).

    Sıra: strip -> NFC -> "İ"->"i", "I"->"ı" (casefold'dan ÖNCE; düz casefold "İ"yi "i"+U+0307
    yapar) -> casefold -> NFC -> iç boşlukları (tüm Unicode boşlukları) tek boşluğa indir.
    Aksan katlaması YOKTUR (ş != s, ö != o, ç != c, ğ != g, ü != u).
    İkinci NFC: casefold çıktısı her zaman NFC değildir ("ß"+U+0307 -> "ss"+U+0307); bunsuz
    fonksiyon idempotent olmaz.
    """
    value = unicodedata.normalize("NFC", value.strip())
    value = value.replace("İ", "i").replace("I", "ı")
    value = unicodedata.normalize("NFC", value.casefold())
    return " ".join(value.split())
