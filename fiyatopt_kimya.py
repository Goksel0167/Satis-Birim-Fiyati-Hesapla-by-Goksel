"""
FiyatOpt Kimya - Yapı Kimyasalları Fiyatlandırma ve Karlılık Optimizasyon Uygulaması
=====================================================================================
Geliştirici: FiyatOpt Kimya Team
Versiyon: 1.0.0
Açıklama: SQLite tabanlı, TCMB kurları entegreli, çift yöntemli fiyat hesaplama uygulaması.
"""

import streamlit as st
import sqlite3
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import pandas as pd
from io import BytesIO
import os
from fpdf import FPDF
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except Exception:
    WEASYPRINT_AVAILABLE = False
from typing import Optional, Tuple, Dict
import traceback
from decimal import Decimal, ROUND_HALF_UP

# ─────────────────────────────────────────────────────────────────────────────
# SAYFA AYARLARI
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FiyatOpt Kimya",
    page_icon="⚗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────────────────────────────────────
# CUSTOM CSS - Modern, Temiz Arayüz
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

    /* Ana tema */
    :root {
        --primary: #1a56db;
        --primary-light: #3b82f6;
        --success: #059669;
        --danger: #dc2626;
        --warning: #d97706;
        --bg-card: #ffffff;
        --bg-light: #f8fafc;
        --border: #e2e8f0;
        --text-main: #0f172a;
        --text-muted: #64748b;
    }

    .stApp {
        font-family: 'Inter', sans-serif;
        background-color: #f1f5f9;
    }

    /* Sidebar stil */
    [data-testid="stSidebar"] {
        background: linear-gradient(160deg, #0f172a 0%, #1e293b 100%);
        border-right: none;
    }
    [data-testid="stSidebar"] * {
        color: #e2e8f0 !important;
    }
    [data-testid="stSidebar"] .stRadio label {
        background: rgba(255,255,255,0.05);
        border-radius: 8px;
        padding: 8px 12px;
        margin: 2px 0;
        transition: all 0.2s;
        display: block;
    }
    [data-testid="stSidebar"] .stRadio label:hover {
        background: rgba(255,255,255,0.12);
    }

    /* Başlık kartı */
    .page-header {
        background: linear-gradient(135deg, #1a56db 0%, #0ea5e9 100%);
        border-radius: 16px;
        padding: 24px 32px;
        margin-bottom: 24px;
        color: white;
        box-shadow: 0 4px 24px rgba(26,86,219,0.3);
    }
    .page-header h1 {
        font-size: 1.75rem;
        font-weight: 700;
        margin: 0 0 4px 0;
        color: white;
    }
    .page-header p {
        font-size: 0.9rem;
        opacity: 0.85;
        margin: 0;
        color: white;
    }

    /* Kur kartları */
    .kur-kart {
        background: #f8fafc;
        border-radius: 12px;
        padding: 16px 20px;
        border: 1px solid #cbd5f5;
        text-align: center;
        box-shadow: 0 1px 6px rgba(15,23,42,0.08);
        transition: transform 0.2s;
    }
    .kur-kart:hover { transform: translateY(-2px); }
    .kur-kart .kur-label { font-size: 0.7rem; font-weight: 700; color: #1e293b; text-transform: uppercase; letter-spacing: 1px; }
    .kur-kart .kur-value { font-size: 1.5rem; font-weight: 800; color: #0f172a; font-family: 'JetBrains Mono', monospace; }
    .kur-kart .kur-sub { font-size: 0.72rem; color: #334155; margin-top: 2px; }

    /* Hesaplama sonuç kartları */
    .result-card {
        background: white;
        border-radius: 14px;
        padding: 24px;
        border: 1px solid var(--border);
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        height: 100%;
    }
    .result-card h3 {
        font-size: 1rem;
        font-weight: 600;
        color: var(--text-main);
        margin: 0 0 16px 0;
        padding-bottom: 12px;
        border-bottom: 2px solid var(--border);
    }
    .metric-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 0;
        border-bottom: 1px solid #f1f5f9;
    }
    .metric-row:last-child { border-bottom: none; }
    .metric-label { font-size: 0.85rem; color: var(--text-muted); }
    .metric-value { font-size: 0.95rem; font-weight: 600; font-family: 'JetBrains Mono', monospace; }
    .metric-value.positive { color: var(--success); }
    .metric-value.negative { color: var(--danger); }
    .metric-value.blue { color: var(--primary); }
    .metric-value.large {
        font-size: 1.3rem;
        font-weight: 700;
        color: var(--primary);
    }

    /* Bilgi kutusu */
    .info-box {
        background: #eff6ff;
        border-left: 4px solid var(--primary);
        border-radius: 0 8px 8px 0;
        padding: 12px 16px;
        margin: 12px 0;
        font-size: 0.85rem;
        color: #1e40af;
    }
    .success-box {
        background: #f0fdf4;
        border-left: 4px solid var(--success);
        border-radius: 0 8px 8px 0;
        padding: 12px 16px;
        margin: 12px 0;
        font-size: 0.85rem;
        color: #065f46;
    }
    .warning-box {
        background: #fffbeb;
        border-left: 4px solid var(--warning);
        border-radius: 0 8px 8px 0;
        padding: 12px 16px;
        margin: 12px 0;
        font-size: 0.85rem;
        color: #92400e;
    }

    /* Tablo stilleri */
    .styled-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.88rem;
        border-radius: 10px;
        overflow: hidden;
    }
    .styled-table th {
        background: #1e293b;
        color: white;
        padding: 10px 14px;
        text-align: left;
        font-weight: 600;
        font-size: 0.82rem;
        letter-spacing: 0.3px;
    }
    .styled-table td {
        padding: 9px 14px;
        border-bottom: 1px solid #f1f5f9;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.83rem;
    }
    .styled-table tr:nth-child(even) td { background: #f8fafc; }
    .styled-table tr:hover td { background: #eff6ff; }
    .td-positive { color: #059669; font-weight: 600; }
    .td-negative { color: #dc2626; font-weight: 600; }
    .td-blue { color: #1a56db; font-weight: 700; }
    .td-usd { background: linear-gradient(90deg, #dbeafe, #eff6ff) !important; }
    .td-eur { background: linear-gradient(90deg, #d1fae5, #f0fdf4) !important; }
    .td-gbp { background: linear-gradient(90deg, #fef3c7, #fffbeb) !important; }
    .td-chf { background: linear-gradient(90deg, #fce7f3, #fdf4ff) !important; }

    /* Yöntem başlıkları */
    .yontem-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: linear-gradient(135deg, #1a56db, #0ea5e9);
        color: white;
        border-radius: 20px;
        padding: 6px 16px;
        font-size: 0.82rem;
        font-weight: 600;
        margin-bottom: 12px;
    }
    .yontem-badge-2 {
        background: linear-gradient(135deg, #059669, #10b981);
    }

    /* Buton stilleri */
    .stButton button {
        border-radius: 8px;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
        transition: all 0.2s;
    }

    /* Divider */
    .section-divider {
        border: none;
        border-top: 2px solid var(--border);
        margin: 20px 0;
    }

    /* Logo */
    .sidebar-logo {
        text-align: center;
        padding: 20px 0 8px 0;
        font-size: 2.5rem;
    }
    .sidebar-title {
        text-align: center;
        font-size: 1.1rem;
        font-weight: 700;
        color: white !important;
        margin-bottom: 4px;
    }
    .sidebar-sub {
        text-align: center;
        font-size: 0.72rem;
        color: #94a3b8 !important;
        margin-bottom: 20px;
        letter-spacing: 1px;
        text-transform: uppercase;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# VERİTABANI İŞLEMLERİ
# ─────────────────────────────────────────────────────────────────────────────
DB_PATH = "fiyatopt.db"

def get_connection() -> sqlite3.Connection:
    """SQLite bağlantısı oluştur."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Veritabanı tablolarını oluştur (ilk çalışmada)."""
    conn = get_connection()
    c = conn.cursor()

    # Ürünler tablosu
    c.execute("""
        CREATE TABLE IF NOT EXISTS urunler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            urun_adi TEXT NOT NULL,
            fabrika TEXT NOT NULL,
            fabrika_kodu TEXT NOT NULL,
            kategori TEXT NOT NULL,
            maliyet REAL NOT NULL,
            nakliye_fabrika REAL NOT NULL DEFAULT 0,
            olusturma_tarihi TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Nakliye tarifeleri tablosu
    c.execute("""
        CREATE TABLE IF NOT EXISTS nakliye (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fabrika TEXT NOT NULL,
            il TEXT NOT NULL,
            ilce TEXT DEFAULT '',
            ucret REAL NOT NULL,
            guncelleme_tarihi TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(fabrika, il, ilce)
        )
    """)

    # Hesaplama geçmişi tablosu
    c.execute("""
        CREATE TABLE IF NOT EXISTS gecmis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            urun_adi TEXT,
            fabrika TEXT,
            sevk_ili TEXT,
            sevk_ilcesi TEXT,
            maliyet REAL,
            nakliye REAL,
            marj REAL,
            yontem1_satis REAL,
            yontem1_kar REAL,
            yontem2_satis REAL,
            yontem2_kar REAL,
            usd_kur REAL,
            eur_kur REAL,
            tarih TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

    # Demo veri yükle (ilk çalışmada boşsa)
    _seed_demo_data()

def _seed_demo_data():
    """İlk çalışmada örnek veri yükle."""
    conn = get_connection()
    c = conn.cursor()

    # Ürün yoksa demo ürünler ekle
    c.execute("SELECT COUNT(*) FROM urunler")
    if c.fetchone()[0] == 0:
        demo_urunler = [
            ("LignoSüper 40", "Gebze", "14", "Ligno", 18.50, 0.80),
            ("LignoPlus 60", "Gebze", "14", "Ligno", 22.00, 0.80),
            ("NaftalinStd 30", "Adana", "16", "Naftalin", 14.20, 1.10),
            ("NaftalinHD 45", "Adana", "16", "Naftalin", 19.80, 1.10),
            ("PCE Akışkan 50", "Trabzon", "15", "PCE", 28.90, 1.50),
            ("PCE Premium 60", "Trabzon", "15", "PCE", 35.00, 1.50),
            ("LignoEco 25", "Adana", "16", "Ligno", 12.00, 1.10),
            ("PCE Flex 40", "Gebze", "14", "PCE", 26.50, 0.80),
        ]
        c.executemany(
            "INSERT INTO urunler (urun_adi, fabrika, fabrika_kodu, kategori, maliyet, nakliye_fabrika) VALUES (?,?,?,?,?,?)",
            demo_urunler
        )

    # Nakliye yoksa demo nakliye ekle
    c.execute("SELECT COUNT(*) FROM nakliye")
    if c.fetchone()[0] == 0:
        demo_nakliye = [
            # Gebze fabrıkası
            ("Gebze", "İstanbul", "", 0.45),
            ("Gebze", "Kocaeli", "", 0.30),
            ("Gebze", "Ankara", "", 0.85),
            ("Gebze", "İzmir", "", 1.10),
            ("Gebze", "Bursa", "", 0.60),
            ("Gebze", "Antalya", "", 1.40),
            ("Gebze", "Adana", "", 1.60),
            ("Gebze", "Konya", "", 1.05),
            # Adana fabrikası
            ("Adana", "Adana", "", 0.25),
            ("Adana", "Mersin", "", 0.40),
            ("Adana", "Gaziantep", "", 0.65),
            ("Adana", "Ankara", "", 1.20),
            ("Adana", "İstanbul", "", 1.70),
            ("Adana", "Antalya", "", 0.90),
            ("Adana", "Konya", "", 0.80),
            ("Adana", "Hatay", "", 0.55),
            # Trabzon fabrikası
            ("Trabzon", "Trabzon", "", 0.20),
            ("Trabzon", "Rize", "", 0.35),
            ("Trabzon", "Samsun", "", 0.70),
            ("Trabzon", "Ankara", "", 1.30),
            ("Trabzon", "İstanbul", "", 1.80),
            ("Trabzon", "Erzurum", "", 0.75),
        ]
        c.executemany(
            "INSERT OR IGNORE INTO nakliye (fabrika, il, ilce, ucret) VALUES (?,?,?,?)",
            demo_nakliye
        )

    conn.commit()
    conn.close()

# ─────────────────────────────────────────────────────────────────────────────
# TCMB KUR ÇEKİMİ
# ─────────────────────────────────────────────────────────────────────────────
TCMB_URL_TEMPLATE = "https://www.tcmb.gov.tr/kurlar/{tarih_yol}/{tarih_dosya}.xml"
TCMB_TODAY_URL = "https://www.tcmb.gov.tr/kurlar/today.xml"

def _parse_tcmb_xml(xml_text: str) -> Tuple[Optional[Dict], Optional[str]]:
    """TCMB XML'inden kur verilerini çıkar."""
    try:
        root = ET.fromstring(xml_text)
        tarih = root.attrib.get("Tarih", "")
        kurlar = {}
        hedef = {"USD": "ABD DOLARI", "EUR": "EURO", "GBP": "İNGİLİZ STERLİNİ", "CHF": "İSVİÇRE FRANGI"}

        for currency in root.findall("Currency"):
            kod = currency.attrib.get("CurrencyCode", "")
            if kod in hedef:
                satis_el = currency.find("ForexSelling")
                if satis_el is not None and satis_el.text:
                    kurlar[kod] = float(satis_el.text.replace(",", "."))

        if len(kurlar) >= 4:
            return kurlar, tarih
        return None, None
    except Exception:
        return None, None

def _tarih_url(tarih: datetime) -> str:
    """TCMB için tarih URL'si oluştur."""
    return TCMB_URL_TEMPLATE.format(
        tarih_yol=tarih.strftime("%Y%m"),
        tarih_dosya=tarih.strftime("%Y%m%d")
    )

@st.cache_data(ttl=3600)  # 1 saat önbellek
def get_tcmb_kurlar() -> Tuple[Optional[Dict], str, str]:
    """
    TCMB'den güncel döviz kurlarını çek.
    Tatil/hafta sonu ise son iş gününe geri git.
    Returns: (kurlar_dict, tarih_str, kaynak_mesaj)
    """
    # Önce today.xml dene
    try:
        resp = requests.get(TCMB_TODAY_URL, timeout=8)
        if resp.status_code == 200:
            kurlar, tarih = _parse_tcmb_xml(resp.text)
            if kurlar:
                return kurlar, tarih, "TCMB Günlük Kur"
    except Exception:
        pass

    # today.xml çalışmadıysa son 10 iş gününü dene
    bugun = datetime.now()
    for geriye in range(1, 11):
        hedef = bugun - timedelta(days=geriye)
        # Hafta sonu atla
        if hedef.weekday() >= 5:
            continue
        try:
            url = _tarih_url(hedef)
            resp = requests.get(url, timeout=8)
            if resp.status_code == 200:
                kurlar, tarih = _parse_tcmb_xml(resp.text)
                if kurlar:
                    return kurlar, tarih, f"Son İş Günü ({hedef.strftime('%d.%m.%Y')})"
        except Exception:
            continue

    # Hiçbiri çalışmadıysa varsayılan değerler kullan
    varsayilan = {"USD": 32.50, "EUR": 35.20, "GBP": 41.30, "CHF": 37.80}
    return varsayilan, "—", "⚠️ Bağlantı yok (tahmini)"

# ─────────────────────────────────────────────────────────────────────────────
# TÜRKİYE İLLERİ
# ─────────────────────────────────────────────────────────────────────────────
ILLER = [
    "Adana", "Adıyaman", "Afyonkarahisar", "Ağrı", "Amasya", "Ankara", "Antalya",
    "Artvin", "Aydın", "Balıkesir", "Bilecik", "Bingöl", "Bitlis", "Bolu",
    "Burdur", "Bursa", "Çanakkale", "Çankırı", "Çorum", "Denizli", "Diyarbakır",
    "Edirne", "Elazığ", "Erzincan", "Erzurum", "Eskişehir", "Gaziantep", "Giresun",
    "Gümüşhane", "Hakkari", "Hatay", "Isparta", "İçel (Mersin)", "İstanbul", "İzmir",
    "Kars", "Kastamonu", "Kayseri", "Kırklareli", "Kırşehir", "Kocaeli", "Konya",
    "Kütahya", "Malatya", "Manisa", "Kahramanmaraş", "Mardin", "Muğla", "Muş",
    "Nevşehir", "Niğde", "Ordu", "Rize", "Sakarya", "Samsun", "Siirt",
    "Sinop", "Sivas", "Tekirdağ", "Tokat", "Trabzon", "Tunceli", "Şanlıurfa",
    "Uşak", "Van", "Yozgat", "Zonguldak", "Aksaray", "Bayburt", "Karaman",
    "Kırıkkale", "Batman", "Şırnak", "Bartın", "Ardahan", "Iğdır", "Yalova",
    "Karabük", "Kilis", "Osmaniye", "Düzce"
]
ILLER_SORTED = sorted(ILLER)

FABRIKALAR = {
    "Gebze (14)": {"ad": "Gebze", "kod": "14"},
    "Adana (16)": {"ad": "Adana", "kod": "16"},
    "Trabzon (15)": {"ad": "Trabzon", "kod": "15"},
}

KATEGORILER = ["Ligno", "Naftalin", "PCE"]

# ─────────────────────────────────────────────────────────────────────────────
# YARDIMCI FONKSİYONLAR
# ─────────────────────────────────────────────────────────────────────────────
def fmt_tl(value: float) -> str:
    """TL formatla."""
    return f"₺{value:,.4f}"

def fmt_doviz(value: float, simge: str = "$") -> str:
    """Döviz formatla."""
    return f"{simge}{value:,.4f}"

def _round_half_up(value: float, ndigits: int = 2) -> float:
    """Yarim ve ustu yukari yuvarla (half-up)."""
    if value is None:
        return 0.0
    quant = Decimal("1").scaleb(-ndigits)
    return float(Decimal(str(value)).quantize(quant, rounding=ROUND_HALF_UP))

def _excel_bytes_from_sheets(sheets: Dict[str, pd.DataFrame]) -> bytes:
    """DataFrame sözlüğünü Excel'e yaz ve bytes döndür."""
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for name, df in sheets.items():
            safe_name = name[:31]
            df.to_excel(writer, index=False, sheet_name=safe_name)
    return buffer.getvalue()

def _pdf_font_setup(pdf: FPDF) -> None:
    """PDF için uygun fontu seç (mümkünse unicode)."""
    win_dir = os.environ.get("WINDIR", "C:\\Windows")
    arial_path = os.path.join(win_dir, "Fonts", "arial.ttf")
    if os.path.exists(arial_path):
        pdf.add_font("ArialUnicode", "", arial_path, uni=True)
        pdf.set_font("ArialUnicode", size=10)
    else:
        pdf.set_font("Helvetica", size=10)

def _pdf_safe(text: str) -> str:
    """Core font kullaniliyorsa turkce karakterleri basitlestir."""
    try:
        text.encode("latin-1")
        return text
    except UnicodeEncodeError:
        return text.encode("latin-1", "ignore").decode("latin-1")

def _html_report_base(page_title: str, content_html: str) -> str:
    """PDF icin sade HTML iskeleti."""
    css = """
    @page { size: A4; margin: 16mm; }
    body { font-family: DejaVu Sans, Arial, sans-serif; background: #f1f5f9; color: #0f172a; }
    .page-header { background: linear-gradient(135deg, #1a56db 0%, #0ea5e9 100%); border-radius: 14px; padding: 16px 20px; color: #fff; }
    .page-header h1 { margin: 0; font-size: 18px; }
    .page-header p { margin: 4px 0 0; font-size: 11px; opacity: 0.9; }
    .info-box { background: #eff6ff; border-left: 4px solid #1a56db; border-radius: 0 8px 8px 0; padding: 10px 12px; margin: 10px 0 14px; font-size: 11px; }
    .two-col { display: flex; gap: 10px; margin-bottom: 10px; }
    .card { background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 12px; box-shadow: 0 2px 6px rgba(0,0,0,0.06); flex: 1; }
    .badge { display: inline-block; background: linear-gradient(135deg, #1a56db, #0ea5e9); color: #fff; border-radius: 999px; padding: 4px 10px; font-size: 10px; font-weight: 600; margin-bottom: 8px; }
    .badge-green { background: linear-gradient(135deg, #059669, #10b981); }
    .metric-table { width: 100%; border-collapse: collapse; font-size: 11px; }
    .metric-table td { padding: 6px 0; border-bottom: 1px solid #f1f5f9; }
    .metric-table td:last-child { text-align: right; font-weight: 600; }
    .table { width: 100%; border-collapse: collapse; font-size: 10px; }
    .table th { background: #1e293b; color: #fff; padding: 6px 8px; text-align: left; }
    .table td { padding: 6px 8px; border-bottom: 1px solid #f1f5f9; }
    .table tr:nth-child(even) td { background: #f8fafc; }
    h3 { margin: 6px 0 8px; font-size: 12px; }
    """
    return f"""
    <!doctype html>
    <html>
    <head>
        <meta charset="utf-8" />
        <title>{page_title}</title>
        <style>{css}</style>
    </head>
    <body>
        {content_html}
    </body>
    </html>
    """

def _html_metric_table(rows: list) -> str:
    """Ana metrikleri tablo olarak yazdir."""
    row_html = "".join([f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in rows])
    return f"<table class=\"metric-table\">{row_html}</table>"

def _html_table_from_df(df: pd.DataFrame, header_title: str = "") -> str:
    """DataFrame'i HTML tabloya cevir."""
    if df is None or df.empty:
        return ""
    head_html = "".join([f"<th>{col}</th>" for col in df.columns])
    body_rows = []
    for _, row in df.iterrows():
        cols = "".join([f"<td>{row[col]}</td>" for col in df.columns])
        body_rows.append(f"<tr>{cols}</tr>")
    header = f"<h3>{header_title}</h3>" if header_title else ""
    return f"{header}<table class=\"table\"><tr>{head_html}</tr>{''.join(body_rows)}</table>"

def _pdf_from_dataframe(title: str, df: pd.DataFrame) -> bytes:
    """DataFrame'i basit tablo olarak PDF'e cevir."""
    if WEASYPRINT_AVAILABLE:
        html = _html_report_base(
            page_title=title,
            content_html=_html_table_from_df(df, header_title=title)
        )
        return HTML(string=html).write_pdf()
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.add_page()
    _pdf_font_setup(pdf)

    pdf.set_font_size(12)
    pdf.cell(0, 8, _pdf_safe(title), ln=1)
    pdf.ln(2)

    pdf.set_font_size(8)
    page_width = pdf.w - pdf.l_margin - pdf.r_margin
    col_count = len(df.columns)
    col_width = max(12, page_width / max(col_count, 1))

    for col in df.columns:
        pdf.cell(col_width, 6, _pdf_safe(str(col)), border=1)
    pdf.ln()

    for _, row in df.iterrows():
        for col in df.columns:
            pdf.cell(col_width, 6, _pdf_safe(str(row[col])), border=1)
        pdf.ln()

    pdf_out = pdf.output(dest="S")
    return bytes(pdf_out) if isinstance(pdf_out, (bytearray, bytes)) else str(pdf_out).encode("latin-1", "ignore")

def _pdf_current_calc(
    urun_adi: str,
    fabrika: str,
    kategori: str,
    maliyet: float,
    nakliye: float,
    marj: float,
    y1: Dict,
    y2: Dict,
    doviz_y1: pd.DataFrame,
    doviz_y2: pd.DataFrame
) -> bytes:
    """Anlik hesaplama raporunu PDF olarak olustur."""
    if WEASYPRINT_AVAILABLE:
        doviz_html_1 = _html_table_from_df(doviz_y1, header_title="Doviz Bazli Satis Fiyatlari (Yontem 1)")
        doviz_html_2 = _html_table_from_df(doviz_y2, header_title="Doviz Bazli Satis Fiyatlari (Yontem 2)")

        y1_rows = [
            ("Birim Maliyet", fmt_tl(y1["maliyet"])),
            ("Nakliye", fmt_tl(y1["nakliye"])),
            ("Toplam Maliyet", fmt_tl(y1["toplam_maliyet"])),
            ("Uygulanan Marj", f"%{marj:.1f}"),
            ("Birim Satis Fiyati", fmt_tl(y1["satis"])),
            ("Birim Kar", f"{fmt_tl(y1["kar"])} (%{y1["kar_pct"]:.1f})"),
        ]
        y2_rows = [
            ("Birim Maliyet", fmt_tl(y2["maliyet"])),
            ("Maliyet x (1+Marj%)", fmt_tl(y2["maliyet_marjli"])),
            ("Nakliye (Eklenen)", fmt_tl(y2["nakliye"])),
            ("Uygulanan Marj", f"%{marj:.1f}"),
            ("Birim Satis Fiyati", fmt_tl(y2["satis"])),
            ("Birim Kar", f"{fmt_tl(y2["kar"])} (%{y2["kar_pct"]:.1f})"),
        ]

        ozet_df = pd.DataFrame({
            "Metrik": ["Birim Satis Fiyati (TL/kg)", "Birim Kar (TL/kg)", "Kar Marji (%)", "USD Satis Fiyati", "EUR Satis Fiyati"],
            "Yontem 1": [
                f"₺{y1['satis']:.4f}",
                f"₺{y1['kar']:.4f}",
                f"%{y1['kar_pct']:.2f}",
                f"${y1['satis']/doviz_y1.iloc[0]['Kur (₺)']:.4f}" if not doviz_y1.empty and "Kur (₺)" in doviz_y1.columns else "—",
                f"€{y1['satis']/doviz_y1.iloc[1]['Kur (₺)']:.4f}" if len(doviz_y1) > 1 else "—",
            ],
            "Yontem 2": [
                f"₺{y2['satis']:.4f}",
                f"₺{y2['kar']:.4f}",
                f"%{y2['kar_pct']:.2f}",
                f"${y2['satis']/doviz_y2.iloc[0]['Kur (₺)']:.4f}" if not doviz_y2.empty and "Kur (₺)" in doviz_y2.columns else "—",
                f"€{y2['satis']/doviz_y2.iloc[1]['Kur (₺)']:.4f}" if len(doviz_y2) > 1 else "—",
            ],
            "Fark (Y1-Y2)": [f"₺{(y1['satis'] - y2['satis']):+.4f}", "—", "—", "—", "—"],
        })

        content = f"""
        <div class="page-header">
            <h1>Fiyat Hesaplama</h1>
            <p>Urun ve sevkiyat bilgilerine gore fiyatlama raporu</p>
        </div>
        <div class="info-box">
            <b>Urun:</b> {urun_adi} &nbsp;|&nbsp; <b>Fabrika:</b> {fabrika} &nbsp;|&nbsp; <b>Kategori:</b> {kategori}
        </div>
        <div class="two-col">
            <div class="card">
                <div class="badge">Yontem 1 - Toplu Marj</div>
                {_html_metric_table(y1_rows)}
            </div>
            <div class="card">
                <div class="badge badge-green">Yontem 2 - Kademeli Marj</div>
                {_html_metric_table(y2_rows)}
            </div>
        </div>
        <div class="two-col">
            <div class="card">{doviz_html_1}</div>
            <div class="card">{doviz_html_2}</div>
        </div>
        <div class="card">{_html_table_from_df(ozet_df, header_title="Yontem Karsilastirma Ozeti")}</div>
        """

        html = _html_report_base(page_title="Fiyat Hesaplama", content_html=content)
        return HTML(string=html).write_pdf()
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.add_page()
    _pdf_font_setup(pdf)

    pdf.set_font_size(12)
    pdf.cell(0, 8, _pdf_safe("Fiyat Hesaplama Raporu"), ln=1)
    pdf.set_font_size(9)
    pdf.cell(0, 6, _pdf_safe(f"Urun: {urun_adi} | Fabrika: {fabrika} | Kategori: {kategori}"), ln=1)
    pdf.cell(0, 6, _pdf_safe(f"Maliyet: {maliyet:.4f} TL/kg | Nakliye: {nakliye:.4f} TL/kg | Marj: %{marj:.1f}"), ln=1)
    pdf.ln(2)

    pdf.set_font_size(10)
    pdf.cell(0, 6, _pdf_safe("Yontem 1"), ln=1)
    pdf.set_font_size(9)
    pdf.cell(0, 6, _pdf_safe(f"Satis: {y1['satis']:.4f} TL/kg | Kar: {y1['kar']:.4f} TL/kg (%{y1['kar_pct']:.2f})"), ln=1)
    pdf.ln(1)

    pdf.set_font_size(10)
    pdf.cell(0, 6, _pdf_safe("Yontem 2"), ln=1)
    pdf.set_font_size(9)
    pdf.cell(0, 6, _pdf_safe(f"Satis: {y2['satis']:.4f} TL/kg | Kar: {y2['kar']:.4f} TL/kg (%{y2['kar_pct']:.2f})"), ln=1)
    pdf.ln(2)

    if not doviz_y1.empty:
        pdf.set_font_size(10)
        pdf.cell(0, 6, _pdf_safe("Doviz Bazli Satis (Yontem 1)"), ln=1)
        pdf.set_font_size(8)
        for _, row in doviz_y1.iterrows():
            pdf.cell(0, 5, _pdf_safe(f"{row['Para Birimi']}: {row['Satış Fiyatı']:.4f} | Kur: {row['Kur (₺)']:.2f}"), ln=1)
        pdf.ln(1)

    if not doviz_y2.empty:
        pdf.set_font_size(10)
        pdf.cell(0, 6, _pdf_safe("Doviz Bazli Satis (Yontem 2)"), ln=1)
        pdf.set_font_size(8)
        for _, row in doviz_y2.iterrows():
            pdf.cell(0, 5, _pdf_safe(f"{row['Para Birimi']}: {row['Satış Fiyatı']:.4f} | Kur: {row['Kur (₺)']:.2f}"), ln=1)

    pdf_out = pdf.output(dest="S")
    return bytes(pdf_out) if isinstance(pdf_out, (bytearray, bytes)) else str(pdf_out).encode("latin-1", "ignore")

def hesapla_yontem1(maliyet: float, nakliye: float, marj_pct: float) -> Dict:
    """
    Yöntem 1: (Maliyet + Nakliye) × (1 + Marj%) = Satış Fiyatı
    Maliyet ve nakliye toplanır, üzerine marj uygulanır.
    """
    toplam_maliyet = maliyet + nakliye
    satis = toplam_maliyet * (1 + marj_pct / 100)
    kar = satis - toplam_maliyet
    kar_pct = (kar / satis * 100) if satis > 0 else 0
    return {
        "maliyet": maliyet,
        "nakliye": nakliye,
        "toplam_maliyet": toplam_maliyet,
        "satis": satis,
        "kar": kar,
        "kar_pct": kar_pct,
    }

def hesapla_yontem2(maliyet: float, nakliye: float, marj_pct: float) -> Dict:
    """
    Yöntem 2: Maliyet × (1 + Marj%) + Nakliye = Satış Fiyatı
    Önce maliyet üzerine marj, sonra nakliye eklenir.
    """
    maliyet_marjli = maliyet * (1 + marj_pct / 100)
    satis = maliyet_marjli + nakliye
    kar = satis - (maliyet + nakliye)
    kar_pct = (kar / satis * 100) if satis > 0 else 0
    return {
        "maliyet": maliyet,
        "nakliye": nakliye,
        "maliyet_marjli": maliyet_marjli,
        "satis": satis,
        "kar": kar,
        "kar_pct": kar_pct,
    }

def nakliye_getir(fabrika: str, il: str, ilce: str = "") -> Optional[float]:
    """
    Nakliye ücretini veritabanından çek.
    Önce fabrika+il+ilçe ara, bulamazsa fabrika+il ara.
    """
    conn = get_connection()
    c = conn.cursor()
    try:
        # İlçe ile ara
        if ilce:
            c.execute(
                "SELECT ucret FROM nakliye WHERE fabrika=? AND il=? AND ilce=?",
                (fabrika, il, ilce)
            )
            row = c.fetchone()
            if row:
                return row["ucret"]
        # Sadece il ile ara
        c.execute(
            "SELECT ucret FROM nakliye WHERE fabrika=? AND il=? AND (ilce='' OR ilce IS NULL)",
            (fabrika, il)
        )
        row = c.fetchone()
        if row:
            return row["ucret"]
        return None
    finally:
        conn.close()

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
def render_sidebar(kurlar: Dict, kur_tarihi: str, kur_kaynak: str):
    """Sol kenar çubuğunu render et."""
    with st.sidebar:
        # Logo & başlık
        st.markdown('<div class="sidebar-logo">⚗️</div>', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-title">FiyatOpt Kimya</div>', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-sub">Fiyatlandırma & Karlılık</div>', unsafe_allow_html=True)

        # Navigasyon
        st.markdown("##### 📌 Menü")
        sayfa = st.radio(
            "Sayfa",
            ["🧮 Fiyat Hesaplama", "📦 Ürün Yönetimi", "🚚 Nakliye Yönetimi", "📊 Geçmiş Kayıtlar"],
            label_visibility="collapsed"
        )

        st.markdown("---")

        # TCMB Kurları
        st.markdown("##### 💱 TCMB Döviz Kurları")
        st.markdown(f"<small style='color:#94a3b8'>📅 {kur_tarihi} · {kur_kaynak}</small>", unsafe_allow_html=True)

        if kurlar:
            col1, col2 = st.columns(2)
            simgeler = {"USD": "🇺🇸", "EUR": "🇪🇺", "GBP": "🇬🇧", "CHF": "🇨🇭"}
            for i, (kod, deger) in enumerate(kurlar.items()):
                with col1 if i % 2 == 0 else col2:
                    st.markdown(f"""
                    <div class="kur-kart" style="margin:4px 0;">
                        <div class="kur-label">{simgeler.get(kod,'')} {kod}</div>
                        <div class="kur-value">₺{deger:.2f}</div>
                    </div>
                    """, unsafe_allow_html=True)

        if st.button("🔄 Kurları Yenile", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        st.markdown("---")
        st.markdown(f"<small style='color:#64748b'>🕒 {datetime.now().strftime('%d.%m.%Y %H:%M')}</small>", unsafe_allow_html=True)
        st.markdown("<small style='color:#475569'>v1.0.0 · SQLite</small>", unsafe_allow_html=True)

    return sayfa

# ─────────────────────────────────────────────────────────────────────────────
# SAYFA 1: FİYAT HESAPLAMA
# ─────────────────────────────────────────────────────────────────────────────
def sayfa_hesaplama(kurlar: Dict):
    st.markdown("""
    <div class="page-header">
        <h1>🧮 Fiyat Hesaplama</h1>
        <p>Ürün ve sevkiyat bilgilerini girerek her iki yöntemle karlılık analizi yapın.</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Ürün Seçimi ──────────────────────────────────────────────────────────
    conn = get_connection()
    urunler_df = pd.read_sql("SELECT * FROM urunler ORDER BY fabrika, urun_adi", conn)
    conn.close()

    if urunler_df.empty:
        st.markdown('<div class="warning-box">⚠️ Henüz ürün eklenmemiş. Lütfen önce <b>Ürün Yönetimi</b> sayfasından ürün ekleyin.</div>', unsafe_allow_html=True)
        return

    col1, col2, col3 = st.columns([3, 2, 2])

    with col1:
        # Ürün listesi: Ürün Adı | Fabrika | Kod
        urun_etiketler = [
            f"{r['urun_adi']} — {r['fabrika']} ({r['fabrika_kodu']})"
            for _, r in urunler_df.iterrows()
        ]
        secili_etiket = st.selectbox("📦 Ürün Seçin", urun_etiketler)
        secili_idx = urun_etiketler.index(secili_etiket)
        secili_urun = urunler_df.iloc[secili_idx]

    with col2:
        sevk_ili = st.selectbox("📍 Sevk İli", ILLER_SORTED)

    with col3:
        sevk_ilcesi = st.text_input("📍 İlçe (Opsiyonel)", placeholder="Örn: Seyhan")

    # ── Nakliye Otomatik Çek ─────────────────────────────────────────────────
    nakliye_bulunan = nakliye_getir(secili_urun["fabrika"], sevk_ili, sevk_ilcesi.strip())

    col_nav1, col_nav2 = st.columns([2, 3])
    with col_nav1:
        if nakliye_bulunan is not None:
            nakliye = st.number_input(
                "🚚 Nakliye (TL/kg)",
                value=float(nakliye_bulunan),
                min_value=0.0, step=0.01, format="%.4f",
                help=f"Tarifeden otomatik yüklendi: {secili_urun['fabrika']} → {sevk_ili}"
            )
            st.markdown(f'<div class="success-box">✅ Nakliye tarifeden otomatik yüklendi: <b>₺{nakliye_bulunan:.4f}/kg</b></div>', unsafe_allow_html=True)
        else:
            nakliye = st.number_input(
                "🚚 Nakliye (TL/kg) — Manuel Giriş",
                value=0.0, min_value=0.0, step=0.01, format="%.4f",
                help="Bu rota için tanımlı nakliye bulunamadı, manuel girin."
            )
            st.markdown(f'<div class="warning-box">⚠️ Bu rota için nakliye tarifesi bulunamadı: <b>{secili_urun["fabrika"]} → {sevk_ili}</b>. Manuel girin veya Nakliye Yönetimi\'nden ekleyin.</div>', unsafe_allow_html=True)

    if "marj_pct" not in st.session_state:
        st.session_state["marj_pct"] = 20.0
    if "marj_slider" not in st.session_state:
        st.session_state["marj_slider"] = st.session_state["marj_pct"]

    with col_nav2:
        m_col1, m_col2, m_col3 = st.columns([1, 6, 1])
        def _marj_azalt():
            st.session_state["marj_pct"] = max(1.0, st.session_state["marj_pct"] - 1.0)
            st.session_state["marj_slider"] = st.session_state["marj_pct"]

        def _marj_arttir():
            st.session_state["marj_pct"] = min(80.0, st.session_state["marj_pct"] + 1.0)
            st.session_state["marj_slider"] = st.session_state["marj_pct"]

        with m_col1:
            st.button("-", use_container_width=True, key="marj_minus", on_click=_marj_azalt)
        with m_col3:
            st.button("+", use_container_width=True, key="marj_plus", on_click=_marj_arttir)

        with m_col2:
            marj = st.slider(
                "📈 Kar Marjı (%)",
                min_value=1.0,
                max_value=80.0,
                value=float(st.session_state["marj_slider"]),
                step=0.5,
                format="%.1f%%",
                key="marj_slider"
            )
            st.session_state["marj_pct"] = marj

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    # ── Ürün Özet Bilgisi ────────────────────────────────────────────────────
    maliyet = float(secili_urun["maliyet"])

    st.markdown(f"""
    <div class="info-box">
        <b>Seçili Ürün:</b> {secili_urun['urun_adi']} &nbsp;|&nbsp;
        <b>Fabrika:</b> {secili_urun['fabrika']} ({secili_urun['fabrika_kodu']}) &nbsp;|&nbsp;
        <b>Kategori:</b> {secili_urun['kategori']} &nbsp;|&nbsp;
        <b>Birim Maliyet:</b> ₺{maliyet:.4f}/kg
    </div>
    """, unsafe_allow_html=True)

    # ── Hesaplama ────────────────────────────────────────────────────────────
    y1 = hesapla_yontem1(maliyet, nakliye, marj)
    y2 = hesapla_yontem2(maliyet, nakliye, marj)

    # ── Yan Yana Yöntem Kartları ─────────────────────────────────────────────
    kart1, kart2 = st.columns(2)
    doviz_df1 = pd.DataFrame()
    doviz_df2 = pd.DataFrame()

    def doviz_tablo_df(satis_tl: float, kurlar: Dict) -> pd.DataFrame:
        """Döviz bazlı satış fiyatları tablosu DataFrame üret."""
        simgeler = {"USD": "🇺🇸 $", "EUR": "🇪🇺 €", "GBP": "🇬🇧 £", "CHF": "🇨🇭 ₣"}
        satirlar = []
        for kod in ["USD", "EUR", "GBP", "CHF"]:
            kur = kurlar.get(kod) if kurlar else None
            if kur and kur > 0:
                doviz_fiyat = _round_half_up(satis_tl / kur, 2)
                satirlar.append({
                    "Para Birimi": f"{simgeler[kod]} {kod}",
                    "Satış Fiyatı": doviz_fiyat,
                    "Satış Fiyatı (₺)": _round_half_up(satis_tl, 2),
                    "Kur (₺)": _round_half_up(kur, 2),
                })
        return pd.DataFrame(satirlar)

    with kart1:
        st.markdown("""
        <div class="yontem-badge">📐 Yöntem 1 — Toplu Marj</div>
        """, unsafe_allow_html=True)
        st.markdown('<div class="info-box" style="font-size:0.78rem">Formül: <b>(Maliyet + Nakliye) × (1 + Marj%)</b></div>', unsafe_allow_html=True)

        kar_renk1 = "positive" if y1["kar"] >= 0 else "negative"

        st.markdown(f"""
        <div class="result-card">
            <div class="metric-row">
                <span class="metric-label">Birim Maliyet</span>
                <span class="metric-value">{fmt_tl(y1['maliyet'])}</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Nakliye</span>
                <span class="metric-value">{fmt_tl(y1['nakliye'])}</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Toplam Maliyet</span>
                <span class="metric-value">{fmt_tl(y1['toplam_maliyet'])}</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Uygulanan Marj</span>
                <span class="metric-value blue">%{marj:.1f}</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Birim Satış Fiyatı</span>
                <span class="metric-value large">{fmt_tl(y1['satis'])}</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Birim Kâr</span>
                <span class="metric-value {kar_renk1}">{fmt_tl(y1['kar'])} (%{y1['kar_pct']:.1f})</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("**💱 Döviz Bazlı Satış Fiyatları**")
        doviz_df1 = doviz_tablo_df(y1["satis"], kurlar)
        if doviz_df1.empty:
            st.markdown('<div class="warning-box">⚠️ Döviz kuru bulunamadı.</div>', unsafe_allow_html=True)
        else:
            st.dataframe(
                doviz_df1,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Satış Fiyatı": st.column_config.NumberColumn(format="%.2f"),
                    "Satış Fiyatı (₺)": st.column_config.NumberColumn(format="₺%.2f"),
                    "Kur (₺)": st.column_config.NumberColumn(format="₺%.2f"),
                }
            )

    with kart2:
        st.markdown("""
        <div class="yontem-badge yontem-badge-2">📊 Yöntem 2 — Kademeli Marj</div>
        """, unsafe_allow_html=True)
        st.markdown('<div class="info-box" style="font-size:0.78rem">Formül: <b>Maliyet × (1 + Marj%) + Nakliye</b></div>', unsafe_allow_html=True)

        kar_renk2 = "positive" if y2["kar"] >= 0 else "negative"

        st.markdown(f"""
        <div class="result-card">
            <div class="metric-row">
                <span class="metric-label">Birim Maliyet</span>
                <span class="metric-value">{fmt_tl(y2['maliyet'])}</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Maliyet × (1+Marj%)</span>
                <span class="metric-value">{fmt_tl(y2['maliyet_marjli'])}</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Nakliye (Eklenen)</span>
                <span class="metric-value">{fmt_tl(y2['nakliye'])}</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Uygulanan Marj</span>
                <span class="metric-value blue">%{marj:.1f}</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Birim Satış Fiyatı</span>
                <span class="metric-value large">{fmt_tl(y2['satis'])}</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Birim Kâr</span>
                <span class="metric-value {kar_renk2}">{fmt_tl(y2['kar'])} (%{y2['kar_pct']:.1f})</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("**💱 Döviz Bazlı Satış Fiyatları**")
        doviz_df2 = doviz_tablo_df(y2["satis"], kurlar)
        if doviz_df2.empty:
            st.markdown('<div class="warning-box">⚠️ Döviz kuru bulunamadı.</div>', unsafe_allow_html=True)
        else:
            st.dataframe(
                doviz_df2,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Satış Fiyatı": st.column_config.NumberColumn(format="%.2f"),
                    "Satış Fiyatı (₺)": st.column_config.NumberColumn(format="₺%.2f"),
                    "Kur (₺)": st.column_config.NumberColumn(format="₺%.2f"),
                }
            )

    # ── Karşılaştırma Özeti ──────────────────────────────────────────────────
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    st.markdown("#### 📋 Yöntem Karşılaştırma Özeti")

    fark = y1["satis"] - y2["satis"]
    ozet_data = {
        "Metrik": ["Birim Satış Fiyatı (TL/kg)", "Birim Kâr (TL/kg)", "Kâr Marjı (%)", "USD Satış Fiyatı", "EUR Satış Fiyatı"],
        "Yöntem 1": [
            f"₺{y1['satis']:.4f}",
            f"₺{y1['kar']:.4f}",
            f"%{y1['kar_pct']:.2f}",
            f"${y1['satis']/kurlar.get('USD',1):.4f}" if kurlar.get("USD") else "—",
            f"€{y1['satis']/kurlar.get('EUR',1):.4f}" if kurlar.get("EUR") else "—",
        ],
        "Yöntem 2": [
            f"₺{y2['satis']:.4f}",
            f"₺{y2['kar']:.4f}",
            f"%{y2['kar_pct']:.2f}",
            f"${y2['satis']/kurlar.get('USD',1):.4f}" if kurlar.get("USD") else "—",
            f"€{y2['satis']/kurlar.get('EUR',1):.4f}" if kurlar.get("EUR") else "—",
        ],
        "Fark (Y1−Y2)": ["—", "—", "—", "—", "—"]
    }
    fark_str = f"₺{fark:+.4f}"
    ozet_data["Fark (Y1−Y2)"][0] = fark_str

    ozet_df = pd.DataFrame(ozet_data)
    st.dataframe(ozet_df, use_container_width=True, hide_index=True)

    # ── Disa Aktar (Excel / PDF) ─────────────────────────────────────────────
    st.markdown("#### 📤 Hesaplama Disa Aktar")
    y1_df = pd.DataFrame([
        {"Metrik": "Birim Maliyet", "Deger": y1["maliyet"]},
        {"Metrik": "Nakliye", "Deger": y1["nakliye"]},
        {"Metrik": "Toplam Maliyet", "Deger": y1["toplam_maliyet"]},
        {"Metrik": "Marj (%)", "Deger": marj},
        {"Metrik": "Satis", "Deger": y1["satis"]},
        {"Metrik": "Kar", "Deger": y1["kar"]},
        {"Metrik": "Kar (%)", "Deger": y1["kar_pct"]},
    ])
    y2_df = pd.DataFrame([
        {"Metrik": "Birim Maliyet", "Deger": y2["maliyet"]},
        {"Metrik": "Maliyet Marjli", "Deger": y2["maliyet_marjli"]},
        {"Metrik": "Nakliye", "Deger": y2["nakliye"]},
        {"Metrik": "Marj (%)", "Deger": marj},
        {"Metrik": "Satis", "Deger": y2["satis"]},
        {"Metrik": "Kar", "Deger": y2["kar"]},
        {"Metrik": "Kar (%)", "Deger": y2["kar_pct"]},
    ])

    excel_bytes = _excel_bytes_from_sheets({
        "Ozet": ozet_df,
        "Yontem1": y1_df,
        "Yontem2": y2_df,
        "Doviz_Y1": doviz_df1,
        "Doviz_Y2": doviz_df2,
    })

    pdf_bytes = _pdf_current_calc(
        urun_adi=secili_urun["urun_adi"],
        fabrika=secili_urun["fabrika"],
        kategori=secili_urun["kategori"],
        maliyet=maliyet,
        nakliye=nakliye,
        marj=marj,
        y1=y1,
        y2=y2,
        doviz_y1=doviz_df1,
        doviz_y2=doviz_df2
    )

    d_col1, d_col2, d_col3 = st.columns([1, 1, 4])
    with d_col1:
        st.download_button(
            "⬇️ Excel",
            data=excel_bytes,
            file_name=f"fiyatopt_hesaplama_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    with d_col2:
        st.download_button(
            "⬇️ PDF",
            data=pdf_bytes,
            file_name=f"fiyatopt_hesaplama_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf",
        )

    # ── Geçmişe Kaydet ───────────────────────────────────────────────────────
    st.markdown("")
    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        if st.button("💾 Hesaplamayı Kaydet", type="primary", use_container_width=True):
            try:
                conn = get_connection()
                conn.execute("""
                    INSERT INTO gecmis (
                        urun_adi, fabrika, sevk_ili, sevk_ilcesi,
                        maliyet, nakliye, marj,
                        yontem1_satis, yontem1_kar,
                        yontem2_satis, yontem2_kar,
                        usd_kur, eur_kur
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                """, (
                    secili_urun["urun_adi"], secili_urun["fabrika"],
                    sevk_ili, sevk_ilcesi,
                    maliyet, nakliye, marj,
                    y1["satis"], y1["kar"],
                    y2["satis"], y2["kar"],
                    kurlar.get("USD"), kurlar.get("EUR")
                ))
                conn.commit()
                conn.close()
                st.success("✅ Hesaplama geçmişe kaydedildi!")
            except Exception as e:
                st.error(f"❌ Kayıt hatası: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# SAYFA 2: ÜRÜN YÖNETİMİ
# ─────────────────────────────────────────────────────────────────────────────
def sayfa_urun_yonetimi():
    st.markdown("""
    <div class="page-header">
        <h1>📦 Ürün Yönetimi</h1>
        <p>Ürün ekleyin, düzenleyin ve mevcut ürün kataloğunu yönetin.</p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["➕ Yeni Ürün Ekle", "📋 Ürün Listesi"])

    with tab1:
        st.markdown("#### Yeni Ürün Bilgileri")
        col1, col2 = st.columns(2)

        with col1:
            urun_adi = st.text_input("Ürün Adı *", placeholder="Örn: LignoSüper 40")
            fabrika_sec = st.selectbox("Fabrika *", list(FABRIKALAR.keys()))
            kategori = st.selectbox("Kategori *", KATEGORILER)

        with col2:
            maliyet = st.number_input("Maliyet (TL/kg) *", min_value=0.01, value=15.00, step=0.01, format="%.4f")
            nakliye_fab = st.number_input("Fabrika Nakliyesi (TL/kg)", min_value=0.0, value=0.80, step=0.01, format="%.4f",
                                          help="Fabrikadan çıkış nakliye maliyeti")

        fabrika_info = FABRIKALAR[fabrika_sec]

        st.markdown(f"""
        <div class="info-box">
            Seçili Fabrika: <b>{fabrika_info['ad']}</b> — Fabrika Kodu: <b>{fabrika_info['kod']}</b>
        </div>
        """, unsafe_allow_html=True)

        if st.button("✅ Ürün Ekle", type="primary"):
            if not urun_adi.strip():
                st.error("❌ Ürün adı boş bırakılamaz!")
            else:
                try:
                    conn = get_connection()
                    conn.execute("""
                        INSERT INTO urunler (urun_adi, fabrika, fabrika_kodu, kategori, maliyet, nakliye_fabrika)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (urun_adi.strip(), fabrika_info["ad"], fabrika_info["kod"], kategori, maliyet, nakliye_fab))
                    conn.commit()
                    conn.close()
                    st.success(f"✅ **{urun_adi}** başarıyla eklendi!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Hata: {e}")

    with tab2:
        conn = get_connection()
        df = pd.read_sql("SELECT * FROM urunler ORDER BY fabrika, kategori, urun_adi", conn)
        conn.close()

        if df.empty:
            st.markdown('<div class="warning-box">Henüz ürün bulunmuyor.</div>', unsafe_allow_html=True)
        else:
            # Filtreleme
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                fab_filtre = st.multiselect("Fabrika Filtrele", ["Gebze", "Adana", "Trabzon"], default=["Gebze", "Adana", "Trabzon"])
            with col_f2:
                kat_filtre = st.multiselect("Kategori Filtrele", KATEGORILER, default=KATEGORILER)
            with col_f3:
                arama = st.text_input("🔍 Ürün Ara", placeholder="Ürün adı ara...")

            df_filtered = df[
                df["fabrika"].isin(fab_filtre) &
                df["kategori"].isin(kat_filtre)
            ]
            if arama:
                df_filtered = df_filtered[df_filtered["urun_adi"].str.contains(arama, case=False, na=False)]

            st.markdown(f"**{len(df_filtered)} ürün** listeleniyor.")

            # Görünüm için sütun adlarını düzenle
            display_df = df_filtered[["id","urun_adi","fabrika","fabrika_kodu","kategori","maliyet","nakliye_fabrika","olusturma_tarihi"]].copy()
            display_df.columns = ["ID","Ürün Adı","Fabrika","Kod","Kategori","Maliyet (₺/kg)","Fabrika Nakliyesi (₺/kg)","Eklenme Tarihi"]

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Maliyet (₺/kg)": st.column_config.NumberColumn(format="₺%.4f"),
                    "Fabrika Nakliyesi (₺/kg)": st.column_config.NumberColumn(format="₺%.4f"),
                }
            )

            # Ürün sil
            st.markdown("---")
            st.markdown("#### 🗑️ Ürün Sil")
            secenekler = [f"[{r['id']}] {r['urun_adi']} — {r['fabrika']}" for _, r in df_filtered.iterrows()]
            if secenekler:
                silinecek = st.selectbox("Silinecek ürünü seçin", secenekler)
                silinecek_id = int(silinecek.split("]")[0].replace("[", ""))
                if st.button("🗑️ Seçili Ürünü Sil", type="secondary"):
                    conn = get_connection()
                    conn.execute("DELETE FROM urunler WHERE id=?", (silinecek_id,))
                    conn.commit()
                    conn.close()
                    st.success("✅ Ürün silindi.")
                    st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# SAYFA 3: NAKLİYE YÖNETİMİ
# ─────────────────────────────────────────────────────────────────────────────
def sayfa_nakliye_yonetimi():
    st.markdown("""
    <div class="page-header">
        <h1>🚚 Nakliye Yönetimi</h1>
        <p>Fabrika bazlı nakliye tarifelerini tanımlayın ve düzenleyin.</p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["➕ Tarife Ekle / Güncelle", "📋 Tarife Listesi"])

    with tab1:
        st.markdown("#### Nakliye Tarifesi Tanımla")

        col1, col2, col3 = st.columns(3)
        with col1:
            n_fabrika = st.selectbox("Fabrika *", ["Gebze", "Adana", "Trabzon"])
        with col2:
            n_il = st.selectbox("Sevk İli *", ILLER_SORTED)
        with col3:
            n_ilce = st.text_input("İlçe (Opsiyonel)", placeholder="Boş bırakılabilir")

        n_ucret = st.number_input("Nakliye Ücreti (TL/kg) *", min_value=0.0, value=1.00, step=0.05, format="%.4f")

        st.markdown(f"""
        <div class="info-box">
            Eklenecek rota: <b>{n_fabrika}</b> → <b>{n_il}</b>{f" / {n_ilce.strip()}" if n_ilce.strip() else ""} = <b>₺{n_ucret:.4f}/kg</b>
        </div>
        """, unsafe_allow_html=True)

        if st.button("✅ Tarife Ekle / Güncelle", type="primary"):
            try:
                conn = get_connection()
                conn.execute("""
                    INSERT INTO nakliye (fabrika, il, ilce, ucret, guncelleme_tarihi)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(fabrika, il, ilce) DO UPDATE SET
                        ucret = excluded.ucret,
                        guncelleme_tarihi = CURRENT_TIMESTAMP
                """, (n_fabrika, n_il, n_ilce.strip(), n_ucret))
                conn.commit()
                conn.close()
                st.success(f"✅ {n_fabrika} → {n_il} tarifesi kaydedildi: ₺{n_ucret:.4f}/kg")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Hata: {e}")

        # Toplu import
        st.markdown("---")
        st.markdown("#### 📂 Toplu Tarife Yükle (CSV)")
        st.markdown('<div class="info-box">CSV formatı: <b>fabrika, il, ilce, ucret</b> (başlık satırı olmalı)</div>', unsafe_allow_html=True)

        yuklu_dosya = st.file_uploader("CSV Dosyası Seç", type=["csv"])
        if yuklu_dosya is not None:
            try:
                csv_df = pd.read_csv(yuklu_dosya)
                st.dataframe(csv_df.head(10), use_container_width=True)
                if st.button("📥 CSV'yi Veritabanına Aktar"):
                    conn = get_connection()
                    basari = 0
                    hata = 0
                    for _, row in csv_df.iterrows():
                        try:
                            conn.execute("""
                                INSERT INTO nakliye (fabrika, il, ilce, ucret)
                                VALUES (?,?,?,?)
                                ON CONFLICT(fabrika, il, ilce) DO UPDATE SET ucret=excluded.ucret
                            """, (str(row.get("fabrika","")), str(row.get("il","")),
                                  str(row.get("ilce","")), float(row.get("ucret",0))))
                            basari += 1
                        except Exception:
                            hata += 1
                    conn.commit()
                    conn.close()
                    st.success(f"✅ {basari} tarife aktarıldı. {hata} hata.")
                    st.rerun()
            except Exception as e:
                st.error(f"❌ CSV okuma hatası: {e}")

    with tab2:
        conn = get_connection()
        df = pd.read_sql("SELECT * FROM nakliye ORDER BY fabrika, il, ilce", conn)
        conn.close()

        if df.empty:
            st.markdown('<div class="warning-box">Henüz nakliye tarifesi eklenmemiş.</div>', unsafe_allow_html=True)
        else:
            # Filtreleme
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                fab_f = st.multiselect("Fabrika", ["Gebze", "Adana", "Trabzon"], default=["Gebze", "Adana", "Trabzon"])
            with col_f2:
                il_ara = st.text_input("🔍 İl Ara", placeholder="İl adı ara...")

            df_f = df[df["fabrika"].isin(fab_f)]
            if il_ara:
                df_f = df_f[df_f["il"].str.contains(il_ara, case=False, na=False)]

            # Özet istatistik
            col_s1, col_s2, col_s3 = st.columns(3)
            col_s1.metric("Toplam Tarife", len(df_f))
            col_s2.metric("Ortalama Ücret", f"₺{df_f['ucret'].mean():.4f}" if not df_f.empty else "—")
            col_s3.metric("Maks. Ücret", f"₺{df_f['ucret'].max():.4f}" if not df_f.empty else "—")

            display_df = df_f[["id","fabrika","il","ilce","ucret","guncelleme_tarihi"]].copy()
            display_df.columns = ["ID","Fabrika","İl","İlçe","Ücret (₺/kg)","Güncelleme"]

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Ücret (₺/kg)": st.column_config.NumberColumn(format="₺%.4f"),
                }
            )

            # Tarife duzelt
            st.markdown("---")
            st.markdown("#### ✏️ Tarife Duzelt")
            tarife_duzelt = [
                f"[{r['id']}] {r['fabrika']} → {r['il']}{' / '+r['ilce'] if r['ilce'] else ''} = ₺{r['ucret']:.4f}"
                for _, r in df_f.iterrows()
            ]
            if tarife_duzelt:
                sec_duzelt = st.selectbox("Duzeltilecek tarife", tarife_duzelt, key="tarife_duzelt_sec")
                sec_id = int(sec_duzelt.split("]")[0].replace("[", ""))
                sec_row = df_f[df_f["id"] == sec_id].iloc[0]

                col_e1, col_e2, col_e3 = st.columns(3)
                with col_e1:
                    fab_list = ["Gebze", "Adana", "Trabzon"]
                    fab_idx = fab_list.index(sec_row["fabrika"]) if sec_row["fabrika"] in fab_list else 0
                    e_fabrika = st.selectbox("Fabrika", fab_list, index=fab_idx, key="tarife_edit_fab")
                with col_e2:
                    il_idx = ILLER_SORTED.index(sec_row["il"]) if sec_row["il"] in ILLER_SORTED else 0
                    e_il = st.selectbox("Sevk Ili", ILLER_SORTED, index=il_idx, key="tarife_edit_il")
                with col_e3:
                    e_ilce = st.text_input("Ilce", value=sec_row["ilce"] or "", key="tarife_edit_ilce")

                e_ucret = st.number_input(
                    "Nakliye Ucreti (TL/kg)",
                    min_value=0.0,
                    value=float(sec_row["ucret"]),
                    step=0.05,
                    format="%.4f",
                    key="tarife_edit_ucret"
                )

                if st.button("✅ Tarifeyi Guncelle", type="primary", key="tarife_edit_btn"):
                    try:
                        conn = get_connection()
                        conn.execute(
                            """
                            UPDATE nakliye
                            SET fabrika=?, il=?, ilce=?, ucret=?, guncelleme_tarihi=CURRENT_TIMESTAMP
                            WHERE id=?
                            """,
                            (e_fabrika, e_il, e_ilce.strip(), e_ucret, sec_id)
                        )
                        conn.commit()
                        conn.close()
                        st.success("✅ Tarife guncellendi.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Guncelleme hatasi: {e}")
            else:
                st.markdown('<div class="warning-box">Liste bos. Duzeltme yapilacak tarife yok.</div>', unsafe_allow_html=True)

            # Tarife sil
            st.markdown("---")
            st.markdown("#### 🗑️ Tarife Sil")
            tarife_sec = [f"[{r['id']}] {r['fabrika']} → {r['il']}{' / '+r['ilce'] if r['ilce'] else ''} = ₺{r['ucret']:.4f}"
                          for _, r in df_f.iterrows()]
            if tarife_sec:
                silinecek_t = st.selectbox("Silinecek tarife", tarife_sec)
                silinecek_tid = int(silinecek_t.split("]")[0].replace("[", ""))
                if st.button("🗑️ Seçili Tarifeyi Sil", type="secondary"):
                    conn = get_connection()
                    conn.execute("DELETE FROM nakliye WHERE id=?", (silinecek_tid,))
                    conn.commit()
                    conn.close()
                    st.success("✅ Tarife silindi.")
                    st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# SAYFA 4: GEÇMİŞ KAYITLAR
# ─────────────────────────────────────────────────────────────────────────────
def sayfa_gecmis():
    st.markdown("""
    <div class="page-header">
        <h1>📊 Geçmiş Kayıtlar</h1>
        <p>Daha önce yapılan tüm fiyat hesaplamalarını görüntüleyin ve analiz edin.</p>
    </div>
    """, unsafe_allow_html=True)

    conn = get_connection()
    df = pd.read_sql("SELECT * FROM gecmis ORDER BY tarih DESC", conn)
    conn.close()

    if df.empty:
        st.markdown('<div class="info-box">📭 Henüz kaydedilmiş hesaplama bulunmuyor. Hesaplama sayfasından hesaplamalarınızı kaydedin.</div>', unsafe_allow_html=True)
        return

    # İstatistikler
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    col_s1.metric("Toplam Kayıt", len(df))
    col_s2.metric("Ort. Y1 Satış", f"₺{df['yontem1_satis'].mean():.4f}")
    col_s3.metric("Ort. Kar Marjı", f"₺{df['yontem1_kar'].mean():.4f}")
    col_s4.metric("Son Güncelleme", df["tarih"].iloc[0][:10] if len(df) > 0 else "—")

    st.markdown("---")

    # Filtreleme
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        urun_filtre = st.text_input("🔍 Ürün Ara")
    with col_f2:
        fab_filtre_g = st.multiselect("Fabrika Filtrele", ["Gebze", "Adana", "Trabzon"], default=["Gebze", "Adana", "Trabzon"])

    df_f = df[df["fabrika"].isin(fab_filtre_g)]
    if urun_filtre:
        df_f = df_f[df_f["urun_adi"].str.contains(urun_filtre, case=False, na=False)]

    # Görünüm
    display_df = df_f[[
        "id","tarih","urun_adi","fabrika","sevk_ili","sevk_ilcesi",
        "maliyet","nakliye","marj",
        "yontem1_satis","yontem1_kar",
        "yontem2_satis","yontem2_kar",
        "usd_kur","eur_kur"
    ]].copy()
    display_df.columns = [
        "ID","Tarih","Ürün","Fabrika","Sevk İli","İlçe",
        "Maliyet","Nakliye","Marj%",
        "Y1 Satış","Y1 Kâr",
        "Y2 Satış","Y2 Kâr",
        "USD Kur","EUR Kur"
    ]

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Maliyet": st.column_config.NumberColumn(format="₺%.4f"),
            "Nakliye": st.column_config.NumberColumn(format="₺%.4f"),
            "Marj%": st.column_config.NumberColumn(format="%.1f%%"),
            "Y1 Satış": st.column_config.NumberColumn(format="₺%.4f"),
            "Y1 Kâr": st.column_config.NumberColumn(format="₺%.4f"),
            "Y2 Satış": st.column_config.NumberColumn(format="₺%.4f"),
            "Y2 Kâr": st.column_config.NumberColumn(format="₺%.4f"),
            "USD Kur": st.column_config.NumberColumn(format="₺%.2f"),
            "EUR Kur": st.column_config.NumberColumn(format="₺%.2f"),
        }
    )

    # CSV Export
    csv_data = display_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button(
        "⬇️ CSV Olarak İndir",
        data=csv_data,
        file_name=f"fiyatopt_gecmis_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
    )

    # Excel / PDF Export
    excel_bytes = _excel_bytes_from_sheets({"Gecmis": display_df})
    pdf_bytes = _pdf_from_dataframe("Gecmis Kayitlar", display_df)

    e_col1, e_col2, e_col3 = st.columns([1, 1, 4])
    with e_col1:
        st.download_button(
            "⬇️ Excel",
            data=excel_bytes,
            file_name=f"fiyatopt_gecmis_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    with e_col2:
        st.download_button(
            "⬇️ PDF",
            data=pdf_bytes,
            file_name=f"fiyatopt_gecmis_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf",
        )

    # Tüm geçmişi temizle
    st.markdown("---")
    st.markdown("#### ⚠️ Geçmişi Temizle")
    if st.checkbox("Tüm geçmişi silmek istediğimi onaylıyorum"):
        if st.button("🗑️ Tüm Geçmişi Sil", type="secondary"):
            conn = get_connection()
            conn.execute("DELETE FROM gecmis")
            conn.commit()
            conn.close()
            st.success("✅ Tüm geçmiş kayıtlar silindi.")
            st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# ANA UYGULAMA
# ─────────────────────────────────────────────────────────────────────────────
def main():
    # Veritabanını başlat
    init_db()

    # TCMB kurlarını çek
    kurlar, kur_tarihi, kur_kaynak = get_tcmb_kurlar()

    # Sidebar
    sayfa = render_sidebar(kurlar, kur_tarihi, kur_kaynak)

    # Aktif sayfayı render et
    try:
        if sayfa == "🧮 Fiyat Hesaplama":
            sayfa_hesaplama(kurlar)
        elif sayfa == "📦 Ürün Yönetimi":
            sayfa_urun_yonetimi()
        elif sayfa == "🚚 Nakliye Yönetimi":
            sayfa_nakliye_yonetimi()
        elif sayfa == "📊 Geçmiş Kayıtlar":
            sayfa_gecmis()
    except Exception as e:
        st.error(f"❌ Sayfa yüklenirken beklenmeyen bir hata oluştu:\n\n```\n{traceback.format_exc()}\n```")

if __name__ == "__main__":
    main()
