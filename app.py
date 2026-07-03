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
    # Streamlit tidak bisa share widget antar tab, jadi kita buat di masing-masing tab
    def build_filters(suffix):
        opsi_bulan    = list(df['Laporan Bulan'].dropna().unique())
        opsi_strategi = list(df['Strategi Pelaksanaan'].dropna().unique())
        opsi_valid    = ["Semua Status"] + list(df['% Valid'].dropna().unique())
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            filter_bulan = st.multiselect("Laporan Bulanan", options=opsi_bulan,
                                          default=opsi_bulan, key=f"bulan_{suffix}")
        with col_f2:
            filter_strategi = st.multiselect("Strategi Pelaksanaan", options=opsi_strategi,
                                             default=opsi_strategi, key=f"strategi_{suffix}")
        with col_f3:
            filter_valid = st.selectbox("Validitas", opsi_valid, key=f"valid_{suffix}")

        df_f = df.copy()
        df_f = df_f[df_f['Laporan Bulan'].isin(filter_bulan)]       if filter_bulan    else pd.DataFrame(columns=df.columns)
        df_f = df_f[df_f['Strategi Pelaksanaan'].isin(filter_strategi)] if filter_strategi else pd.DataFrame(columns=df.columns)
        if filter_valid != "Semua Status":
            df_f = df_f[df_f['% Valid'] == filter_valid]

        kolom_mentah = ['INS1','INS2','INS3','INS4','INS5','INS6','INS7','INS8',
                        'MAT1','MAT2','MAT3','MAT4','MAT5','MAT6','RATA DS','RATA SP','RATA-RATA KESELURUHAN']
        for col in kolom_mentah:
            if col in df_f.columns:
                df_f[col] = pd.to_numeric(df_f[col], errors='coerce')

        if not df_f.empty and 'INS1' in df_f.columns:
            df_f['Engagement Instruktur']      = df_f[['INS1','INS2']].mean(axis=1)
            df_f['Relevance Instruktur']       = df_f[['INS3','INS4']].mean(axis=1)
            df_f['Satisfaction Instruktur']    = df_f[['INS5','INS6','INS7','INS8']].mean(axis=1)
            df_f['Engagement Materi']          = df_f[['MAT1','MAT2']].mean(axis=1)
            df_f['Relevance Materi']           = df_f[['MAT3','MAT4']].mean(axis=1)
            df_f['Satisfaction Materi']        = df_f[['MAT5','MAT6']].mean(axis=1)
            df_f['Satisfaction Sarana Digital']  = df_f['RATA DS']
            df_f['Satisfaction Sarana In Class'] = df_f['RATA SP']

        st.success(f"Terdapat **{len(df_f)}** baris data yang sesuai dengan filter.")
        return df_f

    # ══════════════════════════════════════════════════════════════════
    # TAB 1: ANALYTICS
    # ══════════════════════════════════════════════════════════════════
    with tab_statistik:
        df_filtered = build_filters("analytics")
        kolom_tersedia = df_filtered.columns.tolist()
        st.markdown("---")

        if not df_filtered.empty:
            st.subheader("📋 Raw Data")
            st.dataframe(df_filtered, use_container_width=True)

            st.markdown("### 🔍 Analisis Korelasi")
            col1, col2 = st.columns(2)
            with col1:
                var_x = st.selectbox("Variabel Independen (X):", kolom_tersedia, index=0, key="x_ana")
            with col2:
                var_y = st.selectbox("Variabel Dependen (Y):", kolom_tersedia,
                                     index=min(1, len(kolom_tersedia)-1), key="y_ana")
            st.markdown("---")

            if pd.api.types.is_numeric_dtype(df_filtered[var_x]) and pd.api.types.is_numeric_dtype(df_filtered[var_y]):
                hapus_outlier  = st.checkbox("🧹 Buang Outlier (IQR)", key="out_ana")
                uji_normalitas = st.checkbox("⚖️ Uji Normalitas (Shapiro-Wilk)", key="norm_ana")
                df_clean = df_filtered.copy()

                if hapus_outlier:
                    for v in [var_x, var_y]:
                        Q1, Q3 = df_clean[v].quantile(0.25), df_clean[v].quantile(0.75)
                        IQR = Q3 - Q1
                        df_clean = df_clean[(df_clean[v] >= Q1-1.5*IQR) & (df_clean[v] <= Q3+1.5*IQR)]
                    st.info(f"Tersisa **{len(df_clean)}** baris setelah outlier dihapus.")

                if uji_normalitas and len(df_clean) >= 3:
                    stat_x, p_x = stats.shapiro(df_clean[var_x].dropna())
                    stat_y, p_y = stats.shapiro(df_clean[var_y].dropna())
                    col_n1, col_n2 = st.columns(2)
                    with col_n1:
                        (st.success if p_x > 0.05 else st.error)(f"{'✅' if p_x>0.05 else '❌'} {var_x}: {'Normal' if p_x>0.05 else 'Tidak Normal'} (p={p_x:.3f})")
                    with col_n2:
                        (st.success if p_y > 0.05 else st.error)(f"{'✅' if p_y>0.05 else '❌'} {var_y}: {'Normal' if p_y>0.05 else 'Tidak Normal'} (p={p_y:.3f})")

                if len(df_clean) > 1:
                    st.markdown("---")
                    korelasi = df_clean[var_x].corr(df_clean[var_y])
                    col3, col4 = st.columns([1, 2])
                    with col3: st.metric("Koefisien Korelasi (r)", round(korelasi, 3))
                    with col4:
                        st.write(f"**Sebaran: {var_x} vs {var_y}**")
                        st.scatter_chart(data=df_clean, x=var_x, y=var_y)
            else:
                st.error("⚠️ Kolom yang dipilih bukan format angka.")

            # IPA
            st.markdown("---")
            st.markdown("### 🎯 Importance-Performance Analysis (IPA)")
            try:
                # Copy data agar tidak merusak dataframe asli
                df_ipa = df_filtered.dropna(subset=['RATA-RATA KESELURUHAN']).copy()
                
                # --- 1. SYARAT MINIMAL UKURAN SAMPEL (RESPONSE RATE 40%) ---
                if '% Pengisian' in df_ipa.columns:
                    # FIX ERROR STRING: Hapus tanda '%' dan paksa ubah teks menjadi angka
                    df_ipa['Pengisian_Clean'] = pd.to_numeric(df_ipa['% Pengisian'].astype(str).str.replace('%', '', regex=False), errors='coerce')
                    rata_pengisian = df_ipa['Pengisian_Clean'].mean()
                    
                    # Jika data dari GSheets terbaca puluhan (misal 80, bukan 0.8), bagi dengan 100
                    if pd.notna(rata_pengisian) and rata_pengisian > 1:
                        rata_pengisian = rata_pengisian / 100
                        
                    # Tampilkan Peringatan Jika Response Rate < 40%
                    if pd.notna(rata_pengisian) and rata_pengisian < 0.40:
                        st.warning(f"⚠️ **Peringatan Sampel:** Rata-rata tingkat pengisian (Response Rate) pada data ini hanya **{rata_pengisian*100:.1f}%** (di bawah standar validitas 40%). Titik kuadran mungkin dipengaruhi anomali karena sampel terlalu sedikit.")
                
                # --- 2. PILIHAN LEVEL KEDALAMAN (TOGGLE MAKRO/MIKRO) ---
                level_ipa = st.radio(
                    "🔍 Pilih Kedalaman Analisis Akar Masalah (Drill-down):", 
                    ["📊 Makro (Kategori Utama)", "🔎 Mikro (Sub-Indikator Detail)"], 
                    horizontal=True
                )

                # Syarat minimal baris untuk bisa menghitung korelasi adalah 3 baris
                if len(df_ipa) > 2:
                    
                    if level_ipa == "📊 Makro (Kategori Utama)":
                        # Kategori Level Makro
                        kategori_list = [
                            'Engagement Instruktur', 'Relevance Instruktur', 'Satisfaction Instruktur',
                            'Engagement Materi', 'Relevance Materi', 'Satisfaction Materi',
                            'Satisfaction Sarana Digital', 'Satisfaction Sarana In Class'
                        ]
                        nama_tampil = kategori_list
                        
                    else:
                        # Kategori Level Mikro (Kolom Indikator Mentah)
                        kategori_list = [
                            'INS1','INS2','INS3','INS4','INS5','INS6','INS7','INS8',
                            'MAT1','MAT2','MAT3','MAT4','MAT5','MAT6',
                            'SP1','SP2','SP3','SP4','SP5',
                            'DS1','DS2','DS3','DS4','DS5'
                        ]
                        
                        # --- KAMUS PERTANYAAN (Sesuaikan teks ini dengan kuesioner asli PLN Anda) ---
                        kamus_nama = {
                            'INS1': 'INS1: Partisipasi Aktif',    'INS2': 'INS2: Peserta Jadi Terlibat',
                            'INS3': 'INS3: Konteks Pekerjaan',    'INS4': 'INS4: Contoh Relevan',
                            'INS5': 'INS5: Metode Mengajar',      'INS6': 'INS6: Studi Kasus',
                            'INS7': 'INS7: Manajemen Waktu',      'INS8': 'INS8: Penampilan Profesional',
                            'MAT1': 'MAT1: Diskusi Aktif',        'MAT2': 'MAT2: Motivasi Belajar',
                            'MAT3': 'MAT3: Materi Aplikatif',     'MAT4': 'MAT4: Meningkatkan Kompetensi',
                            'MAT5': 'MAT5: Materi Menarik',       'MAT6': 'MAT6: Bisa direkomendasikan',
                            'SP1':  'SP1: Kenyamanan Kelas',      'SP2':  'SP2: Fasilitas Fisik',
                            'SP3':  'SP3: Peralatan Belajar',     'SP4':  'SP4: Ruang Praktik', 
                            'SP5':  'SP5: Sarana Pendukung',
                            'DS1':  'DS1: Platform Online',       'DS2':  'DS2: Modul Digital',
                            'DS3':  'DS3: Koneksi Internet',      'DS4':  'DS4: Media Interaktif', 
                            'DS5':  'DS5: Fasilitas Digital'
                        }
                        # Translate kode kolom menjadi nama manusiawi
                        nama_tampil = [kamus_nama.get(k, k) for k in kategori_list]

                    kinerja, kepentingan = [], []
                    
                    # --- 3. KALKULASI STATISTIK (KINERJA & KORELASI) ---
                    for kat in kategori_list:
                        if kat in df_ipa.columns:
                            # Lapis keamanan ekstra: paksa ubah teks menjadi angka
                            df_ipa[kat] = pd.to_numeric(df_ipa[kat], errors='coerce')
                            
                            # Hitung Kinerja (Mean)
                            kinerja.append(df_ipa[kat].mean())
                            
                            # Hitung Kepentingan (Korelasi Pearson)
                            corr_val = df_ipa[kat].corr(pd.to_numeric(df_ipa['RATA-RATA KESELURUHAN'], errors='coerce'))
                            kepentingan.append(corr_val)
                        else:
                            kinerja.append(None); kepentingan.append(None)

                    # Buat DataFrame untuk Plotting
                    df_plot_ipa = pd.DataFrame({'Kategori': nama_tampil, 'Kinerja': kinerja, 'Kepentingan': kepentingan})
                    
                    # --- 4. MITIGASI ERROR NaN (Zero Variance) ---
                    mean_kepentingan = df_plot_ipa['Kepentingan'].mean()
                    if pd.isna(mean_kepentingan): 
                        mean_kepentingan = 0.5 # Nilai default jika semua perhitungan korelasi gagal
                        
                    df_plot_ipa['Kepentingan'] = df_plot_ipa['Kepentingan'].fillna(mean_kepentingan)
                    df_plot_ipa = df_plot_ipa.dropna(subset=['Kinerja']) # Hapus baris yang tidak ada data kinerjanya

                    # --- 5. PEMBUATAN GRAFIK PLOTLY ---
                    if not df_plot_ipa.empty:
                        # Fiksasi Sumbu X di 4.5 (Standar TMP PLN)
                        x_cross = 4.5  
                        y_cross = df_plot_ipa['Kepentingan'].mean() 
                        
                        # Plot Scatter
                        fig_ipa = px.scatter(df_plot_ipa, x='Kinerja', y='Kepentingan', text='Kategori')
                        
                        # Atur Ukuran Teks agar tidak menumpuk saat mode Mikro
                        ukuran_teks = 10 if level_ipa == "🔎 Mikro (Sub-Indikator Detail)" else 13
                        
                        fig_ipa.update_traces(
                            textposition='top center', 
                            textfont_size=ukuran_teks,
                            marker=dict(size=12, color='#005b9f', line=dict(width=1,color='DarkSlateGrey'))
                        )
                        
                        # Penambahan Garis Batas Kuadran
                        fig_ipa.add_hline(y=y_cross, line_dash="dash", line_color="#FFC000")
                        fig_ipa.add_vline(x=x_cross, line_dash="dash", line_color="#FFC000", 
                                          annotation_text="Standar TMP (4.5)", annotation_position="top left")
                        
                        # Label 4 Kuadran
                        for ax, ay, txt, col, algn in [
                            (0.01, 0.99, "<b>KUADRAN 1</b><br>🚨 Prioritas Utama", "#d32f2f", "left"),
                            (0.99, 0.99, "<b>KUADRAN 2</b><br>🌟 Pertahankan", "#2e7d32", "right"),
                            (0.01, 0.01, "<b>KUADRAN 3</b><br>📉 Prioritas Sekunder", "#757575", "left"),
                            (0.99, 0.01, "<b>KUADRAN 4</b><br>⚠️ Berlebihan", "#f57c00", "right"),
                        ]:
                            fig_ipa.add_annotation(xref="paper", yref="paper", x=ax, y=ay, text=txt,
                                                   showarrow=False, font=dict(color=col, size=13), align=algn)
                        
                        # Fiksasi batas skala grafik agar tampilan selalu rapi
                        min_x = min(4.0, df_plot_ipa['Kinerja'].min() - 0.1) if not df_plot_ipa['Kinerja'].empty else 4.0
                        min_y = min(-0.1, df_plot_ipa['Kepentingan'].min() - 0.1) if not df_plot_ipa['Kepentingan'].empty else -0.1
                        max_y = max(1.1, df_plot_ipa['Kepentingan'].max() + 0.1) if not df_plot_ipa['Kepentingan'].empty else 1.1
                        
                        fig_ipa.update_layout(
                            height=600 if level_ipa == "📊 Makro (Kategori Utama)" else 700, 
                            margin=dict(t=40,b=40,l=40,r=40),
                            xaxis_range=[min_x, 5.1], yaxis_range=[min_y, max_y],
                            xaxis_title="Kinerja (Rata-rata Skor Kepuasan)", 
                            yaxis_title="Kepentingan (Korelasi terhadap Total Skor)"
                        )
                        
                        st.plotly_chart(fig_ipa, use_container_width=True)

                        # --- 6. AUTO-DIAGNOSIS (KESIMPULAN OTOMATIS) DENGAN UI PREMIUM PLN ---
                        # Cari item yang Kinerjanya < 4.5 DAN Kepentingannya > Rata-rata
                        df_q1 = df_plot_ipa[(df_plot_ipa['Kinerja'] < x_cross) & (df_plot_ipa['Kepentingan'] > y_cross)]
                        q1_items = df_q1['Kategori'].tolist()
                        
                        st.markdown("<h4 style='color: #003366; margin-top: 35px; font-weight: bold; letter-spacing: 0.5px;'>💡 Executive Diagnosis System</h4>", unsafe_allow_html=True)
                        
                        if q1_items:
                            # Membuat baris tabel HTML secara dinamis untuk setiap indikator yang bermasalah
                            rows_html = ""
                            for _, row in df_q1.iterrows():
                                rows_html += f"""
                                <tr style="border-bottom: 1px solid #e0e0e0;">
                                    <td style="padding: 10px; color: #333; font-size: 14px;">{row['Kategori']}</td>
                                    <td style="padding: 10px; text-align: center;"><span style="background-color: #ffeeee; color: #d32f2f; padding: 3px 10px; border-radius: 12px; font-weight: bold; font-size: 13px;">{row['Kinerja']:.2f}</span></td>
                                    <td style="padding: 10px; text-align: center; color: #666; font-size: 14px;">{row['Kepentingan']:.2f}</td>
                                </tr>
                                """
                            
                            # Teks Rekomendasi dinamis berdasarkan pilihan Makro/Mikro
                            if level_ipa == "📊 Makro (Kategori Utama)":
                                rujukan_tindakan = "Direkomendasikan untuk beralih ke <b>Mode Mikro (Sub-Indikator Detail)</b> pada opsi di atas untuk mengisolasi butir pertanyaan spesifik yang memicu penurunan nilai."
                            else:
                                rujukan_tindakan = "Sistem merekomendasikan peninjauan ulang pada aspek operasional terkait butir di atas. Intervensi taktis pada indikator ini akan menghasilkan efisiensi anggaran terbaik karena dampaknya yang masif terhadap kepuasan total."

                            # RENDERING UI KARTU PERINGATAN KRITIS (Tema Corporate Putih-Merah dengan Aksen Biru PLN)
                            ui_html = f"""
                            <div style="background-color: #ffffff; border-radius: 12px; border: 1px solid #e0e0e0; border-left: 8px solid #d32f2f; box-shadow: 0 4px 15px rgba(0,0,0,0.05); padding: 25px; margin-bottom: 25px;">
                                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 15px;">
                                    <span style="font-size: 24px;">🚨</span>
                                    <h5 style="margin: 0; color: #d32f2f; font-size: 18px; font-weight: bold;">Attention Required: Indikator Berada di Kuadran 1 (Prioritas Utama)</h5>
                                </div>
                                <p style="color: #555; font-size: 14.5px; margin: 0 0 20px 0; line-height: 1.5;">
                                    Berikut adalah daftar elemen pembelajaran yang memiliki <b>tingkat pengaruh sangat tinggi</b> terhadap kepuasan total peserta, namun realisasi kinerjanya masih <b>di bawah standar minimal kelulusan (4.50)</b>:
                                </p>
                                
                                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                                    <thead>
                                        <tr style="background-color: #f8f9fa; border-bottom: 2px solid #0055A4; text-align: left;">
                                            <th style="padding: 10px; color: #003366; font-size: 14px; font-weight: bold;">Elemen / Indikator Evaluasi</th>
                                            <th style="padding: 10px; color: #003366; font-size: 14px; font-weight: bold; text-align: center;">Skor Realisasi (Kinerja)</th>
                                            <th style="padding: 10px; color: #003366; font-size: 14px; font-weight: bold; text-align: center;">Dampak Strategis (Korelasi)</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {rows_html}
                                    </tbody>
                                </table>
                                
                                <div style="background-color: #f0f6ff; border-left: 4px solid #0055A4; padding: 15px; border-radius: 4px;">
                                    <h6 style="margin: 0 0 5px 0; color: #003366; font-size: 14px; font-weight: bold;">🎯 Rekomendasi Preskriptif:</h6>
                                    <p style="margin: 0; color: #333; font-size: 13.5px; line-height: 1.5;">{rujukan_tindakan}</p>
                                </div>
                            </div>
                            """
                            st.markdown(ui_html, unsafe_allow_html=True)
                            
                        else:  
                            # RENDERING UI KARTU PRIMA/AMAN (Gradien Deep Blue PLN & Bright Blue dengan Aksen Gold #ffc107)
                            success_html = """
                            <div style="background: linear-gradient(135deg, #003366, #0055A4); border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.12); padding: 30px; margin-bottom: 25px; border-left: 8px solid #ffc107; display: flex; align-items: center; gap: 25px;">
                                <div style="font-size: 40px; background: rgba(255,255,255,0.12); padding: 12px 18px; border-radius: 50%; color: #ffc107;">🏆</div>
                                <div>
                                    <h5 style="margin: 0 0 6px 0; color: #ffc107; font-size: 19px; font-weight: bold; letter-spacing: 0.3px;">Status Operasional: Prima & Kondusif</h5>
                                    <p style="margin: 0; color: #ffffff; font-size: 14.5px; line-height: 1.6; opacity: 0.95;">
                                        Seluruh indikator evaluasi pembelajaran berhasil dipertahankan di luar Kuadran 1. Tidak ditemukan adanya defisit kepuasan pada elemen-elemen kritikal. Pertahankan konsistensi mutu pelayanan ini di UPDL Jakarta.
                                    </p>
                                </div>
                            </div>
                            """
                            st.markdown(success_html, unsafe_allow_html=True)

                        
                    
                    # ==============================================================================
                    # 📜 FITUR TAMBAHAN: HISTORI PERGERAKAN INDIKATOR (EVALUASI TINDAK LANJUT)
                    # ==============================================================================
                    st.markdown("---")
                    st.markdown("### 📜 Histori & Evaluasi Dampak Tindak Lanjut (Tren Antar Bulan)")
                    st.write("Pilih salah satu indikator di bawah ini untuk melihat 'perjalanan' posisinya dari bulan ke bulan. Fitur ini berfungsi mengevaluasi apakah tindak lanjut yang telah dilakukan efektif menaikkan kinerja.")
                    
                    # Ambil daftar bulan yang tersedia untuk mengurutkan histori secara kronologis
                    URUTAN_BULAN = ['Januari','Februari','Maret','April','Mei','Juni','Juli','Agustus','September','Oktober','November','Desember']
                    
                    # Dropdown pilihan indikator yang ingin dilacak historinya
                    list_pelacakan = kategori_list
                    indikator_dipilih = st.selectbox("🎯 Pilih Indikator yang Ingin Dilacak Historinya:", list_pelacakan, key="sb_history_ipa")
                    
                    # Ambil kembali key asli kolom (jika mode mikro menggunakan kamus, kita cari key-nya)
                    col_key_asli = indikator_dipilih
                    if level_ipa == "🔎 Mikro (Sub-Indikator Detail)":
                        # Cari key berdasarkan value di kamus_nama
                        for k, v in kamus_nama.items():
                            if v == indikator_dipilih:
                                col_key_asli = k
                                break
                    
                    # Kumpulkan data per bulan untuk indikator terpilih
                    histori_bulan, histori_kinerja, histori_kepentingan = [], [], []
                    
                    # Gunakan data awal sebelum filter bulan agar historinya lengkap setahun
                    df_global_ctx = df.copy() 
                    
                    # Bersihkan data global dari % dan pastikan numerik
                    if '% Pengisian' in df_global_ctx.columns:
                        df_global_ctx['Pengisian_Clean'] = pd.to_numeric(df_global_ctx['% Pengisian'].astype(str).str.replace('%', '', regex=False), errors='coerce')
                    for k_item in kategori_list:
                        k_key = k_item
                        if level_ipa == "🔎 Mikro (Sub-Indikator Detail)":
                            for kk, vv in kamus_nama.items():
                                if vv == k_item: k_key = kk; break
                        if k_key in df_global_ctx.columns:
                            df_global_ctx[k_key] = pd.to_numeric(df_global_ctx[k_key], errors='coerce')
                    df_global_ctx['RATA-RATA KESELURUHAN'] = pd.to_numeric(df_global_ctx['RATA-RATA KESELURUHAN'], errors='coerce')

                    # Filter berdasarkan urutan kronologis bulan yang ada di dataset
                    bulan_tersedia_di_data = [b for b in URUTAN_BULAN if b in df_global_ctx['Laporan Bulan'].unique()]
                    
                    for bln in bulan_tersedia_di_data:
                        df_bln = df_global_ctx[df_global_ctx['Laporan Bulan'] == bln]
                        if len(df_bln) > 1 and col_key_asli in df_bln.columns:
                            mean_kinerja = df_bln[col_key_asli].mean()
                            corr_kepentingan = df_bln[col_key_asli].corr(pd.to_numeric(df_bln['RATA-RATA KESELURUHAN'], errors='coerce'))
                            
                            if pd.notna(mean_kinerja):
                                histori_bulan.append(bln)
                                histori_kinerja.append(mean_kinerja)
                                histori_kepentingan.append(corr_kepentingan if pd.notna(corr_kepentingan) else 0.5)
                    
                    if len(histori_bulan) >= 2:
                        df_histori_plot = pd.DataFrame({
                            'Bulan': histori_bulan,
                            'Kinerja': histori_kinerja,
                            'Kepentingan': histori_kepentingan
                        })
                        
                        # Membuat Grafik Garis Perjalanan (Trajectory Plot)
                        fig_track = px.line(df_histori_plot, x='Kinerja', y='Kepentingan', text='Bulan', markers=True,
                                            title=f"Rekam Jejak Pergeseran Posisi Kuadran: {indikator_dipilih}")
                        
                        fig_track.update_traces(textposition='top center', line=dict(width=3, color='#ffc107'),
                                                marker=dict(size=10, color='#005b9f'))
                        
                        # Tambahkan crosshair standar baku 4.5
                        fig_track.add_vline(x=4.5, line_dash="dash", line_color="#FFC000")
                        fig_track.add_hline(y=df_histori_plot['Kepentingan'].mean(), line_dash="dash", line_color="#FFC000")
                        
                        fig_track.update_layout(
                            height=450, xaxis_range=[3.8, 5.1],
                            xaxis_title="Kinerja (Skor Kepuasan)", yaxis_title="Kepentingan (Korelasi)"
                        )
                        st.plotly_chart(fig_track, use_container_width=True)
                        
                        # --- TABEL MONITORING EKSEKUSI TINDAK LANJUT ---
                        st.markdown("#### 📝 Log Evaluasi & Efektivitas Tindak Lanjut")
                        
                        # Generate tabel analisa otomatis sebelum vs sesudah
                        b_awal, b_akhir = histori_bulan[0], histori_bulan[-1]
                        k_awal, k_akhir = histori_kinerja[0], histori_kinerja[-1]
                        selisih = k_akhir - k_awal
                        
                        status_efektivitas = "🟢 BERHASIL (Skor Naik)" if selisih > 0 else "🔴 BELUM EFEKTIF (Skor Stagnan/Turun)"
                        if abs(selisih) < 0.05: status_efektivitas = "🟡 BERTAHAN (Perubahan Minimal)"
                        
                        col_t1, col_t2, col_t3 = st.columns(3)
                        col_t1.metric(f"Skor Awal ({b_awal})", f"{k_awal:.2f}")
                        col_t2.metric(f"Skor Akhir ({b_akhir})", f"{k_akhir:.2f}", delta=f"{selisih:+.2f}")
                        col_t3.metric("Kesimpulan Dampak", "Efektif" if selisih > 0 else "Evaluasi Ulang", delta=status_efektivitas, delta_color="normal" if selisih > 0 else "inverse")
                        
                        # Menampilkan contoh format pelaporan formal untuk manajemen
                        st.caption("**Rekomendasi Format Dokumen Tindak Lanjut (Form Evaluasi Mutu):**")
                        df_log_manual = pd.DataFrame({
                            'Periode': [f"{b_awal} s.d {b_akhir}"],
                            'Indikator Masalah': [indikator_dipilih],
                            'Akar Masalah (Kondisi Awal)': [f"Berada di Kuadran 1 pada bulan {b_awal} dengan skor {k_awal:.2f}"],
                            'Tindakan Korektif yang Telah Dilaksanakan': ["(Tulis tindakan nyata, misal: Refreshment Instruktur / Upgrade Bandwidth Wifi)"],
                            'Hasil Check Akhir': [f"Skor naik menjadi {k_akhir:.2f} ({status_efektivitas})"]
                        })
                        st.dataframe(df_log_manual, use_container_width=True, hide_index=True)
                    else:
                        st.info("ℹ️ Data histori bulanan belum mencukupi (minimal dibutuhkan data dari 2 bulan berbeda) untuk menggambar garis trajektori pergeseran tindakan.")
                        
                else:
                    st.warning("⚠️ Data terlalu sedikit (kurang dari 3 baris yang valid) untuk memproses Analisis Kuadran (IPA).")
            
            except Exception as e:
                st.error(f"Gagal memuat visualisasi IPA: {e}")

            # Analisis Komparatif
            st.markdown("---")
            st.markdown("### ⚖️ Analisis Komparatif")
            opsi_skor_final = [c for c in ['RATA-RATA KESELURUHAN','Engagement Instruktur','INS1','INS2',
                'Relevance Instruktur','INS3','INS4','Satisfaction Instruktur','INS5','INS6','INS7','INS8',
                'Engagement Materi','MAT1','MAT2','Relevance Materi','MAT3','MAT4',
                'Satisfaction Materi','MAT5','MAT6','Satisfaction Sarana Digital','RATA DS',
                'Satisfaction Sarana In Class','RATA SP'] if c in df_filtered.columns]
            col_c1, col_c2 = st.columns(2)
            with col_c1: var_grup = st.selectbox("Kategori Pembanding (X):", ['Strategi Pelaksanaan','Laporan Bulan'], key="grup_ana")
            with col_c2: var_skor = st.selectbox("Skor yang Dinilai (Y):", opsi_skor_final, key="skor_ana")

            df_comp = df_filtered.dropna(subset=[var_grup, var_skor])
            if len(df_comp) > 0:
                grup_unik = df_comp[var_grup].unique()
                data_grup = [df_comp[df_comp[var_grup]==g][var_skor] for g in grup_unik]
                fig_box = px.box(df_comp, x=var_grup, y=var_skor, color=var_grup, points="all",
                                 title=f"Distribusi {var_skor} berdasarkan {var_grup}")
                fig_box.update_layout(height=400, showlegend=False, xaxis_title="", yaxis_title="Skor")
                if len(grup_unik) < 2:
                    st.warning("Hanya 1 kelompok — tidak bisa uji komparasi.")
                    st.plotly_chart(fig_box, use_container_width=True)
                else:
                    if len(grup_unik) == 2:
                        stat_val, p_value = stats.ttest_ind(data_grup[0], data_grup[1], nan_policy='omit')
                        jenis_uji = "Independent T-Test"
                    else:
                        stat_val, p_value = stats.f_oneway(*data_grup)
                        jenis_uji = "One-Way ANOVA"
                    st.plotly_chart(fig_box, use_container_width=True)
                    st.write(f"**Hasil Uji ({jenis_uji}):** P-Value = {p_value:.4f}")
                    if p_value < 0.05:
                        st.success(f"Terdapat **PERBEDAAN SIGNIFIKAN** pada {var_skor} antar kelompok.")
                    else:
                        st.info(f"**TIDAK ADA PERBEDAAN SIGNIFIKAN** pada {var_skor} antar kelompok.")
        else:
            st.warning("⚠️ Tidak ada data. Sesuaikan filter.")

except Exception as e:
    with tab_statistik:
        st.error(f"Gagal memuat data: {e}")
    with tab_dashboard:
        st.error(f"Gagal memuat data: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3: AI ASSISTANT
# ══════════════════════════════════════════════════════════════════════════════
with tab_ai:
    st.subheader("🤖 Tanya Asisten EVALYTICS")
    st.write("Gunakan AI untuk menganalisis tren atau meminta saran perbaikan berdasarkan data yang sedang difilter.")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for chat in st.session_state.chat_history:
        with st.chat_message(chat["role"]):
            st.markdown(chat["content"])

    user_question = st.chat_input("Tanya sesuatu tentang data evaluasi Anda...")
    if user_question:
        st.session_state.chat_history.append({"role": "user", "content": user_question})
        with st.chat_message("user"):
            st.markdown(user_question)
        with st.chat_message("assistant"):
            with st.spinner("Gemini sedang berpikir..."):
                try:
                    df_ctx = load_csv(url)
                    context = f"Data evaluasi UPDL Jakarta. Total: {len(df_ctx)} baris. Ringkasan: {df_ctx.describe().to_string()}"
                    full_prompt = f"Konteks:\n{context}\n\nPertanyaan: {user_question}\n\nJawab ringkas, profesional, Bahasa Indonesia."
                    response = model.generate_content(full_prompt)
                    st.markdown(response.text)
                    st.session_state.chat_history.append({"role": "assistant", "content": response.text})
                except Exception as ai_err:
                    st.error(f"Gagal AI: {ai_err}")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4: DATA ENTRY
# ══════════════════════════════════════════════════════════════════════════════
with tab_entry:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">
        <i class="material-icons" style="font-size:30px;color:#0055A4;">cloud_upload</i>
        <div>
            <h2 style="margin:0;color:#003366;">Upload File Evaluasi</h2>
            <p style="margin:0;color:#8a8a8a;font-size:0.9em;">Upload L1, L2, dan Instruktur — sistem otomatis mendeteksi tipe file</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📖 Panduan Cepat", expanded=False):
        col_g1, col_g2, col_g3 = st.columns(3)
        with col_g1: st.markdown("**🔵 File L1** — wajib ada kolom `Ins-Eng-1 of 2` → Sheet **L1 Tertutup**")
        with col_g2: st.markdown("**🟢 File L2** — wajib ada kolom `Confidence Level` → Sheet **L1 Tertutup**")
        with col_g3: st.markdown("**🟠 File Instruktur** — wajib ada `Nama` + `Kode Diklat` → Sheet **Lap Instruktur**")

    # Sub-tab dalam Data Entry
    sub_upload, sub_riwayat, sub_panduan = st.tabs(["📤 Upload & Kirim", "🕒 Riwayat", "📄 Panduan Format"])

    # ── Sub-tab: Upload & Kirim ────────────────────────────────────────────────
    with sub_upload:
        with st.container(border=True):
            uploaded_files = st.file_uploader(
                "Pilih atau seret file Excel/CSV (bisa beberapa sekaligus)",
                type=["xlsx","csv"], accept_multiple_files=True, key="entry_uploader"
            )

        if uploaded_files:
            try:
                all_l1_dfs, all_l2_dfs, all_ins_dfs, file_log = [], [], [], []

                with st.status("🔍 Membaca dan mendeteksi tipe file...", expanded=True) as status_proc:
                    for f in uploaded_files:
                        df_raw = pd.read_csv(f) if f.name.endswith('.csv') else pd.read_excel(f)
                        df_raw.columns = df_raw.columns.astype(str).str.strip()

                        is_instruktur = ('Nama' in df_raw.columns and 'Kode Diklat' in df_raw.columns and 'Confidence Level' not in df_raw.columns)
                        is_l2 = ('Confidence Level' in df_raw.columns and 'Ins-Eng-1 of 2' not in df_raw.columns)
                        is_l1 = ('Ins-Eng-1 of 2' in df_raw.columns and not is_instruktur)

                        if is_instruktur:
                            before = len(df_raw)
                            df_raw = df_raw[~df_raw['Nama'].astype(str).str.strip().str.upper().isin(['UPDL JAKARTA','JAKARTA'])].reset_index(drop=True)
                            excluded = before - len(df_raw)
                            df_ins = build_instruktur_df(df_raw)
                            all_ins_dfs.append(df_ins)
                            excl_note = f" ({excluded} baris dummy dikecualikan)" if excluded > 0 else ""
                            file_log.append({"File":f.name,"Tipe":"🟠 Instruktur","Baris":len(df_raw),"Sheet":"Lap Instruktur"})
                            st.write(f"🟠 **Instruktur** — `{f.name}` ({len(df_raw)} baris{excl_note})")
                            st.session_state.riwayat_upload.append({
                                "nama":f.name,"waktu":datetime.now().strftime("%d/%m/%Y %H:%M"),
                                "tipe":"Instruktur","baris":len(df_raw)})

                        elif is_l1:
                            detect_and_show_column_mismatch(df_raw, INS_COL_NAMES, f.name, "INS")
                            detect_and_show_column_mismatch(df_raw, MAT_COL_NAMES, f.name, "MAT")
                            df_mapped = pd.DataFrame(index=df_raw.index, columns=TARGET_COLUMNS)
                            df_mapped['Kode Pembelajaran']           = df_raw.get('Kode Judul')
                            df_mapped['Judul Pembelajaran/Kegiatan'] = df_raw.get('Judul Pembelajaran')
                            df_mapped['Batch']                       = df_raw.get('Angkatan')
                            df_mapped['Tanggal Mulai']               = df_raw.get('Tgl Mulai')
                            df_mapped['Tanggal Selesai']             = df_raw.get('Tgl Selesai')
                            df_mapped['Strategi Pelaksanaan']        = df_raw.get('Strategi Pelaksana')
                            df_mapped['Peserta Isi L1']              = df_raw.get('P.Isi')
                            df_mapped['Peserta Hadir']               = df_raw.get('P.Hadir')
                            df_mapped['PIC KI']                      = df_raw.get('Bidang')
                            for i, c in enumerate(INS_COL_NAMES, 1): df_mapped[f'INS{i}'] = df_raw.get(c)
                            for i, c in enumerate(MAT_COL_NAMES, 1): df_mapped[f'MAT{i}'] = df_raw.get(c)
                            for i, c in enumerate(SP_COL_NAMES,  1): df_mapped[f'SP{i}']  = df_raw.get(c)
                            for i, c in enumerate(DS_COL_NAMES,  1): df_mapped[f'DS{i}']  = df_raw.get(c)
                            batch_val = df_mapped['Batch'].astype(str).str.replace(r'\.0$','',regex=True).str.strip()
                            tgl_mulai = pd.to_datetime(df_mapped['Tanggal Mulai'],errors='coerce').dt.strftime('%Y%m%d').fillna('NOTGL')
                            df_mapped['Kode Unik'] = df_mapped['Kode Pembelajaran'].astype(str).str.strip()+"."+batch_val+"."+tgl_mulai
                            all_l1_dfs.append(df_mapped)
                            ws_l1 = st.session_state["setting_worksheet"]
                            file_log.append({"File":f.name,"Tipe":"🔵 L1","Baris":len(df_raw),"Sheet":ws_l1})
                            st.write(f"🔵 **L1** — `{f.name}` ({len(df_raw)} baris) → Sheet: **{ws_l1}**")
                            st.session_state.riwayat_upload.append({
                                "nama":f.name,"waktu":datetime.now().strftime("%d/%m/%Y %H:%M"),
                                "tipe":"L1","baris":len(df_raw)})

                        elif is_l2:
                            df_mapped = pd.DataFrame(index=df_raw.index, columns=TARGET_COLUMNS)
                            df_mapped['Kode Pembelajaran']       = df_raw.get('Kode Judul')
                            df_mapped['Judul Pembelajaran/Kegiatan'] = df_raw.get('Judul')
                            df_mapped['Batch']                   = df_raw.get('Angkatan')
                            df_mapped['Tanggal Mulai']           = df_raw.get('Tgl Mulai')
                            df_mapped['Tanggal Selesai']         = df_raw.get('Tgl Selesai')
                            df_mapped['Peserta Hadir']           = df_raw.get('Jumlah Peserta Hadir')
                            df_mapped['Jumlah Peserta Lulus L2'] = df_raw.get('Jumlah Peserta Lulus')
                            df_mapped['Jumlah Peserta Isi L2']   = df_raw.get('Jumlah Peserta Isi')
                            df_mapped['Nilai Confidence']        = df_raw.get('Confidence Level')
                            df_mapped['Nilai Commitment']        = df_raw.get('Commitment Level')
                            batch_val = df_mapped['Batch'].astype(str).str.replace(r'\.0$','',regex=True).str.strip()
                            tgl_mulai = pd.to_datetime(df_mapped['Tanggal Mulai'],errors='coerce').dt.strftime('%Y%m%d').fillna('NOTGL')
                            df_mapped['Kode Unik'] = df_mapped['Kode Pembelajaran'].astype(str).str.strip()+"."+batch_val+"."+tgl_mulai
                            all_l2_dfs.append(df_mapped)
                            ws_l2 = st.session_state["setting_worksheet"]
                            file_log.append({"File":f.name,"Tipe":"🟢 L2","Baris":len(df_raw),"Sheet":ws_l2})
                            st.write(f"🟢 **L2** — `{f.name}` ({len(df_raw)} baris) → Sheet: **{ws_l2}**")
                            st.session_state.riwayat_upload.append({
                                "nama":f.name,"waktu":datetime.now().strftime("%d/%m/%Y %H:%M"),
                                "tipe":"L2","baris":len(df_raw)})
                        else:
                            file_log.append({"File":f.name,"Tipe":"❌ Tidak Dikenal","Baris":len(df_raw),"Sheet":"—"})
                            st.error(f"❌ **{f.name}** tidak dikenali. Kolom: `{'`, `'.join(list(df_raw.columns[:10]))}`...")

                    status_proc.update(label="✅ Selesai!", state="complete", expanded=False)

                if not all_l1_dfs and not all_l2_dfs and not all_ins_dfs:
                    st.stop()

                st.markdown("### 📋 Ringkasan")
                st.dataframe(pd.DataFrame(file_log), use_container_width=True, hide_index=True)

                # Proses L1 + L2
                has_l1l2 = bool(all_l1_dfs or all_l2_dfs)
                has_ins  = bool(all_ins_dfs)

                if has_l1l2:
                    df_l1 = pd.concat(all_l1_dfs, ignore_index=True) if all_l1_dfs else pd.DataFrame(columns=TARGET_COLUMNS)
                    if all_l2_dfs:
                        df_l2_raw  = pd.concat(all_l2_dfs, ignore_index=True)
                        l2_cols_av = [c for c in L2_MERGE_COLS if c in df_l2_raw.columns]
                        df_l2_slim = df_l2_raw[l2_cols_av].groupby('Kode Unik', as_index=False).first()
                        if not df_l1.empty:
                            df_final = df_l1.merge(df_l2_slim, on='Kode Unik', how='left', suffixes=('','_l2'))
                            for col in [c for c in L2_MERGE_COLS if c != 'Kode Unik']:
                                col_l2 = col+'_l2'
                                if col_l2 in df_final.columns:
                                    df_final[col] = df_final[col].combine_first(df_final[col_l2])
                                    df_final.drop(columns=[col_l2], inplace=True)
                        else:
                            df_final = df_l2_raw.copy()
                    else:
                        df_final = df_l1.copy()

                    df_final = df_final.reindex(columns=TARGET_COLUMNS)
                    df_final['Tanggal Selesai'] = pd.to_datetime(df_final['Tanggal Selesai'], errors='coerce')
                    df_final['Tanggal Mulai']   = pd.to_datetime(df_final['Tanggal Mulai'],   errors='coerce')
                    df_final['Cut off Data']    = df_final['Tanggal Selesai'] + pd.Timedelta(days=st.session_state["setting_cutoff"])
                    df_final['Laporan Bulan']   = df_final['Cut off Data'].dt.month.map(BULAN_MAP_ID)
                    today = pd.Timestamp.today().normalize()
                    df_final['Status Pembelajaran'] = df_final['Tanggal Selesai'].apply(
                        lambda x: "Terlaksana" if pd.notna(x) and x<=today else ("Belum Terlaksana" if pd.notna(x) else ""))
                    for col in ['Peserta Isi L1','Peserta Hadir','Jumlah Peserta Lulus L2','Jumlah Peserta Isi L2','Nilai Confidence','Nilai Commitment']:
                        df_final[col] = pd.to_numeric(df_final[col], errors='coerce')
                    df_final['% Pengisian'] = safe_divide(df_final['Peserta Isi L1'], df_final['Peserta Hadir'])
                    df_final['% Valid'] = df_final['% Pengisian'].apply(
                        lambda x: "VALID" if pd.notna(x) and x>st.session_state["setting_threshold"] else ("TIDAK VALID" if pd.notna(x) else ""))
                    df_final['% Pengisian L2'] = safe_divide(df_final['Jumlah Peserta Isi L2'], df_final['Jumlah Peserta Lulus L2'])
                    all_indicators = [f'INS{i}' for i in range(1,10)] + [f'MAT{i}' for i in range(1,8)] + [f'SP{i}' for i in range(1,7)] + [f'DS{i}' for i in range(1,7)]
                    for col in all_indicators:
                        df_final[col] = pd.to_numeric(df_final[col], errors='coerce')
                    df_final['RATA INST'] = df_final[[f'INS{i}' for i in range(1,9)]].mean(axis=1)
                    df_final['RATA MAT']  = df_final[[f'MAT{i}' for i in range(1,7)]].mean(axis=1)
                    df_final['RATA SP']   = df_final[[f'SP{i}'  for i in range(1,6)]].mean(axis=1)
                    df_final['RATA DS']   = df_final[[f'DS{i}'  for i in range(1,6)]].mean(axis=1)
                    df_final['RATA-RATA KESELURUHAN'] = df_final[['RATA INST','RATA MAT','RATA SP','RATA DS']].mean(axis=1)
                    df_final['Jumlah Indikator dibawah 4.5'] = (df_final[all_indicators] < 4.5).sum(axis=1)
                    df_final['Jumlah Indikator diatas 4.5']  = (df_final[all_indicators] >= 4.5).sum(axis=1)
                    df_final.replace([np.inf, -np.inf], np.nan, inplace=True)

                    with st.container(border=True):
                        st.markdown("#### 🗓️ Filter & Preview — L1 & L2")
                        if not df_final['Tanggal Mulai'].isnull().all():
                            min_date = df_final['Tanggal Mulai'].min().date()
                            max_date = df_final['Tanggal Mulai'].max().date()
                            c1, c2 = st.columns(2)
                            start_d = c1.date_input("Mulai", min_date, key="l1l2_start")
                            end_d   = c2.date_input("Sampai", max_date, key="l1l2_end")
                            mask = (df_final['Tanggal Mulai'] >= pd.to_datetime(start_d)) & (df_final['Tanggal Mulai'] <= pd.to_datetime(end_d))
                            df_to_push = df_final.loc[mask].copy()
                        else:
                            df_to_push = df_final.copy()

                        m1, m2, m3, m4 = st.columns(4)
                        rata_l1 = df_to_push['RATA-RATA KESELURUHAN'].mean()
                        total_lulus = df_to_push['Jumlah Peserta Lulus L2'].sum()
                        total_hadir = df_to_push['Peserta Hadir'].sum()
                        pct_lulus   = (total_lulus/total_hadir*100) if total_hadir > 0 else None
                        rata_partisipasi = df_to_push['% Pengisian'].mean()
                        m1.metric("📊 Baris Aktif",  f"{len(df_to_push)}")
                        m2.metric("😊 Rata-rata L1", f"{rata_l1:.2f}" if pd.notna(rata_l1) else "N/A")
                        m3.metric("🎓 % Lulus L2",   f"{pct_lulus:.1f}%" if pct_lulus else "N/A")
                        m4.metric("📋 % Pengisian",  f"{rata_partisipasi*100:.1f}%" if pd.notna(rata_partisipasi) else "N/A")
                        with st.expander(f"🔍 Preview ({len(df_to_push)} baris)", expanded=False):
                            st.dataframe(df_to_push.fillna(""), use_container_width=True)

                if has_ins:
                    df_ins_final = pd.concat(all_ins_dfs, ignore_index=True)
                    df_ins_final['TANGGAL MULAI'] = pd.to_datetime(df_ins_final['TANGGAL MULAI'], errors='coerce')
                    with st.container(border=True):
                        st.markdown("#### 🗓️ Filter & Preview — Instruktur")
                        if not df_ins_final['TANGGAL MULAI'].isnull().all():
                            min_d, max_d = df_ins_final['TANGGAL MULAI'].min().date(), df_ins_final['TANGGAL MULAI'].max().date()
                            fc1, fc2 = st.columns(2)
                            start_ins = fc1.date_input("Mulai", min_d, key="ins_start")
                            end_ins   = fc2.date_input("Sampai", max_d, key="ins_end")
                            mask_ins = (df_ins_final['TANGGAL MULAI'] >= pd.to_datetime(start_ins)) & (df_ins_final['TANGGAL MULAI'] <= pd.to_datetime(end_ins))
                            df_ins_push = df_ins_final.loc[mask_ins].copy()
                        else:
                            df_ins_push = df_ins_final.copy()
                        mi1, mi2, mi3 = st.columns(3)
                        rata_ins = df_ins_push['RATA-RATA PER INSTRUKTUR'].mean()
                        mi1.metric("📚 Sesi Mengajar", f"{len(df_ins_push)}")
                        mi2.metric("⭐ Rata-rata",      f"{rata_ins:.2f}" if pd.notna(rata_ins) else "N/A")
                        mi3.metric("📊 Min/Max",        f"{df_ins_push['RATA-RATA PER INSTRUKTUR'].min():.2f} / {df_ins_push['RATA-RATA PER INSTRUKTUR'].max():.2f}" if pd.notna(rata_ins) else "N/A")
                        with st.expander(f"🔍 Preview ({len(df_ins_push)} baris)", expanded=False):
                            st.dataframe(df_ins_push.fillna(""), use_container_width=True)

                # Tombol Kirim
                st.markdown("---")
                ws_l1l2    = st.session_state["setting_worksheet"]
                ws_ins     = st.session_state["setting_ws_instruktur"]
                sheet_name = st.session_state["setting_sheet"]

                col_info, col_btn = st.columns([2, 1])
                with col_info:
                    with st.container(border=True):
                        parts = []
                        if has_l1l2: parts.append(f"🔵🟢 **{len(df_to_push)} baris L1/L2** → `{ws_l1l2}`")
                        if has_ins:  parts.append(f"🟠 **{len(df_ins_push)} baris Instruktur** → `{ws_ins}`")
                        st.markdown("\n\n".join(parts) or "_Tidak ada data_")
                        st.caption(f"📁 Google Sheets: **{sheet_name}**")

                with col_btn:
                    if st.button("🚀 KIRIM KE GOOGLE SHEETS", use_container_width=True,
                                 disabled=not(has_l1l2 or has_ins), type="primary", key="btn_kirim"):
                        with st.spinner("Menghubungkan..."):
                            client = init_gsheets_connection()
                            hasil = []
                            if has_l1l2:
                                sht = client.open(sheet_name).worksheet(ws_l1l2)
                                max_no = get_sheet_max_no(sht)
                                df_to_push['No'] = range(max_no+1, max_no+1+len(df_to_push))
                                rows = [clean_row_for_sheets(r) for r in df_to_push.reindex(columns=TARGET_COLUMNS).values.tolist()]
                                sht.append_rows(rows, value_input_option='USER_ENTERED')
                                hasil.append(f"✅ **L1 & L2**: {len(rows)} baris → sheet **{ws_l1l2}**")
                            if has_ins:
                                sht_ins = client.open(sheet_name).worksheet(ws_ins)
                                max_no_ins = get_sheet_max_no(sht_ins)
                                df_ins_push_send = df_ins_push.copy()
                                df_ins_push_send.insert(0, 'NO', range(max_no_ins+1, max_no_ins+1+len(df_ins_push)))
                                df_ins_push_send = df_ins_push_send.reindex(columns=LAP_INSTRUKTUR_COLUMNS)
                                rows_ins = [clean_row_for_sheets(r) for r in df_ins_push_send.values.tolist()]
                                sht_ins.append_rows(rows_ins, value_input_option='USER_ENTERED')
                                hasil.append(f"✅ **Instruktur**: {len(rows_ins)} baris → sheet **{ws_ins}**")
                            for h in hasil: st.success(h)
                            st.balloons()

            except Exception as e:
                st.error(f"Terjadi kesalahan: {e}")
                st.exception(e)
        else:
            st.markdown("""
            <div style="text-align:center;padding:40px;color:#aaa;">
                <i class="material-icons" style="font-size:60px;color:#ccc;">upload_file</i>
                <p style="font-size:1.1em;margin-top:10px;">Belum ada file diupload.<br>
                <span style="font-size:0.9em;">Seret file L1, L2, dan/atau Instruktur ke area upload di atas.</span></p>
            </div>
            """, unsafe_allow_html=True)

    # ── Sub-tab: Riwayat ──────────────────────────────────────────────────────
    with sub_riwayat:
        if not st.session_state.riwayat_upload:
            st.info("Belum ada riwayat upload.")
        else:
            for item in reversed(st.session_state.riwayat_upload):
                badge_color = {"L1":"#0055A4","L2":"#1a7a2e","Instruktur":"#b35900"}.get(item['tipe'],"#666")
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:10px;padding:10px 0;border-bottom:1px solid #eee;">
                    <div style="flex:1;">
                        <p style="margin:0;font-weight:bold;">{item['nama']}</p>
                        <p style="margin:0;font-size:0.8em;color:#8a8a8a;">{item['waktu']} &bull; {item['baris']} baris</p>
                    </div>
                    <span style="background:{badge_color}20;color:{badge_color};border:1px solid {badge_color}55;
                                 padding:2px 10px;border-radius:20px;font-size:0.75em;font-weight:bold;">{item['tipe']}</span>
                </div>""", unsafe_allow_html=True)

    # ── Sub-tab: Panduan Format ────────────────────────────────────────────────
    with sub_panduan:
        with st.expander("📖 File L1 — Evaluasi Reaksi", expanded=True):
            st.markdown("- Wajib ada kolom `Ins-Eng-1 of 2`\n- Kolom penting: `Kode Judul`, `Judul Pembelajaran`, `Angkatan`, `Tgl Mulai`, `Tgl Selesai`, `Strategi Pelaksana`, `P.Isi`, `P.Hadir`, `Bidang`")
        with st.expander("📖 File L2 — Evaluasi Pembelajaran", expanded=True):
            st.markdown("- Wajib ada kolom `Confidence Level` (tanpa `Ins-Eng-1 of 2`)\n- Kolom penting: `Kode Judul`, `Judul`, `Angkatan`, `Tgl Mulai`, `Tgl Selesai`, `Jumlah Peserta Hadir/Lulus/Isi`, `Commitment Level`")
        with st.expander("📖 File Instruktur — Laporan Instruktur", expanded=True):
            st.markdown("- Wajib ada kolom `Nama` **DAN** `Kode Diklat`\n- Kolom skor: `Ins-Eng-1 of 2`, `Ins-Eng-2 of 2`, `Ins-Rel-1 of 2`, `Ins-Rel-2 of 2`, `Ins-Sat-1 of 4` s.d. `Ins-Sat-4 of 4`, `Ins-Rat`")
            st.warning("⚠️ Nama kolom **harus persis sama** (case-sensitive). `Mat-Sat-1 0f 2` menggunakan angka nol (0), bukan huruf o.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 5: PENGATURAN
# ══════════════════════════════════════════════════════════════════════════════
with tab_setting:
    st.subheader("⚙️ Pengaturan Data Entry")
    with st.container(border=True):
        st.markdown("#### 🔗 Konfigurasi Google Sheets")
        nama_sheet = st.text_input("Nama File Google Sheets", value=st.session_state["setting_sheet"])

        st.markdown("---")
        st.markdown("#### 📋 Nama Tab (Worksheet)")
        col_ws1, col_ws2 = st.columns(2)
        with col_ws1: nama_worksheet     = st.text_input("Tab — L1 & L2 Tertutup",   value=st.session_state["setting_worksheet"])
        with col_ws2: nama_ws_instruktur = st.text_input("Tab — Lap Instruktur",      value=st.session_state["setting_ws_instruktur"])

        st.markdown("---")
        st.markdown("#### 📅 Cut-off & Threshold")
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            cutoff_hari = st.number_input("Hari Cut-off setelah Tanggal Selesai",
                min_value=1, max_value=30, value=st.session_state["setting_cutoff"])
        with col_s2:
            threshold_valid = st.slider("Minimal % pengisian → VALID",
                0.10, 1.0, value=st.session_state["setting_threshold"], step=0.01, format="%.2f")
            st.info(f"Pengisian ≥ {threshold_valid:.0%} = **VALID**")

        if st.button("💾 Simpan Pengaturan", use_container_width=True):
            st.session_state["setting_sheet"]         = nama_sheet
            st.session_state["setting_worksheet"]     = nama_worksheet
            st.session_state["setting_ws_instruktur"] = nama_ws_instruktur
            st.session_state["setting_cutoff"]        = cutoff_hari
            st.session_state["setting_threshold"]     = threshold_valid
            st.success("✅ Pengaturan berhasil disimpan!")
