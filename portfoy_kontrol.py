"""
Kademeli Alım Portföy Kontrol Scripti
--------------------------------------
Excel tablosundaki her açık lotu okur, güncel kapanış fiyatını çeker,
hedef fiyatla (AlisFiyati * 1.10) karşılaştırır ve YEŞİL/KIRMIZI durum basar.

Excel kolonları (aynen bu isimlerle olmalı):
Hisse | Adet | AlisFiyati | AlisTarihi | HedefFiyat | Durum

Kurulum (Terminal'de bir kere çalıştır):
    pip3 install pandas openpyxl yfinance

Çalıştırma:
    python3 portfoy_kontrol.py
"""
from typing import Optional
import pandas as pd
import yfinance as yf

# ============ BURAYI KENDİNE GÖRE DÜZENLE ============
EXCEL_YOLU = "/Users/burcakyildirim/Desktop/hisse_yönetimi/hisseler.xlsx"
# =======================================================


def guncel_fiyat_getir(hisse_kodu: str) -> Optional[float]:
    """BIST hissesi için en son kapanış fiyatını çeker (yfinance, .IS ekiyle)."""
    try:
        ticker = yf.Ticker(f"{hisse_kodu}.IS")
        veri = ticker.history(period="5d")
        if veri.empty:
            return None
        return round(float(veri["Close"].iloc[-1]), 2)
    except Exception as e:
        print(f"  [!] {hisse_kodu} fiyatı çekilemedi: {e}")
        return None


def main():
    df = pd.read_excel(EXCEL_YOLU)
    df.columns = df.columns.str.strip()  # baştaki/sondaki boşlukları temizle
    df = df.rename(columns={
    "AlışFiyatı": "AlisFiyati",
    "Hedef Fiyat": "HedefFiyat",
})

    # Sadece hâlâ elde tutulan (satılmamış) lotlara bak
    acik_lotlar = df[df["Durum"].astype(str).str.strip().str.lower() != "satildi"].copy()

    if acik_lotlar.empty:
        print("Açık lot bulunamadı. 'Durum' kolonunu kontrol et (küçük harf 'acik' olmalı).")
        return

    # Her benzersiz hisse için tek seferde fiyat çek (aynı hisseyi tekrar tekrar çekmemek için)
    benzersiz_hisseler = acik_lotlar["Hisse"].unique()
    fiyat_cache = {}
    print("Güncel fiyatlar çekiliyor...\n")
    for hisse in benzersiz_hisseler:
        fiyat_cache[hisse] = guncel_fiyat_getir(hisse)

    print(f"{'Hisse':<8}{'Adet':<6}{'Maliyet':<10}{'Hedef':<10}{'Güncel':<10}{'Kâr%':<8}{'Durum'}")
    print("-" * 65)

    for _, satir in acik_lotlar.iterrows():
        hisse = satir["Hisse"]
        adet = satir["Adet"]
        maliyet = satir["AlisFiyati"]
        hedef = satir["HedefFiyat"]
        guncel = fiyat_cache.get(hisse)

        if guncel is None:
            print(f"{hisse:<8}{adet:<6}{maliyet:<10}{hedef:<10}{'???':<10}{'???':<8}⚠️  Fiyat alınamadı")
            continue

        kar_yuzde = round((guncel - maliyet) / maliyet * 100, 2)

        if guncel >= hedef:
            durum = "🟢 SAT (hedefe ulaştı)"
        else:
            durum = "🔴 BEKLE"

        print(f"{hisse:<8}{adet:<6}{maliyet:<10}{hedef:<10}{guncel:<10}{kar_yuzde:<8}{durum}")


if __name__ == "__main__":
    main()
