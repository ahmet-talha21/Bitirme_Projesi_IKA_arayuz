# ESP32 haberleşmesi · ilk prototip

Taşıma: bilgisayar WebSocket istemcisi, ESP32 WebSocket sunucusu. Her mesaj UTF-8 JSON nesnesidir. `ws://192.168.4.1:81` varsayılanı örnektir; cihazın erişim noktası veya yerel ağ IP'si/portuyla eşleşmelidir. İnternete açık bir bağlantı için kimlik doğrulama ve TLS henüz tasarlanmadı; ilk hedef yerel geliştirme ağıdır.

## Uygulamanın kabul ettiği telemetri

```json
{
  "type": "telemetry",
  "x_m": 3.2,
  "y_m": 4.1,
  "yaw_rad": 0.5,
  "speed_mps": 0.4,
  "front_m": 1.3,
  "mode": "autonomous",
  "state": "Rota takip ediliyor"
}
```

- `mode`: `manual` veya `autonomous`; arayüz, bildirilen araç modunu gösterir.
- Konum: yerel metre, alan 0≤X≤20 ve 0≤Y≤14. Yön: +X'ten saat yönünün tersine radyan. İmzalı hız: m/s; mesafe: m.
- Tüm ölçümler zorunlu, sayısal ve sonlu olmalı. Ön mesafe 0–100 m, hız mutlak değeri en fazla 20 m/s; bunlar prototip giriş doğrulama sınırlarıdır, sensör/donanım limitleri değildir.
- Önerilen telemetri sıklığı 10–20 Hz. 1 saniye boyunca geçerli veri gelmezse sayısal göstergeler boşaltılır, mod bilinmiyor gösterilir. Son konum haritada kalır; bu durumda araç durduğu varsayılmaz.
- Enkoder + IMU birleşimi ESP32 veya araç üstündeki hesaplayıcıda yapılacak. Kalibrasyon, başlangıç referansı ve konum güvenilirliği henüz araç üzerinde doğrulanmadı.
- Pil bilgisi, sensör sağlığı ve hata kodları donanım belli olduktan sonra şemaya eklenecek; arayüz bunları uydurmaz.

## Uygulamanın gönderdiği tek araç komutu

```json
{"type": "command", "command": "stop"}
```

İsteğe bağlı yanıt, şimdilik olay kaydına yazılır:

```json
{"type": "ack", "command": "stop", "status": "accepted"}
```

`accepted` yalnızca komutun alındığını belirtir; duruş telemetri/araç tarafından ayrıca doğrulanmalıdır. WebSocket'in açılması araç kontrolünün hazır olduğunu göstermez. Bağlantı geri gelince arayüz hareket komutu veya eski rota göndermez.

## Sonraki entegrasyon aşaması — henüz uygulanmadı

- Komut kimlikleri, ACK/NACK eşleştirme, zaman aşımı, sürüm/yetenek anlaşması.
- Yerel referans kurma ve kalibrasyon; geçerli konum, yön, sensör sağlığı koşulları.
- Rota yükleme/onaylama: metre cinsinden yol noktaları, rota kimliği, hız limiti; atomik kabul veya ret.
- Mod değişikliği, görevi başlat/duraklat/iptal ve bitiş bildirimi.
- Manuel doğrusal/açısal hız komutları ve süreli kontrol yetkisi.
- ESP32 tarafında komut/heartbeat zaman aşımı ve motorları durdurma. Ağ kesilmesinde tarayıcı/masaüstü uygulaması tek başına duruş sağlayamaz.
- Gerçek engelden kaçınma: sensör sayısı/yönü, tarama stratejisi, robot boyutları, minimum dönüş yarıçapı ve yerel planlama. Tek sabit ön sensör, yandan geçişin güvenli olduğunu tek başına kanıtlamaz.
- Fiziksel acil durdurma ve araç üzerinde düşük hızla entegrasyon testleri.

Gerçek hareket düğmeleri bu koşullar doğrulanana kadar devre dışıdır. Simülasyon bu protokolde bir firmware emülatörü değil, bağımsız bir geliştirme modelidir.
