# RAG Grounding Politikalari

Bir yerel RAG sisteminde temel hedef, modelin ezbere veya tahmine dayali cevap vermesini azaltmaktir.
Bu nedenle yanitlar, retrieval katmanindan gelen kaynaklara dayandirilmalidir.

Grounded cevap kurallari:

- Cevap, getirilen kaynak parcilar ile desteklenmelidir.
- Kaynakta gecmeyen kritik bir bilgi dogrudan gercek gibi yazilmamalidir.
- Kaynak yetersizse sistem fallback mesaji vermelidir.
- Birden fazla kaynak birbiriyle celisiyorsa cevap bunu not etmelidir.

Fallback ornekleri:

- "Dokumanlarda bu soruyu destekleyen yeterli bilgi bulunamadi."
- "Mevcut kaynaklar kesin bir sonuc vermiyor."
- "Bu konu icin ek dokuman gerekli."

Asagidaki durumlarda confidence dusuk kabul edilmelidir:

- Sadece tek ve kisa bir chunk bulunmussa
- En yakin chunk mesafesi yuksekse
- Kullanici sorusu cok genelse
- Kaynak metinde acik prosedur yerine sadece tanim varsa

Test onerileri:

- Cevaplanabilir soru: "Foundry Local internet olmadan calisir mi?"
- Cevaplanamaz soru: "2028 yilinda hangi model varsayilan olacak?"
- Kismi cevap sorusu: "Chunk boyutu neden onemlidir?"
