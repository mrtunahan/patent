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


# Türkçe alfabe sırası (q, w, x uluslararası konumlarında); ICU "tr" harmanlamasıyla uyumlu.
_TR_ALPHABET = "abcçdefgğhıijklmnoöpqrsştuüvwxyz"
_TR_RANK = {char: index for index, char in enumerate(_TR_ALPHABET)}


def turkish_sort_key(value: str) -> tuple[tuple[int, int], ...]:
    """Türkçe alfabe sırasına göre sıralama anahtarı (büyük/küçük harf duyarsız).

    normalize_tr çıktısını kullanır. Boşluk, rakam ve noktalama harflerden önce gelir;
    Türkçe alfabede olmayan harfler en sona kod noktasına göre sıralanır.
    Düz normalize_tr çıktısı kod noktasına göre sıralanırsa ç/ğ/ı/ö/ş/ü harfleri z'den sonra düşer.
    """
    key = []
    for char in normalize_tr(value):
        if char in _TR_RANK:
            key.append((2, _TR_RANK[char]))
        elif char.isalpha():
            key.append((3, ord(char)))
        else:
            key.append((1, ord(char)))
    return tuple(key)
