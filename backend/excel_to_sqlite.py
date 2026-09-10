"""
Excel -> SQLite Aktarım Scripti (bir kerelik çalıştırılır)
------------------------------------------------------------
Mevcut Excel dosyandaki lotları okuyup 'portfoy.db' adında
bir SQLite veritabanına aktarır. Bundan sonra FastAPI backend
bu veritabanını kullanacak, Excel'e artık gerek kalmayacak.

Kurulum: gerek yok, sqlite3 Python'a gömülü gelir.

Çalıştırma:
    python3 excel_to_sqlite.py
"""

import os
import sqlite3
import pandas as pd

# Bu dosyanın (excel_to_sqlite.py) bulunduğu klasöre göre otomatik path.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ============ EXCEL DOSYASININ ADINI KENDİNE GÖRE DÜZENLE ============
EXCEL_YOLU = os.path.join(BASE_DIR, "DOSYA_ADIN.xlsx")
DB_YOLU = os.path.join(BASE_DIR, "portfoy.db")
# =======================================================


def main():
    # Excel'i oku, kolon adlarını temizle/normalize et
    df = pd.read_excel(EXCEL_YOLU)
    df.columns = df.columns.str.strip()
    df = df.rename(columns={
        "AlışFiyatı": "AlisFiyati",
        "Hedef Fiyat": "HedefFiyat",
    })

    # Durum kolonundaki boşlukları/büyük-küçük harf farklarını normalize et
    df["Durum"] = df["Durum"].astype(str).str.strip().str.lower()

    # SQLite veritabanına bağlan (dosya yoksa otomatik oluşturulur)
    conn = sqlite3.connect(DB_YOLU)
    cursor = conn.cursor()

    # Tabloyu oluştur (zaten varsa dokunma)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hisse TEXT NOT NULL,
            adet REAL NOT NULL,
            alis_fiyati REAL NOT NULL,
            hedef_fiyat REAL NOT NULL,
            durum TEXT NOT NULL DEFAULT 'acik'
        )
    """)

    # Excel'deki her satırı tabloya ekle
    eklenen = 0
    for _, satir in df.iterrows():
        # AlisFiyati boşsa (nan) o satırı atla, uyar
        if pd.isna(satir["AlisFiyati"]):
            print(f"  [!] Atlandı (AlisFiyati boş): {satir['Hisse']}")
            continue

        cursor.execute(
            """
            INSERT INTO lots (hisse, adet, alis_fiyati, hedef_fiyat, durum)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                satir["Hisse"],
                float(satir["Adet"]),
                float(satir["AlisFiyati"]),
                float(satir["HedefFiyat"]),
                satir["Durum"],
            ),
        )
        eklenen += 1

    conn.commit()
    conn.close()

    print(f"\nTamamlandı: {eklenen} lot '{DB_YOLU}' dosyasına aktarıldı.")


if __name__ == "__main__":
    main()
