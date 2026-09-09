"""
Portföy Takip API (FastAPI)
----------------------------
SQLite veritabanındaki lotları okur, güncel fiyatlarla karşılaştırır,
JSON olarak döner. Ayrıca yeni lot ekleme ve "satıldı" işaretleme
endpoint'lerini sağlar.

Çalıştırma:
    uvicorn main:app --reload

Tarayıcıda test:
    http://127.0.0.1:8000/positions
    http://127.0.0.1:8000/docs   (otomatik oluşan interaktif API dökümantasyonu)
"""

import sqlite3
from typing import Optional

import yfinance as yf
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ============ BURAYI KENDİNE GÖRE DÜZENLE ============
DB_YOLU = "/Users/burcakyildirim/Desktop/hisse_yönetimi/portfoy.db"
# =======================================================

app = FastAPI(title="Portföy Takip API")

# Frontend'in (ileride telefon dahil) API'ye tarayıcıdan erişebilmesi için
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def db_baglan():
    conn = sqlite3.connect(DB_YOLU)
    conn.row_factory = sqlite3.Row  # satırlara isimle erişebilmek için
    return conn


def guncel_fiyat_getir(hisse_kodu: str) -> Optional[float]:
    try:
        ticker = yf.Ticker(f"{hisse_kodu}.IS")
        veri = ticker.history(period="5d")
        if veri.empty:
            return None
        return round(float(veri["Close"].iloc[-1]), 2)
    except Exception:
        return None


class YeniLot(BaseModel):
    hisse: str
    adet: float
    alis_fiyati: float
    hedef_yuzde: float = 10.0  # varsayılan %10 hedef


@app.get("/positions")
def pozisyonlari_getir():
    """Tüm açık lotları güncel fiyatla birlikte döner."""
    conn = db_baglan()
    lotlar = conn.execute(
        "SELECT * FROM lots WHERE lower(trim(durum)) != 'satildi'"
    ).fetchall()
    conn.close()

    # Aynı hisseyi tekrar tekrar çekmemek için cache
    fiyat_cache = {}
    sonuc = []

    for lot in lotlar:
        hisse = lot["hisse"]
        if hisse not in fiyat_cache:
            fiyat_cache[hisse] = guncel_fiyat_getir(hisse)
        guncel = fiyat_cache[hisse]

        kar_yuzde = None
        durum = "veri_yok"
        if guncel is not None:
            kar_yuzde = round((guncel - lot["alis_fiyati"]) / lot["alis_fiyati"] * 100, 2)
            durum = "sat" if guncel >= lot["hedef_fiyat"] else "bekle"

        sonuc.append({
            "id": lot["id"],
            "hisse": hisse,
            "adet": lot["adet"],
            "alis_fiyati": lot["alis_fiyati"],
            "hedef_fiyat": lot["hedef_fiyat"],
            "guncel_fiyat": guncel,
            "kar_yuzde": kar_yuzde,
            "durum": durum,
        })

    return sonuc


@app.post("/lots")
def lot_ekle(lot: YeniLot):
    """Yeni bir alış lotu ekler, hedef fiyatı otomatik hesaplar."""
    hedef_fiyat = round(lot.alis_fiyati * (1 + lot.hedef_yuzde / 100), 4)

    conn = db_baglan()
    cursor = conn.execute(
        """
        INSERT INTO lots (hisse, adet, alis_fiyati, hedef_fiyat, durum)
        VALUES (?, ?, ?, ?, 'acik')
        """,
        (lot.hisse.upper(), lot.adet, lot.alis_fiyati, hedef_fiyat),
    )
    conn.commit()
    yeni_id = cursor.lastrowid
    conn.close()

    return {"id": yeni_id, "mesaj": "Lot eklendi", "hedef_fiyat": hedef_fiyat}


@app.patch("/lots/{lot_id}/sat")
def lot_satildi_isaretle(lot_id: int):
    """Bir lotu 'satildi' olarak işaretler (silmez, geçmişte kalır)."""
    conn = db_baglan()
    sonuc = conn.execute("SELECT id FROM lots WHERE id = ?", (lot_id,)).fetchone()
    if sonuc is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Lot bulunamadı")

    conn.execute("UPDATE lots SET durum = 'satildi' WHERE id = ?", (lot_id,))
    conn.commit()
    conn.close()

    return {"mesaj": f"Lot {lot_id} satıldı olarak işaretlendi"}
