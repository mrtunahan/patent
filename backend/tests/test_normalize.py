import unicodedata

import pytest

from app.core.text import normalize_tr


def nfd(text: str) -> str:
    return unicodedata.normalize("NFD", text)


# --- İ / I / ı / i ---

@pytest.mark.parametrize(
    "raw, expected",
    [
        ("ISPARTA", "ısparta"),
        ("İSTANBUL", "istanbul"),
        ("Işık", "ışık"),
        ("Iğdır", "ığdır"),
        ("IĞDIR", "ığdır"),
        ("İzmir", "izmir"),
        ("ılık", "ılık"),
        ("ILIK", "ılık"),
        ("iplik", "iplik"),
        ("İPLİK", "iplik"),
        ("I", "ı"),
        ("İ", "i"),
        ("ı", "ı"),
        ("i", "i"),
    ],
)
def test_dotted_and_dotless_i(raw, expected):
    assert normalize_tr(raw) == expected


def test_dotted_and_dotless_i_stay_distinct():
    assert normalize_tr("I") != normalize_tr("i")
    assert normalize_tr("ı") != normalize_tr("i")
    assert normalize_tr("ISPARTA") != normalize_tr("isparta")
    assert normalize_tr("ISPARTA") == normalize_tr("ısparta")
    assert normalize_tr("İSPARTA") == normalize_tr("isparta")
    assert normalize_tr("Işık") == normalize_tr("ışık")


def test_no_combining_dot_residue_from_capital_dotted_i():
    for raw in ("İ", "İ", "İSTANBUL", "İSTANBUL", "Çİçek"):
        assert "̇" not in normalize_tr(raw), raw
    assert normalize_tr("İSTANBUL") == "istanbul"


def test_plain_casefold_would_leave_residue_which_is_why_mapping_runs_first():
    assert "̇" in "İ".casefold()  # kök neden kanıtı
    assert normalize_tr("İ") == "i"


# --- diğer Türkçe harfler: büyük/küçük eşleşmesi ---

@pytest.mark.parametrize(
    "upper, lower",
    [("Ş", "ş"), ("Ç", "ç"), ("Ğ", "ğ"), ("Ö", "ö"), ("Ü", "ü")],
)
def test_case_pairs(upper, lower):
    assert normalize_tr(upper) == normalize_tr(lower) == lower
    assert normalize_tr(f"A{upper}A") == normalize_tr(f"a{lower}a")


# --- aksan katlaması YOK ---

@pytest.mark.parametrize(
    "a, b",
    [("şaban", "saban"), ("Çankırı", "Cankırı"), ("ağaç", "agac"), ("öğe", "oge"), ("üç", "uc"),
     ("ğ", "g"), ("ş", "s"), ("ç", "c"), ("ö", "o"), ("ü", "u")],
)
def test_accents_are_not_folded(a, b):
    assert normalize_tr(a) != normalize_tr(b)


# --- NFC ---

def test_decomposed_capital_dotted_i_equals_precomposed():
    decomposed = "İ"
    assert decomposed != "İ"
    assert normalize_tr(decomposed) == normalize_tr("İ") == "i"
    assert normalize_tr("İSTANBUL") == normalize_tr("İSTANBUL")


@pytest.mark.parametrize("char", ["ö", "ü", "ş", "ç", "ğ", "Ö", "Ü", "Ş", "Ç", "Ğ", "İ"])
def test_decomposed_turkish_letters_equal_precomposed(char):
    decomposed = nfd(char)
    assert len(decomposed) > 1  # gerçekten ayrışık biçim test ediliyor
    assert normalize_tr(decomposed) == normalize_tr(char)
    assert normalize_tr(f"x{decomposed}y") == normalize_tr(f"x{char}y")


# --- boşluklar ---

@pytest.mark.parametrize(
    "raw",
    [
        "Çankırı   Karatekin    Üni.",
        "Çankırı\tKaratekin\tÜni.",
        "Çankırı\nKaratekin\r\nÜni.",
        "Çankırı Karatekin  Üni.",   # NBSP
        "Çankırı Karatekin　Üni.",         # em space, ideographic space
        "Çankırı \t\n  Karatekin \u0085 Üni.",
        "  Çankırı Karatekin Üni.  ",
        " \tÇankırı Karatekin Üni.\n",
    ],
)
def test_whitespace_collapsing(raw):
    assert normalize_tr(raw) == "çankırı karatekin üni."


def test_leading_trailing_whitespace_removed():
    assert normalize_tr("  \t abc \n ") == "abc"


@pytest.mark.parametrize("raw", ["", " ", "   ", "\t\n", "  　"])
def test_empty_and_whitespace_only(raw):
    assert normalize_tr(raw) == ""


# --- gerçek şartname örnekleri ---

@pytest.mark.parametrize(
    "raw, expected",
    [
        ("Çankırı Karatekin Üni.", "çankırı karatekin üni."),
        ("ÇANKIRI KARATEKİN ÜNİ.", "çankırı karatekin üni."),
        ("Şabanözü MYO", "şabanözü myo"),
        ("ŞABANÖZÜ MYO", "şabanözü myo"),
        ("Peyzaj Mimarlığı", "peyzaj mimarlığı"),
        ("PEYZAJ MİMARLIĞI", "peyzaj mimarlığı"),
        ("Tasarım Tescili", "tasarım tescili"),
        ("TASARIM TESCİLİ", "tasarım tescili"),
        ("Faydalı Model", "faydalı model"),
        ("Ankara Üni.", "ankara üni."),
        ("Modüler Dış Mekan Özelleştirilebilir Tuz Lambası", "modüler dış mekan özelleştirilebilir tuz lambası"),
        ("Destek Patent", "destek patent"),
    ],
)
def test_spec_examples(raw, expected):
    assert normalize_tr(raw) == expected


def test_spec_examples_equal_across_case_and_spacing():
    assert normalize_tr("Çankırı Karatekin Üni.") == normalize_tr("  ÇANKIRI   KARATEKİN  ÜNİ. ")
    assert normalize_tr("Ankara Üni.") != normalize_tr("Ankara Uni.")  # aksan katlanmaz


# --- idempotent ve saf ---

CORPUS = [
    "", " ", "ISPARTA", "İSTANBUL", "İ", "i̇", "Işık", "ß", "ẞ", "ﬁ", "ŉ", "ǅ", "Σ", "ς",
    "ΐ", "Ǆ", "a  b", "İ̇", "ß̇", "ﬀ̇", "Ç̧", "ö̈̈",
    "Çankırı Karatekin Üni.", "  Tasarım   Tescili  ",
]


@pytest.mark.parametrize("raw", CORPUS)
def test_idempotent_corpus(raw):
    once = normalize_tr(raw)
    assert normalize_tr(once) == once


def test_idempotent_for_every_code_point_alone_and_in_context():
    """Tüm Unicode kod noktaları: tek başına, harfler arasında ve U+0307 ile birleşik."""
    failures = []
    for cp in range(0x110000):
        if 0xD800 <= cp <= 0xDFFF:
            continue
        ch = chr(cp)
        for sample in (ch, f"a{ch}b", f"{ch}̇", f"I{ch}"):
            once = normalize_tr(sample)
            if normalize_tr(once) != once:
                failures.append((hex(cp), sample))
    assert failures == []


def test_idempotence_needs_second_nfc_after_casefold():
    """Kök neden kanıtı: casefold("ß\\u0307") NFC değil; ikinci NFC olmasa ikinci geçiş değişirdi."""
    sample = "ß̇"
    folded = sample.casefold()
    assert folded != unicodedata.normalize("NFC", folded)
    once = normalize_tr(sample)
    assert once == unicodedata.normalize("NFC", once)
    assert normalize_tr(once) == once


def test_pure_function_does_not_mutate_or_depend_on_state():
    raw = "  İSTANBUL  "
    assert normalize_tr(raw) == normalize_tr(raw) == "istanbul"
    assert raw == "  İSTANBUL  "


# --- bilinen sınır (rapora yazıldı) ---

def test_known_limit_lowercase_dotted_i_with_combining_dot_is_not_folded():
    """Girdi zaten küçük harfli ayrışık "i"+U+0307 ise (örn. Python .lower() çıktısı) "i"ye inmez.

    "İ" (U+0130 veya I+U+0307) doğru işlenir; bu durum yalnızca zaten küçültülmüş ayrışık metin içindir.
    Şartnamedeki sıraya eklenmedi; ihtiyaç doğarsa kararla eklenir.
    """
    assert normalize_tr("i̇stanbul") != normalize_tr("istanbul")
    assert normalize_tr("i̇stanbul") == "i̇stanbul"
