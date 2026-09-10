const API_ADRESI = "http://127.0.0.1:8000";

function urlParametresiAl(ad) {
  const params = new URLSearchParams(window.location.search);
  return params.get(ad);
}

async function seviyeleriYukle() {
  const hisse = urlParametresiAl("hisse");
  document.getElementById("detay-baslik").textContent = hisse || "Hisse bulunamadı";
  if (!hisse) return;

  try {
    const yanit = await fetch(`${API_ADRESI}/positions/${hisse}/seviyeler`);
    if (!yanit.ok) throw new Error(`API hatası: ${yanit.status}`);
    const veri = await yanit.json();

    document.getElementById("detay-fiyat").textContent = `Güncel fiyat: ${veri.guncel_fiyat}`;

    const vadeTurkce = { kisa: "Kısa Vade (1 ay)", orta: "Orta Vade (3 ay)", uzun: "Uzun Vade (6 ay)" };
    const icerik = document.getElementById("detay-icerik");

    icerik.innerHTML = ["kisa", "orta", "uzun"].map(vade => {
      const v = veri[vade];
      if (!v) {
        return `<div class="vade-kutu"><h3>${vadeTurkce[vade]}</h3><p class="yukleniyor">Veri yok</p></div>`;
      }

      const p = v.pivot_seviyeleri;
      const ma = v.hareketli_ortalamalar;
      const maSatirlari = Object.entries(ma)
        .map(([ad, deger]) => `<div class="seviye-satir"><span>${ad}</span><span>${deger}</span></div>`)
        .join("");

      return `
        <div class="vade-kutu">
          <h3>${vadeTurkce[vade]}</h3>
          <div class="seviye-grubu">
            <div class="seviye-satir direnc"><span>Direnç 2</span><span>${p.direnc2}</span></div>
            <div class="seviye-satir direnc"><span>Direnç 1</span><span>${p.direnc1}</span></div>
            <div class="seviye-satir pivot"><span>Pivot</span><span>${p.pivot}</span></div>
            <div class="seviye-satir destek"><span>Destek 1</span><span>${p.destek1}</span></div>
            <div class="seviye-satir destek"><span>Destek 2</span><span>${p.destek2}</span></div>
          </div>
          <div class="seviye-grubu">
            ${maSatirlari || '<div class="seviye-satir"><span>Yeterli veri yok</span></div>'}
          </div>
        </div>
      `;
    }).join("");
  } catch (hata) {
    document.getElementById("detay-icerik").innerHTML =
      `<div class="yukleniyor">⚠️ Hata: ${hata.message}<br>Backend (uvicorn) çalışıyor mu kontrol et.</div>`;
  }
}

seviyeleriYukle();
