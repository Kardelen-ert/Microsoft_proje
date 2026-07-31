# Sentetik Bilgi Tabani Indeksi

Bu klasor, yerel RAG asistaninin daha kaliteli cevap verebilmesi icin uretilmis tutarli ve sentetik bir bilgi tabani icerir.

Kapsam:

- Cekis ve fren sistemi
- Kapi sistemi
- HVAC
- Yolcu bilgilendirme sistemi
- Guc dagitimi ve yardimci enerji
- Bakim prosedurleri
- Ariza kodlari
- Operator/bakimci karar kurallari

Ana belgeler:

- `01_system_overview.md`
- `02_fault_response_policy.md`
- `03_brake_and_pneumatic_manual.md`
- `04_door_system_manual.md`
- `05_hvac_manual.md`
- `06_passenger_information_manual.md`
- `07_aux_power_and_battery_manual.md`
- `08_fault_code_catalog.md`
- `09_preventive_maintenance_sop.md`
- `10_diagnostic_decision_rules.md`
- `11_training_faq.md`
- `12_demo_test_questions.md`

Kullanim amaci:

1. Bu belgeler ingest edilir.
2. Sistem bu belgelerden chunk olusturur.
3. Kullanici ariza veya bakim sorusu sorar.
4. Retrieval ilgili chunk'lari bulur.
5. Model, sadece bu kaynaklari kullanarak cevap verir.

Not:

Bu bilgi tabani gercek saha dokumani degildir. Tamamen egitim, demo ve RAG davranis testi amaciyla yapay olarak uretilmistir.
