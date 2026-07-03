import streamlit as st
import pandas as pd
import numpy as np
from scipy import stats
import google.generativeai as genai
import plotly.express as px
import plotly.graph_objects as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import math
import os
import base64
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Smart Evaluation Analytics UPDL Jakarta",
    page_icon="⚡",
    layout="wide"
)

st.markdown("""
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
    <style>
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 18px;
        font-weight: bold;
    }
    .stTabs [data-baseweb="tab"] { color: #666666; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { color: #005b9f !important; }
    .stTabs [data-baseweb="tab-highlight"] { background-color: #ffc107 !important; }
    [data-testid="stFileUploader"] {
        background: #ffffff;
        border: 2px dashed #0055A4;
        border-radius: 12px;
        padding: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
def get_base64_logo(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            import base64
            return base64.b64encode(f.read()).decode()
    return ""

bin_pln       = get_base64_logo("Logo PLN.png")
bin_danantara = get_base64_logo("logo_danantara.png")
img_pln       = f'<img src="data:image/png;base64,{bin_pln}" style="height:85px;object-fit:contain;">' if bin_pln else ""
img_danantara = f'<img src="data:image/png;base64,{bin_danantara}" style="height:40px;object-fit:contain;background:white;padding:4px;border-radius:6px;">' if bin_danantara else ""

st.markdown(f"""
<div style="display:flex;align-items:center;justify-content:space-between;
    background:linear-gradient(90deg,#003366,#0055A4);padding:10px 30px;
    border-radius:12px;color:white;margin-bottom:25px;box-shadow:0px 4px 10px rgba(0,0,0,0.1);">
    <div style="flex:1;display:flex;align-items:center;gap:15px;">{img_danantara}</div>
    <div style="flex:2;text-align:center;">
        <h1 style="margin:0;font-size:1.6em;color:white !important;font-weight:bold;line-height:1.2;">
            &#9889; Smart Evaluation Analytics
        </h1>
        <p style="margin:0;color:rgba(255,255,255,0.8) !important;font-size:0.85em;">
            Dashboard Analitik Interaktif Evaluasi Pembelajaran &bull; UPDL Jakarta
        </p>
    </div>
    <div style="flex:1;display:flex;align-items:center;justify-content:flex-end;">{img_pln}</div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS (Data Entry)
# ─────────────────────────────────────────────────────────────────────────────
TARGET_COLUMNS = [
    'No', 'Laporan Bulan', 'Kode Unik', 'Kode Pembelajaran', 'Judul Pembelajaran/Kegiatan',
    'Batch', 'PIC KI', 'Tanggal Mulai', 'Tanggal Selesai', 'Cut off Data',
    'Strategi Pelaksanaan', 'Peserta Isi L1', 'Peserta Hadir', '% Pengisian', '% Valid',
    'INS1', 'INS2', 'INS3', 'INS4', 'INS5', 'INS6', 'INS7', 'INS8', 'INS9', 'RATA INST',
    'MAT1', 'MAT2', 'MAT3', 'MAT4', 'MAT5', 'MAT6', 'MAT7', 'RATA MAT',
    'SP1', 'SP2', 'SP3', 'SP4', 'SP5', 'SP6', 'RATA SP',
    'DS1', 'DS2', 'DS3', 'DS4', 'DS5', 'DS6', 'RATA DS',
    'RATA-RATA KESELURUHAN', 'Jumlah Indikator dibawah 4.5', 'Jumlah Indikator diatas 4.5',
    'Status Pembelajaran', 'Jenis Penugasan', 'Jenis Instruktur', 'Nama Instruktur',
    'nama instruktur', 'Jumlah Peserta Lulus L2',
    'Jumlah Peserta Isi L2', '% Pengisian L2', 'Nilai Confidence', 'Nilai Commitment', 'Status L2'
]
INS_COL_NAMES = ['Ins-Eng-1 of 2','Ins-Eng-2 of 2','Ins-Rel-1 of 2','Ins-Rel-2 of 2',
                 'Ins-Sat-1 of 4','Ins-Sat-2 of 4','Ins-Sat-3 of 4','Ins-Sat-4 of 4','Ins-Rat']
MAT_COL_NAMES = ['Mat-Eng-1 of 2','Mat-Eng-2 of 2','Mat-Rel-1 of 2','Mat-Rel-2 of 2',
                 'Mat-Sat-1 0f 2','Mat-Sat-2 of 2','Mat-Rat']
SP_COL_NAMES  = ['Sarpras-Sas-1 of 5','Sarpras-Sas-2 of 5','Sarpras-Sas-3 of 5',
                 'Sarpras-Sas-4 of 5','Sarpras-Sas-5 of 5','Sarpras-Rat']
DS_COL_NAMES  = ['Dig-Sas-1 of 5','Dig-Sas-2 of 5','Dig-Sas-3 of 5',
                 'Dig-Sas-4 of 5','Dig-Sas-5 of 5','Dig Rat']
L2_MERGE_COLS = ['Kode Unik','Jumlah Peserta Lulus L2','Jumlah Peserta Isi L2',
                 'Nilai Confidence','Nilai Commitment']
INSTRUKTUR_SOURCE_COLS = [
    'Nama','Tgl Mulai','Tgl Selesai','Kode Diklat','Judul Diklat','Angkatan',
    'Ins-Eng-1 of 2','Ins-Eng-2 of 2','Ins-Rel-1 of 2','Ins-Rel-2 of 2',
    'Ins-Sat-1 of 4','Ins-Sat-2 of 4','Ins-Sat-3 of 4','Ins-Sat-4 of 4','Ins-Rat',
]
LAP_INSTRUKTUR_COLUMNS = [
    'NO','TANGGAL MULAI','TANGGAL SELESAI','DATA CUTOFF','BULAN LAPORAN',
    'NAMA INSTRUKTUR','KODE','JUDUL PEMBELAJARAN','ANGKATAN',
    'RATA-RATA PER INSTRUKTUR',
    'ENG 1','ENG 2','REL 1','REL 2','SAT 1','SAT 2','SAT 3','SAT 4','RATING',
]
BULAN_MAP = {1:'JANUARI',2:'FEBRUARI',3:'MARET',4:'APRIL',5:'MEI',6:'JUNI',
             7:'JULI',8:'AGUSTUS',9:'SEPTEMBER',10:'OKTOBER',11:'NOVEMBER',12:'DESEMBER'}
BULAN_MAP_ID = {1:'Januari',2:'Februari',3:'Maret',4:'April',5:'Mei',6:'Juni',
                7:'Juli',8:'Agustus',9:'September',10:'Oktober',11:'November',12:'Desember'}

# ─────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS (Data Entry)
# ─────────────────────────────────────────────────────────────────────────────

def safe_divide(numerator, denominator):
    return np.where((denominator == 0) | (pd.isna(denominator)), np.nan, numerator / denominator)

def detect_and_show_column_mismatch(df_raw, expected_cols, file_name, section_label):
    missing = [c for c in expected_cols if c not in df_raw.columns]
    if missing:
        st.warning(f"⚠️ **{file_name}** — Kolom {section_label} tidak ditemukan: `{'`, `'.join(missing)}`")
    return missing

def compute_bulan_laporan(tgl_selesai):
    def _calc(ts):
        if pd.isna(ts): return ""
        bulan_next = ts.month % 12 + 1 if ts.day > 18 else ts.month
        return BULAN_MAP.get(bulan_next, "")
    return tgl_selesai.apply(_calc)

def build_instruktur_df(df_raw):
    df = pd.DataFrame()
    df['TANGGAL MULAI']      = pd.to_datetime(df_raw.get('Tgl Mulai'),   errors='coerce')
    df['TANGGAL SELESAI']    = pd.to_datetime(df_raw.get('Tgl Selesai'), errors='coerce')
    df['DATA CUTOFF']        = df['TANGGAL SELESAI'] + pd.Timedelta(days=7)
    df['BULAN LAPORAN']      = compute_bulan_laporan(df['TANGGAL SELESAI'])
    df['NAMA INSTRUKTUR']    = df_raw.get('Nama')
    df['KODE']               = df_raw.get('Kode Diklat')
    df['JUDUL PEMBELAJARAN'] = df_raw.get('Judul Diklat')
    angkatan_raw = df_raw.get('Angkatan')
    df['ANGKATAN'] = (angkatan_raw.astype(str).str.replace(r'\.0$','',regex=True).str.strip().replace('nan','')
                      if angkatan_raw is not None else '')
    for src, dst in [('Ins-Eng-1 of 2','ENG 1'),('Ins-Eng-2 of 2','ENG 2'),
                     ('Ins-Rel-1 of 2','REL 1'),('Ins-Rel-2 of 2','REL 2'),
                     ('Ins-Sat-1 of 4','SAT 1'),('Ins-Sat-2 of 4','SAT 2'),
                     ('Ins-Sat-3 of 4','SAT 3'),('Ins-Sat-4 of 4','SAT 4'),
                     ('Ins-Rat','RATING')]:
        df[dst] = pd.to_numeric(df_raw.get(src), errors='coerce')
    df['RATA-RATA PER INSTRUKTUR'] = df[['ENG 1','ENG 2','REL 1','REL 2','SAT 1','SAT 2','SAT 3','SAT 4']].mean(axis=1)
    return df[LAP_INSTRUKTUR_COLUMNS[1:]]

def clean_row_for_sheets(row):
    clean_row = []
    for val in row:
        if isinstance(val, pd.Timestamp):
            clean_row.append(val.strftime('%Y-%m-%d')); continue
        try:
            if pd.isna(val): clean_row.append(""); continue
        except (TypeError, ValueError): pass
        try:
            fv = float(val)
            if math.isnan(fv) or math.isinf(fv): clean_row.append("")
            elif fv == int(fv): clean_row.append(int(fv))
            else: clean_row.append(round(fv, 4))
        except (ValueError, TypeError):
            clean_row.append(str(val).strip() if val != "" else "")
    return clean_row

def get_sheet_max_no(sheet):
    col_a = sheet.col_values(1)
    max_no = 0
    for val in col_a:
        try:
            num = int(str(val).strip())
            if num > max_no: max_no = num
        except ValueError: continue
    return max_no

def init_gsheets_connection():
    scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    return gspread.authorize(creds)

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE defaults
# ─────────────────────────────────────────────────────────────────────────────
for key, default in [
    ("setting_sheet",         "Monitoring Evaluasi Pembelajaran"),
    ("setting_worksheet",     "L1 Tertutup"),
    ("setting_ws_instruktur", "Lap Instruktur"),
    ("setting_cutoff",        14),
    ("setting_threshold",     0.8),
    ("riwayat_upload",        []),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ─────────────────────────────────────────────────────────────────────────────
# GEMINI
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_resource
def load_gemini_model():
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    return genai.GenerativeModel('gemini-1.5-flash')

model = load_gemini_model()

# ─────────────────────────────────────────────────────────────────────────────
# LOAD DATA DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────
sheet_id = '1IDAmFwTbBQDZcKM3eiiEDcA3KwM9WKqW4zCrk__6-PU'
sheet_name = 'L1%20Tertutup' # %20 adalah representasi karakter spasi pada URL

# Menggunakan endpoint gviz agar bisa secara spesifik memilih nama tab/worksheet
url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}'

col_button, _ = st.columns([0.5, 4])
with col_button:
    if st.button("🔄 Sinkron Data", use_container_width=True):
        st.cache_data.clear()
        st.toast("Menarik data terbaru dari Google Sheets...")

# ─────────────────────────────────────────────────────────────────────────────
# TABS UTAMA — urutan: Data Entry | Analytics | Dashboard | AI | Pengaturan
# ─────────────────────────────────────────────────────────────────────────────
tab_entry, tab_statistik, tab_dashboard, tab_ai, tab_setting = st.tabs([
    "📤 DATA ENTRY",
    "📈 ANALYTICS",
    "📊 DASHBOARD",
    "🤖 AI ASSISTANT",
    "⚙️ PENGATURAN",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB ANALYTICS & DASHBOARD — perlu data dari Google Sheets
# ══════════════════════════════════════════════════════════════════════════════
try:
    @st.cache_data(ttl=300)
    def load_csv(url):
        return pd.read_csv(url)

    df = load_csv(url)

    # ── Filter Global ──────────────────────────────────────────────────────────
    with tab_statistik:
        st.markdown("### 🎛️ Filter Data")
    with tab_dashboard:
        st.markdown("### 🎛️ Filter Data")

    # Tampilkan filter hanya sekali di atas kedua tab — letakkan di luar tab agar shared
    # Streamlit tidak bisa share widget antar tab, jadi
