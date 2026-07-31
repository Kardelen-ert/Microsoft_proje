# Rayli Sistemler Donanim ve Ariza Teshis Asistani

Bu proje, internet baglantisi olmadan calisan kurumsal bir yerel RAG sisteminin ust klasor yapisini barindirir.

## Klasorler

- `backend/`: FastAPI, LangChain, ChromaDB, SQLAlchemy ve Foundry Local entegrasyonunu iceren sunucu tarafi
- `frontend/`: Tablet odakli Flutter istemcisi

Bu asamada yalnizca backend ve frontend ayrimi yapilmis, ana klasor yapisi olusturulmustur.

## Calistirma Notu

- Backend varsayilan olarak `http://127.0.0.1:8010` adresinde calismalidir.
- Flutter Web ayni bilgisayarda acilmiyorsa veya uygulama fiziksel cihazdan erisiyorsa frontend'i su sekilde baslat:
  `flutter run --dart-define=API_BASE_URL=http://BILGISAYAR_IP:8010/api`
- Android emulator icin varsayilan adres `http://10.0.2.2:8010/api` olarak korunur.
