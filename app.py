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
    page_title="Smart Evaluation Analytics UPDL",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS (Data Entry & Pipeline)
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

# URL Sumber Data Global L1 Tertutup (Untuk Analytics & Dashboard)
sheet_id = '1IDAmFwTbBQDZcKM3eiiEDcA3KwM9WKqW4zCrk__6-PU'
sheet_name = 'L1%20Tertutup' 
url = "https://docs.google.com/spreadsheets/d/" + str(sheet_id) + "/gviz/tq?tqx=out:csv&sheet=" + str(sheet_name)

# ─────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────
def get_base64_logo(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

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

def check_credentials(username, password):
    """Mengecek login dan mengambil Role serta Unit_Data dari Google Sheets"""
    try:
        client = init_gsheets_connection()
        sheet = client.open_by_key('1IDAmFwTbBQDZcKM3eiiEDcA3KwM9WKqW4zCrk__6-PU').worksheet('User_Access')
        records = sheet.get_all_records()
        for row in records:
            if str(row.get('Username', '')).strip() == username and str(row.get('Password', '')).strip() == password:
                return str(row.get('Role', '')).strip(), str(row.get('Unit_Data', '')).strip()
        return None, None
    except Exception as e:
        st.error(f"Gagal memverifikasi kredensial. Pastikan tab 'User_Access' sudah ada kolom 'Unit_Data'. Error: {e}")
        return None, None

def get_sheet_max_no(sheet):
    try:
        col_no = sheet.col_values(1)
        if len(col_no) > 1:
            return max([int(x) for x in col_no[1:] if str(x).isdigit()] + [0])
        return 0
    except:
        return 0

def format_tanggal_indo(tgl_input):
    if pd.isna(tgl_input) or str(tgl_input).strip() in ["", "-", "NOTGL", "NaT"]: return "-"
    try:
        if not isinstance(tgl_input, datetime):
            tgl_input = pd.to_datetime(str(tgl_input).split(" ")[0])
        hari = tgl_input.day
        bulan = BULAN_MAP_ID.get(tgl_input.month, "")
        tahun = tgl_input.year
        return f"{hari} {bulan} {tahun}"
    except Exception:
        return str(tgl_input)

# ─────────────────────────────────────────────────────────────────────────────
# GEMINI & SENTIMENT AI
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_resource
def load_gemini_model():
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        return genai.GenerativeModel('gemini-1.5-flash')
    return None
model = load_gemini_model()

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
    except:
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
# SESSION STATE DEFAULTS
# ─────────────────────────────────────────────────────────────────────────────
for key, default in [
    ("setting_sheet",         "Monitoring Evaluasi Pembelajaran"),
    ("setting_worksheet",     "L1 Tertutup"),
    ("setting_ws_master",     "Master_Data_Laporan"),
    ("setting_ws_instruktur", "Detail Instruktur"),
    ("setting_cutoff",        14),
    ("setting_threshold",     0.8),
    ("riwayat_upload",        []),
    ("logged_in",             False),
    ("username",              None),
    ("role",                  None),
    ("unit_data",             None),
]:
    if key not in st.session_state:
        st.session_state[key] = default


# ══════════════════════════════════════════════════════════════════════════════
# HALAMAN LOGIN (SISTEM RBAC)
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state["logged_in"]:
    login_css = """
    <style>
    [data-testid="stSidebar"] {display: none !important;}
    [data-testid="stHeader"] {display: none !important;}
    .stApp { background: linear-gradient(135deg, #17a2b8 0%, #0055A4 100%) !important; }
    .login-wrapper { background-color: #FFFFFF; border-radius: 40px; padding: 40px 30px; box-shadow: 0px 15px 35px rgba(0, 0, 0, 0.2); margin-top: 8vh; text-align: center; }
    .login-title { font-size: 32px; font-weight: 800; color: #111111; margin-bottom: 25px; font-family: 'Segoe UI', sans-serif; }
    [data-testid="stForm"] { border: none !important; padding: 0 !important; }
    .stTextInput input { border-radius: 20px !important; background-color: #F5F7FA !important; border: none !important; padding: 16px 20px !important; font-size: 16px !important; color: #333 !important; }
    .stTextInput input:focus { box-shadow: 0 0 0 2px #17a2b8 !important; }
    [data-testid="stFormSubmitButton"] button { background: linear-gradient(90deg, #17a2b8 0%, #20c997 100%) !important; color: white !important; border: none !important; border-radius: 30px !important; padding: 14px 24px !important; font-size: 18px !important; font-weight: bold !important; width: 100% !important; margin-top: 15px !important; box-shadow: 0px 8px 15px rgba(23, 162, 184, 0.4) !important; transition: all 0.3s ease !important; }
    [data-testid="stFormSubmitButton"] button:hover { transform: translateY(-2px) !important; box-shadow: 0px 12px 20px rgba(23, 162, 184, 0.5) !important; }
    [data-testid="stFormSubmitButton"] p { color: white !important; font-size: 18px !important; margin: 0; }
    </style>
    """
    st.markdown(login_css, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown('<div class="login-wrapper">', unsafe_allow_html=True)
        st.markdown('<div class="login-title">Login Dashboard</div>', unsafe_allow_html=True)
        
        with st.form("form_login"):
            input_user = st.text_input("Username", placeholder="Masukkan Username Anda", label_visibility="collapsed")
            input_pass = st.text_input("Password", type="password", placeholder="Masukkan Password", label_visibility="collapsed")
            
            btn_login = st.form_submit_button("Masuk")
            if btn_login:
                with st.spinner("Memverifikasi kredensial..."):
                    role_user, unit_data = check_credentials(input_user, input_pass)
                    if role_user:
                        st.session_state["logged_in"] = True
                        st.session_state["username"] = input_user
                        st.session_state["role"] = role_user
                        st.session_state["unit_data"] = unit_data
                        st.rerun()
                    else:
                        st.error("Username atau Password tidak valid!")
        st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# HALAMAN UTAMA APLIKASI
# ══════════════════════════════════════════════════════════════════════════════
else:
    st.markdown("""
        <style>
        .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
            font-size: 18px;
            font-weight: bold;
        }
        .stTabs [data-baseweb="tab"] { color: #666666; }
        .stTabs [data-baseweb="tab"][aria-selected="true"] { color: #005b9f !important; }
        .stTabs [data-baseweb="tab-highlight"] { background-color: #ffc107 !important; }
        [data-testid="stFileUploader"] { background: #ffffff; border: 2px dashed #0055A4; border-radius: 12px; padding: 20px; }
        </style>
    """, unsafe_allow_html=True)

    bin_pln = get_base64_logo("Logo PLN.png")
    img_pln = f'<img src="data:image/png;base64,{bin_pln}" style="height:85px;object-fit:contain;">' if bin_pln else ""

    st.markdown(f"""
    <div style="display:flex;align-items:center;justify-content:space-between;
        background:linear-gradient(90deg,#003366,#0055A4);padding:10px 30px;
        border-radius:12px;color:white;margin-bottom:25px;box-shadow:0px 4px 10px rgba(0,0,0,0.1);">
        <div style="flex:2;">
            <h1 style="margin:0;font-size:1.6em;color:white !important;font-weight:bold;line-height:1.2;">
                &#9889; Smart Evaluation Analytics
            </h1>
            <p style="margin:0;color:rgba(255,255,255,0.8) !important;font-size:0.85em;">
                Pusat Intelijen Data Mutu Pembelajaran PLN
            </p>
        </div>
        <div style="flex:1;display:flex;align-items:center;justify-content:flex-end;">{img_pln}</div>
    </div>
    """, unsafe_allow_html=True)

    # Menambahkan tombol Logout di sidebar
    with st.sidebar:
        st.markdown(f"<div style='text-align:center; padding:10px; background:#e2e8f0; border-radius:10px;'>👤 <b>{st.session_state['username']}</b><br><span style='font-size:12px;'>Role: {st.session_state['role']}</span></div>", unsafe_allow_html=True)
        st.markdown("---")
        if st.button("🚪 Logout Aplikasi", use_container_width=True):
            st.session_state["logged_in"] = False
            st.session_state["username"] = None
            st.session_state["role"] = None
            st.session_state["unit_data"] = None
            st.rerun()

    # DYNAMIC TABS BERDASARKAN ROLE
    if st.session_state["role"] == "SuperAdmin":
        tabs = st.tabs(["📤 DATA ENTRY", "📈 ANALYTICS", "📊 DASHBOARD", "📑 REPORT & KATALOG", "🤖 AI ASSISTANT", "⚙️ PENGATURAN"])
        tab_entry, tab_statistik, tab_dashboard, tab_report, tab_ai, tab_setting = tabs
    else:
        # Jika UPDL, hanya tampilkan Tab Report (Laporan Pembelajaran)
        tabs = st.tabs(["📄 Laporan Pembelajaran"])
        tab_report = tabs[0]
        tab_entry = tab_statistik = tab_dashboard = tab_ai = tab_setting = None

    # Load Data CSV Lokal untuk Analytics & Dashboard
    try:
        @st.cache_data(ttl=300)
        def load_csv(url): return pd.read_csv(url)
        df = load_csv(url)
    except Exception as e:
        df = pd.DataFrame()

    def build_filters(suffix):
        opsi_bulan    = list(df['Laporan Bulan'].dropna().unique()) if 'Laporan Bulan' in df.columns else []
        opsi_strategi = list(df['Strategi Pelaksanaan'].dropna().unique()) if 'Strategi Pelaksanaan' in df.columns else []
        
        col_f1, col_f2 = st.columns(2)
        with col_f1: filter_bulan = st.multiselect("Laporan Bulan", options=opsi_bulan, default=opsi_bulan, key=f"bulan_{suffix}")
        with col_f2: filter_strategi = st.multiselect("Strategi Pelaksanaan", options=opsi_strategi, default=opsi_strategi, key=f"strategi_{suffix}")
        
        df_f = df.copy()
        if not df_f.empty:
            if filter_bulan: df_f = df_f[df_f['Laporan Bulan'].isin(filter_bulan)]
            if filter_strategi: df_f = df_f[df_f['Strategi Pelaksanaan'].isin(filter_strategi)]
        return df_f

    # ══════════════════════════════════════════════════════════════════════════════
    # TAB 1: DATA ENTRY 
    # ══════════════════════════════════════════════════════════════════════════════
    if tab_entry:
        with tab_entry:
            st.markdown("""
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">
                <i class="material-icons" style="font-size:30px;color:#0055A4;">cloud_upload</i>
                <div>
                    <h2 style="margin:0;color:#003366;">Upload Data Pembelajaran</h2>
                    <p style="margin:0;color:#8a8a8a;font-size:0.9em;">Gabungkan L1, L2, SMILE, dan Instruktur secara Otomatis</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander("📖 Panduan Cepat (3 Jalur Data)", expanded=True):
                col_g1, col_g2, col_g3 = st.columns(3)
                with col_g1: st.markdown("🔵 **L1 + L2 (Lama)** ➡️ Sheet **L1 Tertutup**\nGabungan Evaluasi Reaksi & L2 HXMS")
                with col_g2: st.markdown("🟣 **L1 + SMILE** ➡️ Sheet **Master Data Laporan**\nData terpadu 2 Kunci Pas untuk Dashboard")
                with col_g3: st.markdown("🟠 **Instruktur** ➡️ Sheet **Detail Instruktur**\nData Penilaian & Jam Terbang Pengajar")

            sub_upload, sub_riwayat = st.tabs(["📤 Upload & Jahit", "🕒 Riwayat"])

            with sub_upload:
                with st.container(border=True):
                    st.info("💡 **Tips:** Untuk hasil terbaik, letakkan seluruh file (L1, SMILE, L2, Instruktur) secara bersamaan ke dalam kotak di bawah ini.")
                    uploaded_files = st.file_uploader("Pilih atau seret file Excel/CSV", type=["xlsx","csv", "xls"], accept_multiple_files=True, key="entry_uploader")

                if uploaded_files:
                    all_l1_dfs, all_l2_dfs, all_smile_dfs, all_ins_dfs, file_log = [], [], [], [], []

                    with st.status("🔍 Membaca dan memetakan jalur file...", expanded=True) as status_proc:
                        for f in uploaded_files:
                            try:
                                if f.name.endswith('.csv'): df_raw = pd.read_csv(f)
                                else: df_raw = pd.read_excel(f)
                                df_raw.columns = df_raw.columns.astype(str).str.strip()

                                is_smile = ('Kode Service Request' in df_raw.columns or 'Peserta Diundang' in df_raw.columns)
                                is_l2 = ('Confidence Level' in df_raw.columns and not is_smile)
                                is_instruktur = ('Nama' in df_raw.columns and 'Kode Diklat' in df_raw.columns)
                                is_l1 = ('Ins-Eng-1 of 2' in df_raw.columns and not is_instruktur)

                                if is_l1:
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
                                    kd_pemb = df_mapped['Kode Pembelajaran'].astype(str).str.replace(' ', '', regex=False).str.upper()
                                    tgl_mulai = pd.to_datetime(df_mapped['Tanggal Mulai'],errors='coerce').dt.strftime('%Y%m%d').fillna('NOTGL')
                                    df_mapped['Kode Unik'] = kd_pemb + "." + tgl_mulai
                                    all_l1_dfs.append(df_mapped)
                                    file_log.append({"File":f.name,"Tipe":"🔵 Evaluasi L1","Baris":len(df_raw)})
                                    st.session_state.riwayat_upload.append({"nama":f.name,"waktu":datetime.now().strftime("%d/%m/%Y %H:%M"),"tipe":"L1","baris":len(df_raw)})

                                elif is_smile:
                                    df_smile = df_raw.copy()
                                    kd_pemb_s = df_smile.get('Kode Pembelajaran', pd.Series(dtype=str)).astype(str).str.replace(' ', '', regex=False).str.upper()
                                    tgl_mulai_s = pd.to_datetime(df_smile.get('Tgl Mulai', pd.Series()), errors='coerce').dt.strftime('%Y%m%d').fillna('NOTGL')
                                    df_smile['Kode Unik'] = kd_pemb_s + "." + tgl_mulai_s
                                    all_smile_dfs.append(df_smile)
                                    file_log.append({"File":f.name,"Tipe":"🟣 SMILE","Baris":len(df_raw)})
                                    st.session_state.riwayat_upload.append({"nama":f.name,"waktu":datetime.now().strftime("%d/%m/%Y %H:%M"),"tipe":"SMILE","baris":len(df_raw)})

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

                                elif is_instruktur:
                                    df_raw = df_raw[~df_raw['Nama'].astype(str).str.strip().str.upper().isin(['UPDL JAKARTA','JAKARTA'])].reset_index(drop=True)
                                    df_ins = pd.DataFrame(columns=DETAIL_INSTRUKTUR_COLUMNS)
                                    df_ins['NIP'] = df_raw.get('NIP')
                                    df_ins['Nama'] = df_raw.get('Nama')
                                    df_ins['Tgl Mulai'] = pd.to_datetime(df_raw.get('Tgl Mulai'), errors='coerce')
                                    df_ins['Tgl Selesai'] = pd.to_datetime(df_raw.get('Tgl Selesai'), errors='coerce')
                                    df_ins['Kode Diklat'] = df_raw.get('Kode Diklat')
                                    df_ins['Judul Diklat'] = df_raw.get('Judul Diklat')
                                    angkatan_raw = df_raw.get('Angkatan')
                                    df_ins['Angkatan'] = (angkatan_raw.astype(str).str.replace(r'\.0$','',regex=True).str.strip().replace('nan','') if angkatan_raw is not None else '')
                                    df_ins['UPDL'] = df_raw.get('UPDL')
                                    df_ins['Jenis Peyelenggaraan'] = df_raw.get('Jenis Peyelenggaraan')
                                    df_ins['Durasi Mengajar'] = pd.to_numeric(df_raw.get('Durasi Mengajar'), errors='coerce')
                                    ins_eng_cols = ['Ins-Eng-1 of 2', 'Ins-Eng-2 of 2']
                                    ins_rel_cols = ['Ins-Rel-1 of 2', 'Ins-Rel-2 of 2']
                                    ins_sat_cols = ['Ins-Sat-1 of 4', 'Ins-Sat-2 of 4', 'Ins-Sat-3 of 4', 'Ins-Sat-4 of 4']
                                    for c in ins_eng_cols + ins_rel_cols + ins_sat_cols + ['Ins-Rat', 'Ins-Val']:
                                        if c in df_raw.columns: df_raw[c] = pd.to_numeric(df_raw[c], errors='coerce')
                                    valid_eng = [c for c in ins_eng_cols if c in df_raw.columns]
                                    valid_rel = [c for c in ins_rel_cols if c in df_raw.columns]
                                    valid_sat = [c for c in ins_sat_cols if c in df_raw.columns]
                                    df_ins['Ins-Eng'] = df_raw[valid_eng].mean(axis=1) if valid_eng else np.nan
                                    df_ins['Ins-Rel'] = df_raw[valid_rel].mean(axis=1) if valid_rel else np.nan
                                    df_ins['Ins-Sat'] = df_raw[valid_sat].mean(axis=1) if valid_sat else np.nan
                                    df_ins['Ins-Rat'] = df_raw.get('Ins-Rat')
                                    df_ins['Ins-Val'] = df_raw.get('Ins-Val')
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

                    if not has_l1l2 and not has_smile_pipe and not has_ins: st.stop()

                    st.markdown("### 📋 Ringkasan File")
                    st.dataframe(pd.DataFrame(file_log), use_container_width=True, hide_index=True)

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
                            else: df_l1_l2_push = df_l2_raw.copy()
                        else: df_l1_l2_push = df_l1.copy()

                        df_l1_l2_push = df_l1_l2_push.reindex(columns=TARGET_COLUMNS)
                        all_indicators = [f'INS{i}' for i in range(1,10)] + [f'MAT{i}' for i in range(1,8)] + [f'SP{i}' for i in range(1,7)] + [f'DS{i}' for i in range(1,7)]
                        for col in all_indicators: df_l1_l2_push[col] = pd.to_numeric(df_l1_l2_push[col], errors='coerce')
                        df_l1_l2_push['RATA INST'] = df_l1_l2_push[[f'INS{i}' for i in range(1,9)]].mean(axis=1)
                        df_l1_l2_push['RATA MAT']  = df_l1_l2_push[[f'MAT{i}' for i in range(1,7)]].mean(axis=1)
                        df_l1_l2_push['RATA SP']   = df_l1_l2_push[[f'SP{i}'  for i in range(1,6)]].mean(axis=1)
                        df_l1_l2_push['RATA DS']   = df_l1_l2_push[[f'DS{i}'  for i in range(1,6)]].mean(axis=1)
                        df_l1_l2_push['RATA-RATA KESELURUHAN'] = df_l1_l2_push[['RATA INST','RATA MAT','RATA SP','RATA DS']].mean(axis=1)

                    df_master_push = pd.DataFrame()
                    if has_smile_pipe:
                        df_smile_raw = pd.concat(all_smile_dfs, ignore_index=True)
                        if all_l1_dfs:
                            df_l1_for_smile = pd.concat(all_l1_dfs, ignore_index=True)
                            for col in all_indicators: df_l1_for_smile[col] = pd.to_numeric(df_l1_for_smile[col], errors='coerce')
                            df_l1_for_smile['RATA INST'] = df_l1_for_smile[[f'INS{i}' for i in range(1,9)]].mean(axis=1)
                            df_l1_for_smile['RATA MAT']  = df_l1_for_smile[[f'MAT{i}' for i in range(1,7)]].mean(axis=1)
                            df_l1_for_smile['RATA SP']   = df_l1_for_smile[[f'SP{i}'  for i in range(1,6)]].mean(axis=1)
                            df_l1_for_smile['RATA DS']   = df_l1_for_smile[[f'DS{i}'  for i in range(1,6)]].mean(axis=1)
                            df_l1_for_smile['RATA-RATA KESELURUHAN'] = df_l1_for_smile[['RATA INST','RATA MAT','RATA SP','RATA DS']].mean(axis=1)
                            df_l1_for_smile['Jumlah Indikator dibawah 4.5'] = (df_l1_for_smile[all_indicators] < 4.5).sum(axis=1)
                            df_l1_for_smile['Jumlah Indikator diatas 4.5']  = (df_l1_for_smile[all_indicators] >= 4.5).sum(axis=1)
                            eval_cols_to_bring = ['Kode Unik', 'Peserta Isi L1', 'RATA INST', 'RATA MAT', 'RATA SP', 'RATA DS', 'RATA-RATA KESELURUHAN', 'Jumlah Indikator dibawah 4.5', 'Jumlah Indikator diatas 4.5']
                            df_l1_slim = df_l1_for_smile[[c for c in eval_cols_to_bring if c in df_l1_for_smile.columns]].groupby('Kode Unik').first().reset_index()
                            df_master_push = df_smile_raw.merge(df_l1_slim, on='Kode Unik', how='left')
                        else: df_master_push = df_smile_raw.copy()

                        df_master_push['Tgl Selesai'] = pd.to_datetime(df_master_push.get('Tgl Selesai', pd.Series()), errors='coerce')
                        df_master_push['Cut off Data'] = df_master_push['Tgl Selesai'] + pd.Timedelta(days=st.session_state["setting_cutoff"])
                        df_master_push['Laporan Bulan'] = df_master_push['Cut off Data'].dt.month.map(BULAN_MAP_ID)
                        today = pd.Timestamp.today().normalize()
                        df_master_push['Status Pembelajaran'] = df_master_push['Tgl Selesai'].apply(lambda x: "Terlaksana" if pd.notna(x) and x<=today else "Belum Terlaksana")
                        df_master_push['Peserta Isi L1'] = pd.to_numeric(df_master_push.get('Peserta Isi L1', pd.Series()), errors='coerce')
                        df_master_push['Peserta Hadir']  = pd.to_numeric(df_master_push.get('Peserta Hadir', pd.Series()), errors='coerce')
                        df_master_push['% Pengisian L1'] = safe_divide(df_master_push['Peserta Isi L1'], df_master_push['Peserta Hadir'])
                        df_master_push['% Valid L1'] = df_master_push['% Pengisian L1'].apply(lambda x: "VALID" if pd.notna(x) and x > st.session_state["setting_threshold"] else "TIDAK VALID")
                        df_master_push = df_master_push.reindex(columns=MASTER_TARGET_COLUMNS)

                    df_ins_push = pd.DataFrame()
                    if has_ins:
                        df_ins_push = pd.concat(all_ins_dfs, ignore_index=True)
                        df_ins_push = df_ins_push.reindex(columns=DETAIL_INSTRUKTUR_COLUMNS)

                    if has_smile_pipe:
                        with st.expander(f"🟣 PREVIEW: MASTER DATA LAPORAN (L1 + SMILE) | {len(df_master_push)} Baris", expanded=True): st.dataframe(df_master_push.fillna(""), use_container_width=True)
                    if has_l1l2:
                        with st.expander(f"🔵 PREVIEW: L1 TERTUTUP (L1 + L2) | {len(df_l1_l2_push)} Baris", expanded=False): st.dataframe(df_l1_l2_push.fillna(""), use_container_width=True)
                    if has_ins:
                        with st.expander(f"🟠 PREVIEW: DETAIL INSTRUKTUR | {len(df_ins_push)} Baris", expanded=False): st.dataframe(df_ins_push.fillna(""), use_container_width=True)

                    st.markdown("---")
                    sheet_name_setting = st.session_state["setting_sheet"]
                    ws_l1_target = st.session_state["setting_worksheet"]
                    ws_master_target = st.session_state["setting_ws_master"]
                    ws_ins_target = st.session_state["setting_ws_instruktur"]

                    col_info, col_btn = st.columns([2, 1])
                    with col_info: st.info(f"Target Penyimpanan Google Sheets Utama: **{sheet_name_setting}**")
                    with col_btn:
                        if st.button("🚀 KIRIM SEMUA KE GOOGLE SHEETS", use_container_width=True, type="primary"):
                            with st.spinner("Mengirim data melalui 3 jalur ke brankas utama..."):
                                try:
                                    client = init_gsheets_connection()
                                    gsheet_file = client.open(sheet_name_setting)
                                    if has_smile_pipe:
                                        sht_master = gsheet_file.worksheet(ws_master_target)
                                        max_no = get_sheet_max_no(sht_master)
                                        df_master_push['No'] = range(max_no+1, max_no+1+len(df_master_push))
                                        rows_master = [clean_row_for_sheets(r) for r in df_master_push.values.tolist()]
                                        sht_master.append_rows(rows_master, value_input_option='USER_ENTERED')
                                        st.success(f"🟣 Berhasil mengirim {len(rows_master)} baris ke Tab **{ws_master_target}**")
                                    if has_l1l2:
                                        sht_l1 = gsheet_file.worksheet(ws_l1_target)
                                        max_no = get_sheet_max_no(sht_l1)
                                        df_l1_l2_push['No'] = range(max_no+1, max_no+1+len(df_l1_l2_push))
                                        rows_l1 = [clean_row_for_sheets(r) for r in df_l1_l2_push.values.tolist()]
                                        sht_l1.append_rows(rows_l1, value_input_option='USER_ENTERED')
                                        st.success(f"🔵 Berhasil mengirim {len(rows_l1)} baris ke Tab **{ws_l1_target}**")
                                    if has_ins:
                                        sht_ins = gsheet_file.worksheet(ws_ins_target)
                                        rows_ins = [clean_row_for_sheets(r) for r in df_ins_push.values.tolist()]
                                        sht_ins.append_rows(rows_ins, value_input_option='USER_ENTERED')
                                        st.success(f"🟠 Berhasil mengirim {len(rows_ins)} baris ke Tab **{ws_ins_target}**")
                                    st.balloons()
                                except Exception as e_push:
                                    st.error(f"Gagal mengirim ke Google Sheets. Error: {e_push}")

            with sub_riwayat:
                if not st.session_state.riwayat_upload:
                    st.info("Belum ada riwayat upload.")
                else:
                    for item in reversed(st.session_state.riwayat_upload):
                        badge_color = {"L1":"#0055A4","L2":"#1a7a2e", "SMILE":"#8e24aa"}.get(item['tipe'],"#666")
                        st.markdown(f"""
                        <div style="display:flex;align-items:center;gap:10px;padding:10px 0;border-bottom:1px solid #eee;">
                            <div style="flex:1;">
                                <p style="margin:0;font-weight:bold;">{item['nama']}</p>
                                <p style="margin:0;font-size:0.8em;color:#8a8a8a;">{item['waktu']} • {item['baris']} baris</p>
                            </div>
                            <span style="background:{badge_color}20;color:{badge_color};border:1px solid {badge_color}55; padding:2px 10px;border-radius:20px;font-size:0.75em;font-weight:bold;">{item['tipe']}</span>
                        </div>""", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════════
    # TAB 2: ANALYTICS
    # ══════════════════════════════════════════════════════════════════════════════
    if tab_statistik:
        with tab_statistik:
            st.markdown("### 🎛️ Filter Data Analitik")
            df_ana = build_filters("analytics")
            if not df_ana.empty:
                st.write(f"Menampilkan **{len(df_ana)}** data siap analisis.")
            else:
                st.warning("Data kosong atau belum memuat data dari Master.")

    # ══════════════════════════════════════════════════════════════════════════════
    # TAB 3: DASHBOARD
    # ══════════════════════════════════════════════════════════════════════════════
    if tab_dashboard:
        with tab_dashboard:
            st.markdown("### 🎛️ Filter Dashboard")
            df_dash = build_filters("dashboard")
            
            if not df_dash.empty:
                skor_evaluasi = df_dash['RATA-RATA KESELURUHAN'].mean() if 'RATA-RATA KESELURUHAN' in df_dash.columns else 0
                ind_kurang = df_dash['Jumlah Indikator dibawah 4.5'].sum() if 'Jumlah Indikator dibawah 4.5' in df_dash.columns else 0
                ind_lebih = df_dash['Jumlah Indikator diatas 4.5'].sum() if 'Jumlah Indikator diatas 4.5' in df_dash.columns else 0
                
                st.markdown("---")
                col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
                with col_kpi1: st.metric("🌟 Rata-rata Kepuasan L1",  f"{skor_evaluasi:.2f}")
                with col_kpi2: st.metric("⚠️ Indikator < 4.5",  int(ind_kurang))
                with col_kpi3: st.metric("✅ Indikator ≥ 4.5",  int(ind_lebih))
            else:
                st.info("Silakan muat Master Data Laporan Anda di tab Pengaturan.")

    # ══════════════════════════════════════════════════════════════════════════════
    # TAB 4: REPORT & KATALOG (TERMASUK INTEGRASI DATABASE NASIONAL)
    # ══════════════════════════════════════════════════════════════════════════════
    if tab_report:
        with tab_report:
            # KAMUS NAMA MANAGER BERDASARKAN UPDL
            # (Silakan isi nama manager di bawah ini sesuai data aslinya)
            KAMUS_MANAGER = {
                "UPDL JAKARTA": "ZAKI YAMANI KERTAPATI",
                "UPDL PADANG": "NAMA MANAGER PADANG",
                "UPDL SEMARANG": "NAMA MANAGER SEMARANG",
                "UPDL BOGOR": "NAMA MANAGER BOGOR",
                "UPDL SURABAYA": "NAMA MANAGER SURABAYA",
                "UPDL MAKASSAR": "NAMA MANAGER MAKASSAR",
                "UPDL BANJARBARU": "NAMA MANAGER BANJARBARU",
                "UPDL PALEMBANG": "NAMA MANAGER PALEMBANG",
                "UPDL PANDAAN": "NAMA MANAGER PANDAAN",
                "UPDL TUNTUNGAN": "NAMA MANAGER TUNTUNGAN",
                "UPDL BUKITTINGGI": "NAMA MANAGER BUKITTINGGI",
                # Tambahkan nama UPDL lain jika ada ...
            }

            if st.session_state["role"] == "SuperAdmin":
                sub_rep_generator, sub_lap_pembelajaran, sub_katalog = st.tabs(["📑 Report Generator (Lokal)", "📄 Laporan Pembelajaran (Nasional)", "👨‍🏫 Katalog Instruktur"])
            else:
                st.markdown("## 📄 Generator Laporan Pembelajaran (Akses Terbatas)")
                sub_lap_pembelajaran = st.container()

            # --- Report Bulanan Lokal (Khusus SuperAdmin) ---
            if st.session_state["role"] == "SuperAdmin":
                with sub_rep_generator:
                    st.markdown("### 📑 Generator Laporan Manajemen (Otomatis)")
                    st.info("Fitur penyusunan laporan evaluasi bulanan keseluruhan (Menggunakan Data Lokal UPDL terkait).")

            # --- REPORT PEMBELAJARAN DENGAN DATABASE NASIONAL ---
            with sub_lap_pembelajaran:
                if st.session_state["role"] == "SuperAdmin":
                    st.markdown("### 📄 Generator Laporan Pembelajaran Per Kelas")
                st.write("Mengekstrak Laporan Pembelajaran dari *Database Nasional* secara otomatis sesuai hak akses unit.")

                try:
                    # KONEKSI KE SPREADSHEET NASIONAL
                    sheet_id_nasional = '1h-5D5susznSg6nDl2cqgxVu05zSVyTSW19VICYDLtuU'
                    tab_name_nasional = urllib.parse.quote('I_Gabungan_Detail')
                    url_master_nasional = f"https://docs.google.com/spreadsheets/d/{sheet_id_nasional}/gviz/tq?tqx=out:csv&sheet={tab_name_nasional}"
                    
                    req_master = urllib.request.Request(url_master_nasional, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req_master) as response:
                        df_master_nasional = pd.read_csv(io.BytesIO(response.read()))
                    
                    df_master_nasional.columns = df_master_nasional.columns.astype(str).str.strip()
                    col_updl = 'Sumber Data Implementasi'
                    
                    if col_updl in df_master_nasional.columns and 'Judul Pembelajaran' in df_master_nasional.columns:
                        df_master_nasional[col_updl] = df_master_nasional[col_updl].astype(str).str.strip().str.upper()
                        
                        df_filter = pd.DataFrame()
                        updl_pilih = ""
                        
                        # --- LOGIKA RBAC ---
                        if st.session_state["role"] == "UPDL":
                            updl_pilih = str(st.session_state.get("unit_data", "")).strip().upper()
                            df_filter = df_master_nasional[df_master_nasional[col_updl] == updl_pilih]
                            st.success(f"🔐 Akses Data Terkunci untuk: **{updl_pilih}**")
                        elif st.session_state["role"] == "SuperAdmin":
                            list_updl = sorted([u for u in df_master_nasional[col_updl].unique() if str(u).strip() not in ['', 'NAN', 'NONE']])
                            with st.container(border=True):
                                updl_pilih = st.selectbox("🏢 Pilih UPDL (Filter SuperAdmin):", list_updl, key="sa_updl_filter")
                            df_filter = df_master_nasional[df_master_nasional[col_updl] == updl_pilih]
                            
                        if not df_filter.empty:
                            df_filter['Opsi_Dropdown'] = df_filter.apply(
                                lambda x: f"{str(x.get('Judul Pembelajaran', '-')).strip()} ({format_tanggal_indo(x.get('Tgl Mulai'))} s.d {format_tanggal_indo(x.get('Tgl Akhir', x.get('Tgl Selesai')))})", 
                                axis=1
                            )
                            list_judul = df_filter['Opsi_Dropdown'].dropna().unique().tolist()
                            
                            if list_judul:
                                with st.container(border=True):
                                    col_j1, col_j2 = st.columns([2, 1])
                                    with col_j1:
                                        judul_pilih = st.selectbox("📚 Pilih Judul Pembelajaran:", list_judul, key="judul_report_pembelajaran")
                                    with col_j2:
                                        st.markdown("<br>", unsafe_allow_html=True)
                                        btn_gen_kelas = st.button("🚀 Generate Laporan Kelas", type="primary", use_container_width=True)
                                
                                if btn_gen_kelas:
                                    def format_tgl_indo(tgl_str):
                                        if pd.isna(tgl_str) or str(tgl_str).strip() in ['', '-', 'NOTGL']: return "-"
                                        try:
                                            dt = pd.to_datetime(tgl_str)
                                            bulan_indo = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
                                            return f"{dt.day} {bulan_indo[dt.month-1]} {dt.year}"
                                        except: return str(tgl_str)

                                    with st.spinner(f"Mengekstrak data pembelajaran {updl_pilih}..."):
                                        df_kelas = df_filter[df_filter['Opsi_Dropdown'] == judul_pilih].iloc[0]
                                        judul_asli = df_kelas.get('Judul Pembelajaran', '-')
                                        
                                        # VARIABEL DINAMIS DARI KAMUS DATA
                                        nama_updl_display = updl_pilih
                                        nama_manager_display = KAMUS_MANAGER.get(updl_pilih, "[ Nama Manager Belum Diatur ]")
                                        
                                        kode_pemb = df_kelas.get('Kode Pembelajaran', '-')
                                        no_surat = df_kelas.get('No Surat Penugasan', '-')
                                        tgl_surat_indo = format_tgl_indo(df_kelas.get('Tanggal Surat Penugasan', '-'))
                                        no_surat_panggil = df_kelas.get('Nomor Surat Pemanggilan Peserta', '-')
                                        if pd.isna(no_surat_panggil) or str(no_surat_panggil).strip() == "": no_surat_panggil = "-"

                                        kode_sr_raw = df_kelas.get('Kode Service Request', '')
                                        jenis_prog = df_kelas.get('Jenis Program', '')
                                        if pd.isna(kode_sr_raw): kode_sr_raw = ""
                                        if pd.isna(jenis_prog): jenis_prog = ""
                                        kode_sr = f"{kode_sr_raw} - {jenis_prog}".strip(" -")
                                        if not kode_sr: kode_sr = "-"
                                        
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
                                            except: return v_str
                                                
                                        pct_hadir = f_pct_str(df_kelas.get('% Kehadiran', '-'))
                                        pct_lulus = f_pct_str(df_kelas.get('% Kelulusan', '-'))
                                        isi_l1 = df_kelas.get('Peserta Isi L1', 0)
                                        pct_isi = f_pct_str(df_kelas.get('% Pengisian L1', df_kelas.get('% Pengisian', '-')))
                                        
                                        tgl_mulai_indo = format_tgl_indo(df_kelas.get('Tgl Mulai', '-'))
                                        tgl_selesai_indo = format_tgl_indo(df_kelas.get('Tgl Akhir', df_kelas.get('Tgl Selesai', '-')))
                                        
                                        instruktur = df_kelas.get('Instruktur/ Fasilitator', '-')
                                        if pd.isna(instruktur) or str(instruktur).strip() == "": instruktur = "[ Ketik Nama Instruktur Disini ]"
                                        
                                        tempat = df_kelas.get('Tempat Pelaksanaan', df_kelas.get('Lokasi Pelaksanaan', '-'))
                                        if pd.isna(tempat) or str(tempat).strip() == "": tempat = f"PT PLN (Persero) {nama_updl_display}"
                                        
                                        metode_raw = str(df_kelas.get('Strategi Pelaksanaan', '-')).strip()
                                        dict_metode = {"ICT": "In Class Training (ICT)", "DL": "Distance Learning (DL)", "SL": "Self Learning (SL)", "BL": "Blended Learning (BL)", "HL": "Hybrid Learning (HL)"}
                                        metode = dict_metode.get(metode_raw.upper(), metode_raw)
                                        
                                        def format_rp(val):
                                            try: return f"Rp {int(float(val)):,}".replace(',', '.')
                                            except: return "Rp 0"
                                        rab = format_rp(df_kelas.get('RAB Pelaksanaan', 0))
                                        realisasi = format_rp(df_kelas.get('Realisasi Biaya Pelaksanaan', 0))
                                        
                                        def f_skor(v):
                                            try: return f"{float(str(v).replace(',','.')):.2f}"
                                            except: return "-"
                                            
                                        skor_mat = f_skor(df_kelas.get('RATA MAT', 0))
                                        skor_ins = f_skor(df_kelas.get('RATA INST', 0))
                                        skor_sp_off = f_skor(df_kelas.get('RATA SP', 0))
                                        skor_sp_on = f_skor(df_kelas.get('RATA DS', 0))
                                        skor_tot = f_skor(df_kelas.get('RATA-RATA KESELURUHAN', 0))
                                        
                                        baris_evaluasi = f"<tr><td style='text-align:center;'>1</td><td>Materi</td><td style='text-align:center; font-weight:bold;'>{skor_mat}</td></tr>\n"
                                        baris_evaluasi += f"<tr><td style='text-align:center;'>2</td><td>Instruktur</td><td style='text-align:center; font-weight:bold;'>{skor_ins}</td></tr>\n"
                                        
                                        no_urut = 3
                                        m_upper = metode_raw.upper()
                                        if m_upper in ['ICT', 'BL', 'HL']:
                                            baris_evaluasi += f"<tr><td style='text-align:center;'>{no_urut}</td><td>Sarana Prasarana Offline (In-Class)</td><td style='text-align:center; font-weight:bold;'>{skor_sp_off}</td></tr>\n"
                                            no_urut += 1
                                        if m_upper in ['DL', 'SL', 'BL', 'HL']:
                                            baris_evaluasi += f"<tr><td style='text-align:center;'>{no_urut}</td><td>Sarana Prasarana Online (Digital)</td><td style='text-align:center; font-weight:bold;'>{skor_sp_on}</td></tr>\n"
                                            no_urut += 1
                                            
                                        baris_evaluasi += f"<tr style='background-color: #f1f5f9;'><td style='text-align:center; font-weight:bold; color:#003366;'>{no_urut}</td><td style='font-weight:bold; color:#003366;'>Rata-Rata Keseluruhan</td><td style='text-align:center; font-weight:bold; color:#003366; font-size:12pt;'>{skor_tot}</td></tr>"

                                        pos_html, neg_html = "<span style='color:#94a3b8; font-style:italic;'>Nihil / Tidak ada catatan apresiasi.</span>", "<span style='color:#94a3b8; font-style:italic;'>Nihil / Tidak ada catatan masukan.</span>"
                                        jml_pos_kelas, jml_neg_kelas = 0, 0
                                        
                                        try:
                                            apresi_raw = str(df_kelas.get('KOMENTAR APRESIASI', '')).strip()
                                            masuk_raw = str(df_kelas.get('KOMENTAR MASUKAN', '')).strip()
                                            
                                            pos_texts = [t.strip() for t in apresi_raw.split('\n') if t.strip() and t.lower() not in ['nan', 'none', '-']]
                                            neg_texts = [t.strip() for t in masuk_raw.split('\n') if t.strip() and t.lower() not in ['nan', 'none', '-']]
                                            
                                            jml_pos_kelas, jml_neg_kelas = len(pos_texts), len(neg_texts)
                                            
                                            if pos_texts: pos_html = "<ul style='margin:0; padding-left:15px; color: #334155; line-height: 1.6;'>" + "".join([f"<li style='margin-bottom:6px;'>{t}</li>" for t in pos_texts]) + "</ul>"
                                            if neg_texts: neg_html = "<ul style='margin:0; padding-left:15px; color: #334155; line-height: 1.6;'>" + "".join([f"<li style='margin-bottom:6px;'>{t}</li>" for t in neg_texts]) + "</ul>"
                                        except: pass

                                        narasi_eksekutif_kelas = f"Dokumen ini merangkum <i>post-implementation review</i> untuk pelaksanaan program <b>{judul_asli}</b> ({kode_pemb}), menyajikan evaluasi metrik kehadiran ({pct_hadir}), efisiensi anggaran, dan tingkat kepuasan pelanggan dengan Skor Rata-rata Keseluruhan sebesar <b>{skor_tot}</b>, guna memastikan penyelarasan operasional dengan standar mutu <i>Service Excellence</i> {nama_updl_display}."
                                        
                                        html_kelas = f"""
                                        <html xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:w='urn:schemas-microsoft-com:office:word' xmlns='http://www.w3.org/TR/REC-html40'>
                                        <head><meta charset="utf-8">
                                            <style>
                                                body {{ font-family: 'Segoe UI', Arial, sans-serif; font-size: 11pt; color: #1e293b; }}
                                                .cover-page {{ background: linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%); color: #003366; padding: 50px 40px; text-align: center; height: 100%; }}
                                                .cover-title {{ font-size: 26pt; font-weight: 800; letter-spacing: 2px; margin-top: 150px; margin-bottom: 20px; text-transform: uppercase; line-height: 1.3; color: #003366; }}
                                                .cover-subtitle {{ font-size: 16pt; font-weight: normal; margin-bottom: 10px; line-height: 1.4; color: #003366; }}
                                                .cover-code {{ font-size: 14pt; color: #0055A4; margin-bottom: 150px; }}
                                                .cover-footer {{ font-size: 14pt; font-weight: bold; letter-spacing: 1px; bottom: 50px; width: 100%; color: #003366; }}
                                                h4 {{ color: #0055A4; border-bottom: 2px solid #cbd5e1; padding-bottom: 5px; margin-top: 25px; margin-bottom: 10px; font-size: 12pt; text-transform: uppercase; }}
                                                table {{ width: 100%; border-collapse: collapse; margin-bottom: 15px; font-size: 10.5pt; }}
                                                th {{ background-color: #003366; color: white; padding: 8px; text-align: left; }}
                                                td {{ border: 1px solid #cbd5e1; padding: 10px 8px; vertical-align: middle; }}
                                                .zebra tr:nth-child(even) td {{ background-color: #f8fafc; }}
                                                p {{ text-align: justify; margin-top: 0; line-height: 1.6; color: #334155; }}
                                                ul {{ margin-top: 0; padding-left: 20px; line-height: 1.6; color: #334155; }}
                                            </style>
                                        </head>
                                        <body>
                                            <div class="cover-page">
                                                <table style="width: 100%; border: none;">
                                                    <tr>
                                                        <td style="text-align: left; border: none; width: 50%; padding:0;"><img src="data:image/png;base64,{bin_danantara}" height="40" style="background:white; padding:5px; border-radius:4px;"></td>
                                                        <td style="text-align: right; border: none; width: 50%; padding:0;"><img src="data:image/png;base64,{bin_pln}" height="60"></td>
                                                    </tr>
                                                </table>
                                                <div class="cover-title">LAPORAN PELAKSANAAN<br>PEMBELAJARAN PENUGASAN</div>
                                                <div class="cover-subtitle">{str(judul_asli).upper()}</div>
                                                <div class="cover-code">({kode_pemb})</div>
                                                <br><br><br><br><br><br><br><br><br><br><br><br>
                                                <div class="cover-footer">PT PLN (PERSERO) {nama_updl_display}</div>
                                            </div>
                                            <br clear="all" style="page-break-before:always" />
                                            <div style="padding: 20px 40px;">
                                                <h4 style="text-align: center; color: #003366; border: none; margin-bottom: 10px; text-transform: uppercase;">EXECUTIVE SUMMARY</h4>
                                                <div style="text-align: justify; margin-bottom: 25px;">{narasi_eksekutif_kelas}</div>
                                                
                                                <h4>1. DASAR PELAKSANAAN</h4>
                                                <ul>
                                                    <li>Surat Penugasan No. <b>{no_surat}</b> pada tanggal <b>{tgl_surat_indo}</b></li>
                                                    <li>Service Request (SR): <b>{kode_sr}</b></li>
                                                    <li>Nomor Surat Pemanggilan: <b>{no_surat_panggil}</b></li>
                                                </ul>
                                                
                                                <h4>2. INFORMASI KEPESERTAAN</h4>
                                                <table class="zebra">
                                                    <tr><td>Rencana Jumlah Peserta</td><td style="text-align:center; font-weight:bold;">{int(rencana_peserta) if not pd.isna(rencana_peserta) else 0}</td></tr>
                                                    <tr><td>Peserta diundang</td><td style="text-align:center; font-weight:bold;">{int(diundang) if not pd.isna(diundang) else 0}</td></tr>
                                                    <tr><td>Peserta Hadir</td><td style="text-align:center; font-weight:bold; color: #0055A4;">{int(hadir) if not pd.isna(hadir) else 0}</td></tr>
                                                    <tr><td>Persentase Peserta Hadir</td><td style="text-align:center; font-weight:bold;">{pct_hadir}</td></tr>
                                                    <tr><td>Peserta Lulus</td><td style="text-align:center; font-weight:bold; color: #15803d;">{int(lulus) if not pd.isna(lulus) else 0}</td></tr>
                                                    <tr><td>Persentase Peserta Lulus</td><td style="text-align:center; font-weight:bold; color: #15803d;">{pct_lulus}</td></tr>
                                                </table>

                                                <h4>3. WAKTU, METODE DAN TEMPAT</h4>
                                                <ul>
                                                    <li><b>Tanggal:</b> {tgl_mulai_indo} s.d {tgl_selesai_indo}</li>
                                                    <li><b>Metode:</b> {metode}</li>
                                                    <li><b>Tempat:</b> {tempat}</li>
                                                    <li><b>Narasumber:</b> {instruktur}</li>
                                                </ul>

                                                <h4>4. BIAYA PEMBELAJARAN</h4>
                                                <table class="zebra">
                                                    <tr><th style="width: 60%; text-align:center;">Komponen Biaya</th><th style="width: 40%; text-align:center;">Nominal (Rp)</th></tr>
                                                    <tr><td>Rencana Biaya</td><td style="text-align:right;"><b>{rab}</b></td></tr>
                                                    <tr><td>Realisasi Biaya</td><td style="text-align:right; color: #003366;"><b>{realisasi}</b></td></tr>
                                                </table>

                                                <h4 style="page-break-before: always;">5. EVALUASI PEMBELAJARAN</h4>
                                                <p>Persentase partisipasi pengisian peserta sebesar <b>{pct_isi}</b>.</p>
                                                <table class="zebra">
                                                    <tr><th style="width: 10%; text-align:center;">No</th><th style="width: 60%;">Indikator Kepuasan</th><th style="width: 30%; text-align:center;">Skor (1-5)</th></tr>
                                                    {baris_evaluasi}
                                                </table>

                                                <h4>6. CUSTOMER VOICE</h4>
                                                <table>
                                                    <tr><th style="width: 50%; text-align:center;">Komentar Apresiasi ({jml_pos_kelas})</th><th style="width: 50%; text-align:center;">Komentar Masukan / Evaluasi ({jml_neg_kelas})</th></tr>
                                                    <tr>
                                                        <td style="padding: 12px; background-color: #f8fafc; vertical-align:top;">{pos_html}</td>
                                                        <td style="padding: 12px; background-color: #fff1f2; vertical-align:top;">{neg_html}</td>
                                                    </tr>
                                                </table>

                                                <br><br><br>
                                                <table style="width:100%; border: none; page-break-inside:avoid;">
                                                    <tr style="page-break-inside:avoid;">
                                                        <td style="width:50%; border: none;"></td>
                                                        <td style="width:50%; border: none; text-align:center;">
                                                            Mengetahui,<br><b>MANAGER {nama_updl_display}</b><br><br><br><br><br>
                                                            <b>{nama_manager_display}</b>
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
                                                    <li>Lampiran 5: Dokumentasi Pelaksanaan / Foto Kegiatan</li>
                                                </ul>
                                            </div>
                                        </body>
                                        </html>
                                        """
                                        st.success(f"✅ Laporan {judul_asli} siap diunduh!")
                                        st.download_button(label="📥 DOWNLOAD LAPORAN KELAS (.doc)", data=html_kelas.encode('utf-8'), file_name=f"Laporan_Pelaksanaan_{kode_pemb.replace('.','_')}.doc", mime="application/msword", type="primary")
                        else:
                            st.info(f"Belum ada kelas yang diselenggarakan oleh {updl_pilih} di Database Nasional.")
                    else:
                        st.error("Gagal membaca struktur Database Nasional. Pastikan kolom 'Sumber Data Implementasi' dan 'Judul Pembelajaran' tersedia pada file tersebut.")
                except Exception as e:
                    st.error(f"Gagal memuat Data Nasional: {e}")

            if st.session_state["role"] == "SuperAdmin":
                with sub_katalog:
                    st.markdown("### 👨‍🏫 Katalog & Rekomendasi Instruktur")
                    st.info("Katalog instruktur menggunakan dataset lokal.")

    # ══════════════════════════════════════════════════════════════════════════════
    # TAB 5: AI ASSISTANT
    # ══════════════════════════════════════════════════════════════════════════════
    if tab_ai:
        with tab_ai:
            st.subheader("🤖 Tanya Asisten EVALYTICS")
            st.write("Gunakan AI untuk menganalisis tren atau meminta saran perbaikan berdasarkan data Master Laporan.")

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
                    if model:
                        with st.spinner("Gemini sedang berpikir..."):
                            try:
                                context = f"Data evaluasi UPDL. Total: {len(df)} baris. Ringkasan: {df.describe().to_string()}"
                                full_prompt = f"Konteks:\n{context}\n\nPertanyaan: {user_question}\n\nJawab ringkas, profesional, Bahasa Indonesia."
                                response = model.generate_content(full_prompt)
                                st.markdown(response.text)
                                st.session_state.chat_history.append({"role": "assistant", "content": response.text})
                            except Exception as ai_err:
                                st.error(f"Gagal AI: {ai_err}")
                    else:
                        st.warning("API Key Gemini belum diset.")

    # ══════════════════════════════════════════════════════════════════════════════
    # TAB 6: PENGATURAN
    # ══════════════════════════════════════════════════════════════════════════════
    if tab_setting:
        with tab_setting:
            st.subheader("⚙️ Pengaturan Aplikasi")
            with st.container(border=True):
                st.markdown("#### 🔗 Konfigurasi Google Sheets (Target Master Data Laporan)")
                nama_sheet = st.text_input("Nama File Google Sheets", value=st.session_state["setting_sheet"])
                st.markdown("---")
                
                st.markdown("#### 📋 Nama Tab (Worksheet) Tujuan")
                col_ws1, col_ws2, col_ws3 = st.columns(3)
                with col_ws1: nama_worksheet     = st.text_input("Tab — L1 & L2 (Lama)", value=st.session_state["setting_worksheet"])
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
