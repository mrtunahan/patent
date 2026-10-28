import unicodedata

import pytest

from app.core.text import normalize_tr, turkish_sort_key


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("ISPARTA", "ısparta"), ("İSTANBUL", "istanbul"), ("Işık", "ışık"), ("Iğdır", "ığdır"),
        ("IĞDIR", "ığdır"), ("iplik", "iplik"), ("İPLİK", "iplik"), ("I", "ı"), ("İ", "i"),
    ],
)
def test_dotted_and_dotless_i(raw, expected):
    assert normalize_tr(raw) == expected


def test_i_variants_stay_distinct_and_no_combining_dot_residue():
    assert normalize_tr("ISPARTA") != normalize_tr("isparta")
    assert normalize_tr("İSPARTA") == normalize_tr("isparta")
    assert "̇" not in normalize_tr("İSTANBUL")
    assert "̇" in "İ".casefold()  # düz casefold artık bırakır; İ->i eşlemesi bu yüzden önce
    assert normalize_tr("İSTANBUL") == "istanbul"  # ayrışık İ


@pytest.mark.parametrize("upper, lower", [("Ş", "ş"), ("Ç", "ç"), ("Ğ", "ğ"), ("Ö", "ö"), ("Ü", "ü")])
def test_case_pairs(upper, lower):
    assert normalize_tr(upper) == normalize_tr(lower) == lower


@pytest.mark.parametrize("a, b", [("şaban", "saban"), ("ağaç", "agac"), ("öğe", "oge"), ("üç", "uc")])
def test_accents_are_not_folded(a, b):
    assert normalize_tr(a) != normalize_tr(b)


@pytest.mark.parametrize("char", ["ö", "ü", "ş", "ç", "ğ", "Ö", "Ş", "İ"])
def test_nfc_decomposed_equals_precomposed(char):
    decomposed = unicodedata.normalize("NFD", char)
    assert len(decomposed) > 1
    assert normalize_tr(decomposed) == normalize_tr(char)


@pytest.mark.parametrize(
    "raw", ["Çankırı   Karatekin\tÜni.", "Çankırı Karatekin\n\r\nÜni.", "  Çankırı　Karatekin Üni.  "]
)
def test_whitespace_collapsing_and_trim(raw):
    assert normalize_tr(raw) == "çankırı karatekin üni."


@pytest.mark.parametrize("raw", ["", "   ", "\t\n "])
def test_empty_and_whitespace_only(raw):
    assert normalize_tr(raw) == ""


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("Çankırı Karatekin Üni.", "çankırı karatekin üni."),
        ("ŞABANÖZÜ MYO", "şabanözü myo"),
        ("PEYZAJ MİMARLIĞI", "peyzaj mimarlığı"),
        ("TASARIM TESCİLİ", "tasarım tescili"),
    ],
)
def test_spec_examples(raw, expected):
    assert normalize_tr(raw) == expected


@pytest.mark.parametrize("raw", ["ISPARTA", "İSTANBUL", "İ", "ß̇", "ﬀ̇", "  Tasarım   Tescili  "])
def test_idempotent_examples(raw):
    once = normalize_tr(raw)
    assert normalize_tr(once) == once


def test_known_limit_lowercase_dotted_i_with_combining_dot_is_not_folded():
    """Bilinçli sınır (README): zaten küçük harfli ayrışık i+U+0307 'i'ye inmez."""
    assert normalize_tr("i̇stanbul") != normalize_tr("istanbul")


def test_turkish_sort_key_orders_by_turkish_alphabet():
    names = ["Zonguldak", "Çankırı", "Ankara", "Şabanözü", "Sivas", "Işık", "İzmir", "Ulus", "Üsküdar"]
    expected = ["Ankara", "Çankırı", "Işık", "İzmir", "Sivas", "Şabanözü", "Ulus", "Üsküdar", "Zonguldak"]
    assert sorted(names, key=turkish_sort_key) == expected
    assert sorted(names, key=normalize_tr) != expected  # düz kod noktası sırası ç/ş/ü'yü z'den sonra atar
    assert turkish_sort_key("ışık") == turkish_sort_key("IŞIK")
