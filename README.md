# FiyatOpt Kimya

Streamlit tabanli fiyatlandirma ve karlilik hesaplama uygulamasi (TCMB kurlari entegre).

## Ozellikler
- Iki farkli fiyatlama yontemi ile hesaplama
- TCMB gunluk doviz kurlari
- Nakliye tarifeleri ve urun yonetimi
- Gecmis kayitlar, CSV/Excel/PDF ciktilar

## Kurulum
```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Calistirma
```bash
.venv\Scripts\python.exe -m streamlit run "fiyatopt_kimya.py"
```
Uygulama: http://localhost:8501

## Disa Aktarim
- Fiyat Hesaplama sayfasinda: Excel ve PDF
- Gecmis Kayitlar sayfasinda: CSV, Excel ve PDF

## Sorun Giderme
- `ModuleNotFoundError: 'fpdf'`: `pip install -r requirements.txt`
- Streamlit farkli Python ortaminda aciliyorsa, yukaridaki calistirma komutunu kullanin.

## Notlar
- `fiyatopt.db` yerel veritabani dosyasidir ve `.gitignore` ile dislanir.
- PDF uretimi icin WeasyPrint kullanilir; Streamlit Cloud icin `packages.txt` gereklidir.
