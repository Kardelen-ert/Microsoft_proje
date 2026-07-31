# Sample Sources

Bu klasor, local RAG demosu icin uretilmis hazir bilgi tabani kaynaklarini icerir.

Dosyalar:

- `01_foundry_local_basics.md`
- `02_rag_grounding_policy.md`
- `03_brake_system_diagnostics.md`
- `04_passenger_information_faults.md`
- `05_maintenance_faq.txt`
- `06_demo_questions.md`

Onerilen ingest akisi:

1. Bu klasordeki `.md` ve `.txt` dosyalarini `/api/documents/ingest` endpoint'ine ver.
2. Ardindan `/api/documents/status` ile chunk ve dokuman sayisini kontrol et.
3. Son olarak frontend test laboratuvarindan demo sorularini calistir.
