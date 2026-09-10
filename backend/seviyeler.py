"""
Pivot Noktası Tabanlı Destek/Direnç + Hareketli Ortalama Hesaplama
----------------------------------------------------------------------
Klasik "floor pivot" yöntemiyle otomatik destek/direnç hesaplar.
Manuel giriş gerekmez, geçmiş High/Low/Close verisinden hesaplanır.

Formül (bir önceki dönemin High/Low/Close'undan):
  Pivot (P) = (High + Low + Close) / 3
  R1 = 2P - Low        S1 = 2P - High
  R2 = P + (High-Low)  S2 = P - (High-Low)

Vade eşlemesi:
  Kısa vade  -> son 1 AYIN High/Low/Close'u
  Orta vade  -> son 3 AYIN High/Low/Close'u
  Uzun vade  -> son 6 AYIN High/Low/Close'u

Tek başına test etmek için:
    python3 seviyeler.py POLTK
"""

import sys
import pandas as pd
import yfinance as yf

VADELER = {
    "kisa": "1mo",
    "orta": "3mo",
    "uzun": "6mo",
}

HAREKETLI_ORTALAMA_PERIYOTLARI = {
    "kisa": [5, 9, 21],
    "orta": [21, 50, 100],
    "uzun": [100, 200],
}


def pivot_hesapla(high: float, low: float, close: float) -> dict:
    pivot = (high + low + close) / 3
    return {
        "direnc2": round(pivot + (high - low), 2),
        "direnc1": round(2 * pivot - low, 2),
        "pivot": round(pivot, 2),
        "destek1": round(2 * pivot - high, 2),
        "destek2": round(pivot - (high - low), 2),
    }


def hareketli_ortalamalar_hesapla(gunluk_veri: pd.DataFrame, periyotlar: list) -> dict:
    sonuc = {}
    for periyot in periyotlar:
        if len(gunluk_veri) >= periyot:
            sonuc[f"MA{periyot}"] = round(
                float(gunluk_veri["Close"].rolling(periyot).mean().iloc[-1]), 2
            )
    return sonuc


def seviyeleri_hesapla(hisse_kodu: str) -> dict:
    ticker = yf.Ticker(f"{hisse_kodu}.IS")

    # Hareketli ortalamalar en uzun periyot (200 gün) için yeterli veri lazım
    tum_veri = ticker.history(period="1y", interval="1d")
    if tum_veri.empty:
        return None

    guncel_fiyat = round(float(tum_veri["Close"].iloc[-1]), 2)
    sonuc = {"guncel_fiyat": guncel_fiyat}

    for vade_adi, period in VADELER.items():
        vade_verisi = ticker.history(period=period, interval="1d")
        if vade_verisi.empty:
            sonuc[vade_adi] = None
            continue

        high = float(vade_verisi["High"].max())
        low = float(vade_verisi["Low"].min())
        close = float(vade_verisi["Close"].iloc[-1])

        sonuc[vade_adi] = {
            "pivot_seviyeleri": pivot_hesapla(high, low, close),
            "hareketli_ortalamalar": hareketli_ortalamalar_hesapla(
                tum_veri, HAREKETLI_ORTALAMA_PERIYOTLARI[vade_adi]
            ),
        }

    return sonuc


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanım: python3 seviyeler.py HISSE_KODU")
        print("Örnek:    python3 seviyeler.py POLTK")
        sys.exit(1)

    hisse = sys.argv[1].upper()
    print(f"\n{hisse} için pivot seviyeleri hesaplanıyor...\n")

    sonuc = seviyeleri_hesapla(hisse)
    if sonuc is None:
        print("Veri alınamadı.")
        sys.exit(1)

    print(f"Güncel fiyat: {sonuc['guncel_fiyat']}\n")

    vade_turkce = {"kisa": "KISA VADE (1 ay)", "orta": "ORTA VADE (3 ay)", "uzun": "UZUN VADE (6 ay)"}
    for vade_adi in ["kisa", "orta", "uzun"]:
        veri = sonuc[vade_adi]
        print(f"--- {vade_turkce[vade_adi]} ---")
        if veri is None:
            print("  veri alınamadı\n")
            continue
        p = veri["pivot_seviyeleri"]
        print(f"  Direnç 2: {p['direnc2']}")
        print(f"  Direnç 1: {p['direnc1']}")
        print(f"  Pivot   : {p['pivot']}")
        print(f"  Destek 1: {p['destek1']}")
        print(f"  Destek 2: {p['destek2']}")
        print(f"  Hareketli Ortalamalar: {veri['hareketli_ortalamalar']}")
        print()