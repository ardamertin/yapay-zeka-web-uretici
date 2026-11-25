import os
import re
import time
from google import genai
from google.genai import types

API_KEY = os.environ.get("GEMINI_API_KEY", "GEMINI_API_ANAHTARINIZI_BURAYA_YAZIN")

SISTEM_MESAJI = """
Sen kıdemli bir Frontend ve UI/UX geliştiricisisin. Kullanıcının tasarım talebine göre birbirine tam uyumlu 3 ayrı HTML5 sayfası üreteceksin:
1. index.html (Login Sayfası: E-posta alanı, Şifre alanı, Şifre göster/gizle butonu, Giriş Yap butonu, Şifremi Unuttum -> forgot_password.html bağlantısı, Üye Ol -> signup.html bağlantısı)
2. forgot_password.html (Şifremi Unuttum Sayfası: Başlık, E-posta adresi alanı, Şifre sıfırlama bağlantısı gönder butonu, Giriş sayfasına dön -> index.html bağlantısı)
3. signup.html (Üye Ol Sayfası: Ad Soyad alanı, E-posta alanı, Şifre alanı, Şifre tekrar alanı, her iki şifre alanında göster/gizle butonu, Üye Ol butonu, Giriş sayfasına dön -> index.html bağlantısı)

KESİN KURALLAR:
- Yanıtında SADECE aşağıdaki üç ayıraç etiketini ve altlarında ilgili saf HTML kodunu döndür. Açıklama yazma!
===INDEX.HTML===
[index.html kodu]
===FORGOT_PASSWORD.HTML===
[forgot_password.html kodu]
===SIGNUP.HTML===
[signup.html kodu]

- Tüm CSS (<style>) ve JavaScript (<script>) kodları harici dosya olmadan doğrudan her HTML dosyasının içine gömülü olmalıdır.
- Tasarım: Modern, mobil uyumlu (responsive), koyu mor/lacivert arka planlı Dark Mode, cam efekti (glassmorphism), mor-mavi neon butonlar ve hover parlama efektleri içermelidir.
- JavaScript Doğrulamaları: Boş alan kontrolü, regex ile e-posta formatı kontrolü, şifre uzunluk/eşleşme kontrolü (signup sayfasında) ve kullanıcıya ekranda şık uyarı/başarı mesajı gösterimi mutlaka çalışır halde olmalıdır.
"""

ORNEK_TASARIM_TALEBI = (
    "Modern, profesyonel, karanlık temalı bir üyelik sistemi oluştur. "
    "Mor ve mavi neon renkler kullan. Login, Forgot Password ve Signup sayfaları aynı tasarım dilini kullansın. "
    "Sayfalar arasında geçişler çalışsın. Butonların üzerine gelindiğinde parlama efekti oluşsun."
)

def temizle_markdown(metin: str) -> str:
    metin = re.sub(r"^```html\s*", "", metin.strip(), flags=re.IGNORECASE)
    metin = re.sub(r"^```\s*", "", metin.strip())
    metin = re.sub(r"\s*```$", "", metin.strip())
    return metin.strip()

def sayfalari_ayristir_ve_kaydet(ham_cikti: str) -> None:
    ayiraclar = [
        ("index.html", "===INDEX.HTML==="),
        ("forgot_password.html", "===FORGOT_PASSWORD.HTML==="),
        ("signup.html", "===SIGNUP.HTML==="),
    ]
    for i, (dosya_adi, baslangic_etiketi) in enumerate(ayiraclar):
        if baslangic_etiketi not in ham_cikti:
            raise ValueError(f"Model çıktısında beklenen etiket bulunamadı: {baslangic_etiketi}")
        baslangic_indeksi = ham_cikti.index(baslangic_etiketi) + len(baslangic_etiketi)
        if i + 1 < len(ayiraclar):
            sonraki_etiket = ayiraclar[i + 1][1]
            bitis_indeksi = ham_cikti.index(sonraki_etiket)
            icerik = ham_cikti[baslangic_indeksi:bitis_indeksi]
        else:
            icerik = ham_cikti[baslangic_indeksi:]
        temiz_html = temizle_markdown(icerik)
        with open(dosya_adi, "w", encoding="utf-8") as dosya:
            dosya.write(temiz_html)
        print(f"[BASARILI] {dosya_adi} olusturuldu ({len(temiz_html)} karakter).")

def uygun_modelleri_bul(client) -> list:
    modeller = ["gemini-3.8-flash", "gemini-3.8-pro", "gemini-3.5-flash"]
    try:
        for m in client.models.list():
            ad = m.name.replace("models/", "")
            if "gemini" in ad and "embedding" not in ad and ad not in modeller:
                modeller.append(ad)
    except Exception:
        pass
    return modeller

def main():
    print("=== Yapay Zeka Destekli Web Sayfasi Uretici ===")
    kullanici_talebi = input("Web sitesi tasarim talebinizi girin (Varsayilan ornek icin Enter'a basin):\n> ").strip()
    if not kullanici_talebi:
        kullanici_talebi = ORNEK_TASARIM_TALEBI
        print("\n[BILGI] Varsayilan neon karanlik tema talebi kullaniliyor...")

    client = genai.Client(api_key=API_KEY)
    tam_istem = f"{SISTEM_MESAJI}\n\nKullanıcı talebi:\n{kullanici_talebi}"

    response = None
    for model_adi in uygun_modelleri_bul(client):
        try:
            print(f"\n[BEKLEYIN] {model_adi} modeline baglaniliyor ve 3 sayfa uretiliyor...")
            response = client.models.generate_content(
                model=model_adi,
                contents=tam_istem,
                config=types.GenerateContentConfig(temperature=0.5, max_output_tokens=16000),
            )
            if response and response.text and "===INDEX.HTML===" in response.text:
                break
        except Exception as e:
            print(f"[UYARI] {model_adi} atlandi: {str(e)[:90]}...")
            time.sleep(1)

    if response is None or not response.text:
        raise RuntimeError("API su an yanit vermiyor, lutfen biraz sonra tekrar deneyin.")

    sayfalari_ayristir_ve_kaydet(response.text)
    print("\n[TAMAMLANDI] Tum HTML dosyalari hazir!")

if __name__ == "__main__":
    main()