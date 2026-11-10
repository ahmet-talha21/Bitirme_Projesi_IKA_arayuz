# İKA kontrol arayüzü — başlangıç taslağı

Durum: İlk çalışan prototip hazır. Kullanıcının kararı: Windows masaüstü, ESP32 ile Wi-Fi/WebSocket, enkoder + IMU, mesafe sensörüyle engelden kaçınma ve çizilmiş rotaya dönüş. PySide6 kullanılıyor. Gerçek araç hareket kontrolü henüz etkin değil.

## Amaç

Bitirme projesindeki insansız kara aracıyla haberleşmek, durumunu izlemek ve aracı kontrol etmek. Araç hazır olmadığı için ilk geliştirme aşamasında açıkça etiketlenmiş bir simülasyon kullanılacak. Simülasyondaki başarı, gerçek araçla haberleşmenin doğrulandığı anlamına gelmez.

## Önerilen ekran yapısı

- Üst durum alanı: çalışma modu, bağlantı durumu, son veri zamanı ve uyarılar.
- Sürüş alanı: manuel kontrol, hız sınırı, kontrol kaynağı ve durdurma komutu.
- Telemetri alanı: donanımda mevcut olduğu doğrulanan ölçümler; birimleri ve güncellik bilgisiyle.
- Görüntü ve konum alanı: kamera ve konum donanımı varsa etkinleştirilecek paneller.
- Bağlantı ayarları: seçilecek protokole uygun bağlantı parametreleri.
- Olay kaydı: bağlantılar, komutlar, onaylar ve hatalar; zaman bilgisiyle.

Panellerin önceliği ve yerleşimi kullanım senaryosu yanıtlandıktan sonra kesinleşecek.

## Kontrol davranışı için tasarım ilkeleri

- Simülasyon ve gerçek araç modu görünür biçimde ayrılmalı.
- Bağlı değilken hareket komutları gönderilmemeli; eski telemetri güncelmiş gibi gösterilmemeli.
- Komutun gönderilmesi, araç tarafından kabul edilmesi ve uygulanması ayrı durumlar olarak ele alınmalı. Onay mekanizması protokole bağlıdır.
- Manuel sürüşte tuş/düğme bırakma, pencerenin odağını kaybetmesi ve bağlantı kesilmesi senaryoları tanımlanmalı.
- Bağlantı geri geldiğinde önceki hareket otomatik sürdürülmemeli.
- Haberleşme kaybında duruş, araç tarafındaki zaman aşımı mekanizmasıyla da sağlanmalı; arayüz tek başına bunu garanti edemez.
- Yazılımdaki durdurma komutu, donanımsal acil durdurmanın yerine geçmez. Gerçek durdurma davranışı araç ekibiyle doğrulanmalı.
- Hız limitleri, komut sıklığı, zaman aşımı süreleri ve birimler araç özellikleriyle birlikte kararlaştırılmalı.

## İlk görüşmedeki sorular ve güncel durum

1. Windows masaüstü olarak kesinleşti.
2. Aracın kullanım amacı, sürüş sistemi, sensörleri ve kamera donanımı.
3. ESP32 / Wi-Fi / WebSocket kesinleşti; mesaj taslağı ESP32_PROTOKOL.md içinde, firmware bekleniyor.
4. Klavye, ekran kontrolleri ve oyun kumandası ihtiyaçları.
5. Manuel/otonom çalışma, görev planlama ve harita ihtiyacı.
6. Telemetri alanları, ölçüm birimleri, güncelleme hızları ve kayıt ihtiyaçları.
7. Aracın kontrol yetkisi, bağlantı kaybı ve durdurma davranışları.

## İlk sürümün doğrulanması

Rota dosyası, engelden kaçınma/rotaya dönüş, durdurma, manuel sürüş, arayüz çizimi ve yerel WebSocket telemetri testleri mevcut. Gerçek cihaz ve Windows üzerinde entegrasyon ayrıca doğrulanacak.
