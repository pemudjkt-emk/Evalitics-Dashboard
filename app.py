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
import urllib.request
import io
import re

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Smart Evaluation Analytics UPDL Jakarta",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Menghapus CSS tab lama dan sedikit merapikan area Uploader
st.markdown("""
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
    <style>
    [data-testid="stFileUploader"] {
        background: #ffffff;
        border: 2px dashed #0055A4;
        border-radius: 12px;
        padding: 20px;
    }
    /* Mempercantik font di sidebar */
    [data-testid="stSidebar"] [data-testid="stRadio"] label p {
        font-size: 16px;
        font-weight: 500;
    }
    </style>
""", unsafe_allow_html=True)
# ─────────────────────────────────────────────────────────────────────────────
# HEADER (TETAP DI KONTEN UTAMA AGAR EKSKLUSIF)
# ─────────────────────────────────────────────────────────────────────────────
def get_base64_logo(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
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
            Website Analitik Interaktif Evaluasi Pembelajaran UPDL Jakarta
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

# TARGET KOLOM UNTUK SHEET "MASTER DATA LAPORAN" (JALUR 3: L1 + SMILE)
MASTER_TARGET_COLUMNS = [
    'No', 'Kode Unik', 'Laporan Bulan',
    'Kode Service Request', 'Jenis Program', 'Judul Pembelajaran', 'Kode Pembelajaran',
    'Strategi Pelaksanaan', 'Lokasi Pelaksanaan', 'Tempat Pelaksanaan', 'No Surat Penugasan', 'Tanggal Surat Penugasan',
    'Nomor Surat Pemanggilan Peserta', 'Instruktur/ Fasilitator',
    'Tgl Mulai', 'Tgl Selesai', 'Rencana Jumlah Peserta', 'Peserta Diundang', 'Peserta Hadir', 'Peserta Lulus',
    '% Kehadiran', '% Kelulusan', 'RAB Pelaksanaan', 'Realisasi Biaya Pelaksanaan',
    'Peserta Isi L1', '% Pengisian L1', '% Valid L1',
    'RATA INST', 'RATA MAT', 'RATA SP', 'RATA DS', 'RATA-RATA KESELURUHAN',
    'Jumlah Indikator dibawah 4.5', 'Jumlah Indikator diatas 4.5', 'Status Pembelajaran'
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

DETAIL_INSTRUKTUR_COLUMNS = [
    'NIP', 'Nama', 'Tgl Mulai', 'Tgl Selesai', 'Kode Diklat', 'Judul Diklat',
    'Angkatan', 'UPDL', 'Jenis Peyelenggaraan', 'Durasi Mengajar',
    'Ins-Eng', 'Ins-Rel', 'Ins-Sat', 'Ins-Rat', 'Ins-Val'
]

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

def build_instruktur_df(df_raw):
    df = pd.DataFrame(columns=DETAIL_INSTRUKTUR_COLUMNS)
    df['NIP'] = df_raw.get('NIP')
    df['Nama'] = df_raw.get('Nama')
    df['Tgl Mulai'] = pd.to_datetime(df_raw.get('Tgl Mulai'), errors='coerce')
    df['Tgl Selesai'] = pd.to_datetime(df_raw.get('Tgl Selesai'), errors='coerce')
    df['Kode Diklat'] = df_raw.get('Kode Diklat')
    df['Judul Diklat'] = df_raw.get('Judul Diklat')
    
    angkatan_raw = df_raw.get('Angkatan')
    df['Angkatan'] = (angkatan_raw.astype(str).str.replace(r'\.0$','',regex=True).str.strip().replace('nan','')
                      if angkatan_raw is not None else '')
    
    df['UPDL'] = df_raw.get('UPDL')
    df['Jenis Peyelenggaraan'] = df_raw.get('Jenis Peyelenggaraan')
    df['Durasi Mengajar'] = pd.to_numeric(df_raw.get('Durasi Mengajar'), errors='coerce')
    
    ins_eng_cols = ['Ins-Eng-1 of 2', 'Ins-Eng-2 of 2']
    ins_rel_cols = ['Ins-Rel-1 of 2', 'Ins-Rel-2 of 2']
    ins_sat_cols = ['Ins-Sat-1 of 4', 'Ins-Sat-2 of 4', 'Ins-Sat-3 of 4', 'Ins-Sat-4 of 4']
    
    for c in ins_eng_cols + ins_rel_cols + ins_sat_cols + ['Ins-Rat', 'Ins-Val']:
        if c in df_raw.columns:
            df_raw[c] = pd.to_numeric(df_raw[c], errors='coerce')
            
    valid_eng = [c for c in ins_eng_cols if c in df_raw.columns]
    valid_rel = [c for c in ins_rel_cols if c in df_raw.columns]
    valid_sat = [c for c in ins_sat_cols if c in df_raw.columns]
    
    df['Ins-Eng'] = df_raw[valid_eng].mean(axis=1) if valid_eng else np.nan
    df['Ins-Rel'] = df_raw[valid_rel].mean(axis=1) if valid_rel else np.nan
    df['Ins-Sat'] = df_raw[valid_sat].mean(axis=1) if valid_sat else np.nan
    
    df['Ins-Rat'] = df_raw.get('Ins-Rat')
    df['Ins-Val'] = df_raw.get('Ins-Val')
    
    return df

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

def init_gsheets_connection():
    scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    return gspread.authorize(creds)

def get_sheet_max_no(sheet):
    try:
        col_no = sheet.col_values(1)
        if len(col_no) > 1:
            return max([int(x) for x in col_no[1:] if str(x).isdigit()] + [0])
        return 0
    except:
        return 0

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE defaults
# ─────────────────────────────────────────────────────────────────────────────
for key, default in [
    ("setting_sheet",         "Monitoring Evaluasi Pembelajaran"),
    ("setting_worksheet",     "L1 Tertutup"),
    ("setting_ws_master",     "Master_Data_Laporan"),
    ("setting_ws_instruktur", "Detail Instruktur"),
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
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        return genai.GenerativeModel('gemini-1.5-flash')
    return None

model = load_gemini_model()

# ─────────────────────────────────────────────────────────────────────────────
# ENGINE SENTIMENT ANALYSIS (OPEN-SOURCE LEXICON)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=86400)
def load_opensource_lexicon():
    url_pos = "https://raw.githubusercontent.com/masdevid/ID-OpinionWords/master/positive.txt"
    url_neg = "https://raw.githubusercontent.com/masdevid/ID-OpinionWords/master/negative.txt"
    try:
        pos_data = urllib.request.urlopen(url_pos).read().decode('utf-8').split('\n')
        neg_data = urllib.request.urlopen(url_neg).read().decode('utf-8').split('\n')
        pos_set = set([kata.strip() for kata in pos_data if kata.strip() and not kata.startswith(';')])
        neg_set = set([kata.strip() for kata in neg_data if kata.strip() and not kata.startswith(';')])
        return pos_set, neg_set
    except Exception as e:
        return set(), set()

kamus_positif, kamus_negatif = load_opensource_lexicon()
kata_negasi = {'tidak', 'bukan', 'jangan', 'kurang', 'ga', 'gak', 'enggak', 'tdk'}

def analisis_sentimen_opensource(teks):
    if pd.isna(teks) or str(teks).strip() == "": return "Netral"
    teks_bersih = re.sub(r'[^\w\s]', '', str(teks).lower())
    kata_kata = teks_bersih.split()
    skor = 0
    i = 0
    while i < len(kata_kata):
        kata = kata_kata[i]
        if kata in kata_negasi and i + 1 < len(kata_kata):
            kata_berikutnya = kata_kata[i+1]
            if kata_berikutnya in kamus_positif: skor -= 1  
            elif kata_berikutnya in kamus_negatif: skor += 1  
            i += 2; continue
        if kata in kamus_positif: skor += 1
        elif kata in kamus_negatif: skor -= 1
        i += 1
    if skor > 0: return "Positif"
    elif skor < 0: return "Negatif"
    else: return "Netral"


# ─────────────────────────────────────────────────────────────────────────────
# MENU NAVIGASI (SIDEBAR)
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🧭 Menu Navigasi")
    
    menu_selection = st.radio(
        "Pilih Modul Aplikasi:",
        [
            "📤 DATA ENTRY",
            "📈 ANALYTICS",
            "📊 DASHBOARD",
            "🤖 AI ASSISTANT",
            "🚨 EARLY WARNING",
            "📑 REPORT & KATALOG",
            "⚙️ PENGATURAN"
        ]
    )
    
    st.markdown("---")
    if st.button("🔄 Sinkron Data Terkini", use_container_width=True):
        st.cache_data.clear()
        st.toast("Menarik data terbaru dari Google Sheets...")

# URL Sumber Data Global (Dibutuhkan oleh Analytics, Dashboard & Report)
sheet_id = '1IDAmFwTbBQDZcKM3eiiEDcA3KwM9WKqW4zCrk__6-PU'
sheet_name = 'L1%20Tertutup' 
url = "https://docs.google.com/spreadsheets/d/" + str(sheet_id) + "/gviz/tq?tqx=out:csv&sheet=" + str(sheet_name)


# ══════════════════════════════════════════════════════════════════════════════
# ROUTING KONTEN BERDASARKAN PILIHAN SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════

if menu_selection in ["📈 ANALYTICS", "📊 DASHBOARD"]:
    try:
        @st.cache_data(ttl=300)
        def load_csv(url):
            return pd.read_csv(url)

        df = load_csv(url)
        st.markdown("### 🎛️ Filter Data")

        def build_filters(suffix):
            opsi_bulan    = list(df['Laporan Bulan'].dropna().unique())
            opsi_strategi = list(df['Strategi Pelaksanaan'].dropna().unique())
            opsi_valid    = ["Semua Status"] + list(df['% Valid'].dropna().unique())
            
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                filter_bulan = st.multiselect("Laporan Bulan", options=opsi_bulan,
                                              default=opsi_bulan, key=f"bulan_{suffix}")
            with col_f2:
                filter_strategi = st.multiselect("Strategi Pelaksanaan", options=opsi_strategi,
                                                 default=opsi_strategi, key=f"strategi_{suffix}")
            with col_f3:
                filter_valid = st.selectbox("Validitas", opsi_valid, key=f"valid_{suffix}")

            df_f = df.copy()
            
            df_f = df_f[df_f['Laporan Bulan'].isin(filter_bulan)] if filter_bulan else df_f
            df_f = df_f[df_f['Strategi Pelaksanaan'].isin(filter_strategi)] if filter_strategi else df_f
            
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

        # ---------------------------------------------------------
        # KONTEN: 📈 ANALYTICS
        # ---------------------------------------------------------
        if menu_selection == "📈 ANALYTICS":
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
                    df_ipa = df_filtered.dropna(subset=['RATA-RATA KESELURUHAN']).copy()
                    if '% Pengisian' in df_ipa.columns:
                        df_ipa['Pengisian_Clean'] = pd.to_numeric(df_ipa['% Pengisian'].astype(str).str.replace('%', '', regex=False), errors='coerce')
                        rata_pengisian = df_ipa['Pengisian_Clean'].mean()
                        if pd.notna(rata_pengisian) and rata_pengisian > 1:
                            rata_pengisian = rata_pengisian / 100
                        if pd.notna(rata_pengisian) and rata_pengisian < 0.40:
                            st.warning(f"⚠️ **Peringatan Sampel:** Rata-rata tingkat pengisian (Response Rate) pada data ini hanya **{rata_pengisian*100:.1f}%** (di bawah standar validitas 40%). Titik kuadran mungkin dipengaruhi anomali karena sampel terlalu sedikit.")
                    
                    level_ipa = st.radio(
                        "🔍 Pilih Kedalaman Analisis Akar Masalah (Drill-down):", 
                        ["📊 Makro (Kategori Utama)", "🔎 Mikro (Sub-Indikator Detail)"], 
                        horizontal=True
                    )

                    if len(df_ipa) > 2:
                        if level_ipa == "📊 Makro (Kategori Utama)":
                            kategori_list = [
                                'Engagement Instruktur', 'Relevance Instruktur', 'Satisfaction Instruktur',
                                'Engagement Materi', 'Relevance Materi', 'Satisfaction Materi',
                                'Satisfaction Sarana Digital', 'Satisfaction Sarana In Class'
                            ]
                            nama_tampil = kategori_list
                        else:
                            kategori_list = [
                                'INS1','INS2','INS3','INS4','INS5','INS6','INS7','INS8',
                                'MAT1','MAT2','MAT3','MAT4','MAT5','MAT6',
                                'SP1','SP2','SP3','SP4','SP5',
                                'DS1','DS2','DS3','DS4','DS5'
                            ]
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
                            nama_tampil = [kamus_nama.get(k, k) for k in kategori_list]

                        kinerja, kepentingan = [], []
                        
                        for kat in kategori_list:
                            if kat in df_ipa.columns:
                                df_ipa[kat] = pd.to_numeric(df_ipa[kat], errors='coerce')
                                kinerja.append(df_ipa[kat].mean())
                                corr_val = df_ipa[kat].corr(pd.to_numeric(df_ipa['RATA-RATA KESELURUHAN'], errors='coerce'))
                                kepentingan.append(corr_val)
                            else:
                                kinerja.append(None); kepentingan.append(None)

                        df_plot_ipa = pd.DataFrame({'Kategori': nama_tampil, 'Kinerja': kinerja, 'Kepentingan': kepentingan})
                        mean_kepentingan = df_plot_ipa['Kepentingan'].mean()
                        if pd.isna(mean_kepentingan): mean_kepentingan = 0.5 
                        df_plot_ipa['Kepentingan'] = df_plot_ipa['Kepentingan'].fillna(mean_kepentingan)
                        df_plot_ipa = df_plot_ipa.dropna(subset=['Kinerja']) 

                        if not df_plot_ipa.empty:
                            x_cross = 4.5  
                            y_cross = df_plot_ipa['Kepentingan'].mean() 
                            
                            fig_ipa = px.scatter(df_plot_ipa, x='Kinerja', y='Kepentingan', text='Kategori')
                            ukuran_teks = 10 if level_ipa == "🔎 Mikro (Sub-Indikator Detail)" else 13
                            fig_ipa.update_traces(textposition='top center', textfont_size=ukuran_teks, marker=dict(size=12, color='#005b9f', line=dict(width=1,color='DarkSlateGrey')))
                            fig_ipa.add_hline(y=y_cross, line_dash="dash", line_color="#FFC000")
                            fig_ipa.add_vline(x=x_cross, line_dash="dash", line_color="#FFC000", annotation_text="Standar TMP (4.5)", annotation_position="top left")
                            
                            for ax, ay, txt, col, algn in [
                                (0.01, 0.99, "<b>KUADRAN 1</b><br>🚨 Prioritas Utama", "#d32f2f", "left"),
                                (0.99, 0.99, "<b>KUADRAN 2</b><br>🌟 Pertahankan", "#2e7d32", "right"),
                                (0.01, 0.01, "<b>KUADRAN 3</b><br>📉 Prioritas Sekunder", "#757575", "left"),
                                (0.99, 0.01, "<b>KUADRAN 4</b><br>⚠️ Berlebihan", "#f57c00", "right"),
                            ]:
                                fig_ipa.add_annotation(xref="paper", yref="paper", x=ax, y=ay, text=txt, showarrow=False, font=dict(color=col, size=13), align=algn)
                            
                            min_x = min(4.0, df_plot_ipa['Kinerja'].min() - 0.1) if not df_plot_ipa['Kinerja'].empty else 4.0
                            min_y = min(-0.1, df_plot_ipa['Kepentingan'].min() - 0.1) if not df_plot_ipa['Kepentingan'].empty else -0.1
                            max_y = max(1.1, df_plot_ipa['Kepentingan'].max() + 0.1) if not df_plot_ipa['Kepentingan'].empty else 1.1
                            
                            fig_ipa.update_layout(height=600 if level_ipa == "📊 Makro (Kategori Utama)" else 700, margin=dict(t=40,b=40,l=40,r=40), xaxis_range=[min_x, 5.1], yaxis_range=[min_y, max_y], xaxis_title="Kinerja (Rata-rata Skor Kepuasan)", yaxis_title="Kepentingan (Korelasi terhadap Total Skor)")
                            st.plotly_chart(fig_ipa, use_container_width=True)

                            q1_items = df_plot_ipa[(df_plot_ipa['Kinerja'] < x_cross) & (df_plot_ipa['Kepentingan'] > y_cross)]['Kategori'].tolist()
                            st.markdown("<h4 style='color: #003366; margin-top: 30px;'>💡 Executive Diagnosis</h4>", unsafe_allow_html=True)
                            
                            if q1_items:
                                list_html = "".join([f"<li style='margin-bottom: 5px;'><b>{item}</b></li>" for item in q1_items])
                                rek_text = "Beralih ke <b>Mode Mikro</b> di pengaturan atas untuk melihat rincian sub-indikator spesifik yang menjadi akar masalah." if level_ipa == "📊 Makro (Kategori Utama)" else "Segera susun rencana perbaikan operasional untuk indikator di atas. Elevasi di area ini akan memberikan dampak paling masif terhadap lonjakan total skor evaluasi."
                                
                                alert_html = f"""<div style="padding: 20px; border-radius: 10px; border-left: 8px solid #d32f2f; background-color: #fdf5f5; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 20px;">
                                    <div style="display: flex; align-items: flex-start; gap: 15px;">
                                        <div style="font-size: 32px; margin-top: 2px;">🚨</div>
                                        <div style="width: 100%;">
                                            <h4 style="margin: 0 0 8px 0; color: #d32f2f; font-size: 18px;">Peringatan Area Kritis (Kuadran 1)</h4>
                                            <p style="margin: 0 0 10px 0; color: #444; font-size: 15px;">Ditemukan indikator yang <b>sangat memengaruhi kepuasan peserta</b>, namun kinerjanya <b>di bawah standar PLN (4.5)</b>:</p>
                                            <ul style="margin: 0 0 15px 0; padding-left: 20px; color: #b71c1c; font-size: 15px;">{list_html}</ul>
                                            <div style="padding: 10px 15px; background-color: rgba(0, 85, 164, 0.08); border-radius: 6px; border-left: 4px solid #0055A4;">
                                                <p style="margin: 0; font-size: 14px; color: #003366;"><b>Tindak Lanjut:</b> {rek_text}</p>
                                            </div></div></div></div>"""
                                st.markdown(alert_html, unsafe_allow_html=True)
                            else: 
                                success_html = """<div style="padding: 25px; border-radius: 10px; background: linear-gradient(135deg, #003366, #0055A4); box-shadow: 0 4px 10px rgba(0,0,0,0.15); margin-bottom: 20px; border-left: 8px solid #ffc107; display: flex; align-items: center; gap: 20px;">
                                    <div style="font-size: 45px; background: rgba(255,255,255,0.1); padding: 10px 15px; border-radius: 50%;">🏆</div>
                                    <div><h4 style="margin: 0 0 5px 0; color: #ffc107; font-size: 20px;">Kinerja Prima Luar Biasa!</h4>
                                    <p style="margin: 0; color: #ffffff; font-size: 15px; line-height: 1.5; opacity: 0.9;">Tidak ada indikator krusial yang jatuh di Kuadran 1 pada periode evaluasi ini. Terus pertahankan kualitas pelayanan dan materi Anda sesuai standar ekselensi UPDL Jakarta.</p></div></div>"""
                                st.markdown(success_html, unsafe_allow_html=True)
                        
                        st.markdown("---")
                        st.markdown("### 📜 Histori & Evaluasi Dampak Tindak Lanjut (Tren Antar Bulan)")
                        st.write("Pilih salah satu indikator di bawah ini untuk melihat 'perjalanan' posisinya dari bulan ke bulan.")
                        URUTAN_BULAN = ['Februari','Maret','April','Mei','Juni','Juli','Agustus','September','Oktober','November','Desember']
                        list_pelacakan = kategori_list
                        indikator_dipilih = st.selectbox("🎯 Pilih Indikator yang Ingin Dilacak Historinya:", list_pelacakan, key="sb_history_ipa")
                        
                        col_key_asli = indikator_dipilih
                        if level_ipa == "🔎 Mikro (Sub-Indikator Detail)":
                            for k, v in kamus_nama.items():
                                if v == indikator_dipilih:
                                    col_key_asli = k; break
                        
                        histori_bulan, histori_kinerja, histori_kepentingan = [], [], []
                        
                        # Load data global untuk context
                        try:
                            df_global_ctx = pd.read_csv(url)
                            if '% Pengisian' in df_global_ctx.columns: df_global_ctx['Pengisian_Clean'] = pd.to_numeric(df_global_ctx['% Pengisian'].astype(str).str.replace('%', '', regex=False), errors='coerce')
                            for k_item in kategori_list:
                                k_key = k_item
                                if level_ipa == "🔎 Mikro (Sub-Indikator Detail)":
                                    for kk, vv in kamus_nama.items():
                                        if vv == k_item: k_key = kk; break
                                if k_key in df_global_ctx.columns: df_global_ctx[k_key] = pd.to_numeric(df_global_ctx[k_key], errors='coerce')
                            df_global_ctx['RATA-RATA KESELURUHAN'] = pd.to_numeric(df_global_ctx['RATA-RATA KESELURUHAN'], errors='coerce')

                            bulan_tersedia_di_data = [b for b in URUTAN_BULAN if b in df_global_ctx['Laporan Bulan'].unique()]
                            for bln in bulan_tersedia_di_data:
                                df_bln = df_global_ctx[df_global_ctx['Laporan Bulan'] == bln]
                                if len(df_bln) > 1 and col_key_asli in df_bln.columns:
                                    mean_kinerja = df_bln[col_key_asli].mean()
                                    corr_kepentingan = df_bln[col_key_asli].corr(pd.to_numeric(df_bln['RATA-RATA KESELURUHAN'], errors='coerce'))
                                    if pd.notna(mean_kinerja):
                                        histori_bulan.append(bln); histori_kinerja.append(mean_kinerja); histori_kepentingan.append(corr_kepentingan if pd.notna(corr_kepentingan) else 0.5)
                            
                            if len(histori_bulan) >= 2:
                                df_histori_plot = pd.DataFrame({'Bulan': histori_bulan, 'Kinerja': histori_kinerja, 'Kepentingan': histori_kepentingan})
                                fig_track = px.line(df_histori_plot, x='Kinerja', y='Kepentingan', text='Bulan', markers=True, title=f"Rekam Jejak Pergeseran Posisi Kuadran: {indikator_dipilih}")
                                fig_track.update_traces(textposition='top center', line=dict(width=3, color='#ffc107'), marker=dict(size=10, color='#005b9f'))
                                fig_track.add_vline(x=4.5, line_dash="dash", line_color="#FFC000")
                                fig_track.add_hline(y=df_histori_plot['Kepentingan'].mean(), line_dash="dash", line_color="#FFC000")
                                fig_track.update_layout(height=450, xaxis_range=[3.8, 5.1], xaxis_title="Kinerja (Skor Kepuasan)", yaxis_title="Kepentingan (Korelasi)")
                                st.plotly_chart(fig_track, use_container_width=True)
                                
                                st.markdown("#### 📝 Log Evaluasi & Efektivitas Tindak Lanjut")
                                b_awal, b_akhir = histori_bulan[0], histori_bulan[-1]
                                k_awal, k_akhir = histori_kinerja[0], histori_kinerja[-1]
                                selisih = k_akhir - k_awal
                                status_efektivitas = "🟢 BERHASIL (Skor Naik)" if selisih > 0 else "🔴 BELUM EFEKTIF (Skor Stagnan/Turun)"
                                if abs(selisih) < 0.05: status_efektivitas = "🟡 BERTAHAN (Perubahan Minimal)"
                                
                                col_t1, col_t2, col_t3 = st.columns(3)
                                col_t1.metric(f"Skor Awal ({b_awal})", f"{k_awal:.2f}")
                                col_t2.metric(f"Skor Akhir ({b_akhir})", f"{k_akhir:.2f}", delta=f"{selisih:+.2f}")
                                col_t3.metric("Kesimpulan Dampak", "Efektif" if selisih > 0 else "Evaluasi Ulang", delta=status_efektivitas, delta_color="normal" if selisih > 0 else "inverse")
                            else:
                                st.info("ℹ️ Data histori bulanan belum mencukupi.")
                        except Exception as e:
                            st.error(f"Gagal memuat visualisasi histori: {e}")
                    else:
                        st.warning("⚠️ Data terlalu sedikit untuk memproses Analisis Kuadran (IPA).")
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
                    fig_box = px.box(df_comp, x=var_grup, y=var_skor, color=var_grup, points="all", title=f"Distribusi {var_skor} berdasarkan {var_grup}")
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
                        if p_value < 0.05: st.success(f"Terdapat **PERBEDAAN SIGNIFIKAN** pada {var_skor} antar kelompok.")
                        else: st.info(f"**TIDAK ADA PERBEDAAN SIGNIFIKAN** pada {var_skor} antar kelompok.")
            else:
                st.warning("⚠️ Tidak ada data. Sesuaikan filter.")

        # ---------------------------------------------------------
        # KONTEN: 📊 DASHBOARD
        # ---------------------------------------------------------
        elif menu_selection == "📊 DASHBOARD":
            df_filtered_dash = build_filters("dashboard")
            st.markdown("---")
            if not df_filtered_dash.empty:
                skor_evaluasi = df_filtered_dash['RATA-RATA KESELURUHAN'].mean()
                ind_kurang    = df_filtered_dash['Jumlah Indikator dibawah 4.5'].sum() if 'Jumlah Indikator dibawah 4.5' in df_filtered_dash.columns else 0
                ind_lebih     = df_filtered_dash['Jumlah Indikator diatas 4.5'].sum()  if 'Jumlah Indikator diatas 4.5'  in df_filtered_dash.columns else 0

                col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
                with col_kpi1: st.metric("🌟 Skor Evaluasi L1",  f"{skor_evaluasi:.2f}" if pd.notna(skor_evaluasi) else "N/A")
                with col_kpi2: st.metric("⚠️ Indikator < 4.5",  int(ind_kurang))
                with col_kpi3: st.metric("✅ Indikator ≥ 4.5",  int(ind_lebih))
                st.markdown("---")

                col_chart_l, col_chart_r = st.columns([3, 2])
                with col_chart_l:
                    st.markdown("#### 📈 Skor L1 per Strategi Pelaksanaan")
                    df_grafik = df_filtered_dash.groupby('Strategi Pelaksanaan')['RATA-RATA KESELURUHAN'].mean().reset_index()
                    fig = px.bar(df_grafik, x='Strategi Pelaksanaan', y='RATA-RATA KESELURUHAN', text='RATA-RATA KESELURUHAN', color_discrete_sequence=['#005b9f'])
                    fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
                    fig.add_hline(y=4.5, line_dash="dash", line_color="#FFC000", annotation_text="Standar TMP (4.5)", annotation_position="top left")
                    fig.update_layout(height=350, bargap=0.5, yaxis_range=[0,5], yaxis_title="Rata-rata Skor", xaxis_title="", margin=dict(t=40,b=0,l=0,r=0))
                    st.plotly_chart(fig, use_container_width=True)

                with col_chart_r:
                    st.markdown("#### 🕸️ Radar — Rata-rata Kategori")
                    kategori_radar = {
                        'Eng. Instruktur':'Engagement Instruktur','Rel. Instruktur':'Relevance Instruktur',
                        'Sat. Instruktur':'Satisfaction Instruktur','Eng. Materi':'Engagement Materi',
                        'Rel. Materi':'Relevance Materi','Sat. Materi':'Satisfaction Materi',
                        'Sarana Digital':'Satisfaction Sarana Digital','Sarana In-Class':'Satisfaction Sarana In Class',
                    }
                    labels = [k for k,v in kategori_radar.items() if v in df_filtered_dash.columns]
                    values = [df_filtered_dash[kategori_radar[k]].mean() for k in labels]
                    if labels:
                        fig_radar = go.Figure(go.Scatterpolar(r=values+[values[0]], theta=labels+[labels[0]], fill='toself', fillcolor='rgba(0,85,164,0.15)', line=dict(color='#0055A4',width=2)))
                        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True,range=[0,5])), showlegend=False, height=350, margin=dict(t=30,b=30,l=30,r=30))
                        st.plotly_chart(fig_radar, use_container_width=True)

                st.markdown("---")
                if 'Laporan Bulan' in df_filtered_dash.columns:
                    st.markdown("#### 📆 Tren Skor L1 per Bulan")
                    URUTAN = ['Januari','Februari','Maret','April','Mei','Juni','Juli','Agustus','September','Oktober','November','Desember']
                    df_tren = df_filtered_dash.groupby('Laporan Bulan')['RATA-RATA KESELURUHAN'].mean().reset_index()
                    df_tren['sort_key'] = df_tren['Laporan Bulan'].apply(lambda x: URUTAN.index(x) if x in URUTAN else 99)
                    df_tren = df_tren.sort_values('sort_key')
                    fig_tren = px.line(df_tren, x='Laporan Bulan', y='RATA-RATA KESELURUHAN', markers=True, color_discrete_sequence=['#0055A4'])
                    fig_tren.add_hline(y=4.5, line_dash="dash", line_color="#FFC000", annotation_text="Standar 4.5", annotation_position="top left")
                    fig_tren.update_layout(yaxis_range=[0,5], height=300, yaxis_title="Rata-rata Skor", xaxis_title="")
                    st.plotly_chart(fig_tren, use_container_width=True)

                with st.expander(f"📄 Tabel Data Lengkap ({len(df_filtered_dash)} baris)", expanded=False):
                    st.dataframe(df_filtered_dash, use_container_width=True)
            else:
                st.warning("⚠️ Tidak ada data. Sesuaikan filter.")

    except Exception as e:
        st.error(f"Gagal memuat data: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# KONTEN: 🤖 AI ASSISTANT
# ══════════════════════════════════════════════════════════════════════════════
elif menu_selection == "🤖 AI ASSISTANT":
    st.subheader("🤖 Tanya Asisten EVALYTICS")
    st.write("Gunakan AI untuk menganalisis tren atau meminta saran perbaikan berdasarkan data yang sedang difilter.")

    if "chat_history" not in st.session_state: st.session_state.chat_history = []
    for chat in st.session_state.chat_history:
        with st.chat_message(chat["role"]): st.markdown(chat["content"])

    user_question = st.chat_input("Tanya sesuatu tentang data evaluasi Anda...")
    if user_question:
        st.session_state.chat_history.append({"role": "user", "content": user_question})
        with st.chat_message("user"): st.markdown(user_question)
        with st.chat_message("assistant"):
            with st.spinner("Gemini sedang berpikir..."):
                try:
                    df_ctx = pd.read_csv(url)
                    context = f"Data evaluasi UPDL Jakarta. Total: {len(df_ctx)} baris. Ringkasan: {df_ctx.describe().to_string()}"
                    full_prompt = f"Konteks:\n{context}\n\nPertanyaan: {user_question}\n\nJawab ringkas, profesional, Bahasa Indonesia."
                    if model:
                        response = model.generate_content(full_prompt)
                        st.markdown(response.text)
                        st.session_state.chat_history.append({"role": "assistant", "content": response.text})
                    else:
                        st.error("API Key Gemini belum diatur.")
                except Exception as ai_err:
                    st.error(f"Gagal AI: {ai_err}")

# ══════════════════════════════════════════════════════════════════════════════
# KONTEN: 📤 DATA ENTRY
# ══════════════════════════════════════════════════════════════════════════════
elif menu_selection == "📤 DATA ENTRY":
    st.markdown("""
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">
        <i class="material-icons" style="font-size:30px;color:#0055A4;">cloud_upload</i>
        <div>
            <h2 style="margin:0;color:#003366;">Upload File Evaluasi</h2>
            <p style="margin:0;color:#8a8a8a;font-size:0.9em;">Gabungkan L1, L2, SMILE, dan Instruktur secara Otomatis</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📖 Panduan Cepat (3 Jalur Data)", expanded=True):
        col_g1, col_g2, col_g3 = st.columns(3)
        with col_g1: st.markdown("🔵 **L1 + L2 (Lama)** ➡️ Sheet **L1 Tertutup**\nGabungan Evaluasi Reaksi & L2 HXMS")
        with col_g2: st.markdown("🟣 **L1 + SMILE** ➡️ Sheet **Master Data Laporan**\nData terpadu 2 Kunci Pas untuk Dashboard")
        with col_g3: st.markdown("🟠 **Instruktur** ➡️ Sheet **Detail Instruktur**\nData Penilaian & Jam Terbang Pengajar")

    sub_upload, sub_riwayat, sub_panduan = st.tabs(["📤 Upload & Kirim", "🕒 Riwayat", "📄 Panduan Format"])

    with sub_upload:
        with st.container(border=True):
            st.info("💡 **Tips:** Untuk hasil terbaik, letakkan seluruh file (L1, SMILE, L2, Instruktur) secara bersamaan ke dalam kotak di bawah ini.")
            uploaded_files = st.file_uploader(
                "Pilih atau seret file Excel/CSV",
                type=["xlsx","csv", "xls"], accept_multiple_files=True, key="entry_uploader"
            )

        if uploaded_files:
            all_l1_dfs, all_l2_dfs, all_smile_dfs, all_ins_dfs, file_log = [], [], [], [], []

            with st.status("🔍 Membaca dan memetakan jalur file...", expanded=True) as status_proc:
                for f in uploaded_files:
                    try:
                        if f.name.endswith('.csv'): df_raw = pd.read_csv(f)
                        else: df_raw = pd.read_excel(f)
                        df_raw.columns = df_raw.columns.astype(str).str.strip()

                        # Identifikasi Jalur File
                        is_smile = ('Kode Service Request' in df_raw.columns or 'Peserta Diundang' in df_raw.columns)
                        is_l2 = ('Confidence Level' in df_raw.columns and not is_smile)
                        is_instruktur = ('Nama' in df_raw.columns and 'Kode Diklat' in df_raw.columns and 'Confidence Level' not in df_raw.columns)
                        is_l1 = ('Ins-Eng-1 of 2' in df_raw.columns and not is_instruktur)

                        # --- JALUR L1 ---
                        if is_l1:
                            detect_and_show_column_mismatch(df_raw, INS_COL_NAMES, f.name, "INS")
                            detect_and_show_column_mismatch(df_raw, MAT_COL_NAMES, f.name, "MAT")
                            df_mapped = pd.DataFrame(index=df_raw.index, columns=TARGET_COLUMNS)
                            df_mapped['Kode Pembelajaran']       = df_raw.get('Kode Judul')
                            df_mapped['Judul Pembelajaran/Kegiatan'] = df_raw.get('Judul Pembelajaran')
                            df_mapped['Batch']                   = df_raw.get('Angkatan')
                            df_mapped['Tanggal Mulai']           = df_raw.get('Tgl Mulai')
                            df_mapped['Tanggal Selesai']         = df_raw.get('Tgl Selesai')
                            df_mapped['Strategi Pelaksanaan']    = df_raw.get('Strategi Pelaksana')
                            df_mapped['Peserta Isi L1']          = df_raw.get('P.Isi')
                            df_mapped['Peserta Hadir']           = df_raw.get('P.Hadir')
                            df_mapped['PIC KI']                  = df_raw.get('Bidang')
                            
                            for i, c in enumerate(INS_COL_NAMES, 1): df_mapped[f'INS{i}'] = df_raw.get(c)
                            for i, c in enumerate(MAT_COL_NAMES, 1): df_mapped[f'MAT{i}'] = df_raw.get(c)
                            for i, c in enumerate(SP_COL_NAMES,  1): df_mapped[f'SP{i}']  = df_raw.get(c)
                            for i, c in enumerate(DS_COL_NAMES,  1): df_mapped[f'DS{i}']  = df_raw.get(c)
                            
                            # Kunci Pas PENGHUBUNG
                            kd_pemb = df_mapped['Kode Pembelajaran'].astype(str).str.replace(' ', '', regex=False).str.upper()
                            tgl_mulai = pd.to_datetime(df_mapped['Tanggal Mulai'],errors='coerce').dt.strftime('%Y%m%d').fillna('NOTGL')
                            df_mapped['Kode Unik'] = kd_pemb + "." + tgl_mulai
                            
                            all_l1_dfs.append(df_mapped)
                            file_log.append({"File":f.name,"Tipe":"🔵 Evaluasi L1","Baris":len(df_raw)})
                            st.session_state.riwayat_upload.append({"nama":f.name,"waktu":datetime.now().strftime("%d/%m/%Y %H:%M"),"tipe":"L1","baris":len(df_raw)})

                        # --- JALUR SMILE ---
                        elif is_smile:
                            df_smile = df_raw.copy()
                            kd_pemb_s = df_smile.get('Kode Pembelajaran', pd.Series(dtype=str)).astype(str).str.replace(' ', '', regex=False).str.upper()
                            tgl_mulai_s = pd.to_datetime(df_smile.get('Tgl Mulai', pd.Series()), errors='coerce').dt.strftime('%Y%m%d').fillna('NOTGL')
                            df_smile['Kode Unik'] = kd_pemb_s + "." + tgl_mulai_s
                            
                            all_smile_dfs.append(df_smile)
                            file_log.append({"File":f.name,"Tipe":"🟣 SMILE","Baris":len(df_raw)})
                            st.session_state.riwayat_upload.append({"nama":f.name,"waktu":datetime.now().strftime("%d/%m/%Y %H:%M"),"tipe":"SMILE","baris":len(df_raw)})

                        # --- JALUR L2 ---
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
                            
                            kd_pemb = df_mapped['Kode Pembelajaran'].astype(str).str.replace(' ', '', regex=False).str.upper()
                            tgl_mulai = pd.to_datetime(df_mapped['Tanggal Mulai'],errors='coerce').dt.strftime('%Y%m%d').fillna('NOTGL')
                            df_mapped['Kode Unik'] = kd_pemb + "." + tgl_mulai
                            
                            all_l2_dfs.append(df_mapped)
                            file_log.append({"File":f.name,"Tipe":"🟢 L2 HXMS","Baris":len(df_raw)})
                            st.session_state.riwayat_upload.append({"nama":f.name,"waktu":datetime.now().strftime("%d/%m/%Y %H:%M"),"tipe":"L2","baris":len(df_raw)})

                        # --- JALUR INSTRUKTUR ---
                        elif is_instruktur:
                            df_raw = df_raw[~df_raw['Nama'].astype(str).str.strip().str.upper().isin(['UPDL JAKARTA','JAKARTA'])].reset_index(drop=True)
                            df_ins = build_instruktur_df(df_raw) 
                            all_ins_dfs.append(df_ins)
                            file_log.append({"File":f.name,"Tipe":"🟠 Instruktur","Baris":len(df_raw)})
                            st.session_state.riwayat_upload.append({"nama":f.name,"waktu":datetime.now().strftime("%d/%m/%Y %H:%M"),"tipe":"Instruktur","baris":len(df_raw)})
                        
                        else:
                            st.error(f"❌ **{f.name}** tidak dikenali formatnya.")

                    except Exception as e_file:
                        st.error(f"Gagal memproses file {f.name}: {e_file}")

                status_proc.update(label="✅ Selesai memetakan jalur file!", state="complete", expanded=False)

            has_l1l2 = bool(all_l1_dfs or all_l2_dfs)
            has_smile_pipe = bool(all_smile_dfs)
            has_ins = bool(all_ins_dfs)

            if not has_l1l2 and not has_smile_pipe and not has_ins:
                st.stop()

            st.markdown("### 📋 Ringkasan File")
            st.dataframe(pd.DataFrame(file_log), use_container_width=True, hide_index=True)

            # ==========================================================
            # PIPELINE 1: L1 + L2 -> L1 TERTUTUP
            # ==========================================================
            df_l1_l2_push = pd.DataFrame()
            if has_l1l2:
                df_l1 = pd.concat(all_l1_dfs, ignore_index=True) if all_l1_dfs else pd.DataFrame(columns=TARGET_COLUMNS)
                if all_l2_dfs:
                    df_l2_raw  = pd.concat(all_l2_dfs, ignore_index=True)
                    l2_cols_av = [c for c in L2_MERGE_COLS if c in df_l2_raw.columns]
                    df_l2_slim = df_l2_raw[l2_cols_av].groupby('Kode Unik', as_index=False).first()
                    
                    if not df_l1.empty:
                        df_l1_l2_push = df_l1.merge(df_l2_slim, on='Kode Unik', how='left', suffixes=('','_l2'))
                        for col in [c for c in L2_MERGE_COLS if c != 'Kode Unik']:
                            col_l2 = col+'_l2'
                            if col_l2 in df_l1_l2_push.columns:
                                df_l1_l2_push[col] = df_l1_l2_push[col].combine_first(df_l1_l2_push[col_l2])
                                df_l1_l2_push.drop(columns=[col_l2], inplace=True)
                    else:
                        df_l1_l2_push = df_l2_raw.copy()
                else:
                    df_l1_l2_push = df_l1.copy()

                df_l1_l2_push = df_l1_l2_push.reindex(columns=TARGET_COLUMNS)
                
                df_l1_l2_push['Tanggal Selesai'] = pd.to_datetime(df_l1_l2_push['Tanggal Selesai'], errors='coerce')
                df_l1_l2_push['Tanggal Mulai']   = pd.to_datetime(df_l1_l2_push['Tanggal Mulai'],   errors='coerce')
                df_l1_l2_push['Cut off Data']    = df_l1_l2_push['Tanggal Selesai'] + pd.Timedelta(days=st.session_state["setting_cutoff"])
                df_l1_l2_push['Laporan Bulan']   = df_l1_l2_push['Cut off Data'].dt.month.map(BULAN_MAP_ID)
                today = pd.Timestamp.today().normalize()
                df_l1_l2_push['Status Pembelajaran'] = df_l1_l2_push['Tanggal Selesai'].apply(
                    lambda x: "Terlaksana" if pd.notna(x) and x<=today else ("Belum Terlaksana" if pd.notna(x) else ""))
                
                for col in ['Peserta Isi L1','Peserta Hadir','Jumlah Peserta Lulus L2','Jumlah Peserta Isi L2','Nilai Confidence','Nilai Commitment']:
                    df_l1_l2_push[col] = pd.to_numeric(df_l1_l2_push[col], errors='coerce')
                
                df_l1_l2_push['% Pengisian'] = safe_divide(df_l1_l2_push['Peserta Isi L1'], df_l1_l2_push['Peserta Hadir'])
                df_l1_l2_push['% Valid'] = df_l1_l2_push['% Pengisian'].apply(
                    lambda x: "VALID" if pd.notna(x) and x>st.session_state["setting_threshold"] else ("TIDAK VALID" if pd.notna(x) else ""))
                df_l1_l2_push['% Pengisian L2'] = safe_divide(df_l1_l2_push['Jumlah Peserta Isi L2'], df_l1_l2_push['Jumlah Peserta Lulus L2'])
                
                all_indicators = [f'INS{i}' for i in range(1,10)] + [f'MAT{i}' for i in range(1,8)] + [f'SP{i}' for i in range(1,7)] + [f'DS{i}' for i in range(1,7)]
                for col in all_indicators:
                    df_l1_l2_push[col] = pd.to_numeric(df_l1_l2_push[col], errors='coerce')
                
                df_l1_l2_push['RATA INST'] = df_l1_l2_push[[f'INS{i}' for i in range(1,9)]].mean(axis=1)
                df_l1_l2_push['RATA MAT']  = df_l1_l2_push[[f'MAT{i}' for i in range(1,7)]].mean(axis=1)
                df_l1_l2_push['RATA SP']   = df_l1_l2_push[[f'SP{i}'  for i in range(1,6)]].mean(axis=1)
                df_l1_l2_push['RATA DS']   = df_l1_l2_push[[f'DS{i}'  for i in range(1,6)]].mean(axis=1)
                df_l1_l2_push['RATA-RATA KESELURUHAN'] = df_l1_l2_push[['RATA INST','RATA MAT','RATA SP','RATA DS']].mean(axis=1)
                
                df_l1_l2_push['Jumlah Indikator dibawah 4.5'] = (df_l1_l2_push[all_indicators] < 4.5).sum(axis=1)
                df_l1_l2_push['Jumlah Indikator diatas 4.5']  = (df_l1_l2_push[all_indicators] >= 4.5).sum(axis=1)
                df_l1_l2_push.replace([np.inf, -np.inf], np.nan, inplace=True)

            # ==========================================================
            # PIPELINE 2: L1 + SMILE -> MASTER DATA LAPORAN
            # ==========================================================
            df_master_push = pd.DataFrame()
            if has_smile_pipe:
                df_smile_raw = pd.concat(all_smile_dfs, ignore_index=True)
                
                if all_l1_dfs:
                    df_l1_for_smile = pd.concat(all_l1_dfs, ignore_index=True)
                    all_indicators_sm = [f'INS{i}' for i in range(1,10)] + [f'MAT{i}' for i in range(1,8)] + [f'SP{i}' for i in range(1,7)] + [f'DS{i}' for i in range(1,7)]
                    
                    for col in all_indicators_sm:
                        df_l1_for_smile[col] = pd.to_numeric(df_l1_for_smile[col], errors='coerce')
                    df_l1_for_smile['RATA INST'] = df_l1_for_smile[[f'INS{i}' for i in range(1,9)]].mean(axis=1)
                    df_l1_for_smile['RATA MAT']  = df_l1_for_smile[[f'MAT{i}' for i in range(1,7)]].mean(axis=1)
                    df_l1_for_smile['RATA SP']   = df_l1_for_smile[[f'SP{i}'  for i in range(1,6)]].mean(axis=1)
                    df_l1_for_smile['RATA DS']   = df_l1_for_smile[[f'DS{i}'  for i in range(1,6)]].mean(axis=1)
                    df_l1_for_smile['RATA-RATA KESELURUHAN'] = df_l1_for_smile[['RATA INST','RATA MAT','RATA SP','RATA DS']].mean(axis=1)
                    df_l1_for_smile['Jumlah Indikator dibawah 4.5'] = (df_l1_for_smile[all_indicators_sm] < 4.5).sum(axis=1)
                    df_l1_for_smile['Jumlah Indikator diatas 4.5']  = (df_l1_for_smile[all_indicators_sm] >= 4.5).sum(axis=1)
                    
                    eval_cols_to_bring = [
                        'Kode Unik', 'Peserta Isi L1', 'RATA INST', 'RATA MAT', 'RATA SP', 'RATA DS', 
                        'RATA-RATA KESELURUHAN', 'Jumlah Indikator dibawah 4.5', 'Jumlah Indikator diatas 4.5'
                    ]
                    df_l1_slim = df_l1_for_smile[[c for c in eval_cols_to_bring if c in df_l1_for_smile.columns]].groupby('Kode Unik').first().reset_index()
                    df_master_push = df_smile_raw.merge(df_l1_slim, on='Kode Unik', how='left')
                else:
                    df_master_push = df_smile_raw.copy()

                df_master_push['Tgl Selesai'] = pd.to_datetime(df_master_push.get('Tgl Selesai', pd.Series()), errors='coerce')
                df_master_push['Cut off Data'] = df_master_push['Tgl Selesai'] + pd.Timedelta(days=st.session_state["setting_cutoff"])
                df_master_push['Laporan Bulan'] = df_master_push['Cut off Data'].dt.month.map(BULAN_MAP_ID)
                
                today = pd.Timestamp.today().normalize()
                df_master_push['Status Pembelajaran'] = df_master_push['Tgl Selesai'].apply(
                    lambda x: "Terlaksana" if pd.notna(x) and x<=today else "Belum Terlaksana"
                )
                
                df_master_push['Peserta Isi L1'] = pd.to_numeric(df_master_push.get('Peserta Isi L1', pd.Series()), errors='coerce')
                df_master_push['Peserta Hadir']  = pd.to_numeric(df_master_push.get('Peserta Hadir', pd.Series()), errors='coerce')
                df_master_push['% Pengisian L1'] = safe_divide(df_master_push['Peserta Isi L1'], df_master_push['Peserta Hadir'])
                df_master_push['% Valid L1'] = df_master_push['% Pengisian L1'].apply(
                    lambda x: "VALID" if pd.notna(x) and x > st.session_state["setting_threshold"] else "TIDAK VALID"
                )

                # PEMETAAN KOLOM TAMBAHAN UNTUK LAPORAN KELAS
                df_master_push['Tempat Pelaksanaan'] = df_smile_raw.get('Lokasi Pelaksanaan')
                df_master_push['Nomor Surat Pemanggilan Peserta'] = df_smile_raw.get('Nomor Surat Pemanggilan Peserta')
                df_master_push['Rencana Jumlah Peserta'] = df_smile_raw.get('Rencana Jumlah Peserta')
                df_master_push['Instruktur/ Fasilitator'] = df_smile_raw.get('Instruktur/ Fasilitator')
                df_master_push['Peserta Diundang'] = df_smile_raw.get('Peserta Diundang')
                df_master_push['% Kehadiran'] = df_smile_raw.get('% Kehadiran')
                df_master_push['% Kelulusan'] = df_smile_raw.get('% Kelulusan')

                df_master_push = df_master_push.reindex(columns=MASTER_TARGET_COLUMNS)

            # ==========================================================
            # PIPELINE 3: INSTRUKTUR -> DETAIL INSTRUKTUR
            # ==========================================================
            df_ins_push = pd.DataFrame()
            if has_ins:
                df_ins_push = pd.concat(all_ins_dfs, ignore_index=True)
                df_ins_push = df_ins_push.reindex(columns=DETAIL_INSTRUKTUR_COLUMNS)

            # ----------------------------------------------------------
            # TAMPILAN PREVIEW (AKORDEON)
            # ----------------------------------------------------------
            if has_smile_pipe:
                with st.expander(f"🟣 PREVIEW: MASTER DATA LAPORAN (L1 + SMILE) | {len(df_master_push)} Baris", expanded=True):
                    st.dataframe(df_master_push.fillna(""), use_container_width=True)
            if has_l1l2:
                with st.expander(f"🔵 PREVIEW: L1 TERTUTUP (L1 + L2) | {len(df_l1_l2_push)} Baris", expanded=False):
                    st.dataframe(df_l1_l2_push.fillna(""), use_container_width=True)
            if has_ins:
                with st.expander(f"🟠 PREVIEW: DETAIL INSTRUKTUR | {len(df_ins_push)} Baris", expanded=False):
                    st.dataframe(df_ins_push.fillna(""), use_container_width=True)

            st.markdown("---")
            sheet_name_setting = st.session_state["setting_sheet"]
            ws_l1_target = st.session_state["setting_worksheet"]
            ws_master_target = st.session_state["setting_ws_master"]
            ws_ins_target = st.session_state["setting_ws_instruktur"]

            col_info, col_btn = st.columns([2, 1])
            with col_info:
                st.info(f"Target Penyimpanan Google Sheets Utama: **{sheet_name_setting}**")
            
            with col_btn:
                if st.button("🚀 KIRIM SEMUA KE GOOGLE SHEETS", use_container_width=True, type="primary"):
                    with st.spinner("Mengirim data melalui jalur masing-masing ke brankas utama..."):
                        try:
                            client = init_gsheets_connection()
                            gsheet_file = client.open(sheet_name_setting)

                            # Push Master Data (SMILE + L1)
                            if has_smile_pipe:
                                sht_master = gsheet_file.worksheet(ws_master_target)
                                max_no = get_sheet_max_no(sht_master)
                                df_master_push['No'] = range(max_no+1, max_no+1+len(df_master_push))
                                rows_master = [clean_row_for_sheets(r) for r in df_master_push.values.tolist()]
                                # TAMBAHKAN table_range='A1' DI SINI 👇
                                sht_master.append_rows(rows_master, value_input_option='USER_ENTERED', table_range='A1')
                                st.success(f"🟣 Berhasil mengirim {len(rows_master)} baris ke Tab **{ws_master_target}**")

                            # Push L1 Tertutup (L1 + L2)
                            if has_l1l2:
                                sht_l1 = gsheet_file.worksheet(ws_l1_target)
                                max_no = get_sheet_max_no(sht_l1)
                                df_l1_l2_push['No'] = range(max_no+1, max_no+1+len(df_l1_l2_push))
                                rows_l1 = [clean_row_for_sheets(r) for r in df_l1_l2_push.values.tolist()]
                                # TAMBAHKAN table_range='A1' DI SINI 👇
                                sht_l1.append_rows(rows_l1, value_input_option='USER_ENTERED', table_range='A1')
                                st.success(f"🔵 Berhasil mengirim {len(rows_l1)} baris ke Tab **{ws_l1_target}**")

                            # Push Instruktur
                            if has_ins:
                                sht_ins = gsheet_file.worksheet(ws_ins_target)
                                rows_ins = [clean_row_for_sheets(r) for r in df_ins_push.values.tolist()]
                                # TAMBAHKAN table_range='A1' DI SINI 👇
                                sht_ins.append_rows(rows_ins, value_input_option='USER_ENTERED', table_range='A1')
                                st.success(f"🟠 Berhasil mengirim {len(rows_ins)} baris ke Tab **{ws_ins_target}**")

                            st.balloons()
                        except Exception as e_push:
                            st.error(f"Gagal mengirim ke Google Sheets. Pastikan nama tab benar. Error: {e_push}")

    with sub_riwayat:
        if not st.session_state.riwayat_upload:
            st.info("Belum ada riwayat upload.")
        else:
            for item in reversed(st.session_state.riwayat_upload):
                badge_color = {"L1":"#0055A4","L2":"#1a7a2e", "SMILE":"#8e24aa", "Instruktur":"#b35900"}.get(item['tipe'],"#666")
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:10px;padding:10px 0;border-bottom:1px solid #eee;">
                    <div style="flex:1;">
                        <p style="margin:0;font-weight:bold;">{item['nama']}</p>
                        <p style="margin:0;font-size:0.8em;color:#8a8a8a;">{item['waktu']} • {item['baris']} baris</p>
                    </div>
                    <span style="background:{badge_color}20;color:{badge_color};border:1px solid {badge_color}55;
                    padding:2px 10px;border-radius:20px;font-size:0.75em;font-weight:bold;">{item['tipe']}</span>
                </div>""", unsafe_allow_html=True)

    with sub_panduan:
        with st.expander("📖 File L1 — Evaluasi Reaksi", expanded=True):
            st.markdown("- Wajib ada kolom `Ins-Eng-1 of 2`\n- Kolom penting: `Kode Judul`, `Judul Pembelajaran`, `Angkatan`, `Tgl Mulai`, `Tgl Selesai`, `Strategi Pelaksana`, `P.Isi`, `P.Hadir`, `Bidang`")
        with st.expander("📖 File L2 — Evaluasi Pembelajaran (Legacy)", expanded=True):
            st.markdown("- Wajib ada kolom `Confidence Level` (tanpa `Ins-Eng-1 of 2`)\n- Kolom penting: `Kode Judul`, `Judul`, `Angkatan`, `Tgl Mulai`, `Tgl Selesai`, `Jumlah Peserta Hadir/Lulus/Isi`, `Commitment Level`")
        with st.expander("📖 File SMILE — Laporan Pelaksanaan (Baru)", expanded=True):
            st.markdown("- Wajib ada kolom `Kode Service Request` atau `Peserta Diundang`\n- Kolom penting: `Kode Pembelajaran`, `Judul Pembelajaran`, `Batch`, `Tgl Mulai`, `Tgl Selesai`, `Peserta Hadir`, `Peserta Lulus`")
        with st.expander("📖 File Instruktur — Detail Instruktur", expanded=True):
            st.markdown("- Wajib ada kolom `Nama` **DAN** `Kode Diklat`\n- Kolom skor: `Ins-Eng-1 of 2`, `Ins-Eng-2 of 2`, `Ins-Rel-1 of 2`, `Ins-Rel-2 of 2`, `Ins-Sat-1 of 4` s.d. `Ins-Sat-4 of 4`, `Ins-Rat`")

# ══════════════════════════════════════════════════════════════════════════════
# KONTEN: 🚨 EARLY WARNING
# ══════════════════════════════════════════════════════════════════════════════
elif menu_selection == "🚨 EARLY WARNING":
    st.markdown("### 🚨 Sentiment Analysis (Deteksi Keluhan Otomatis)")
    st.write("Sistem melihat komentar peserta secara *real-time* dari Google Sheets menggunakan **Open-Source Sentiment Lexicon**.")
    try:
        sheet_id_komentar = '1IDAmFwTbBQDZcKM3eiiEDcA3KwM9WKqW4zCrk__6-PU'
        sheet_name_komentar = 'Detail%20Komentar%20L1' 
        url_komentar = "https://docs.google.com/spreadsheets/d/" + str(sheet_id_komentar) + "/gviz/tq?tqx=out:csv&sheet=" + str(sheet_name_komentar)
        
        @st.cache_data(ttl=300)
        def load_csv_komentar(url): return pd.read_csv(url)
        
        df_komentar = load_csv_komentar(url_komentar)
        
        if not df_komentar.empty:
            st.success(f"✅ Berhasil memuat **{len(df_komentar)} baris komentar** dari sheet 'Detail Komentar L1'.")
            col_setup1, col_wa_setup2 = st.columns(2)
            with col_setup1: kolom_teks = st.selectbox("🎯 Pilih Kolom Komentar/Saran Peserta:", df_komentar.columns.tolist(), key="teks_sentimen")
            with col_wa_setup2:
                opsi_kolom = df_komentar.columns.tolist()
                idx_bulan = 0
                for kandidat in ['Laporan Bulan', 'Bulan', 'bulan', 'LAPORAN BULAN']:
                    if kandidat in opsi_kolom: idx_bulan = opsi_kolom.index(kandidat); break
                kolom_bulan = st.selectbox("📅 Pilih Kolom Bulan:", opsi_kolom, index=idx_bulan, key="bulan_kol_sentimen")
            
            opsi_bulan_tersedia = list(df_komentar[kolom_bulan].dropna().unique())
            filter_bulan_sentimen = st.multiselect("🎛️ Filter Berdasarkan Bulan Laporan:", options=opsi_bulan_tersedia, default=opsi_bulan_tersedia, key="filter_bulan_sentimen")
            
            if kolom_teks and filter_bulan_sentimen:
                with st.spinner("Sistem sedang memfilter dan menganalisis sentimen komentar..."):
                    df_analisis = df_komentar[df_komentar[kolom_bulan].isin(filter_bulan_sentimen)].copy()
                    if not df_analisis.empty:
                        df_analisis['Sentimen'] = df_analisis[kolom_teks].apply(analisis_sentimen_opensource)
                        df_keluhan = df_analisis[df_analisis['Sentimen'] == 'Negatif']
                        st.markdown("---")
                        
                        if not df_keluhan.empty:
                            st.error(f"⚠️ **AWAS!** Ditemukan **{len(df_keluhan)} keluhan (Sentimen Negatif)** pada bulan terpilih!")
                            kolom_tampil = [kolom_teks, 'Sentimen'] 
                            for col in ['Judul Pembelajaran/Kegiatan', 'Kode Unik', 'Nama Pelatihan', kolom_bulan]:
                                if col in df_analisis.columns and col not in kolom_tampil: kolom_tampil.insert(0, col)
                            st.dataframe(df_keluhan[kolom_tampil], use_container_width=True)
                            
                            st.markdown("#### 🚀 Eskalasi Tindak Lanjut Otomatis")
                            col_wa1, col_wa2 = st.columns(2)
                            with col_wa1:
                                if st.button("📱 Kirim Peringatan ke WhatsApp PIC Sarpras", use_container_width=True): st.success("✅ [SIMULASI] Peringatan otomatis berhasil dikirim ke WhatsApp PIC Sarana & Prasarana!"); st.balloons()
                            with col_wa2:
                                if st.button("📧 Kirim Peringatan ke Email Evaluator", use_container_width=True): st.success("✅ [SIMULASI] Email rekap keluhan otomatis telah diteruskan ke Tim Evaluator!")
                        else:
                            st.success("🎉 **Luar Biasa!** Tidak ditemukan sentimen negatif (keluhan) pada bulan yang dipilih. Semua berjalan prima.")
                            
                        st.markdown("---")
                        st.markdown("#### 📊 Ringkasan Proporsi Sentimen Komentar (Periode Terpilih)")
                        ringkasan_sentimen = df_analisis['Sentimen'].value_counts().reset_index()
                        ringkasan_sentimen.columns = ['Kategori Sentimen', 'Jumlah']
                        fig_pie = px.pie(ringkasan_sentimen, values='Jumlah', names='Kategori Sentimen', color='Kategori Sentimen', color_discrete_map={'Positif':'#2e7d32', 'Netral':'#9e9e9e', 'Negatif':'#d32f2f'}, hole=0.45)
                        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                        fig_pie.update_layout(height=400, showlegend=False, margin=dict(t=10,b=10,l=10,r=10))
                        
                        col_pie1, col_pie2 = st.columns([1, 1])
                        with col_pie1: st.plotly_chart(fig_pie, use_container_width=True)
                        with col_pie2: st.markdown("<br><br>", unsafe_allow_html=True); st.write("Donut Chart di samping menampilkan rangkuman sentimen dari bulan yang Anda centang pada filter di atas.")
                    else: st.warning("⚠️ Tidak ada data komentar pada bulan yang dipilih.")
            else: st.warning("💡 Silakan pilih minimal satu bulan pada filter di atas untuk memulai analisis.")
        else: st.warning("⚠️ Sheet 'Detail Komentar L1' berhasil diakses, namun datanya kosong.")
    except Exception as e: st.error(f"❌ Gagal memuat data dari Sheet 'Detail Komentar L1'. Detail error: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# KONTEN: 📑 REPORT & KATALOG
# ══════════════════════════════════════════════════════════════════════════════
elif menu_selection == "📑 REPORT & KATALOG":
    sub_rep_generator, sub_lap_pembelajaran, sub_katalog = st.tabs(["📑 Report Generator", "📄 Laporan Pembelajaran", "👨‍🏫 Katalog Instruktur"])
    
    # ─────────────────────────────────────────────────────────────────────────
    # --- SUB TAB 1: REPORT GENERATOR ---
    # ─────────────────────────────────────────────────────────────────────────
    with sub_rep_generator:
        st.markdown("### 📑 Generator Laporan Manajemen Mutu (Executive Edition)")
        st.write("Menyusun laporan evaluasi mutu komprehensif berstandar konsultan (McKinsey/PwC style) lengkap dengan AI Executive Summary, Scorecard Pilar, Visual Matriks IPA, Voice of Customer, dan Tabel Rencana Tindak Lanjut Preskriptif dari Gemini AI.")
        
        try:
            url_rep = "https://docs.google.com/spreadsheets/d/" + str(sheet_id) + "/gviz/tq?tqx=out:csv&sheet=L1%20Tertutup"
            req_rep = urllib.request.Request(url_rep, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req_rep) as response:
                csv_bytes = response.read()
            df_rep_raw = pd.read_csv(io.BytesIO(csv_bytes))
            
            df_rep_raw.columns = df_rep_raw.columns.astype(str).str.strip()
            
            # Pelacakan nama kolom otomatis (kebal terhadap spasi berlebih)
            kolom_ditemukan = None
            for col in df_rep_raw.columns:
                if 'laporan bulan' in col.lower() or 'bulan' in col.lower():
                    kolom_ditemukan = col
                    break
            
            if not kolom_ditemukan:
                st.error(f"⚠️ Kolom periode bulan gagal terdeteksi! Kolom yang tersedia saat ini: {', '.join(df_rep_raw.columns.tolist()[:10])}...")
                st.stop()
                
            if kolom_ditemukan != 'Laporan Bulan':
                df_rep_raw.rename(columns={kolom_ditemukan: 'Laporan Bulan'}, inplace=True)
            
            URUTAN_BULAN_STD = [
                'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
                'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
            ]
            
            bulan_di_data = df_rep_raw['Laporan Bulan'].dropna().unique().tolist()
            opsi_bulan_rep = [b for b in URUTAN_BULAN_STD if b in bulan_di_data]
            sisa_bulan = [b for b in bulan_di_data if b not in URUTAN_BULAN_STD and b not in ['nan', 'None', '', 'Laporan Bulan']]
            opsi_bulan_rep.extend(sisa_bulan)
            
            if opsi_bulan_rep:
                with st.container(border=True):
                    col_r1, col_r2 = st.columns([2, 1])
                    with col_r1:
                        bulan_pilih = st.selectbox("📅 Pilih Periode Laporan:", opsi_bulan_rep, key="bln_report")
                    with col_r2:
                        st.markdown("<br>", unsafe_allow_html=True)
                        btn_generate = st.button("🚀 Generate Laporan Eksekutif", type="primary", use_container_width=True)
                
                if btn_generate:
                    with st.spinner(f"Menyusun analisis data, visualisasi IPA, & merumuskan tindak lanjut AI untuk periode {bulan_pilih}..."):
                        df_bln = df_rep_raw[df_rep_raw['Laporan Bulan'].str.lower() == str(bulan_pilih).strip().lower()].copy()
                        total_sesi = len(df_bln)
                        
                        semua_butir = [f'INS{i}' for i in range(1, 10)] + [f'MAT{i}' for i in range(1, 8)] + [f'SP{i}' for i in range(1, 7)] + [f'DS{i}' for i in range(1, 7)]
                        kolom_skor_tambahan = ['RATA-RATA KESELURUHAN', 'RATA INST', 'RATA MAT', 'RATA SP', 'RATA DS']
                        for c in semua_butir + kolom_skor_tambahan:
                            if c in df_bln.columns:
                                df_bln[c] = pd.to_numeric(df_bln[c], errors='coerce')
                        
                        ins_cols_aktif = [f'INS{i}' for i in range(1, 9) if f'INS{i}' in df_bln.columns]
                        mat_cols_aktif = [f'MAT{i}' for i in range(1, 7) if f'MAT{i}' in df_bln.columns]
                        sp_cols_aktif  = [f'SP{i}' for i in range(1, 6) if f'SP{i}' in df_bln.columns]
                        ds_cols_aktif  = [f'DS{i}' for i in range(1, 6) if f'DS{i}' in df_bln.columns]
                        
                        skor_instruktur = df_bln['RATA INST'].mean() if ('RATA INST' in df_bln.columns and not df_bln['RATA INST'].dropna().empty) else (df_bln[ins_cols_aktif].mean(axis=1).mean() if ins_cols_aktif else np.nan)
                        skor_materi     = df_bln['RATA MAT'].mean() if ('RATA MAT' in df_bln.columns and not df_bln['RATA MAT'].dropna().empty) else (df_bln[mat_cols_aktif].mean(axis=1).mean() if mat_cols_aktif else np.nan)
                        skor_sarpras    = df_bln['RATA SP'].mean() if ('RATA SP' in df_bln.columns and not df_bln['RATA SP'].dropna().empty) else (df_bln[sp_cols_aktif].mean(axis=1).mean() if sp_cols_aktif else np.nan)
                        skor_digital    = df_bln['RATA DS'].mean() if ('RATA DS' in df_bln.columns and not df_bln['RATA DS'].dropna().empty) else (df_bln[ds_cols_aktif].mean(axis=1).mean() if ds_cols_aktif else np.nan)
                        
                        rata_l1 = df_bln['RATA-RATA KESELURUHAN'].mean() if ('RATA-RATA KESELURUHAN' in df_bln.columns and not df_bln['RATA-RATA KESELURUHAN'].dropna().empty) else np.nanmean([skor_instruktur, skor_materi, skor_sarpras, skor_digital])

                        list_pic_ki = []
                        if 'PIC KI' in df_bln.columns:
                            list_pic_ki = [str(p).strip() for p in df_bln['PIC KI'].dropna().unique() if str(p).strip() not in ["", "nan", "None"]]
                        elif 'Bidang' in df_bln.columns:
                            list_pic_ki = [str(p).strip() for p in df_bln['Bidang'].dropna().unique() if str(p).strip() not in ["", "nan", "None"]]
                        teks_pic_ki = ", ".join(list_pic_ki) if list_pic_ki else "Seluruh Bidang Terkait"

                        if 'INS1' in df_bln.columns and 'INS2' in df_bln.columns:
                            df_bln['Engagement Instruktur'] = df_bln[['INS1','INS2']].mean(axis=1)
                        if 'INS3' in df_bln.columns and 'INS4' in df_bln.columns:
                            df_bln['Relevance Instruktur'] = df_bln[['INS3','INS4']].mean(axis=1)
                        if all(k in df_bln.columns for k in ['INS5','INS6','INS7','INS8']):
                            df_bln['Satisfaction Instruktur'] = df_bln[['INS5','INS6','INS7','INS8']].mean(axis=1)
                        if 'MAT1' in df_bln.columns and 'MAT2' in df_bln.columns:
                            df_bln['Engagement Materi'] = df_bln[['MAT1','MAT2']].mean(axis=1)
                        if 'MAT3' in df_bln.columns and 'MAT4' in df_bln.columns:
                            df_bln['Relevance Materi'] = df_bln[['MAT3','MAT4']].mean(axis=1)
                        if 'MAT5' in df_bln.columns and 'MAT6' in df_bln.columns:
                            df_bln['Satisfaction Materi'] = df_bln[['MAT5','MAT6']].mean(axis=1)
                        if 'RATA DS' in df_bln.columns:
                            df_bln['Satisfaction Sarana Digital'] = df_bln['RATA DS']
                        elif ds_cols_aktif:
                            df_bln['Satisfaction Sarana Digital'] = df_bln[ds_cols_aktif].mean(axis=1)
                        if 'RATA SP' in df_bln.columns:
                            df_bln['Satisfaction Sarana In Class'] = df_bln['RATA SP']
                        elif sp_cols_aktif:
                            df_bln['Satisfaction Sarana In Class'] = df_bln[sp_cols_aktif].mean(axis=1)

                        if 'RATA-RATA KESELURUHAN' not in df_bln.columns or df_bln['RATA-RATA KESELURUHAN'].dropna().empty:
                            df_bln['RATA-RATA KESELURUHAN'] = df_bln[['Engagement Instruktur', 'Relevance Instruktur', 'Satisfaction Instruktur', 'Engagement Materi', 'Relevance Materi', 'Satisfaction Materi', 'Satisfaction Sarana Digital', 'Satisfaction Sarana In Class']].mean(axis=1)

                        kategori_ipa_list = [
                            'Engagement Instruktur', 'Relevance Instruktur', 'Satisfaction Instruktur', 
                            'Engagement Materi', 'Relevance Materi', 'Satisfaction Materi', 
                            'Satisfaction Sarana Digital', 'Satisfaction Sarana In Class'
                        ]
                        df_bln_ipa = df_bln.dropna(subset=['RATA-RATA KESELURUHAN']).copy()
                        df_plot_rep = pd.DataFrame()
                        df_q1_detail = pd.DataFrame()
                        q1_items = []
                        ipa_canvas_html = ""
                        x_cross = 4.50
                        y_cross = 0.50
                        
                        if len(df_bln_ipa) >= 2:
                            kinerja_list, kep_list, kat_valid = [], [], []
                            for kat in kategori_ipa_list:
                                if kat in df_bln_ipa.columns:
                                    k_val = df_bln_ipa[kat].mean()
                                    corr_val = df_bln_ipa[kat].corr(df_bln_ipa['RATA-RATA KESELURUHAN'])
                                    if pd.notna(k_val):
                                        kinerja_list.append(k_val)
                                        kep_list.append(corr_val if pd.notna(corr_val) else 0.5)
                                        kat_valid.append(kat)
                                        
                            if kat_valid:
                                df_plot_rep = pd.DataFrame({'Kategori': kat_valid, 'Kinerja': kinerja_list, 'Kepentingan': kep_list})
                                y_cross = df_plot_rep['Kepentingan'].mean()
                                df_q1_detail = df_plot_rep[(df_plot_rep['Kinerja'] < x_cross) & (df_plot_rep['Kepentingan'] > y_cross)].copy()
                                q1_items = df_q1_detail['Kategori'].tolist()
                                
                                min_x = min(3.8, df_plot_rep['Kinerja'].min() - 0.1)
                                max_x = 5.05
                                min_y = min(-0.1, df_plot_rep['Kepentingan'].min() - 0.1)
                                max_y = max(1.05, df_plot_rep['Kepentingan'].max() + 0.1)
                                
                                def hitung_pos_canvas(k, r):
                                    px_left = ((k - min_x) / (max_x - min_x)) * 100
                                    px_top = (1 - ((r - min_y) / (max_y - min_y))) * 100
                                    return max(3, min(94, px_left)), max(6, min(90, px_top))
                                
                                cross_x_pct, _ = hitung_pos_canvas(x_cross, y_cross)
                                _, cross_y_pct = hitung_pos_canvas(x_cross, y_cross)
                                
                                titik_html = ""
                                for _, r_pt in df_plot_rep.iterrows():
                                    pos_l, pos_t = hitung_pos_canvas(r_pt['Kinerja'], r_pt['Kepentingan'])
                                    is_q1 = (r_pt['Kinerja'] < x_cross) and (r_pt['Kepentingan'] > y_cross)
                                    dot_bg = "#dc2626" if is_q1 else "#0f172a"
                                    badge_bg = "#fee2e2" if is_q1 else "#e2e8f0"
                                    badge_border = "#ef4444" if is_q1 else "#94a3b8"
                                    
                                    titik_html += f"""
                                    <div style="position: absolute; left: {pos_l:.1f}%; top: {pos_t:.1f}%; transform: translate(-50%, -50%);">
                                        <div style="width: 10px; height: 10px; background-color: {dot_bg}; border: 2px solid #ffffff; border-radius: 50%; box-shadow: 0 1px 3px rgba(0,0,0,0.3); margin: auto;"></div>
                                        <div style="font-size: 7.5pt; font-weight: 600; color: {dot_bg}; background: {badge_bg}; border: 1px solid {badge_border}; padding: 1px 4px; border-radius: 3px; white-space: nowrap; margin-top: 2px;">
                                            {r_pt['Kategori']} ({r_pt['Kinerja']:.2f})
                                        </div>
                                    </div>
                                    """
                                
                                ipa_canvas_html = f"""
                                <div style="margin: 16px 0 12px 0; border: 1px solid #cbd5e1; background-color: #f8fafc; border-radius: 8px; padding: 14px;">
                                    <div style="font-size: 10pt; font-weight: 700; color: #0f172a; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;">
                                        Visualisasi Matriks Importance-Performance Analysis (IPA)
                                    </div>
                                    <div style="position: relative; width: 100%; height: 350px; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px;">
                                        <div style="position: absolute; left: {cross_x_pct:.1f}%; top: 0; bottom: 0; width: 2px; border-left: 2px dashed #f59e0b;"></div>
                                        <div style="position: absolute; top: {cross_y_pct:.1f}%; left: 0; right: 0; height: 2px; border-top: 2px dashed #f59e0b;"></div>
                                        
                                        <div style="position: absolute; top: 8px; left: 10px; font-size: 8pt; font-weight: 700; color: #b91c1c; background: #fff1f2; border: 1px solid #fecdd3; padding: 3px 6px; border-radius: 4px;">
                                            KUADRAN I: PRIORITAS UTAMA (KRITIS)
                                        </div>
                                        <div style="position: absolute; top: 8px; right: 10px; font-size: 8pt; font-weight: 700; color: #15803d; background: #f0fdf4; border: 1px solid #bbf7d0; padding: 3px 6px; border-radius: 4px; text-align: right;">
                                            KUADRAN II: PERTAHANKAN PRESTASI
                                        </div>
                                        <div style="position: absolute; bottom: 8px; left: 10px; font-size: 8pt; font-weight: 700; color: #475569; background: #f1f5f9; border: 1px solid #cbd5e1; padding: 3px 6px; border-radius: 4px;">
                                            KUADRAN III: PRIORITAS RENDAH
                                        </div>
                                        <div style="position: absolute; bottom: 8px; right: 10px; font-size: 8pt; font-weight: 700; color: #c2410c; background: #fff7ed; border: 1px solid #fed7aa; padding: 3px 6px; border-radius: 4px; text-align: right;">
                                            KUADRAN IV: BERLEBIHAN (MAINTAIN)
                                        </div>
                                        
                                        {titik_html}
                                    </div>
                                    <div style="display: flex; justify-content: space-between; font-size: 8pt; color: #64748b; margin-top: 6px;">
                                        <span>← Kinerja Rendah (Di Bawah Harapan)</span>
                                        <span><b>Batas TMP PLN (4.50)</b> | <b>Garis Rata-rata Kepentingan ({y_cross:.2f})</b></span>
                                        <span>Kinerja Tinggi (Sangat Memuaskan) →</span>
                                    </div>
                                </div>
                                """

                        # 4. Diagnosis Mendalam Indikator Kuadran 1
                        penjelasan_q1_html = ""
                        kamus_deskripsi_indikator = {
                            'Engagement Instruktur': "Tingkat partisipasi interaktif dan kemampuan melibatkan peserta dalam diskusi kelas.",
                            'Relevance Instruktur': "Aplikabilitas materi terhadap pekerjaan nyata di unit kerja serta kejelasan contoh kasus.",
                            'Satisfaction Instruktur': "Metode penyampaian materi, penguasaan studi kasus, dan manajemen waktu pengajaran.",
                            'Engagement Materi': "Daya tarik bahan ajar dan kemampuan menstimulasi motivasi belajar peserta.",
                            'Relevance Materi': "Relevansi silabus terhadap peningkatan kompetensi dan kebutuhan operasional di lapangan.",
                            'Satisfaction Materi': "Kualitas estetika visual bahan tayang dan kejelasan struktur modul.",
                            'Satisfaction Sarana Digital': "Kestabilan platform online, aksesibilitas modul digital, dan keandalan jaringan internet.",
                            'Satisfaction Sarana In Class': "Kenyamanan fisik ruang kelas, peralatan praktikum, dan fasilitas penunjang di UPDL."
                        }

                        if not df_q1_detail.empty:
                            penjelasan_q1_html += "<div style='margin-top: 10px;'>"
                            for _, r_q1 in df_q1_detail.iterrows():
                                kat_name = r_q1['Kategori']
                                kin_val = r_q1['Kinerja']
                                kep_val = r_q1['Kepentingan']
                                gap_val = 4.50 - kin_val
                                desc_text = kamus_deskripsi_indikator.get(kat_name, "Elemen pembelajaran utama yang memerlukan evaluasi.")
                                
                                penjelasan_q1_html += f"""
                                <div style="border-left: 4px solid #dc2626; background: #fff8f8; padding: 10px 14px; border-radius: 0 6px 6px 0; margin-bottom: 8px; border: 1px solid #fee2e2; border-left-width: 4px;">
                                    <div style="font-weight: 700; color: #991b1b; font-size: 10.5pt; margin-bottom: 2px;">
                                        {kat_name} <span style="font-weight: 400; color: #475569; font-size: 9.5pt;">(Realisasi: <b>{kin_val:.2f}</b> / 5.00 | Korelasi: <b>{kep_val:.3f}</b> | Gap TMP: <b style="color:#b91c1c;">-{gap_val:.2f}</b>)</span>
                                    </div>
                                    <div style="font-size: 9.5pt; color: #334155; margin-bottom: 2px;"><b>Fokus Elemen:</b> {desc_text}</div>
                                    <div style="font-size: 9.5pt; color: #7f1d1d;"><b>Akar Masalah:</b> Indikator ini merupakan <i>Key Driver</i> yang sangat sensitif terhadap kepuasan akhir peserta (Korelasi > {y_cross:.2f}), namun skor riilnya berada di bawah standar TMP (4.50). Mengabaikan indikator ini berpotensi menurunkan citra kualitas pembelajaran secara signifikan.</div>
                                </div>
                                """
                            penjelasan_q1_html += "</div>"
                        else:
                            penjelasan_q1_html = "<div style='background:#f0fdf4; border:1px solid #bbf7d0; padding:10px 14px; border-radius:6px; color:#166534; font-size:10pt;'><b>Status Mutu Prima:</b> Tidak ditemukan indikator yang jatuh ke dalam Kuadran 1. Seluruh variabel strategis berhasil memenuhi atau melampaui standar kinerja korporat (TMP 4.50).</div>"

                        # 5. Suara Pelanggan (Tabel Konsultan Bersih)
                        jml_pos, jml_neg = 0, 0
                        tabel_suara_pelanggan_html = ""
                        list_semua_masukan_raw = []
                        
                        try:
                            sheet_id_komentar = '1IDAmFwTbBQDZcKM3eiiEDcA3KwM9WKqW4zCrk__6-PU'
                            url_k = "https://docs.google.com/spreadsheets/d/" + str(sheet_id_komentar) + "/gviz/tq?tqx=out:csv&sheet=Detail%20Komentar%20L1"
                            req_k = urllib.request.Request(url_k, headers={'User-Agent': 'Mozilla/5.0'})
                            with urllib.request.urlopen(req_k) as response_k:
                                df_k_raw = pd.read_csv(io.BytesIO(response_k.read()))
                                
                            df_k_raw.columns = df_k_raw.columns.astype(str).str.strip()
                            
                            # Penyesuaian Kolom Berdasarkan Indeks & Nama Kolom Google Sheets
                            col_bulan_k = df_k_raw.columns[3] if len(df_k_raw.columns) > 3 else 'Bulan'       # Kolom D
                            col_judul_k = df_k_raw.columns[4] if len(df_k_raw.columns) > 4 else 'Judul Diklat' # Kolom E (Judul Diklat)
                            col_teks_k  = df_k_raw.columns[10] if len(df_k_raw.columns) > 10 else 'Komentar'    # Kolom K
                            col_jenis_k = df_k_raw.columns[13] if len(df_k_raw.columns) > 13 else 'Jenis'       # Kolom N

                            # Filter dan Pembersihan Data
                            df_k_raw[col_bulan_k] = df_k_raw[col_bulan_k].astype(str).str.strip()
                            df_k_bln = df_k_raw[df_k_raw[col_bulan_k].str.lower() == str(bulan_pilih).strip().lower()].copy()

                            if not df_k_bln.empty:
                                def tentukan_kategori_komentar(row):
                                    val_n = str(row.get(col_jenis_k, '')).strip().lower()
                                    if 'positif' in val_n or 'apresiasi' in val_n:
                                        return 'Positif'
                                    elif 'negatif' in val_n or 'masukan' in val_n or 'keluhan' in val_n or 'saran' in val_n:
                                        return 'Negatif'
                                    return analisis_sentimen_opensource(row.get(col_teks_k, ''))

                                df_k_bln['Kategori_Final'] = df_k_bln.apply(tentukan_kategori_komentar, axis=1)
                                jml_pos = len(df_k_bln[df_k_bln['Kategori_Final'] == 'Positif'])
                                jml_neg = len(df_k_bln[df_k_bln['Kategori_Final'] == 'Negatif'])
                                
                                baris_tabel_komentar = ""
                                daftar_judul_k = df_k_bln[col_judul_k].dropna().unique()
                                
                                for idx, jdl in enumerate(daftar_judul_k, 1):
                                    sub_df = df_k_bln[df_k_bln[col_judul_k] == jdl]
                                    pos_list = sub_df[sub_df['Kategori_Final'] == 'Positif'][col_teks_k].dropna().tolist()
                                    neg_list = sub_df[sub_df['Kategori_Final'] == 'Negatif'][col_teks_k].dropna().tolist()
                                    
                                    for item_neg in neg_list:
                                        list_semua_masukan_raw.append(f"[{jdl}] {item_neg}")
                                    
                                    # Pencocokan PIC KI dari sheet L1
                                    pic_jdl = "-"
                                    col_judul_l1 = next((c for c in ['Judul Pembelajaran/Kegiatan', 'Judul Pembelajaran', 'Judul'] if c in df_bln.columns), None)
                                    col_pic_l1   = next((c for c in ['PIC KI', 'Bidang'] if c in df_bln.columns), None)
                                    if col_judul_l1 and col_pic_l1:
                                        match_pic = df_bln[df_bln[col_judul_l1].astype(str).str.strip().str.lower() == str(jdl).strip().lower()][col_pic_l1].dropna()
                                        if not match_pic.empty:
                                            pic_jdl = str(match_pic.iloc[0])
                                            
                                    pos_html = "<ul style='margin: 0; padding-left: 14px; font-size: 9pt;'>" + "".join([f"<li style='margin-bottom: 2px; color: #15803d;'>{t}</li>" for t in pos_list]) + "</ul>" if pos_list else "<span style='color: #94a3b8; font-size: 9pt;'>-</span>"
                                    neg_html = "<ul style='margin: 0; padding-left: 14px; font-size: 9pt;'>" + "".join([f"<li style='margin-bottom: 2px; color: #b91c1c;'>{t}</li>" for t in neg_list]) + "</ul>" if neg_list else "<span style='color: #94a3b8; font-size: 9pt;'>-</span>"
                                    
                                    bg_row = "#ffffff" if idx % 2 != 0 else "#f8fafc"
                                    baris_tabel_komentar += f"""
                                    <tr style="background-color: {bg_row}; border-bottom: 1px solid #e2e8f0;">
                                        <td style="padding: 8px 6px; text-align: center; vertical-align: top; font-weight: bold; color: #64748b;">{idx}</td>
                                        <td style="padding: 8px 10px; vertical-align: top; color: #0f172a; font-weight: 600;">{jdl}</td>
                                        <td style="padding: 8px 6px; text-align: center; vertical-align: top; color: #0284c7; font-weight: 600;">{pic_jdl}</td>
                                        <td style="padding: 8px 10px; vertical-align: top;">{pos_html}</td>
                                        <td style="padding: 8px 10px; vertical-align: top;">{neg_html}</td>
                                    </tr>
                                    """
                                
                                tabel_suara_pelanggan_html = f"""
                                <table style="width: 100%; border-collapse: collapse; font-size: 9.5pt; margin-top: 10px; margin-bottom: 12px; border: 1px solid #cbd5e1;" border="1">
                                    <thead>
                                        <tr style="background-color: #0f172a; color: #ffffff; text-align: center;">
                                            <th style="padding: 8px 6px; width: 4%;">No</th>
                                            <th style="padding: 8px 10px; width: 32%; text-align: left;">Judul Pembelajaran</th>
                                            <th style="padding: 8px 6px; width: 10%;">PIC KI</th>
                                            <th style="padding: 8px 10px; width: 27%; text-align: left;">Komentar Apresiasi</th>
                                            <th style="padding: 8px 10px; width: 27%; text-align: left;">Komentar Masukan / Evaluasi</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {baris_tabel_komentar}
                                    </tbody>
                                </table>
                                """
                            else:
                                tabel_suara_pelanggan_html = "<p style='color: #64748b;'><i>Tidak ada rekaman komentar peserta untuk periode ini.</i></p>"
                        except Exception as e_k:
                            tabel_suara_pelanggan_html = f"<p><i>Gagal memproses data komentar: {e_k}</i></p>"

                        # 6. Strategic Action Plan & Rekomendasi Preskriptif
                        pilar_kurang_tmp = []
                        if pd.notna(skor_instruktur) and skor_instruktur < 4.50: pilar_kurang_tmp.append(f"Kinerja Instruktur ({skor_instruktur:.2f})")
                        if pd.notna(skor_materi) and skor_materi < 4.50: pilar_kurang_tmp.append(f"Materi Pembelajaran ({skor_materi:.2f})")
                        if pd.notna(skor_sarpras) and skor_sarpras < 4.50: pilar_kurang_tmp.append(f"Sarana In-Class ({skor_sarpras:.2f})")
                        if pd.notna(skor_digital) and skor_digital < 4.50: pilar_kurang_tmp.append(f"Sarana Digital ({skor_digital:.2f})")

                        gap_tmp_text = f"Fokus utama perbaikan ditargetkan pada pilar dengan realisasi skor di bawah target korporat 4.50, yaitu: <b>{', '.join(pilar_kurang_tmp)}</b>. Manajemen perlu memberlakukan standardisasi kesiapan kurikulum, refreshment metode pengajaran instruktur, dan audit sarana berkala." if pilar_kurang_tmp else "Seluruh 4 pilar utama telah melampaui batas TMP (≥ 4.50). Manajemen dianjurkan memperkuat SOP guna mempertahankan stabilitas mutu operasional."
                        q1_action_text = f"Berdasarkan prinsip efisiensi sumber daya (Pareto Principle), alokasi anggaran dan intervensi wajib difokuskan pada area <b>Kuadran 1 ({', '.join(q1_items)})</b>. Perbaikan di area ini memberikan daya ungkit (leverage) paling masif terhadap lonjakan indeks kepuasan pelanggan." if q1_items else "Tidak ada area kritis di Kuadran 1. Pengendalian mutu difokuskan pada pengawasan preventif."

                        # 7. GENERASI TINDAK LANJUT MENDALAM VIA GEMINI AI (DENGAN SAFE FALLBACK)
                        tabel_tindak_lanjut_ai_html = ""
                        if list_semua_masukan_raw:
                            sample_masukan = list_semua_masukan_raw[:25]
                            teks_masukan_input = "\n".join([f"- {m}" for m in sample_masukan])
                            rows_plan = ""
                            
                            try:
                                prompt_action_plan = f"""
Bertindaklah sebagai Senior Quality Management Specialist di PLN UPDL Jakarta.
Berikut adalah rekaman suara masukan/keluhan peserta pelatihan:
{teks_masukan_input}

Buatkan tabel Rencana Tindak Lanjut Operasional (Action Plan) konkret dari UPDL Jakarta untuk menjawab isu-isu di atas.
Klasifikasikan ke dalam kategori area yang relevan (misal: Instruktur & Pengajaran, Materi & Silabus Diklat, Sarana Ruang Kelas/In-Class, atau Sarana Digital & Jaringan).

Output WAJIB HANYA berupa baris-baris tag HTML <tr>...</tr> (tanpa pembungkus ```html):
<tr>
    <td style="padding: 8px 10px; vertical-align: top; font-weight: 600; color: #003366;">[Nama Kategori/Pilar]</td>
    <td style="padding: 8px 10px; vertical-align: top; color: #b91c1c;">[Ringkasan Poin Masukan Terkait]</td>
    <td style="padding: 8px 10px; vertical-align: top; color: #15803d; font-weight: 500;">[Rencana Tindak Lanjut Operasional UPDL Jakarta]</td>
    <td style="padding: 8px 10px; vertical-align: top; text-align: center; font-weight: 600; color: #0284c7;">[PIC: Sarpras / Akademik / Instruktur / PIC KI]</td>
</tr>
Tuliskan 3 hingga 5 baris isu paling utama dengan bahasa korporat baku PLN.
"""
                                if model:
                                    ai_plan_resp = model.generate_content(prompt_action_plan)
                                    if ai_plan_resp and hasattr(ai_plan_resp, 'text'):
                                        rows_plan = ai_plan_resp.text.strip().replace('```html', '').replace('```', '')
                            except Exception as e_ai:
                                rows_plan = ""

                            if not rows_plan or "<tr" not in rows_plan:
                                fallback_rows = []
                                for idx_m, item_m in enumerate(sample_masukan[:4], 1):
                                    txt_clean = item_m.strip()
                                    kat_area = "Sarana & Prasarana"
                                    pic_area = "PIC Sarpras"
                                    solusi_area = "Pemeriksaan dan perbaikan fasilitas kelas, AC, dan perlengkapan praktikum sebelum sesi dimulai."
                                    
                                    lower_m = txt_clean.lower()
                                    if any(w in lower_m for w in ['instruktur', 'pengajar', 'suara', 'bicara', 'waktu', 'jadwal']):
                                        kat_area = "Kinerja Instruktur"
                                        pic_area = "Pengelola Instruktur"
                                        solusi_area = "Briefing pengajar terkait alokasi waktu dan peningkatan interaksi aktif bersama peserta."
                                    elif any(w in lower_m for w in ['materi', 'modul', 'ppt', 'studi kasus', 'silabus', 'teori']):
                                        kat_area = "Materi Pembelajaran"
                                        pic_area = "PIC Akademik"
                                        solusi_area = "Pemutakhiran studi kasus aktual dan penyesuaian bobot latihan modul."
                                    elif any(w in lower_m for w in ['aplikasi', 'jaringan', 'wifi', 'internet', 'web', 'login']):
                                        kat_area = "Sarana Digital"
                                        pic_area = "Tim TI & Media"
                                        solusi_area = "Optimalisasi bandwidth internet dan pengecekan aksesibilitas platform e-learning."

                                    fallback_rows.append(f"""
                                    <tr style="background-color: {'#ffffff' if idx_m % 2 != 0 else '#f8fafc'};">
                                        <td style="padding: 8px 10px; vertical-align: top; font-weight: 600; color: #003366;">{kat_area}</td>
                                        <td style="padding: 8px 10px; vertical-align: top; color: #b91c1c;">{txt_clean}</td>
                                        <td style="padding: 8px 10px; vertical-align: top; color: #15803d; font-weight: 500;">{solusi_area}</td>
                                        <td style="padding: 8px 10px; vertical-align: top; text-align: center; font-weight: 600; color: #0284c7;">{pic_area}</td>
                                    </tr>
                                    """)
                                rows_plan = "".join(fallback_rows)

                            tabel_tindak_lanjut_ai_html = f"""
                            <div style="margin-top: 14px;">
                                <div style="font-weight: 700; color: #003366; font-size: 10pt; margin-bottom: 6px; text-transform: uppercase;">
                                    Matriks Tindak Lanjut & Resolusi Keluhan Peserta (Action Item Tracker - UPDL Jakarta)
                                </div>
                                <table style="width: 100%; border-collapse: collapse; font-size: 9.5pt; border: 1px solid #cbd5e1;" border="1">
                                    <thead>
                                        <tr style="background-color: #003366; color: #ffffff; text-align: left;">
                                            <th style="padding: 8px 10px; width: 18%;">Kategori Area</th>
                                            <th style="padding: 8px 10px; width: 32%;">Isu / Masukan Peserta</th>
                                            <th style="padding: 8px 10px; width: 35%;">Rencana Tindak Lanjut Operasional (UPDL Jakarta)</th>
                                            <th style="padding: 8px 10px; width: 15%; text-align: center;">PIC Terkait</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {rows_plan}
                                    </tbody>
                                </table>
                            </div>
                            """
                        else:
                            tabel_tindak_lanjut_ai_html = "<div style='background:#f0fdf4; border:1px solid #bbf7d0; padding:10px 14px; border-radius:6px; color:#166534; font-size:9.5pt; margin-top:8px;'><b>Zero Defect:</b> Tidak terdapat rekaman keluhan atau masukan negatif pada periode ini. Tindak lanjut berfokus pada pemeliharaan standar layanan prima.</div>"

                        # 8. Gemini AI: Executive Summary Berstandar Konsultan
                        narasi_eksekutif_ai = ""
                        try:
                            prompt_ai = f"""
                            Bertindaklah sebagai Senior Management Consultant (McKinsey/PwC style) untuk PLN UPDL Jakarta. Buatkan Ringkasan Eksekutif (Executive Summary) formal, berbobot, padat, dan analitis (maksimal 2 paragraf) untuk Laporan Evaluasi Mutu Pembelajaran Level 1.
                            
                            Fakta Data Periode {bulan_pilih}:
                            - Total Pelaksanaan: {total_sesi} sesi/pelatihan.
                            - Rata-rata Skor L1 Keseluruhan: {rata_l1:.2f} (Standar TMP PLN: 4.50).
                            - Capaian Pilar: Instruktur = {skor_instruktur:.2f}, Materi = {skor_materi:.2f}, Sarana In-Class = {skor_sarpras:.2f}, Sarana Digital = {skor_digital:.2f}.
                            - Pilar di Bawah TMP: {', '.join(pilar_kurang_tmp) if pilar_kurang_tmp else 'Semua Pilar Memenuhi TMP'}.
                            - Indikator Kritis Kuadran 1: {', '.join(q1_items) if q1_items else 'Nihil (Tidak Ada)'}.
                            - Voice of Customer: {jml_pos} Apresiasi dan {jml_neg} Masukan/Keluhan.
                            - PIC KI yang bertugas: {teks_pic_ki}.
                            
                            Struktur Narasi:
                            - Paragraf 1: Analisis komprehensif performa mutu pembelajaran periode berjalan, perbandingan terhadap standar korporat (TMP 4.50), serta peran kolaborasi bersama PIC KI.
                            - Paragraf 2: Diagnosis area kritis Kuadran 1 IPA, sintesis suara pelanggan, dan arah kebijakan prioritas perbaikan mutu.
                            - Gaya Bahasa: Profesional, tajam, berbasis bukti data, tanpa markdown bintang tebal.
                            """
                            if model:
                                ai_resp = model.generate_content(prompt_ai)
                                narasi_eksekutif_ai = ai_resp.text.strip().replace('\n', '<br>')
                            else:
                                raise Exception("Model AI tidak tersedia")
                        except Exception as ai_err:
                            narasi_eksekutif_ai = f"Pada periode {bulan_pilih}, evaluasi mutu pembelajaran Level 1 mencatatkan skor rata-rata sebesar {rata_l1:.2f} dari {total_sesi} batch pelatihan yang diselenggarakan bersama PIC KI ({teks_pic_ki}). Capaian mutu mencakup pilar Instruktur ({skor_instruktur:.2f}), Materi ({skor_materi:.2f}), Sarana In-Class ({skor_sarpras:.2f}), dan Sarana Digital ({skor_digital:.2f}).<br><br>Pemetaan analitik IPA mengidentifikasi fokus perbaikan pada area strategis dengan dukungan {jml_pos} komentar apresiasi dan {jml_neg} masukan sebagai landasan perbaikan mutu berkesinambungan di UPDL Jakarta."

                        def format_pill_badge(skor):
                            if pd.isna(skor): return "<span style='color:#64748b;'>N/A</span>"
                            if skor >= 4.50:
                                return "<span style='background-color:#dcfce7; color:#15803d; padding:2px 8px; border-radius:12px; font-weight:600; font-size:8.5pt;'>Memenuhi TMP</span>"
                            return "<span style='background-color:#fee2e2; color:#b91c1c; padding:2px 8px; border-radius:12px; font-weight:600; font-size:8.5pt;'>Di Bawah TMP</span>"

                        def format_skor_val(val):
                            return f"{val:.2f}" if pd.notna(val) else "-"

                        # 9. Template Dokumen Word Berstandar Konsultan Global (.DOC)
                        html_content = f"""
                        <html>
                        <head>
                            <meta charset="utf-8">
                            <style>
                                body {{ font-family: 'Segoe UI', Arial, Helvetica, sans-serif; line-height: 1.5; color: #1e293b; font-size: 11pt; }}
                                h2, h3, h4 {{ font-family: 'Segoe UI', Arial, sans-serif; }}
                                table {{ border-collapse: collapse; width: 100%; }}
                            </style>
                        </head>
                        <body>
                            <!-- HEADER UTAMA KONSULTAN -->
                            <div style="border-bottom: 3px solid #0055A4; padding-bottom: 12px; margin-bottom: 20px;">
                                <table style="width: 100%; border: none;">
                                    <tr>
                                        <td style="vertical-align: middle; border: none;">
                                            <div style="font-size: 8.5pt; font-weight: 700; color: #0055A4; text-transform: uppercase; letter-spacing: 1px;">
                                                PLN CORPORATE UNIVERSITY &bull; UPDL JAKARTA
                                            </div>
                                            <h2 style="margin: 2px 0 0 0; color: #003366; font-size: 17pt;">
                                                LAPORAN EVALUASI MUTU PEMBELAJARAN (LEVEL 1)
                                            </h2>
                                            <div style="font-size: 11pt; color: #64748b; margin-top: 2px;">
                                                Executive Performance Report &bull; Periode: <b>{bulan_pilih.upper()}</b>
                                            </div>
                                        </td>
                                        <td style="text-align: right; vertical-align: middle; border: none; width: 30%;">
                                            <div style="background: #f1f5f9; padding: 6px 12px; border-radius: 6px; display: inline-block; text-align: right;">
                                                <div style="font-size: 8pt; color: #64748b;">Grand Average Score</div>
                                                <div style="font-size: 16pt; font-weight: 800; color: {'#15803d' if rata_l1 >= 4.50 else '#b91c1c'};">
                                                    {format_skor_val(rata_l1)} <span style="font-size: 9pt; font-weight: normal; color: #64748b;">/ 5.00</span>
                                                </div>
                                            </div>
                                        </td>
                                    </tr>
                                </table>
                            </div>

                            <!-- METADATA PROYEK -->
                            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 10px 14px; margin-bottom: 18px;">
                                <table style="width: 100%; border: none; font-size: 9.5pt;">
                                    <tr>
                                        <td style="width: 20%; color: #64748b; border: none;"><b>Periode Analisis:</b></td>
                                        <td style="width: 30%; color: #0f172a; border: none;"><b>{bulan_pilih}</b></td>
                                        <td style="width: 20%; color: #64748b; border: none;"><b>Total Implementasi:</b></td>
                                        <td style="width: 30%; color: #0f172a; border: none;"><b>{total_sesi} Sesi / Pelatihan</b></td>
                                    </tr>
                                    <tr>
                                        <td style="color: #64748b; border: none;"><b>PIC KI Terkait:</b></td>
                                        <td style="color: #0f172a; border: none;" colspan="3">{teks_pic_ki}</td>
                                    </tr>
                                </table>
                            </div>

                            <!-- 1. EXECUTIVE SUMMARY -->
                            <h3 style="color: #003366; font-size: 12.5pt; border-bottom: 1.5px solid #cbd5e1; padding-bottom: 4px; margin-bottom: 8px;">
                                1. RINGKASAN EKSEKUTIF (EXECUTIVE SUMMARY)
                            </h3>
                            <div style="background: #ffffff; border-left: 4px solid #0055A4; padding: 10px 14px; margin-bottom: 18px; text-align: justify; background-color: #f8fafc; border: 1px solid #e2e8f0; border-left-width: 4px;">
                                <p style="margin: 0; font-size: 10.5pt; line-height: 1.55;">{narasi_eksekutif_ai}</p>
                            </div>

                            <!-- 2. PILAR SCORECARD -->
                            <h3 style="color: #003366; font-size: 12.5pt; border-bottom: 1.5px solid #cbd5e1; padding-bottom: 4px; margin-bottom: 8px;">
                                2. CAPAIAN KINERJA MUTU PER PILAR EVALUASI
                            </h3>
                            <table style="width: 100%; border-collapse: collapse; font-size: 10pt; margin-bottom: 18px; border: 1px solid #cbd5e1;" border="1">
                                <thead>
                                    <tr style="background-color: #003366; color: #ffffff; text-align: left;">
                                        <th style="padding: 8px 10px;">Pilar Evaluasi Pembelajaran</th>
                                        <th style="padding: 8px 10px; text-align: center; width: 15%;">Realisasi Skor</th>
                                        <th style="padding: 8px 10px; text-align: center; width: 15%;">Target TMP</th>
                                        <th style="padding: 8px 10px; text-align: center; width: 20%;">Status Mutu</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr style="background-color: #ffffff; border-bottom: 1px solid #e2e8f0;">
                                        <td style="padding: 7px 10px;"><b>1. Kinerja Instruktur</b> (Engagement, Relevance, Satisfaction)</td>
                                        <td style="padding: 7px 10px; text-align: center; font-weight: 700;">{format_skor_val(skor_instruktur)}</td>
                                        <td style="padding: 7px 10px; text-align: center; color: #64748b;">4.50</td>
                                        <td style="padding: 7px 10px; text-align: center;">{format_pill_badge(skor_instruktur)}</td>
                                    </tr>
                                    <tr style="background-color: #f8fafc; border-bottom: 1px solid #e2e8f0;">
                                        <td style="padding: 7px 10px;"><b>2. Materi Pembelajaran</b> (Engagement, Relevance, Satisfaction)</td>
                                        <td style="padding: 7px 10px; text-align: center; font-weight: 700;">{format_skor_val(skor_materi)}</td>
                                        <td style="padding: 7px 10px; text-align: center; color: #64748b;">4.50</td>
                                        <td style="padding: 7px 10px; text-align: center;">{format_pill_badge(skor_materi)}</td>
                                    </tr>
                                    <tr style="background-color: #ffffff; border-bottom: 1px solid #e2e8f0;">
                                        <td style="padding: 7px 10px;"><b>3. Sarana & Prasarana In-Class</b> (Kenyamanan & Fasilitas Fisik)</td>
                                        <td style="padding: 7px 10px; text-align: center; font-weight: 700;">{format_skor_val(skor_sarpras)}</td>
                                        <td style="padding: 7px 10px; text-align: center; color: #64748b;">4.50</td>
                                        <td style="padding: 7px 10px; text-align: center;">{format_pill_badge(skor_sarpras)}</td>
                                    </tr>
                                    <tr style="background-color: #f8fafc; border-bottom: 1px solid #e2e8f0;">
                                        <td style="padding: 7px 10px;"><b>4. Sarana Digital</b> (Aplikasi, Modul Digital, Jaringan)</td>
                                        <td style="padding: 7px 10px; text-align: center; font-weight: 700;">{format_skor_val(skor_digital)}</td>
                                        <td style="padding: 7px 10px; text-align: center; color: #64748b;">4.50</td>
                                        <td style="padding: 7px 10px; text-align: center;">{format_pill_badge(skor_digital)}</td>
                                    </tr>
                                    <tr style="background-color: #f1f5f9; font-weight: 800; border-top: 2px solid #003366;">
                                        <td style="padding: 9px 10px; color: #003366;">RATA-RATA TOTAL KESELURUHAN</td>
                                        <td style="padding: 9px 10px; text-align: center; font-size: 11pt; color: #003366;">{format_skor_val(rata_l1)}</td>
                                        <td style="padding: 9px 10px; text-align: center; color: #64748b;">4.50</td>
                                        <td style="padding: 9px 10px; text-align: center;">
                                            {'<span style="background-color:#15803d; color:#ffffff; padding:3px 10px; border-radius:12px; font-size:8.5pt;">STATUS PRIMA</span>' if pd.notna(rata_l1) and rata_l1 >= 4.50 else '<span style="background-color:#b91c1c; color:#ffffff; padding:3px 10px; border-radius:12px; font-size:8.5pt;">PERLU EVALUASI</span>'}
                                        </td>
                                    </tr>
                                </tbody>
                            </table>

                            <!-- 3. IPA MATRIX & DIAGNOSIS -->
                            <h3 style="color: #003366; font-size: 12.5pt; border-bottom: 1.5px solid #cbd5e1; padding-bottom: 4px; margin-bottom: 8px;">
                                3. PEMETAAN AREA KRITIS (IMPORTANCE-PERFORMANCE ANALYSIS)
                            </h3>
                            {ipa_canvas_html}
                            {penjelasan_q1_html}

                            <!-- 4. VOICE OF CUSTOMER -->
                            <h3 style="color: #003366; font-size: 12.5pt; border-bottom: 1.5px solid #cbd5e1; padding-bottom: 4px; margin-bottom: 8px; margin-top: 20px;">
                                4. SUARA PELANGGAN (VOICE OF CUSTOMER PER JUDUL PEMBELAJARAN)
                            </h3>
                            <p style="font-size: 10pt; color: #475569; margin: 0 0 6px 0;">
                                Rekapitulasi umpan balik peserta mencatat total <b>{jml_pos} apresiasi positif</b> dan <b>{jml_neg} masukan/keluhan operasional</b> pada periode {bulan_pilih}:
                            </p>
                            {tabel_suara_pelanggan_html}

                            <!-- 5. STRATEGIC ROADMAP -->
                            <h3 style="color: #003366; font-size: 12.5pt; border-bottom: 1.5px solid #cbd5e1; padding-bottom: 4px; margin-bottom: 8px; margin-top: 20px;">
                                5. STRATEGIC ROADMAP & REKOMENDASI TINDAK LANJUT
                            </h3>
                            <div style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px 16px; margin-bottom: 25px;">
                                <div style="margin-bottom: 10px;">
                                    <div style="font-weight: 700; color: #003366; font-size: 10.5pt; margin-bottom: 2px;">
                                        A. Pemenuhan Standar Minimum TMP Korporat (Target: 4.50)
                                    </div>
                                    <div style="font-size: 9.5pt; color: #334155; text-align: justify;">{gap_tmp_text}</div>
                                </div>
                                <div style="margin-bottom: 10px;">
                                    <div style="font-weight: 700; color: #003366; font-size: 10.5pt; margin-bottom: 2px;">
                                        B. Intervensi Preskriptif Indikator Kuadran 1 (Prioritas Utama)
                                    </div>
                                    <div style="font-size: 9.5pt; color: #334155; text-align: justify;">{q1_action_text}</div>
                                </div>
                                <div>
                                    <div style="font-weight: 700; color: #003366; font-size: 10.5pt; margin-bottom: 2px;">
                                        C. Resolusi Masukan Peserta & Continuous Improvement
                                    </div>
                                    <div style="font-size: 9.5pt; color: #334155; text-align: justify;">
                                        Merespons <b>{jml_neg} komentar masukan</b> yang tercatat, PIC KI bersama pengelola diklat diwajibkan menyusun <i>Action Item Tracker</i> penanganan isu spesifik per pembelajaran dan mengevaluasi efektivitasnya pada siklus evaluasi mutu bulan berikutnya.
                                    </div>
                                </div>
                            </div>

                            <!-- LEMBAR PENGESAHAN -->
                            <table style="width: 100%; border: none; margin-top: 30px; font-size: 10pt;">
                                <tr>
                                    <td style="width: 50%; border: none;"></td>
                                    <td style="width: 50%; border: none; text-align: center;">
                                        Disusun secara otomatis oleh sistem <b>EVALYTICS</b><br>
                                        UPDL Jakarta, {datetime.now().strftime('%d %B %Y')}<br><br><br><br><br>
                                        <b>( _________________________ )</b><br>
                                        Tim Pengendalian Mutu & Kinerja
                                    </td>
                                </tr>
                            </table>
                        </body>
                        </html>
                        """
                        
                        st.success("✅ Dokumen Laporan Manajemen Mutu (Executive Edition) berhasil disusun!")
                        st.download_button(
                            label="📥 DOWNLOAD LAPORAN EKSEKUTIF (.doc)",
                            data=html_content.encode('utf-8'),
                            file_name=f"Laporan_Mutu_EVALYTICS_{bulan_pilih}_Executive.doc",
                            mime="application/msword",
                            type="primary"
                        )
                        with st.expander("👀 Pratinjau Tampilan Eksekutif (Live Preview)"):
                            st.markdown(html_content, unsafe_allow_html=True)
            else:
                st.info("Belum ada data bulan yang tersedia untuk dibuatkan laporan.")
        except Exception as e:
            st.error(f"Gagal memuat data sumber untuk laporan: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # --- SUB TAB 2: LAPORAN PEMBELAJARAN (NEW - MASTER DATA LAPORAN) ---
    # ─────────────────────────────────────────────────────────────────────────
    with sub_lap_pembelajaran:
        st.markdown("### 📄 Generator Laporan Pembelajaran Per Kelas")
        st.write("Menyusun laporan pelaksanaan spesifik per kelas dari Master Data Laporan, mencakup realisasi peserta, biaya, evaluasi, dan komentar berstandar *Consulting Style*.")
        
        try:
            url_master = "https://docs.google.com/spreadsheets/d/" + str(sheet_id) + "/gviz/tq?tqx=out:csv&sheet=Master_Data_Laporan"
            req_master = urllib.request.Request(url_master, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req_master) as response:
                df_master = pd.read_csv(io.BytesIO(response.read()))
            
            df_master.columns = df_master.columns.astype(str).str.strip()
            
            if 'Judul Pembelajaran' in df_master.columns:
                list_judul = df_master['Judul Pembelajaran'].dropna().astype(str).str.strip().unique().tolist()
                
                if list_judul:
                    with st.container(border=True):
                        col_j1, col_j2 = st.columns([2, 1])
                        with col_j1:
                            judul_pilih = st.selectbox("📚 Pilih Judul Pembelajaran:", list_judul, key="judul_report_pembelajaran")
                        with col_j2:
                            st.markdown("<br>", unsafe_allow_html=True)
                            btn_gen_kelas = st.button("🚀 Generate Laporan Kelas", type="primary", use_container_width=True)
                    
                    if btn_gen_kelas:
                        with st.spinner(f"Mengekstrak data pelaksanaan {judul_pilih}..."):
                            df_kelas = df_master[df_master['Judul Pembelajaran'].astype(str).str.strip() == judul_pilih].iloc[0]
                            
                            # 1. Dasar Pelaksanaan
                            kode_pemb = df_kelas.get('Kode Pembelajaran', '-')
                            no_surat = df_kelas.get('No Surat Penugasan', '-')
                            tgl_surat = df_kelas.get('Tanggal Surat Penugasan', '-')
                            
                            no_surat_panggil = df_kelas.get('Nomor Surat Pemanggilan Peserta', '-')
                            if pd.isna(no_surat_panggil) or str(no_surat_panggil).strip() == "": no_surat_panggil = "-"

                            kode_sr_raw = df_kelas.get('Kode Service Request', '')
                            if pd.isna(kode_sr_raw): kode_sr_raw = ""
                            jenis_prog = df_kelas.get('Jenis Program', '')
                            if pd.isna(jenis_prog): jenis_prog = ""
                            kode_sr = f"{kode_sr_raw} - {jenis_prog}".strip(" -")
                            if not kode_sr: kode_sr = "-"
                            
                            # 2. Jumlah Peserta
                            rencana_peserta = df_kelas.get('Rencana Jumlah Peserta', 0)
                            diundang = df_kelas.get('Peserta Diundang', 0)
                            hadir = df_kelas.get('Peserta Hadir', 0)
                            lulus = df_kelas.get('Peserta Lulus', 0)
                            
                            def f_pct_str(v):
                                v_str = str(v).strip()
                                if v_str in ['nan', 'None', '', '-']: return "-"
                                if '%' in v_str: return v_str
                                try:
                                    val = float(v_str)
                                    if val <= 1.0 and val > 0: return f"{val*100:.1f}%"
                                    return f"{val:.1f}%"
                                except:
                                    return v_str
                                    
                            pct_hadir = f_pct_str(df_kelas.get('% Kehadiran', '-'))
                            pct_lulus = f_pct_str(df_kelas.get('% Kelulusan', '-'))
                            
                            isi_l1 = df_kelas.get('Peserta Isi L1', 0)
                            pct_isi = f_pct_str(df_kelas.get('% Pengisian L1', '-'))
                            
                            # 3. Waktu, Metode, Tempat
                            tgl_mulai = df_kelas.get('Tgl Mulai', '-')
                            tgl_selesai = df_kelas.get('Tgl Selesai', '-')
                            
                            instruktur = df_kelas.get('Instruktur/ Fasilitator', '-')
                            if pd.isna(instruktur) or str(instruktur).strip() == "": instruktur = "[ Ketik Nama Instruktur Disini ]"
                            
                            tempat = df_kelas.get('Tempat Pelaksanaan', df_kelas.get('Lokasi Pelaksanaan', '-'))
                            if pd.isna(tempat) or str(tempat).strip() == "": tempat = "PT PLN (Persero) UPDL JAKARTA"
                            
                            dict_metode = {
                                "ICT": "In Class Training (ICT)",
                                "DL": "Distance Learning (DL)",
                                "SL": "Self Learning (SL)",
                                "BL": "Blended Learning (BL)",
                                "HL": "Hybrid Learning (HL)"
                            }
                            metode_raw = str(df_kelas.get('Strategi Pelaksanaan', '-')).strip()
                            metode = dict_metode.get(metode_raw.upper(), metode_raw)
                            
                            # 4. Realisasi Biaya
                            def format_rp(val):
                                try: return f"Rp {int(float(val)):,}".replace(',', '.')
                                except: return "Rp 0"
                                    
                            rab = format_rp(df_kelas.get('RAB Pelaksanaan', 0))
                            realisasi = format_rp(df_kelas.get('Realisasi Biaya Pelaksanaan', 0))
                            
                            # 5. Evaluasi
                            def f_skor(v):
                                try: return f"{float(v):.2f}"
                                except: return "-"
                                
                            skor_mat = f_skor(df_kelas.get('RATA MAT', 0))
                            skor_ins = f_skor(df_kelas.get('RATA INST', 0))
                            skor_sp_off = f_skor(df_kelas.get('RATA SP', 0))
                            skor_sp_on = f_skor(df_kelas.get('RATA DS', 0))
                            skor_tot = f_skor(df_kelas.get('RATA-RATA KESELURUHAN', 0))
                            
                            # 6. Komentar
                            pos_html, neg_html = "-", "-"
                            jml_pos_kelas, jml_neg_kelas = 0, 0
                            try:
                                url_k = "https://docs.google.com/spreadsheets/d/" + str(sheet_id) + "/gviz/tq?tqx=out:csv&sheet=Detail%20Komentar%20L1"
                                req_k = urllib.request.Request(url_k, headers={'User-Agent': 'Mozilla/5.0'})
                                with urllib.request.urlopen(req_k) as res_k:
                                    df_k_raw = pd.read_csv(io.BytesIO(res_k.read()))
                                
                                df_k_raw.columns = df_k_raw.columns.astype(str).str.strip()
                                
                                col_judul_k = df_k_raw.columns[4] if len(df_k_raw.columns) > 4 else 'Judul Diklat'
                                col_teks_k  = df_k_raw.columns[10] if len(df_k_raw.columns) > 10 else 'Komentar'
                                col_jenis_k = df_k_raw.columns[13] if len(df_k_raw.columns) > 13 else 'Jenis'
                                
                                df_k_bln = df_k_raw[df_k_raw[col_judul_k].astype(str).str.strip().str.lower() == str(judul_pilih).strip().lower()].copy()
                                
                                if not df_k_bln.empty:
                                    def tentukan_kategori_komentar(row):
                                        val_n = str(row.get(col_jenis_k, '')).strip().lower()
                                        if 'positif' in val_n or 'apresiasi' in val_n: return 'Positif'
                                        elif 'negatif' in val_n or 'masukan' in val_n or 'keluhan' in val_n or 'saran' in val_n: return 'Negatif'
                                        return analisis_sentimen_opensource(row.get(col_teks_k, ''))

                                    df_k_bln['Sentimen'] = df_k_bln.apply(tentukan_kategori_komentar, axis=1)
                                    pos_texts = df_k_bln[df_k_bln['Sentimen'] == 'Positif'][col_teks_k].dropna().tolist()
                                    neg_texts = df_k_bln[df_k_bln['Sentimen'] == 'Negatif'][col_teks_k].dropna().tolist()
                                    
                                    jml_pos_kelas, jml_neg_kelas = len(pos_texts), len(neg_texts)
                                    
                                    pos_html = "<ul style='margin:0; padding-left:15px; color: #334155; line-height: 1.6;'>" + "".join([f"<li style='margin-bottom:6px;'>{t}</li>" for t in pos_texts]) + "</ul>" if pos_texts else "<span style='color:#94a3b8; font-style:italic;'>Nihil / Tidak ada catatan apresiasi.</span>"
                                    neg_html = "<ul style='margin:0; padding-left:15px; color: #334155; line-height: 1.6;'>" + "".join([f"<li style='margin-bottom:6px;'>{t}</li>" for t in neg_texts]) + "</ul>" if neg_texts else "<span style='color:#94a3b8; font-style:italic;'>Nihil / Tidak ada catatan masukan.</span>"
                            except Exception as e_k:
                                pos_html = f"Gagal memuat komentar: {e_k}"
                                neg_html = f"Gagal memuat komentar: {e_k}"
                                
                            html_kelas = f"""
                            <html xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:w='urn:schemas-microsoft-com:office:word' xmlns='[http://www.w3.org/TR/REC-html40](http://www.w3.org/TR/REC-html40)'>
                            <head>
                                <meta charset="utf-8">
                                <style>
                                    body {{ font-family: 'Segoe UI', Arial, sans-serif; font-size: 11pt; color: #1e293b; }}
                                    .cover-page {{ background: linear-gradient(135deg, #001f3f 0%, #0055A4 100%); color: white; padding: 50px 40px; text-align: center; height: 100%; }}
                                    .cover-title {{ font-size: 26pt; font-weight: 800; letter-spacing: 2px; margin-top: 150px; margin-bottom: 20px; text-transform: uppercase; line-height: 1.3; }}
                                    .cover-subtitle {{ font-size: 16pt; font-weight: normal; margin-bottom: 10px; line-height: 1.4; }}
                                    .cover-code {{ font-size: 14pt; color: #6cb2eb; margin-bottom: 150px; }}
                                    .cover-footer {{ font-size: 14pt; font-weight: bold; letter-spacing: 1px; bottom: 50px; width: 100%; }}
                                    h4 {{ color: #0055A4; border-bottom: 2px solid #cbd5e1; padding-bottom: 5px; margin-top: 25px; margin-bottom: 10px; font-size: 12pt; text-transform: uppercase; }}
                                    table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; font-size: 10.5pt; }}
                                    th {{ background-color: #003366; color: white; padding: 8px; text-align: left; }}
                                    td {{ border: 1px solid #cbd5e1; padding: 8px; vertical-align: top; }}
                                    .zebra tr:nth-child(even) td {{ background-color: #f8fafc; }}
                                    p {{ text-align: justify; margin-top: 0; line-height: 1.6; color: #334155; }}
                                    ul {{ margin-top: 0; padding-left: 20px; line-height: 1.6; color: #334155; }}
                                </style>
                            </head>
                            <body>
                                <!-- COVER PAGE -->
                                <div class="cover-page">
                                    <table style="width: 100%; border: none;">
                                        <tr>
                                            <td style="text-align: left; border: none; width: 50%;"><img src="data:image/png;base64,{bin_danantara}" height="40" style="background:white; padding:5px; border-radius:4px;"></td>
                                            <td style="text-align: right; border: none; width: 50%;"><img src="data:image/png;base64,{bin_pln}" height="60"></td>
                                        </tr>
                                    </table>
                                    
                                    <div class="cover-title">LAPORAN PELAKSANAAN<br>PEMBELAJARAN PENUGASAN</div>
                                    <div class="cover-subtitle">{str(judul_pilih).upper()}</div>
                                    <div class="cover-code">({kode_pemb})</div>
                                    
                                    <br><br><br><br><br><br><br><br><br><br><br><br>
                                    <div class="cover-footer">PT PLN (PERSERO) UPDL JAKARTA</div>
                                </div>
                                
                                <br clear="all" style="page-break-before:always" />
                                
                                <!-- CONTENT PAGE -->
                                <div style="padding: 20px 40px;">
                                    <p><b>Executive Summary:</b> Dokumen ini merangkum <i>post-implementation review</i> untuk pelaksanaan program <b>{judul_pilih}</b> ({kode_pemb}), menyajikan evaluasi metrik kehadiran, efisiensi anggaran, dan tingkat kepuasan pelanggan guna memastikan penyelarasan operasional dengan standar mutu <i>Service Excellence</i> UPDL Jakarta.</p>
                                    
                                    <h4>1. DASAR PELAKSANAAN</h4>
                                    <p>Inisiatif pembelajaran ini dieksekusi berdasarkan mandat korporat melalui Surat Penugasan No. <b>{no_surat}</b> yang diterbitkan pada tanggal <b>{tgl_surat}</b>. Sebagai landasan administratif tambahan, pemanggilan peserta diatur melalui Surat Pemanggilan No. <b>{no_surat_panggil}</b> dengan Kode Service Request (SR): <b>{kode_sr}</b>.</p>
                                    
                                    <h4>2. JUMLAH PESERTA (METRIK PARTISIPASI & KELULUSAN)</h4>
                                    <p>Tingkat konversi (<i>Conversion Rate</i>) kehadiran dan kelulusan peserta merupakan indikator utama efektivitas pemanggilan dan kualitas penyampaian materi. Berikut adalah rincian capaian partisipasi dan akademik:</p>
                                    <table class="zebra">
                                        <tr><th style="width: 70%; text-align:center;">Indikator Partisipasi & Akademik</th><th style="width: 30%; text-align:center;">Realisasi / Capaian</th></tr>
                                        <tr><td>Rencana Jumlah Peserta (Target)</td><td style="text-align:center; font-weight:bold;">{rencana_peserta} Orang</td></tr>
                                        <tr><td>Peserta Diundang</td><td style="text-align:center; font-weight:bold;">{diundang} Orang</td></tr>
                                        <tr><td>Peserta Hadir (Actual Attendance)</td><td style="text-align:center; font-weight:bold; color: #0055A4;">{hadir} Orang</td></tr>
                                        <tr><td>Persentase Kehadiran (Attendance Rate)</td><td style="text-align:center; font-weight:bold;">{pct_hadir}</td></tr>
                                        <tr><td>Peserta Lulus (Passing Volume)</td><td style="text-align:center; font-weight:bold; color: #15803d;">{lulus} Orang</td></tr>
                                        <tr><td>Persentase Kelulusan (Passing Rate)</td><td style="text-align:center; font-weight:bold; color: #15803d;">{pct_lulus}</td></tr>
                                    </table>

                                    <h4>3. WAKTU, METODE DAN TEMPAT PEMBELAJARAN</h4>
                                    <p>Pelaksanaan program diorkestrasi menggunakan kerangka kerja operasional berikut:</p>
                                    <ul>
                                        <li><b>Durasi Pelaksanaan:</b> {tgl_mulai} s.d {tgl_selesai}</li>
                                        <li><b>Metode Pembelajaran:</b> {metode}</li>
                                        <li><b>Tempat Pelaksanaan:</b> {tempat}</li>
                                        <li><b>Narasumber/Instruktur:</b> {instruktur}</li>
                                    </ul>

                                    <h4>4. REALISASI BIAYA (EFISIENSI ANGGARAN)</h4>
                                    <p>Optimalisasi sumber daya finansial diukur melalui komparasi Rencana Anggaran Biaya (RAB) terhadap realisasi aktual, guna menjamin <i>Cost Effectiveness</i> kegiatan operasional:</p>
                                    <table class="zebra">
                                        <tr><th style="width: 60%; text-align:center;">Komponen Pembiayaan</th><th style="width: 40%; text-align:center;">Nominal (Rp)</th></tr>
                                        <tr><td>RAB Pelaksanaan (Budgeted)</td><td style="text-align:right;"><b>{rab}</b></td></tr>
                                        <tr><td>Realisasi Biaya Pelaksanaan (Actual)</td><td style="text-align:right; color: #003366;"><b>{realisasi}</b></td></tr>
                                    </table>

                                    <h4 style="page-break-before: always;">5. EVALUASI PEMBELAJARAN (ANALISIS KINERJA MUTU L1)</h4>
                                    <p>Evaluasi Level 1 mengukur kualitas kepuasan pelanggan secara komprehensif. Dengan tingkat partisipasi pengisian (<i>Response Rate</i>) sebesar <b>{pct_isi}</b> ({isi_l1} responden), berikut adalah pemetaan skor kepuasan peserta (Skala 1-5, Target TMP: 4.50):</p>
                                    <table class="zebra">
                                        <tr><th style="width: 10%; text-align:center;">No</th><th style="width: 60%;">Pilar Evaluasi Mutu</th><th style="width: 30%; text-align:center;">Realisasi Skor</th></tr>
                                        <tr><td style="text-align:center;">1</td><td>Kualitas Materi Pembelajaran</td><td style="text-align:center; font-weight:bold;">{skor_mat}</td></tr>
                                        <tr><td style="text-align:center;">2</td><td>Kinerja Instruktur & Fasilitator</td><td style="text-align:center; font-weight:bold;">{skor_ins}</td></tr>
                                        <tr><td style="text-align:center;">3</td><td>Sarana Prasarana Offline (In-Class)</td><td style="text-align:center; font-weight:bold;">{skor_sp_off}</td></tr>
                                        <tr><td style="text-align:center;">4</td><td>Sarana Prasarana Online (Digital)</td><td style="text-align:center; font-weight:bold;">{skor_sp_on}</td></tr>
                                        <tr style="background-color: #f1f5f9;"><td style="text-align:center; font-weight:bold; color:#003366;">5</td><td style="font-weight:bold; color:#003366;">Rata-Rata Komposit Keseluruhan</td><td style="text-align:center; font-weight:bold; color:#003366; font-size:12pt;">{skor_tot}</td></tr>
                                    </table>

                                    <h4>6. CUSTOMER VOICE (KOMENTAR APRESIASI & MASUKAN)</h4>
                                    <p>Analisis kualitatif terhadap sentimen peserta membagi umpan balik menjadi dua pilar utama: Kekuatan Layanan (Apresiasi) dan Area Pengembangan (Masukan):</p>
                                    <table>
                                        <tr><th style="width: 50%; text-align:center; background-color: #0f172a;">Komentar Apresiasi ({jml_pos_kelas})</th><th style="width: 50%; text-align:center; background-color: #0f172a;">Komentar Masukan / Evaluasi ({jml_neg_kelas})</th></tr>
                                        <tr>
                                            <td style="padding: 12px; background-color: #f8fafc;">{pos_html}</td>
                                            <td style="padding: 12px; background-color: #fff1f2;">{neg_html}</td>
                                        </tr>
                                    </table>

                                    <br><br><br>
                                    <table style="width:100%; border: none;">
                                        <tr>
                                            <td style="width:50%; border: none;"></td>
                                            <td style="width:50%; border: none; text-align:center;">
                                                Mengetahui,<br><b>MANAGER UPDL JAKARTA</b><br><br><br><br><br>
                                                <b>( _________________________ )</b>
                                            </td>
                                        </tr>
                                    </table>

                                    <h3 style="page-break-before: always; color:#003366; border-bottom: 2px solid #003366; padding-bottom:5px;">7. LAMPIRAN DOKUMEN</h3>
                                    <p>Berikut adalah kelengkapan administrasi dan bukti pelaksanaan program:</p>
                                    <ul style="line-height:2.0; font-weight:bold; color: #0055A4;">
                                        <li>Lampiran 1: Dasar Surat Penugasan</li>
                                        <li>Lampiran 2: Surat Pemanggilan Peserta</li>
                                        <li>Lampiran 3: Rundown Pelaksanaan</li>
                                        <li>Lampiran 4: Daftar Hadir Peserta (Presensi)</li>
                                        <li>Lampiran 5: Dokumentasi Pelaksanaan / Foto Kegiatan <i>(Silakan paste foto langsung di bawah ini)</i></li>
                                    </ul>
                                </div>
                            </body>
                            </html>
                            """
                            
                            st.success(f"✅ Dokumen Laporan Pembelajaran {judul_pilih} berhasil disusun!")
                            st.download_button(
                                label="📥 DOWNLOAD LAPORAN KELAS (.doc)",
                                data=html_kelas.encode('utf-8'),
                                file_name=f"Laporan_Pelaksanaan_{kode_pemb.replace('.','_')}.doc",
                                mime="application/msword",
                                type="primary"
                            )
                            with st.expander("👀 Pratinjau Desain Dokumen (Live Preview)"):
                                st.markdown(html_kelas, unsafe_allow_html=True)
                else:
                    st.info("⚠️ Belum ada data 'Judul Pembelajaran' yang tersedia di Master Data Laporan.")
            else:
                st.error("Kolom 'Judul Pembelajaran' tidak ditemukan di Master Data Laporan. Pastikan penamaan kolom sudah benar.")
        except Exception as e:
            st.error(f"Gagal memuat Master Data Laporan: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # --- SUB TAB 3: KATALOG INSTRUKTUR ---
    # ─────────────────────────────────────────────────────────────────────────
    with sub_katalog:
        st.markdown("### 👨‍🏫 Katalog & Rapor Instruktur Terbobot")
        st.write("Sistem rekomendasi objektif berbasis **Composite Performance Index** yang menggabungkan kepuasan mutu (`Ins-Rat`) dan stabilitas jam terbang.")
        
        sheet_id_ins = '1IDAmFwTbBQDZcKM3eiiEDcA3KwM9WKqW4zCrk__6-PU'
        url_ins_katalog = "https://docs.google.com/spreadsheets/d/" + str(sheet_id_ins) + "/gviz/tq?tqx=out:csv&sheet=Detail%20Instruktur"
        
        try:
            req_ins = urllib.request.Request(url_ins_katalog, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req_ins) as response_ins:
                df_katalog_raw = pd.read_csv(io.BytesIO(response_ins.read()))
                
            df_katalog_raw.columns = df_katalog_raw.columns.astype(str).str.strip()
            
            if not df_katalog_raw.empty:
                for c in ['Ins-Eng', 'Ins-Rel', 'Ins-Sat', 'Ins-Rat', 'Durasi Mengajar']:
                    if c in df_katalog_raw.columns:
                        df_katalog_raw[c] = pd.to_numeric(df_katalog_raw[c], errors='coerce')
                
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    if 'UPDL' in df_katalog_raw.columns:
                        list_updl = ["Semua UPDL"] + list(df_katalog_raw['UPDL'].dropna().unique())
                        selected_updl = st.selectbox("🏢 Pilih UPDL Penyelenggara:", list_updl, key="k_updl")
                    else:
                        selected_updl = "Semua UPDL"
                        st.info("ℹ️ Kolom UPDL belum terdeteksi. Silakan upload data baru.")
                        
                with col_f2:
                    if selected_updl != "Semua UPDL" and 'UPDL' in df_katalog_raw.columns:
                        df_filt_updl = df_katalog_raw[df_katalog_raw['UPDL'] == selected_updl]
                    else:
                        df_filt_updl = df_katalog_raw
                        
                    if 'Judul Diklat' in df_filt_updl.columns:
                        list_diklat = ["Semua Pembelajaran"] + list(df_filt_updl['Judul Diklat'].dropna().unique())
                    else:
                        list_diklat = ["Semua Pembelajaran"]
                    selected_diklat = st.selectbox("📚 Pilih Judul Pembelajaran:", list_diklat, key="k_diklat")
                
                with st.expander("⚖️ Konfigurasi Pembobotan & Ambang Batas Rekomendasi", expanded=False):
                    col_w1, col_w2 = st.columns([3, 2])
                    with col_w1:
                        bobot_skor = st.slider("Bobot Skor Mutu Kepuasan (%):", min_value=10, max_value=90, value=70, step=5, key="w_skor")
                        bobot_jam = 100 - bobot_skor
                        st.caption(f"Proporsi: **{bobot_skor}% Mutu Evaluasi** : **{bobot_jam}% Jam Terbang**")
                    with col_w2:
                        min_jam_terbang = st.number_input("Syarat Minimal Mengajar (Threshold Top Rekomendasi):", min_value=1, max_value=10, value=2, step=1, key="min_jt")
                        st.caption(f"Instruktur dengan jam terbang < {min_jam_terbang} kali akan ditandai sebagai *Evaluasi Awal*.")

                if selected_diklat != "Semua Pembelajaran":
                    df_final_kat = df_filt_updl[df_filt_updl['Judul Diklat'] == selected_diklat]
                else:
                    df_final_kat = df_filt_updl
                    
                if not df_final_kat.empty and 'Nama' in df_final_kat.columns:
                    agg_dict = {
                        'Skor_Akhir_InsRat': ('Ins-Rat', 'mean'),
                        'Avg_Engagement': ('Ins-Eng', 'mean'),
                        'Avg_Relevance': ('Ins-Rel', 'mean'),
                        'Avg_Satisfaction': ('Ins-Sat', 'mean'),
                        'Frekuensi_Mengajar': ('Nama', 'count')
                    }
                    if 'Durasi Mengajar' in df_final_kat.columns:
                        agg_dict['Total_Durasi_Jam'] = ('Durasi Mengajar', 'sum')

                    df_kat_grouped = df_final_kat.groupby(['Nama']).agg(**agg_dict).reset_index()
                    
                    w_mutu_dec = bobot_skor / 100.0
                    w_jam_dec = bobot_jam / 100.0
                    
                    df_kat_grouped['Norm_Skor'] = df_kat_grouped['Skor_Akhir_InsRat'] / 5.0
                    max_frek = df_kat_grouped['Frekuensi_Mengajar'].max()
                    if pd.isna(max_frek) or max_frek == 0: max_frek = 1
                    df_kat_grouped['Norm_Jam'] = df_kat_grouped['Frekuensi_Mengajar'] / max_frek
                    
                    df_kat_grouped['Indeks_Rekomendasi'] = (
                        (df_kat_grouped['Norm_Skor'] * w_mutu_dec) + 
                        (df_kat_grouped['Norm_Jam'] * w_jam_dec)
                    ) * 100.0
                    
                    df_kat_grouped['Status_Eligible'] = df_kat_grouped['Frekuensi_Mengajar'].apply(
                        lambda x: "Eligible" if x >= min_jam_terbang else f"Evaluasi Awal (< {min_jam_terbang}x)"
                    )
                    
                    df_kat_grouped = df_kat_grouped.sort_values(by='Indeks_Rekomendasi', ascending=False).reset_index(drop=True)
                    df_eligible = df_kat_grouped[df_kat_grouped['Status_Eligible'] == "Eligible"]
                    
                    if selected_diklat != "Semua Pembelajaran":
                        st.markdown("### 🏆 Top Rekomendasi Instruktur")
                        if not df_eligible.empty:
                            top_n = min(3, len(df_eligible))
                            cols = st.columns(top_n)
                            for i in range(top_n):
                                with cols[i]:
                                    nama_ins = df_eligible['Nama'].iloc[i]
                                    skor_ins = df_eligible['Skor_Akhir_InsRat'].iloc[i]
                                    jam_ins = df_eligible['Frekuensi_Mengajar'].iloc[i]
                                    indeks_ins = df_eligible['Indeks_Rekomendasi'].iloc[i]
                                    
                                    st.metric(
                                        label=f"🥇 Peringkat {i+1}: {nama_ins}",
                                        value=f"{indeks_ins:.1f} Poin",
                                        delta=f"{skor_ins:.2f} ⭐ | {jam_ins}x Mengajar",
                                        delta_color="normal"
                                    )
                        else:
                            st.warning(f"⚠️ Belum ada instruktur yang memenuhi syarat minimal {min_jam_terbang} kali mengajar untuk pembelajaran ini.")
                        st.markdown("---")
                        
                    st.subheader("📋 Detail Rapor & Peringkat Komposit")
                    show_kategori = st.checkbox("Tampilkan Detail Sub-Kategori (Ins-Eng, Ins-Rel, Ins-Sat)", value=True, key="k_showkat")
                    
                    display_cols = ['Nama', 'Indeks_Rekomendasi', 'Skor_Akhir_InsRat', 'Frekuensi_Mengajar', 'Status_Eligible']
                    if 'Total_Durasi_Jam' in df_kat_grouped.columns:
                        display_cols.insert(4, 'Total_Durasi_Jam')
                        
                    if show_kategori:
                        display_cols += ['Avg_Engagement', 'Avg_Relevance', 'Avg_Satisfaction']
                        
                    col_cfg = {
                        "Nama": st.column_config.TextColumn("Nama Instruktur"),
                        "Indeks_Rekomendasi": st.column_config.NumberColumn("Indeks Rekomendasi", format="%.1f 🎯", help="Hasil gabungan terbobot Mutu Evaluasi dan Jam Terbang"),
                        "Skor_Akhir_InsRat": st.column_config.NumberColumn("Skor Mutu (Ins-Rat)", format="%.2f ⭐"),
                        "Frekuensi_Mengajar": st.column_config.NumberColumn("Jam Terbang (Kali)"),
                        "Status_Eligible": st.column_config.TextColumn("Status Kualifikasi"),
                        "Avg_Engagement": st.column_config.NumberColumn("Engagement", format="%.2f"),
                        "Avg_Relevance": st.column_config.NumberColumn("Relevance", format="%.2f"),
                        "Avg_Satisfaction": st.column_config.NumberColumn("Satisfaction", format="%.2f"),
                    }
                    if 'Total_Durasi_Jam' in df_kat_grouped.columns:
                        col_cfg["Total_Durasi_Jam"] = st.column_config.NumberColumn("Total Jam Mengajar (JP/Jam)", format="%.1f")

                    st.dataframe(
                        df_kat_grouped[display_cols],
                        use_container_width=True,
                        hide_index=True,
                        column_config=col_cfg
                    )
                else:
                    st.info("⚠️ Data instruktur tidak ditemukan untuk kriteria pencarian ini.")
            else:
                st.warning("⚠️ Database Instruktur kosong atau belum ditarik dari Google Sheets.")
        except Exception as e:
            st.error(f"Gagal memuat data Katalog Instruktur: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# KONTEN: ⚙️ PENGATURAN
# ══════════════════════════════════════════════════════════════════════════════
elif menu_selection == "⚙️ PENGATURAN":
    st.subheader("⚙️ Pengaturan Aplikasi")
    with st.container(border=True):
        st.markdown("#### 🔗 Konfigurasi Google Sheets (Target Master Data Laporan)")
        nama_sheet = st.text_input("Nama File Google Sheets Utama", value=st.session_state["setting_sheet"])

        st.markdown("---")
        st.markdown("#### 📋 Nama Tab (Worksheet) Tujuan Data Pipeline")
        col_ws1, col_ws2, col_ws3 = st.columns(3)
        with col_ws1: nama_worksheet     = st.text_input("Tab — L1 & L2 (Legacy)", value=st.session_state["setting_worksheet"])
        with col_ws2: nama_ws_master     = st.text_input("Tab — Master Laporan (Baru)", value=st.session_state["setting_ws_master"])
        with col_ws3: nama_ws_instruktur = st.text_input("Tab — Detail Instruktur", value=st.session_state["setting_ws_instruktur"])

        st.markdown("---")
        st.markdown("#### 📅 Cut-off & Threshold")
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            cutoff_hari = st.number_input("Hari Cut-off Laporan Setelah Tanggal Selesai", min_value=1, max_value=30, value=st.session_state["setting_cutoff"])
        with col_s2:
            threshold_valid = st.slider("Minimal Persentase Pengisian Menjadi VALID", 0.10, 1.0, value=st.session_state["setting_threshold"], step=0.01, format="%.2f")
            st.info(f"Jika Partisipasi Isi ≥ {threshold_valid:.0%}, maka = **VALID**")

        if st.button("💾 Simpan Pengaturan", use_container_width=True, type="primary"):
            st.session_state["setting_sheet"]         = nama_sheet
            st.session_state["setting_worksheet"]     = nama_worksheet
            st.session_state["setting_ws_master"]     = nama_ws_master
            st.session_state["setting_ws_instruktur"] = nama_ws_instruktur
            st.session_state["setting_cutoff"]        = cutoff_hari
            st.session_state["setting_threshold"]     = threshold_valid
            st.success("✅ Pengaturan berhasil disimpan! Sistem akan merujuk ke tab Master Data Anda.")
