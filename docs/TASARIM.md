# İKA kontrol arayüzü — başlangıç taslağı

Durum: Gereksinimler kullanıcıyla netleştiriliyor. Bu belge kesinleşmiş donanım veya protokol gereksinimi tanımlamaz.

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

## Henüz netleşmeyen kararlar

1. Masaüstü veya web uygulaması; hedef cihazlar ve işletim sistemi.
2. Aracın kullanım amacı, sürüş sistemi, sensörleri ve kamera donanımı.
3. Haberleşme altyapısı, mesaj biçimleri ve araç tarafındaki yazılım.
4. Klavye, ekran kontrolleri ve oyun kumandası ihtiyaçları.
5. Manuel/otonom çalışma, görev planlama ve harita ihtiyacı.
6. Telemetri alanları, ölçüm birimleri, güncelleme hızları ve kayıt ihtiyaçları.
7. Aracın kontrol yetkisi, bağlantı kaybı ve durdurma davranışları.

## İlk sürümün doğrulanması

Teknoloji seçildikten sonra simülasyonla bağlantı açma/kapatma, telemetri güncelliği, manuel kontrolü bırakma, durdurma ve bağlantı kaybı davranışları test edilecek. Gerçek cihaz entegrasyonu ayrıca doğrulanacak.
