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
L2_MERGE_COLS = ['Kode Unik', 'Peserta Hadir', 'Jumlah Peserta Lulus L2', 'Jumlah Peserta Isi L2',
                 'Nilai Confidence', 'Nilai Commitment']
INSTRUKTUR_SOURCE_COLS = [
    'Nama','Tgl Mulai','Tgl Selesai','Kode Diklat','Judul Diklat','Angkatan',
    'Ins-Eng-1 of 2','Ins-Eng-2 of 2','Ins-Rel-1 of 2','Ins-Rel-2 of 2',
    'Ins-Sat-1 of 4','Ins-Sat-2 of 4','Ins-Sat-3 of 4','Ins-Sat-4 of 4','Ins-Rat',
]

BULAN_MAP_ID = {1:'Januari',2:'Februari',3:'Maret',4:'April',5:'Mei',6:'Juni',
                7:'Juli',8:'Agustus',9:'September',10:'Oktober',11:'November',12:'Desember'}

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
    ("setting_worksheet",     "Master_Data_Laporan"),
    ("setting_ws_instruktur", "Detail Instruktur"),
    ("setting_cutoff",        14),
    ("setting_threshold",     0.8),
    ("riwayat_upload",        []),
]:
    if key not in st.session_state:
        st.session_state[key] = default

@st.cache_resource
def load_gemini_model():
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        return genai.GenerativeModel('gemini-1.5-flash')
    return None
model = load_gemini_model()

# ─────────────────────────────────────────────────────────────────────────────
# TABS SETUP
# ─────────────────────────────────────────────────────────────────────────────
bin_pln = get_base64_logo("Logo PLN.png")
img_pln = f'<img src="data:image/png;base64,{bin_pln}" style="height:85px;object-fit:contain;">' if bin_pln else "<b>PLN UPDL JAKARTA</b>"

st.markdown(f"""
<div style="display:flex;align-items:center;justify-content:space-between;
    background:linear-gradient(90deg,#003366,#0055A4);padding:10px 30px;
    border-radius:12px;color:white;margin-bottom:25px;box-shadow:0px 4px 10px rgba(0,0,0,0.1);">
    <div style="flex:2;">
        <h1 style="margin:0;font-size:1.6em;color:white !important;font-weight:bold;line-height:1.2;">
            &#9889; Smart Evaluation Analytics
        </h1>
        <p style="margin:0;color:rgba(255,255,255,0.8) !important;font-size:0.85em;">
            Pusat Intelijen Data Mutu Pembelajaran UPDL Jakarta
        </p>
    </div>
    <div style="flex:1;display:flex;align-items:center;justify-content:flex-end;">{img_pln}</div>
</div>
""", unsafe_allow_html=True)

tab_entry, tab_statistik, tab_dashboard, tab_report, tab_ai, tab_setting = st.tabs([
    "📤 DATA ENTRY", 
    "📈 ANALYTICS", 
    "📊 DASHBOARD", 
    "📑 REPORT & KATALOG", 
    "🤖 AI ASSISTANT", 
    "⚙️ PENGATURAN"
])

# URL Sumber Data Global
sheet_id = '1RitrlhPmYvxAax2gmZHyhyLX5a8j4xEjwpytlBMxvs8'
url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv'

try:
    @st.cache_data(ttl=300)
    def load_csv(url):
        return pd.read_csv(url)
    df = load_csv(url)
except Exception as e:
    df = pd.DataFrame()

def build_filters(suffix):
    opsi_bulan    = list(df['Laporan Bulan'].dropna().unique()) if 'Laporan Bulan' in df.columns else []
    opsi_strategi = list(df['Strategi Pelaksanaan'].dropna().unique()) if 'Strategi Pelaksanaan' in df.columns else []
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filter_bulan = st.multiselect("Laporan Bulan", options=opsi_bulan, default=opsi_bulan, key=f"bulan_{suffix}")
    with col_f2:
        filter_strategi = st.multiselect("Strategi Pelaksanaan", options=opsi_strategi, default=opsi_strategi, key=f"strategi_{suffix}")
    
    df_f = df.copy()
    if not df_f.empty:
        if filter_bulan: df_f = df_f[df_f['Laporan Bulan'].isin(filter_bulan)]
        if filter_strategi: df_f = df_f[df_f['Strategi Pelaksanaan'].isin(filter_strategi)]
    return df_f

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1: DATA ENTRY (SMILE + L1 PENJAHITAN OTOMATIS BERBASIS 2 KUNCI)
# ══════════════════════════════════════════════════════════════════════════════
with tab_entry:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">
        <i class="material-icons" style="font-size:30px;color:#0055A4;">cloud_upload</i>
        <div>
            <h2 style="margin:0;color:#003366;">Upload Data Pembelajaran</h2>
            <p style="margin:0;color:#8a8a8a;font-size:0.9em;">Gabungkan File Evaluasi Level 1 dan Laporan SMILE (Ujian L2/Akademik)</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    sub_upload, sub_riwayat = st.tabs(["📤 Upload & Jahit", "🕒 Riwayat"])

    with sub_upload:
        with st.container(border=True):
            st.info("💡 **Tips:** Untuk hasil terbaik (Master Data Laporan utuh), letakkan **File L1** dan **File SMILE** secara bersamaan ke dalam kotak di bawah ini.")
            uploaded_files = st.file_uploader(
                "Pilih atau seret file Excel/CSV dari Evaluasi L1 & SMILE",
                type=["xlsx","csv", "xls"], accept_multiple_files=True, key="entry_uploader"
            )

        if uploaded_files:
            all_l1_dfs, all_l2_dfs, all_ins_dfs, file_log = [], [], [], []

            with st.status("🔍 Membaca dan menjahit file...", expanded=True) as status_proc:
                for f in uploaded_files:
                    try:
                        if f.name.endswith('.csv'): df_raw = pd.read_csv(f)
                        else: df_raw = pd.read_excel(f)
                        df_raw.columns = df_raw.columns.astype(str).str.strip()

                        # Identifikasi jenis file
                        is_instruktur = ('Nama' in df_raw.columns and 'Kode Diklat' in df_raw.columns and 'Confidence Level' not in df_raw.columns)
                        is_l2_smile = ('Peserta Lulus' in df_raw.columns or 'Confidence Level' in df_raw.columns or 'Jumlah Peserta Lulus' in df_raw.columns) and 'Ins-Eng-1 of 2' not in df_raw.columns
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
                            df_mapped['PIC KI']                  = df_raw.get('Bidang')
                            
                            for i, c in enumerate(INS_COL_NAMES, 1): df_mapped[f'INS{i}'] = df_raw.get(c)
                            for i, c in enumerate(MAT_COL_NAMES, 1): df_mapped[f'MAT{i}'] = df_raw.get(c)
                            for i, c in enumerate(SP_COL_NAMES,  1): df_mapped[f'SP{i}']  = df_raw.get(c)
                            for i, c in enumerate(DS_COL_NAMES,  1): df_mapped[f'DS{i}']  = df_raw.get(c)
                            
                            # KUNCI PAS PENGHUBUNG (Kode + Tgl Mulai)
                            kd_pemb = df_mapped['Kode Pembelajaran'].astype(str).str.replace(' ', '', regex=False).str.upper()
                            tgl_mulai = pd.to_datetime(df_mapped['Tanggal Mulai'],errors='coerce').dt.strftime('%Y%m%d').fillna('NOTGL')
                            df_mapped['Kode Unik'] = kd_pemb + "." + tgl_mulai
                            
                            all_l1_dfs.append(df_mapped)
                            file_log.append({"File":f.name,"Tipe":"🔵 Evaluasi L1","Baris":len(df_raw)})
                            st.session_state.riwayat_upload.append({"nama":f.name,"waktu":datetime.now().strftime("%d/%m/%Y %H:%M"),"tipe":"L1","baris":len(df_raw)})

                        elif is_l2_smile:
                            df_mapped = pd.DataFrame(index=df_raw.index, columns=TARGET_COLUMNS)
                            df_mapped['Kode Pembelajaran']       = df_raw.get('Kode Pembelajaran') if 'Kode Pembelajaran' in df_raw.columns else df_raw.get('Kode Judul')
                            df_mapped['Judul Pembelajaran/Kegiatan'] = df_raw.get('Judul Pembelajaran') if 'Judul Pembelajaran' in df_raw.columns else df_raw.get('Judul')
                            df_mapped['Batch']                   = df_raw.get('Batch') if 'Batch' in df_raw.columns else df_raw.get('Angkatan')
                            df_mapped['Tanggal Mulai']           = df_raw.get('Tgl Mulai')
                            df_mapped['Tanggal Selesai']         = df_raw.get('Tgl Selesai')
                            
                            df_mapped['Peserta Hadir']           = df_raw.get('Peserta Hadir') if 'Peserta Hadir' in df_raw.columns else df_raw.get('Jumlah Peserta Hadir')
                            df_mapped['Jumlah Peserta Lulus L2'] = df_raw.get('Peserta Lulus') if 'Peserta Lulus' in df_raw.columns else df_raw.get('Jumlah Peserta Lulus')
                            df_mapped['Jumlah Peserta Isi L2']   = df_raw.get('Jumlah Peserta Isi')
                            df_mapped['Nilai Confidence']        = df_raw.get('Confidence Level')
                            df_mapped['Nilai Commitment']        = df_raw.get('Commitment Level')
                            
                            # KUNCI PAS PENGHUBUNG (Kode + Tgl Mulai)
                            kd_pemb = df_mapped['Kode Pembelajaran'].astype(str).str.replace(' ', '', regex=False).str.upper()
                            tgl_mulai = pd.to_datetime(df_mapped['Tanggal Mulai'],errors='coerce').dt.strftime('%Y%m%d').fillna('NOTGL')
                            df_mapped['Kode Unik'] = kd_pemb + "." + tgl_mulai
                            
                            all_l2_dfs.append(df_mapped)
                            file_log.append({"File":f.name,"Tipe":"🟢 SMILE / L2","Baris":len(df_raw)})
                            st.session_state.riwayat_upload.append({"nama":f.name,"waktu":datetime.now().strftime("%d/%m/%Y %H:%M"),"tipe":"L2","baris":len(df_raw)})

                        elif is_instruktur:
                            file_log.append({"File":f.name,"Tipe":"🟠 Instruktur","Baris":len(df_raw)})
                            st.warning(f"File {f.name} dikenali sebagai Instruktur. Saat ini fokus penyatuan adalah Master Data Laporan (L1 & SMILE).")
                        
                        else:
                            st.error(f"❌ **{f.name}** tidak dikenali formatnya.")

                    except Exception as e_file:
                        st.error(f"Gagal memproses file {f.name}: {e_file}")

                status_proc.update(label="✅ Selesai membaca file!", state="complete", expanded=False)

            if not all_l1_dfs and not all_l2_dfs:
                st.stop()

            st.markdown("### 📋 Ringkasan File")
            st.dataframe(pd.DataFrame(file_log), use_container_width=True, hide_index=True)

            # Proses Penjahitan (Merging L1 & L2)
            df_l1 = pd.concat(all_l1_dfs, ignore_index=True) if all_l1_dfs else pd.DataFrame(columns=TARGET_COLUMNS)
            
            if all_l2_dfs:
                df_l2_raw  = pd.concat(all_l2_dfs, ignore_index=True)
                l2_cols_av = [c for c in L2_MERGE_COLS if c in df_l2_raw.columns]
                # Ambil baris pertama L2 jika ada duplikat kode unik
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
            
            # Perhitungan & Standardisasi Final
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
                st.markdown("#### 🗓️ Preview Final Master Data Gabungan")
                m1, m2, m3, m4 = st.columns(4)
                rata_l1 = df_final['RATA-RATA KESELURUHAN'].mean()
                total_lulus = df_final['Jumlah Peserta Lulus L2'].sum()
                total_hadir = df_final['Peserta Hadir'].sum()
                pct_lulus   = (total_lulus/total_hadir*100) if total_hadir > 0 else None
                rata_partisipasi = df_final['% Pengisian'].mean()
                
                m1.metric("📊 Baris Siap Masuk",  f"{len(df_final)}")
                m2.metric("😊 Rata-rata Kepuasan L1", f"{rata_l1:.2f}" if pd.notna(rata_l1) else "N/A")
                m3.metric("🎓 Kelulusan SMILE L2",   f"{pct_lulus:.1f}%" if pct_lulus else "N/A")
                m4.metric("📋 Respon Pengisian",  f"{rata_partisipasi*100:.1f}%" if pd.notna(rata_partisipasi) else "N/A")
                
                with st.expander(f"🔍 Cek Kerapian Data ({len(df_final)} baris)", expanded=True):
                    cols_to_show = ['Kode Pembelajaran', 'Judul Pembelajaran/Kegiatan', 'Tanggal Mulai', 'RATA-RATA KESELURUHAN', 'Peserta Hadir', 'Jumlah Peserta Lulus L2']
                    st.dataframe(df_final[cols_to_show].fillna(""), use_container_width=True)

            st.markdown("---")
            ws_target = st.session_state["setting_worksheet"]
            sheet_name_setting = st.session_state["setting_sheet"]

            col_info, col_btn = st.columns([2, 1])
            with col_info:
                st.info(f"Target Penyimpanan: Spreadsheet **{sheet_name_setting}** ➡️ Tab **{ws_target}**")
            
            with col_btn:
                if st.button("🚀 KIRIM KE MASTER DATA GOOGLE SHEETS", use_container_width=True, type="primary"):
                    with st.spinner("Mengirim data ke brankas utama..."):
                        try:
                            client = init_gsheets_connection()
                            sht = client.open(sheet_name_setting).worksheet(ws_target)
                            max_no = get_sheet_max_no(sht)
                            df_final['No'] = range(max_no+1, max_no+1+len(df_final))
                            rows = [clean_row_for_sheets(r) for r in df_final.reindex(columns=TARGET_COLUMNS).values.tolist()]
                            sht.append_rows(rows, value_input_option='USER_ENTERED')
                            st.success(f"✅ Hore! Berhasil menambahkan {len(rows)} baris utuh ke Master Data Laporan!")
                            st.balloons()
                        except Exception as e_push:
                            st.error(f"Gagal mengirim ke Google Sheets: {e_push}")

    with sub_riwayat:
        if not st.session_state.riwayat_upload:
            st.info("Belum ada riwayat upload.")
        else:
            for item in reversed(st.session_state.riwayat_upload):
                badge_color = {"L1":"#0055A4","L2":"#1a7a2e"}.get(item['tipe'],"#666")
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:10px;padding:10px 0;border-bottom:1px solid #eee;">
                    <div style="flex:1;">
                        <p style="margin:0;font-weight:bold;">{item['nama']}</p>
                        <p style="margin:0;font-size:0.8em;color:#8a8a8a;">{item['waktu']} • {item['baris']} baris</p>
                    </div>
                    <span style="background:{badge_color}20;color:{badge_color};border:1px solid {badge_color}55;
                    padding:2px 10px;border-radius:20px;font-size:0.75em;font-weight:bold;">{item['tipe']}</span>
                </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2: ANALYTICS
# ══════════════════════════════════════════════════════════════════════════════
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
# TAB 4: REPORT & KATALOG
# ══════════════════════════════════════════════════════════════════════════════
with tab_report:
    sub_rep_generator, sub_katalog = st.tabs(["📑 Report Generator", "👨‍🏫 Katalog Instruktur"])
    
    with sub_rep_generator:
        st.markdown("### 📑 Generator Laporan Manajemen (Otomatis)")
        st.write("Fitur ini menyusun seluruh hasil analitik, IPA, dan sentimen menjadi dokumen naratif resmi (Microsoft Word).")
        try:
            opsi_bulan_rep = list(df['Laporan Bulan'].dropna().unique()) if 'Laporan Bulan' in df.columns else []
            if opsi_bulan_rep:
                with st.container(border=True):
                    col_r1, col_r2 = st.columns([2, 1])
                    with col_r1: bulan_pilih = st.selectbox("📅 Pilih Periode Laporan:", opsi_bulan_rep, key="bln_report")
                    with col_r2: 
                        st.markdown("<br>", unsafe_allow_html=True)
                        btn_generate = st.button("🚀 Generate Dokumen Laporan", type="primary", use_container_width=True)
                    
                    if btn_generate:
                        st.success(f"Logika pembentukan laporan Word untuk bulan {bulan_pilih} akan berjalan di sini dan menyerap Master Data Laporan.")
            else:
                st.info("Tidak ada data bulan yang ditemukan di Master Data.")
        except Exception as e:
            st.error(f"Gagal memuat Report Generator: {e}")

    with sub_katalog:
        st.markdown("### 👨‍🏫 Katalog & Rekomendasi Instruktur")
        st.info("Logika pembobotan (Mutu vs Jam Terbang) beserta filter ambang batas (contoh: Minimal 2x Mengajar) akan aktif menyesuaikan Data Instruktur.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5: AI ASSISTANT
# ══════════════════════════════════════════════════════════════════════════════
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
                        context = f"Data evaluasi UPDL Jakarta. Total: {len(df)} baris. Ringkasan: {df.describe().to_string()}"
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
with tab_setting:
    st.subheader("⚙️ Pengaturan Aplikasi")
    with st.container(border=True):
        st.markdown("#### 🔗 Konfigurasi Google Sheets (Target Master Data Laporan)")
        nama_sheet = st.text_input("Nama File Google Sheets", value=st.session_state["setting_sheet"])
        st.markdown("---")
        
        st.markdown("#### 📋 Nama Tab (Worksheet)")
        col_ws1, col_ws2 = st.columns(2)
        with col_ws1: nama_worksheet     = st.text_input("Tab — Master Data Laporan L1/SMILE",    value=st.session_state["setting_worksheet"])
        with col_ws2: nama_ws_instruktur = st.text_input("Tab — Detail Instruktur",  value=st.session_state["setting_ws_instruktur"])
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
            st.session_state["setting_ws_instruktur"] = nama_ws_instruktur
            st.session_state["setting_cutoff"]        = cutoff_hari
            st.session_state["setting_threshold"]     = threshold_valid
            st.success("✅ Pengaturan berhasil disimpan! Sistem akan merujuk ke tab Master Data Anda.")
