// Mac'te backend'i çalıştırdığın adres. Telefondan aynı wifi ile
// erişmek istediğinde burayı Mac'in yerel IP'sine çevireceğiz
// (örn: "http://192.168.1.23:8000"), şimdilik localhost yeterli.
const API_ADRESI = "http://127.0.0.1:8000";

async function verileriYukle() {
  const icerik = document.getElementById("icerik");
  const sonGuncelleme = document.getElementById("son-guncelleme");
  icerik.innerHTML = '<div class="yukleniyor">Veriler çekiliyor...</div>';

  try {
    const yanit = await fetch(`${API_ADRESI}/positions`);
    if (!yanit.ok) throw new Error(`API hatası: ${yanit.status}`);
    const lotlar = await yanit.json();

    sonGuncelleme.textContent =
      `Son güncelleme: ${new Date().toLocaleTimeString("tr-TR")} — ${lotlar.length} açık lot`;

    if (lotlar.length === 0) {
      icerik.innerHTML = '<div class="yukleniyor">Açık lot bulunamadı.</div>';
      return;
    }

    const satirlar = lotlar.map(lot => {
      const karSinifi = lot.kar_yuzde === null ? "" :
        (lot.kar_yuzde >= 0 ? "kar-pozitif" : "kar-negatif");

      const rozetHaritasi = {
        sat: '<span class="rozet rozet-sat">🟢 SAT</span>',
        bekle: '<span class="rozet rozet-bekle">🔴 BEKLE</span>',
        veri_yok: '<span class="rozet rozet-veriyok">⚠️ VERİ YOK</span>',
      };

      return `
        <tr>
          <td><strong>${lot.hisse}</strong></td>
          <td>${lot.adet}</td>
          <td>${lot.alis_fiyati.toFixed(2)}</td>
          <td>${lot.hedef_fiyat.toFixed(2)}</td>
          <td>${lot.guncel_fiyat !== null ? lot.guncel_fiyat.toFixed(2) : "—"}</td>
          <td class="${karSinifi}">${lot.kar_yuzde !== null ? lot.kar_yuzde.toFixed(2) + "%" : "—"}</td>
          <td>${rozetHaritasi[lot.durum] || lot.durum}</td>
          <td><button class="sat-btn" onclick="lotSat(${lot.id}, '${lot.hisse}')">Sat</button></td>
        </tr>
      `;
    }).join("");

    icerik.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Hisse</th>
            <th>Adet</th>
            <th>Maliyet</th>
            <th>Hedef</th>
            <th>Güncel</th>
            <th>Kâr%</th>
            <th>Durum</th>
            <th></th>
          </tr>
        </thead>
        <tbody>${satirlar}</tbody>
      </table>
    `;
  } catch (hata) {
    icerik.innerHTML = `<div class="yukleniyor">⚠️ Hata: ${hata.message}<br>Backend (uvicorn) çalışıyor mu kontrol et.</div>`;
  }
}

// ---------- Yeni lot ekleme pop-up'ı ----------

function modalAc() {
  document.getElementById("modal-arkaplan").classList.remove("gizli");
}

function modalKapat() {
  document.getElementById("modal-arkaplan").classList.add("gizli");
  document.getElementById("lot-formu").reset();
}

// Arka plana (kutunun dışına) tıklayınca da kapansın
function modalDisaTikla(event) {
  if (event.target.id === "modal-arkaplan") {
    modalKapat();
  }
}

async function lotEkle(event) {
  event.preventDefault(); // formun sayfayı yenilemesini engelle

  const yeniLot = {
    hisse: document.getElementById("form-hisse").value.trim().toUpperCase(),
    adet: parseFloat(document.getElementById("form-adet").value),
    alis_fiyati: parseFloat(document.getElementById("form-fiyat").value),
    hedef_yuzde: parseFloat(document.getElementById("form-hedef").value),
  };

  try {
    const yanit = await fetch(`${API_ADRESI}/lots`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(yeniLot),
    });
    if (!yanit.ok) throw new Error(`API hatası: ${yanit.status}`);

    modalKapat();
    verileriYukle(); // tabloyu tazele
  } catch (hata) {
    alert(`Lot eklenemedi: ${hata.message}`);
  }
}

// ---------- Satış işaretleme ----------

async function lotSat(lotId, hisseKodu) {
  const emin = confirm(`${hisseKodu} (lot #${lotId}) satıldı olarak işaretlensin mi?`);
  if (!emin) return;

  try {
    const yanit = await fetch(`${API_ADRESI}/lots/${lotId}/sat`, {
      method: "PATCH",
    });
    if (!yanit.ok) throw new Error(`API hatası: ${yanit.status}`);

    verileriYukle(); // tabloyu tazele, o satır artık görünmeyecek
  } catch (hata) {
    alert(`İşlem başarısız: ${hata.message}`);
  }
}

verileriYukle();