# Yolcu Bilgilendirme Sistemi Kullanim ve Ariza Notlari

## Sistem Bilesenleri

- Merkez kontrol modulu
- Ic ekranlar
- Dis ekranlar
- Sesli anons birimi
- Rota paketi ve istasyon verisi
- Ag gecidi

## Belirtiler

### Belirti: Ic ekran donuyor ama anons calisiyor

Muhtemel nedenler:

- Ekran kontrol modulu yeniden baslatma gerektiriyor
- Veri guncellemesi yarim kalmis
- Ic ekran veri yolunda gecici kesinti var

Onerilen adimlar:

1. Son hata kodu not edilir.
2. Ekran modulu servis ekranindan yeniden baslatilir.
3. Rota paketi surumu dogrulanir.
4. Sorun devam ederse kablolama ve haberlesme arabirimi kontrol edilir.

### Belirti: Ekran ve anons birlikte durdu

Muhtemel nedenler:

- Merkez kontrol modulu enerjisiz
- Ag gecidi arizali
- Uygulama servisi kilitlendi

Karar notu:

Hem gorsel hem sesli bilgilendirme ayni anda kesildiyse lokal cihazdan cok merkezi kontrol veya enerji kaynagi arastirilmalidir.

### Belirti: Yanlis istasyon bilgisi gosteriliyor

Muhtemel nedenler:

- Rota paketi eski
- Konum tetigi gecikmeli
- Dogrulama tablosu hatali yuklenmis

Bu durumda once yazilim/veri surumu kontrol edilir, mekanik ariza varsayilmaz.
