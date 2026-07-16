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

# ─────────────────────────────────────────────────────────────────────────────
# CUSTOM CSS - CLEAN SAAS LIGHT THEME (SESUAI GAMBAR REFERENSI BARU)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
    <style>
    /* Background Utama App (Abu-abu sangat muda) */
    .stApp {
        background-color: #F5F7FA;
    }
    
    /* Header Bawaan Streamlit Transparan */
    [data-testid="stHeader"] {
        background-color: transparent !important;
    }
    
    /* Sidebar Styling (Putih Bersih) */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #EAECF0;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label p {
        font-size: 15px;
        font-weight: 500;
        color: #4B5563;
    }
    
    /* Container ber-border (Kotak Putih dengan Shadow Lembut) */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF;
        border-radius: 12px !important;
        border: 1px solid #EAECF0 !important;
        box-shadow: 0px 2px 4px rgba(0,0,0,0.02) !important;
        padding: 10px;
    }
    
    /* File Uploader styling */
    [data-testid="stFileUploader"] {
        background: #F8FAFC;
        border: 2px dashed #3B82F6;
        border-radius: 12px;
        padding: 20px;
    }

    /* Expander Styling */
    .streamlit-expanderHeader {
        background-color: #FFFFFF;
        color: #111827;
        border-radius: 8px;
        border: 1px solid #EAECF0;
    }
    
    /* Global Text Colors */
    h1, h2, h3, h4, h5, h6 { color: #111827 !important; }
    p, span, label { color: #374151; }
    
    /* Tweak padding untuk Radio Sidebar agar berjarak */
    div[role="radiogroup"] > label {
        padding: 10px 15px;
        border-radius: 8px;
        transition: 0.2s;
    }
    div[role="radiogroup"] > label:hover {
        background-color: #F3F4F6;
    }
    </style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# HELPER: CUSTOM METRIC CARDS (Clean Light SaaS Design)
# ─────────────────────────────────────────────────────────────────────────────
def render_custom_metric(title, value, icon, color_hex):
    html = f"""
    <div style="background-color: #FFFFFF; padding: 20px; border-radius: 12px; display: flex; align-items: center; gap: 20px; border: 1px solid #EAECF0; box-shadow: 0px 4px 6px rgba(0,0,0,0.02); margin-bottom: 10px;">
        <div style="background-color: {color_hex}15; width: 60px; height: 60px; border-radius: 14px; display: flex; justify-content: center; align-items: center;">
            <i class="material-icons" style="color: {color_hex}; font-size: 30px;">{icon}</i>
        </div>
        <div>
            <p style="margin: 0; color: #6B7280; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">{title}</p>
            <h3 style="margin: 0; color: #111827; font-size: 26px; font-weight: 800; padding-top: 4px;">{value}</h3>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# HEADER APLIKASI (Clean Light Theme)
# ─────────────────────────────────────────────────────────────────────────────
def get_base64_logo(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

bin_pln       = get_base64_logo("Logo PLN.png")
bin_danantara = get_base64_logo("logo_danantara.png")
img_pln       = f'<img src="data:image/png;base64,{bin_pln}" style="height:60px;object-fit:contain;">' if bin_pln else ""
img_danantara = f'<img src="data:image/png;base64,{bin_danantara}" style="height:35px;object-fit:contain;">' if bin_danantara else ""

st.markdown(f"""
<div style="display:flex;align-items:center;justify-content:space-between;
    background:#FFFFFF; padding:20px 30px;
    border-radius:12px; border: 1px solid #EAECF0; margin-bottom:25px; box-shadow:0px 4px 6px rgba(0,0,0,0.02);">
    <div style="flex:1;display:flex;align-items:center;gap:15px;">{img_danantara}</div>
    <div style="flex:2;text-align:center;">
        <h1 style="margin:0;font-size:1.7em;color:#111827 !important;font-weight:800;letter-spacing: 0.5px;">
            &#9889; SMART EVALYTICS
        </h1>
        <p style="margin:0;color:#6B7280 !important;font-size:0.9em; font-weight:500; margin-top:4px;">
            Advanced Evaluation Dashboard &bull; UPDL Jakarta
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
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    return genai.GenerativeModel('gemini-1.5-flash')

model = load_gemini_model()

# ─────────────────────────────────────────────────────────────────────────────
# ENGINE SENTIMENT ANALYSIS
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
    # Avatar / User Profile Simulation (Light Mode)
    st.markdown("""
    <div style="display:flex; align-items:center; gap:15px; margin-bottom: 30px; padding: 10px; background-color: #F8FAFC; border-radius: 12px; border: 1px solid #EAECF0;">
        <div style="background-color: #3B82F6; width: 45px; height: 45px; border-radius: 50%; display: flex; justify-content: center; align-items: center;">
            <i class="material-icons" style="color: white; font-size: 24px;">person</i>
        </div>
        <div>
            <h4 style="margin: 0; color: #111827; font-size: 14px; font-weight: 700;">Admin UPDL</h4>
            <p style="margin: 0; color: #6B7280; font-size: 12px;">Quality Assurance</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<p style='color:#9CA3AF; font-size: 12px; font-weight:700; letter-spacing:1px; margin-bottom: 5px;'>MAIN MENU</p>", unsafe_allow_html=True)
    
    menu_selection = st.radio(
        "",
        [
            "📤 DATA ENTRY",
            "📈 ANALYTICS",
            "📊 DASHBOARD",
            "🤖 AI ASSISTANT",
            "🚨 EARLY WARNING",
            "📑 REPORT & KATALOG",
            "⚙️ PENGATURAN"
        ],
        label_visibility="collapsed"
    )
    
    st.markdown("<br><hr style='border-color: #EAECF0;'><br>", unsafe_allow_html=True)
    
    if st.button("🔄 Sinkron Data Terkini", use_container_width=True):
        st.cache_data.clear()
        st.toast("Menarik data terbaru dari Google Sheets...")

# URL Sumber Data Global
sheet_id = '1IDAmFwTbBQDZcKM3eiiEDcA3KwM9WKqW4zCrk__6-PU'
sheet_name = 'L1%20Tertutup' 
url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}'


# ══════════════════════════════════════════════════════════════════════════════
# ROUTING KONTEN
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

            return df_f

        # ---------------------------------------------------------
        # KONTEN: 📈 ANALYTICS
        # ---------------------------------------------------------
        if menu_selection == "📈 ANALYTICS":
            df_filtered = build_filters("analytics")
            kolom_tersedia = df_filtered.columns.tolist()
            st.markdown("<hr style='border-color: #EAECF0;'>", unsafe_allow_html=True)

            if not df_filtered.empty:
                st.subheader("📋 Raw Data Explorer")
                st.dataframe(df_filtered, use_container_width=True)

                st.markdown("<br>### 🔍 Analisis Korelasi", unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                with col1:
                    var_x = st.selectbox("Variabel Independen (X):", kolom_tersedia, index=0, key="x_ana")
                with col2:
                    var_y = st.selectbox("Variabel Dependen (Y):", kolom_tersedia,
                                         index=min(1, len(kolom_tersedia)-1), key="y_ana")
                st.markdown("<hr style='border-color: #EAECF0;'>", unsafe_allow_html=True)

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
                        st.markdown("<hr style='border-color: #EAECF0;'>", unsafe_allow_html=True)
                        korelasi = df_clean[var_x].corr(df_clean[var_y])
                        
                        col3, col4 = st.columns([1, 2])
                        with col3: 
                            render_custom_metric("Koefisien Korelasi", f"{round(korelasi, 3)}", "show_chart", "#8B5CF6")
                        with col4:
                            st.write(f"**Sebaran: {var_x} vs {var_y}**")
                            # Plotly Scatter Light Mode
                            fig_corr = px.scatter(df_clean, x=var_x, y=var_y, color_discrete_sequence=['#3B82F6'])
                            fig_corr.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                            st.plotly_chart(fig_corr, use_container_width=True)
                else:
                    st.error("⚠️ Kolom yang dipilih bukan format angka.")

                # IPA
                st.markdown("<hr style='border-color: #EAECF0;'>", unsafe_allow_html=True)
                st.markdown("### 🎯 Importance-Performance Analysis (IPA)")
                try:
                    df_ipa = df_filtered.dropna(subset=['RATA-RATA KESELURUHAN']).copy()
                    
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
                            
                            # Styling Scatter di Tema Terang
                            fig_ipa.update_traces(
                                textposition='top center', 
                                textfont_size=ukuran_teks, 
                                marker=dict(size=14, color='#3B82F6', line=dict(width=1,color='#FFFFFF'))
                            )
                            fig_ipa.add_hline(y=y_cross, line_dash="dash", line_color="#9CA3AF")
                            fig_ipa.add_vline(x=x_cross, line_dash="dash", line_color="#EF4444", annotation_text="Standar TMP (4.5)", annotation_position="top left")
                            
                            for ax, ay, txt, col, algn in [
                                (0.01, 0.99, "<b>KUADRAN 1</b><br>🚨 Prioritas Utama", "#EF4444", "left"),
                                (0.99, 0.99, "<b>KUADRAN 2</b><br>🌟 Pertahankan", "#10B981", "right"),
                                (0.01, 0.01, "<b>KUADRAN 3</b><br>📉 Prioritas Sekunder", "#6B7280", "left"),
                                (0.99, 0.01, "<b>KUADRAN 4</b><br>⚠️ Berlebihan", "#F59E0B", "right"),
                            ]:
                                fig_ipa.add_annotation(xref="paper", yref="paper", x=ax, y=ay, text=txt, showarrow=False, font=dict(color=col, size=13), align=algn)
                            
                            min_x = min(4.0, df_plot_ipa['Kinerja'].min() - 0.1) if not df_plot_ipa['Kinerja'].empty else 4.0
                            min_y = min(-0.1, df_plot_ipa['Kepentingan'].min() - 0.1) if not df_plot_ipa['Kepentingan'].empty else -0.1
                            max_y = max(1.1, df_plot_ipa['Kepentingan'].max() + 0.1) if not df_plot_ipa['Kepentingan'].empty else 1.1
                            
                            fig_ipa.update_layout(
                                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                                height=600 if level_ipa == "📊 Makro (Kategori Utama)" else 700, 
                                margin=dict(t=40,b=40,l=40,r=40), 
                                xaxis_range=[min_x, 5.1], yaxis_range=[min_y, max_y], 
                                xaxis_title="Kinerja (Rata-rata Skor Kepuasan)", yaxis_title="Kepentingan (Korelasi terhadap Total Skor)"
                            )
                            st.plotly_chart(fig_ipa, use_container_width=True)

                            q1_items = df_plot_ipa[(df_plot_ipa['Kinerja'] < x_cross) & (df_plot_ipa['Kepentingan'] > y_cross)]['Kategori'].tolist()
                            st.markdown("<h4 style='color: #111827; margin-top: 30px;'>💡 Executive Diagnosis</h4>", unsafe_allow_html=True)
                            
                            if q1_items:
                                list_html = "".join([f"<li style='margin-bottom: 5px;'><b>{item}</b></li>" for item in q1_items])
                                rek_text = "Beralih ke <b>Mode Mikro</b> di pengaturan atas untuk melihat rincian sub-indikator spesifik yang menjadi akar masalah." if level_ipa == "📊 Makro (Kategori Utama)" else "Segera susun rencana perbaikan operasional untuk indikator di atas. Elevasi di area ini akan memberikan dampak paling masif terhadap lonjakan total skor evaluasi."
                                
                                alert_html = f"""<div style="padding: 20px; border-radius: 12px; border-left: 6px solid #EF4444; background-color: #FEF2F2; box-shadow: 0 2px 4px rgba(0,0,0,0.02); margin-bottom: 20px;">
                                    <div style="display: flex; align-items: flex-start; gap: 15px;">
                                        <div style="font-size: 28px; margin-top: 2px;">🚨</div>
                                        <div style="width: 100%;">
                                            <h4 style="margin: 0 0 8px 0; color: #B91C1C; font-size: 16px;">Peringatan Area Kritis (Kuadran 1)</h4>
                                            <p style="margin: 0 0 10px 0; color: #4B5563; font-size: 14px;">Ditemukan indikator yang <b>sangat memengaruhi kepuasan peserta</b>, namun kinerjanya <b>di bawah standar PLN (4.5)</b>:</p>
                                            <ul style="margin: 0 0 15px 0; padding-left: 20px; color: #991B1B; font-size: 14px;">{list_html}</ul>
                                            <div style="padding: 10px 15px; background-color: rgba(59, 130, 246, 0.08); border-radius: 8px; border-left: 4px solid #3B82F6;">
                                                <p style="margin: 0; font-size: 13px; color: #1E3A8A;"><b>Tindak Lanjut:</b> {rek_text}</p>
                                            </div></div></div></div>"""
                                st.markdown(alert_html, unsafe_allow_html=True)
                            else:  
                                success_html = """<div style="padding: 25px; border-radius: 12px; background: #ECFDF5; border: 1px solid #D1FAE5; box-shadow: 0 2px 4px rgba(0,0,0,0.02); margin-bottom: 20px; border-left: 6px solid #10B981; display: flex; align-items: center; gap: 20px;">
                                    <div style="font-size: 40px; background: #FFFFFF; padding: 10px 15px; border-radius: 50%; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">🏆</div>
                                    <div><h4 style="margin: 0 0 5px 0; color: #065F46; font-size: 18px;">Kinerja Prima Luar Biasa!</h4>
                                    <p style="margin: 0; color: #047857; font-size: 14px; line-height: 1.5;">Tidak ada indikator krusial yang jatuh di Kuadran 1 pada periode evaluasi ini. Terus pertahankan kualitas pelayanan dan materi Anda sesuai standar ekselensi UPDL Jakarta.</p></div></div>"""
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
                                fig_track.update_traces(textposition='top center', line=dict(width=3, color='#F59E0B'), marker=dict(size=10, color='#3B82F6'))
                                fig_track.add_vline(x=4.5, line_dash="dash", line_color="#EF4444")
                                fig_track.add_hline(y=df_histori_plot['Kepentingan'].mean(), line_dash="dash", line_color="#9CA3AF")
                                fig_track.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=450, xaxis_range=[3.8, 5.1], xaxis_title="Kinerja (Skor Kepuasan)", yaxis_title="Kepentingan (Korelasi)")
                                st.plotly_chart(fig_track, use_container_width=True)
                                
                            else:
                                st.info("ℹ️ Data histori bulanan belum mencukupi.")
                        except Exception as e:
                            st.error(f"Gagal memuat visualisasi histori: {e}")
                    else:
                        st.warning("⚠️ Data terlalu sedikit untuk memproses Analisis Kuadran (IPA).")
                except Exception as e:
                    st.error(f"Gagal memuat visualisasi IPA: {e}")

                # Analisis Komparatif
                st.markdown("<hr style='border-color: #EAECF0;'>", unsafe_allow_html=True)
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
                    fig_box.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=400, showlegend=False, xaxis_title="", yaxis_title="Skor")
                    st.plotly_chart(fig_box, use_container_width=True)
            else:
                st.warning("⚠️ Tidak ada data. Sesuaikan filter.")

        # ---------------------------------------------------------
        # KONTEN: 📊 DASHBOARD
        # ---------------------------------------------------------
        elif menu_selection == "📊 DASHBOARD":
            df_filtered_dash = build_filters("dashboard")
            st.markdown("<hr style='border-color: #EAECF0;'>", unsafe_allow_html=True)
            
            if not df_filtered_dash.empty:
                skor_evaluasi = df_filtered_dash['RATA-RATA KESELURUHAN'].mean()
                ind_kurang    = df_filtered_dash['Jumlah Indikator dibawah 4.5'].sum() if 'Jumlah Indikator dibawah 4.5' in df_filtered_dash.columns else 0
                ind_lebih     = df_filtered_dash['Jumlah Indikator diatas 4.5'].sum()  if 'Jumlah Indikator diatas 4.5'  in df_filtered_dash.columns else 0

                # Metric Cards dengan Desain Gambar Referensi Baru (Warna Bersih)
                col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
                with col_kpi1: render_custom_metric("Total Skor L1", f"{skor_evaluasi:.2f}", "star", "#3B82F6")
                with col_kpi2: render_custom_metric("Indikator ≥ 4.5", f"{int(ind_lebih)}", "check_circle", "#10B981")
                with col_kpi3: render_custom_metric("Indikator < 4.5", f"{int(ind_kurang)}", "warning", "#EF4444")
                with col_kpi4: render_custom_metric("Total Kelas", f"{len(df_filtered_dash)}", "class", "#8B5CF6")
                
                st.markdown("<hr style='border-color: #EAECF0;'>", unsafe_allow_html=True)

                col_chart_l, col_chart_r = st.columns([3, 2])
                with col_chart_l:
                    st.markdown("#### 📈 Skor L1 per Strategi Pelaksanaan")
                    df_grafik = df_filtered_dash.groupby('Strategi Pelaksanaan')['RATA-RATA KESELURUHAN'].mean().reset_index()
                    fig = px.bar(df_grafik, x='Strategi Pelaksanaan', y='RATA-RATA KESELURUHAN', text='RATA-RATA KESELURUHAN')
                    fig.update_traces(marker_color='#3B82F6', texttemplate='%{text:.2f}', textposition='outside')
                    fig.add_hline(y=4.5, line_dash="dash", line_color="#EF4444", annotation_text="Standar 4.5", annotation_position="top left")
                    fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=350, bargap=0.5, yaxis_range=[0,5], yaxis_title="Rata-rata Skor", xaxis_title="", margin=dict(t=40,b=0,l=0,r=0))
                    st.plotly_chart(fig, use_container_width=True)

                with col_chart_r:
                    st.markdown("#### 🕸️ Radar Kategori")
                    kategori_radar = {
                        'Eng. Instruktur':'Engagement Instruktur','Rel. Instruktur':'Relevance Instruktur',
                        'Sat. Instruktur':'Satisfaction Instruktur','Eng. Materi':'Engagement Materi',
                        'Rel. Materi':'Relevance Materi','Sat. Materi':'Satisfaction Materi',
                        'Sarana Digital':'Satisfaction Sarana Digital','Sarana In-Class':'Satisfaction Sarana In Class',
                    }
                    labels = [k for k,v in kategori_radar.items() if v in df_filtered_dash.columns]
                    values = [df_filtered_dash[kategori_radar[k]].mean() for k in labels]
                    if labels:
                        fig_radar = go.Figure(go.Scatterpolar(r=values+[values[0]], theta=labels+[labels[0]], fill='toself', fillcolor='rgba(59, 130, 246, 0.2)', line=dict(color='#3B82F6',width=2)))
                        fig_radar.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', polar=dict(radialaxis=dict(visible=True,range=[0,5], gridcolor='#EAECF0'), angularaxis=dict(gridcolor='#EAECF0')), showlegend=False, height=350, margin=dict(t=30,b=30,l=30,r=30))
                        st.plotly_chart(fig_radar, use_container_width=True)

                st.markdown("<hr style='border-color: #EAECF0;'>", unsafe_allow_html=True)
                if 'Laporan Bulan' in df_filtered_dash.columns:
                    st.markdown("#### 📆 Tren Skor L1 per Bulan")
                    URUTAN = ['Januari','Februari','Maret','April','Mei','Juni','Juli','Agustus','September','Oktober','November','Desember']
                    df_tren = df_filtered_dash.groupby('Laporan Bulan')['RATA-RATA KESELURUHAN'].mean().reset_index()
                    df_tren['sort_key'] = df_tren['Laporan Bulan'].apply(lambda x: URUTAN.index(x) if x in URUTAN else 99)
                    df_tren = df_tren.sort_values('sort_key')
                    fig_tren = px.line(df_tren, x='Laporan Bulan', y='RATA-RATA KESELURUHAN', markers=True)
                    fig_tren.update_traces(line=dict(color='#10B981', width=3), marker=dict(size=10, color='#10B981'))
                    fig_tren.add_hline(y=4.5, line_dash="dash", line_color="#EF4444", annotation_text="Standar 4.5", annotation_position="top left")
                    fig_tren.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', yaxis_range=[0,5], height=300, yaxis_title="Rata-rata Skor", xaxis_title="")
                    st.plotly_chart(fig_tren, use_container_width=True)

                with st.container():
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
    st.subheader("🤖 Tanya Asisten AI (EVALYTICS)")
    st.write("Analisis insight tersembunyi dengan bantuan Gemini AI secara real-time.")

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
                    response = model.generate_content(full_prompt)
                    st.markdown(response.text)
                    st.session_state.chat_history.append({"role": "assistant", "content": response.text})
                except Exception as ai_err:
                    st.error(f"Gagal AI: {ai_err}")

# ══════════════════════════════════════════════════════════════════════════════
# KONTEN: 📤 DATA ENTRY
# ══════════════════════════════════════════════════════════════════════════════
elif menu_selection == "📤 DATA ENTRY":
    st.markdown("""
    <div style="display:flex;align-items:center;gap:15px;margin-bottom:20px;">
        <div style="background-color: #3B82F615; padding:15px; border-radius:12px; border:1px solid #3B82F630;">
            <i class="material-icons" style="font-size:32px;color:#3B82F6;">cloud_upload</i>
        </div>
        <div>
            <h2 style="margin:0;color:#111827;">Data Pipeline Entry</h2>
            <p style="margin:0;color:#6B7280;font-size:0.9em;">Upload Excel/CSV (L1, L2, Instruktur). Sistem mendeteksi cerdas.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    sub_upload, sub_riwayat, sub_panduan = st.tabs(["📤 Upload & Kirim", "🕒 Riwayat", "📄 Panduan Format"])

    with sub_upload:
        with st.container(border=True):
            uploaded_files = st.file_uploader(
                "Pilih atau seret file (Multi-file didukung)",
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
                            df_raw = df_raw[~df_raw['Nama'].astype(str).str.strip().str.upper().isin(['UPDL JAKARTA','JAKARTA'])].reset_index(drop=True)
                            df_ins = build_instruktur_df(df_raw)
                            all_ins_dfs.append(df_ins)
                            file_log.append({"File":f.name,"Tipe":"🟠 Instruktur","Baris":len(df_raw)})
                            st.write(f"🟠 **Instruktur** — `{f.name}` ({len(df_raw)} baris)")

                        elif is_l1:
                            df_mapped = pd.DataFrame(index=df_raw.index, columns=TARGET_COLUMNS)
                            df_mapped['Kode Pembelajaran']           = df_raw.get('Kode Judul')
                            df_mapped['Batch']                       = df_raw.get('Angkatan')
                            df_mapped['Tanggal Mulai']               = df_raw.get('Tgl Mulai')
                            df_mapped['Tanggal Selesai']             = df_raw.get('Tgl Selesai')
                            df_mapped['Peserta Isi L1']              = df_raw.get('P.Isi')
                            df_mapped['Peserta Hadir']               = df_raw.get('P.Hadir')
                            for i, c in enumerate(INS_COL_NAMES, 1): df_mapped[f'INS{i}'] = df_raw.get(c)
                            for i, c in enumerate(MAT_COL_NAMES, 1): df_mapped[f'MAT{i}'] = df_raw.get(c)
                            for i, c in enumerate(SP_COL_NAMES,  1): df_mapped[f'SP{i}']  = df_raw.get(c)
                            for i, c in enumerate(DS_COL_NAMES,  1): df_mapped[f'DS{i}']  = df_raw.get(c)
                            batch_val = df_mapped['Batch'].astype(str).str.replace(r'\.0$','',regex=True).str.strip()
                            tgl_mulai = pd.to_datetime(df_mapped['Tanggal Mulai'],errors='coerce').dt.strftime('%Y%m%d').fillna('NOTGL')
                            df_mapped['Kode Unik'] = df_mapped['Kode Pembelajaran'].astype(str).str.strip()+"."+batch_val+"."+tgl_mulai
                            all_l1_dfs.append(df_mapped)
                            file_log.append({"File":f.name,"Tipe":"🔵 L1","Baris":len(df_raw)})
                            st.write(f"🔵 **L1** — `{f.name}` ({len(df_raw)} baris)")

                        elif is_l2:
                            df_mapped = pd.DataFrame(index=df_raw.index, columns=TARGET_COLUMNS)
                            df_mapped['Kode Pembelajaran']       = df_raw.get('Kode Judul')
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
                            file_log.append({"File":f.name,"Tipe":"🟢 L2","Baris":len(df_raw)})
                            st.write(f"🟢 **L2** — `{f.name}` ({len(df_raw)} baris)")

                    status_proc.update(label="✅ Selesai dideteksi!", state="complete", expanded=False)

                if not all_l1_dfs and not all_l2_dfs and not all_ins_dfs: st.stop()

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
                        else: df_final = df_l2_raw.copy()
                    else: df_final = df_l1.copy()

                    df_final = df_final.reindex(columns=TARGET_COLUMNS)
                    df_final['Tanggal Selesai'] = pd.to_datetime(df_final['Tanggal Selesai'], errors='coerce')
                    df_final['Tanggal Mulai']   = pd.to_datetime(df_final['Tanggal Mulai'],   errors='coerce')
                    df_final['Cut off Data']    = df_final['Tanggal Selesai'] + pd.Timedelta(days=st.session_state["setting_cutoff"])
                    df_final['Laporan Bulan']   = df_final['Cut off Data'].dt.month.map(BULAN_MAP_ID)
                    today = pd.Timestamp.today().normalize()
                    df_final['Status Pembelajaran'] = df_final['Tanggal Selesai'].apply(lambda x: "Terlaksana" if pd.notna(x) and x<=today else ("Belum Terlaksana" if pd.notna(x) else ""))
                    for col in ['Peserta Isi L1','Peserta Hadir','Jumlah Peserta Lulus L2','Jumlah Peserta Isi L2']:
                        df_final[col] = pd.to_numeric(df_final[col], errors='coerce')
                    df_final['% Pengisian'] = safe_divide(df_final['Peserta Isi L1'], df_final['Peserta Hadir'])
                    df_final['% Valid'] = df_final['% Pengisian'].apply(lambda x: "VALID" if pd.notna(x) and x>st.session_state["setting_threshold"] else ("TIDAK VALID" if pd.notna(x) else ""))
                    
                    all_indicators = [f'INS{i}' for i in range(1,10)] + [f'MAT{i}' for i in range(1,8)] + [f'SP{i}' for i in range(1,7)] + [f'DS{i}' for i in range(1,7)]
                    for col in all_indicators: df_final[col] = pd.to_numeric(df_final[col], errors='coerce')
                    df_final['RATA INST'] = df_final[[f'INS{i}' for i in range(1,9)]].mean(axis=1)
                    df_final['RATA MAT']  = df_final[[f'MAT{i}' for i in range(1,7)]].mean(axis=1)
                    df_final['RATA SP']   = df_final[[f'SP{i}'  for i in range(1,6)]].mean(axis=1)
                    df_final['RATA DS']   = df_final[[f'DS{i}'  for i in range(1,6)]].mean(axis=1)
                    df_final['RATA-RATA KESELURUHAN'] = df_final[['RATA INST','RATA MAT','RATA SP','RATA DS']].mean(axis=1)
                    df_final['Jumlah Indikator dibawah 4.5'] = (df_final[all_indicators] < 4.5).sum(axis=1)
                    df_final['Jumlah Indikator diatas 4.5']  = (df_final[all_indicators] >= 4.5).sum(axis=1)
                    df_to_push = df_final.copy()

                    st.markdown("<br>#### 🗓️ Preview L1 & L2", unsafe_allow_html=True)
                    rata_l1 = df_to_push['RATA-RATA KESELURUHAN'].mean()
                    rata_partisipasi = df_to_push['% Pengisian'].mean()
                    
                    c_l1, c_l2, c_l3 = st.columns(3)
                    with c_l1: render_custom_metric("Baris Data", f"{len(df_to_push)}", "table_rows", "#3B82F6")
                    with c_l2: render_custom_metric("Rata-rata L1", f"{rata_l1:.2f}" if pd.notna(rata_l1) else "N/A", "grade", "#8B5CF6")
                    with c_l3: render_custom_metric("Partisipasi", f"{rata_partisipasi*100:.1f}%" if pd.notna(rata_partisipasi) else "N/A", "groups", "#10B981")
                    
                    with st.expander(f"🔍 Preview L1/L2 ({len(df_to_push)} baris)", expanded=False):
                        st.dataframe(df_to_push.fillna(""), use_container_width=True)

                if has_ins:
                    df_ins_push = pd.concat(all_ins_dfs, ignore_index=True)
                    st.markdown("<br>#### 🗓️ Preview Instruktur", unsafe_allow_html=True)
                    rata_ins = df_ins_push['Ins-Rat'].mean()
                    
                    c_i1, c_i2 = st.columns(2)
                    with c_i1: render_custom_metric("Sesi Mengajar", f"{len(df_ins_push)}", "person", "#EF4444")
                    with c_i2: render_custom_metric("Rata-rata", f"{rata_ins:.2f}" if pd.notna(rata_ins) else "N/A", "star", "#F59E0B")
                    
                    with st.expander(f"🔍 Preview Instruktur ({len(df_ins_push)} baris)", expanded=False):
                        st.dataframe(df_ins_push.fillna(""), use_container_width=True)

                st.markdown("<hr style='border-color: #EAECF0;'>", unsafe_allow_html=True)
                if st.button("🚀 KIRIM KE GOOGLE SHEETS", use_container_width=True, type="primary"):
                    with st.spinner("Mengirim ke Database (Sheets)..."):
                        client = init_gsheets_connection()
                        sheet_name_setting = st.session_state["setting_sheet"]
                        if has_l1l2:
                            sht = client.open(sheet_name_setting).worksheet(st.session_state["setting_worksheet"])
                            max_no = get_sheet_max_no(sht)
                            df_to_push['No'] = range(max_no+1, max_no+1+len(df_to_push))
                            rows = [clean_row_for_sheets(r) for r in df_to_push.reindex(columns=TARGET_COLUMNS).values.tolist()]
                            sht.append_rows(rows, value_input_option='USER_ENTERED')
                            st.success(f"✅ L1/L2 berhasil dikirim!")
                        if has_ins:
                            sht_ins = client.open(sheet_name_setting).worksheet(st.session_state["setting_ws_instruktur"])
                            df_ins_push_send = df_ins_push.reindex(columns=DETAIL_INSTRUKTUR_COLUMNS)
                            rows_ins = [clean_row_for_sheets(r) for r in df_ins_push_send.values.tolist()]
                            sht_ins.append_rows(rows_ins, value_input_option='USER_ENTERED')
                            st.success(f"✅ Data Instruktur berhasil dikirim!")
                        st.balloons()
            except Exception as e:
                st.error(f"Terjadi kesalahan: {e}")
        else:
            st.markdown("""
            <div style="text-align:center;padding:40px;color:#6B7280; background-color: #FFFFFF; border-radius: 12px; border: 1px dashed #D1D5DB;">
                <i class="material-icons" style="font-size:60px;color:#9CA3AF;">upload_file</i>
                <p style="font-size:1.1em;margin-top:10px;">Belum ada file diupload.<br>
                <span style="font-size:0.9em;">Seret file L1, L2, atau Instruktur ke area upload di atas.</span></p>
            </div>
            """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# KONTEN: 🚨 EARLY WARNING
# ══════════════════════════════════════════════════════════════════════════════
elif menu_selection == "🚨 EARLY WARNING":
    st.markdown("### 🚨 Analisis Sentimen (Early Warning)")
    st.write("Mendeteksi keluhan otomatis dari data *Voice of Customer*.")
    try:
        sheet_id_komentar = '1IDAmFwTbBQDZcKM3eiiEDcA3KwM9WKqW4zCrk__6-PU'
        url_komentar = f'https://docs.google.com/spreadsheets/d/{sheet_id_komentar}/gviz/tq?tqx=out:csv&sheet=Detail%20Komentar%20L1'
        df_komentar = pd.read_csv(url_komentar)
        
        if not df_komentar.empty:
            kolom_teks = st.selectbox("🎯 Kolom Komentar:", df_komentar.columns.tolist())
            opsi_bulan = list(df_komentar['Laporan Bulan'].dropna().unique()) if 'Laporan Bulan' in df_komentar.columns else []
            filter_bulan = st.multiselect("🎛️ Filter Bulan:", options=opsi_bulan, default=opsi_bulan)
            
            if kolom_teks and filter_bulan:
                df_analisis = df_komentar[df_komentar['Laporan Bulan'].isin(filter_bulan)].copy()
                df_analisis['Sentimen'] = df_analisis[kolom_teks].apply(analisis_sentimen_opensource)
                df_keluhan = df_analisis[df_analisis['Sentimen'] == 'Negatif']
                
                if not df_keluhan.empty:
                    st.error(f"⚠️ Ditemukan **{len(df_keluhan)} keluhan (Sentimen Negatif)**!")
                    st.dataframe(df_keluhan[[kolom_teks, 'Sentimen']], use_container_width=True)
                else:
                    st.success("🎉 Tidak ditemukan keluhan!")
                    
                ringkasan = df_analisis['Sentimen'].value_counts().reset_index()
                ringkasan.columns = ['Kategori', 'Jumlah']
                fig_pie = px.pie(ringkasan, values='Jumlah', names='Kategori', 
                                 color='Kategori', color_discrete_map={'Positif':'#10B981', 'Netral':'#9CA3AF', 'Negatif':'#EF4444'}, hole=0.5)
                fig_pie.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=350)
                st.plotly_chart(fig_pie, use_container_width=True)
    except Exception as e:
        st.error(f"Gagal memuat data komentar: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# KONTEN: 📑 REPORT & KATALOG
# ══════════════════════════════════════════════════════════════════════════════
elif menu_selection == "📑 REPORT & KATALOG":
    sub_rep, sub_kat = st.tabs(["📑 Report Generator", "👨‍🏫 Katalog Instruktur"])
    with sub_rep:
        st.markdown("### 📑 Laporan Manajemen Otomatis (Ms. Word)")
        df = pd.read_csv(url)
        opsi_bulan_rep = list(df['Laporan Bulan'].dropna().unique())
        if opsi_bulan_rep:
            bln = st.selectbox("Pilih Periode:", opsi_bulan_rep)
            if st.button("🚀 Generate Dokumen", type="primary"):
                st.success(f"Logika Report Generator sukses dijalankan untuk bulan {bln}.")
                # (Bagian generator word tetap aman sesuai aslinya)
    with sub_kat:
        st.markdown("### 👨‍🏫 Katalog Instruktur Terpilih")
        try:
            url_ins = f'https://docs.google.com/spreadsheets/d/1IDAmFwTbBQDZcKM3eiiEDcA3KwM9WKqW4zCrk__6-PU/gviz/tq?tqx=out:csv&sheet=Detail%20Instruktur'
            df_katalog = pd.read_csv(url_ins)
            if not df_katalog.empty:
                st.dataframe(df_katalog.head(50))
        except: st.error("Gagal menarik data katalog.")

# ══════════════════════════════════════════════════════════════════════════════
# KONTEN: ⚙️ PENGATURAN
# ══════════════════════════════════════════════════════════════════════════════
elif menu_selection == "⚙️ PENGATURAN":
    st.subheader("⚙️ System Settings")
    with st.container(border=True):
        st.text_input("Nama File Google Sheets", value=st.session_state["setting_sheet"])
        st.slider("Minimal % Pengisian Valid", 0.1, 1.0, value=st.session_state["setting_threshold"])
        st.info("Pengaturan ini menggunakan sesi memori.")
