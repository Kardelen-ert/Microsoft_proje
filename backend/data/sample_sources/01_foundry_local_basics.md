# Foundry Local Temelleri

Foundry Local, buyuk dil modellerini kullanicinin cihazinda calistirmak icin tasarlanmis yerel bir calisma katmanidir.
Bu yaklasimda veri buluta gitmeden cihaz icinde kalir. Bu nedenle internet baglantisi olmadan da yanit uretilebilir.

Temel prensipler:

- Model cagirilari yerel calisir.
- Hassas dokumanlar cihaz disina cikmaz.
- Kucuk ve orta olcekli bilgi tabanlari icin hizli prototip kurulabilir.
- CPU veya uygun hizlandirici mevcutsa yanit suresi iyilesir.

Foundry Local kullanan bir soru-cevap asistaninda ideal akis sunlardir:

1. Kaynak dokumanlar sisteme yuklenir.
2. Dokumanlar parcalanir.
3. Her parca icin embedding uretilir.
4. Kullanici sorusu embedding'e cevrilir.
5. En ilgili parcilar bulunur.
6. Bu parcilar model baglami olarak kullanilir.
7. Model, sadece verilen baglam uzerinden cevap uretir.

En iyi uygulamalar:

- Soru yetersizse modelin "yeterli bilgi yok" demesi istenmelidir.
- Kaynak parcilar kisa ama anlamsal olarak butun kalacak bicimde bolunmelidir.
- Ayni bilgi farkli dokumanlarda geciyorsa metadata ile kaynak ayrimi korunmalidir.
- Gereksiz uzun baglam, cevap kalitesini dusurebilir.
