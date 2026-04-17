import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Konfigurasi Awal
st.set_page_config(page_title="Analytics Center PLN", layout="wide")

# Penarikan Data (Gunakan ID yang sama)
sheet_id = '1RitrlhPmYvxAax2gmZHyhyLX5a8j4xEjwpytlBMxvs8'
url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv'

@st.cache_data(ttl=600)
def load_data():
    return pd.read_csv(url)

# --- MULAI BLOK TRY ---
try:
    df = load_data()

    # Header Utama
    st.title("📊 Sistem Evaluasi Terpadu")
    
    # 2. DEFINISI TAB
    tab_korelasi, tab_dashboard = st.tabs(["🔍 Analisa Korelasi", "📈 Dashboard Overview"])

    # ==========================================
    # ISI TAB 1: ANALISA KORELASI
    # ==========================================
    with tab_korelasi:
    import streamlit as st
import pandas as pd

# Konfigurasi Halaman & Judul (Sesuaikan dengan milik Anda)
st.set_page_config(page_title="Smart Evaluation Analytics", page_icon="⚡", layout="wide")

col_logo, col_judul = st.columns([1, 8])
with col_logo:
    # Asumsi Anda menggunakan logo PLN lokal seperti langkah sebelumnya
    st.image("logo_pln.png", width=80) 
with col_judul:
    st.title("Smart Evaluation Analytics")
st.write("Dashboard interaktif untuk menganalisis korelasi data evaluasi pembelajaran.")
st.markdown("---")

# ==========================================
# 1. MENAMBAHKAN TOMBOL REFRESH INTERNAL
# ==========================================
# Membuat kolom agar tombol tidak terlalu lebar
col_button, col_empty = st.columns([2, 8])

with col_button:
    # Jika tombol diklik, Streamlit akan otomatis memuat ulang halaman
    if st.button("🔄 Perbarui Data Sekarang", use_container_width=True):
        st.toast("Menarik data terbaru dari Google Sheets...") # Memunculkan notifikasi pop-up kecil

# ==========================================
# 2. PENARIKAN DATA GOOGLE SHEETS
# ==========================================
sheet_id = '1RitrlhPmYvxAax2gmZHyhyLX5a8j4xEjwpytlBMxvs8'
url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv'

try:
    df = pd.read_csv(url)
    
    st.subheader("📋 Data Evaluasi Mentah")
    st.dataframe(df, use_container_width=True)

    # ==========================================
    # ISI TAB 2: DASHBOARD
    # ==========================================
    with tab_dashboard:
        st.header("Ringkasan Eksekutif")
        
        # Masukkan kode Grid (3 kolom) dan Scorecards Anda di sini
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Peserta", len(df))
        col2.metric("Rata-rata Skor", round(df[kolom_numeric[0]].mean(), 2))
        
        st.write("Visualisasi ringkasan lainnya...")

# --- TUTUP DENGAN EXCEPT ---
except Exception as e:
    st.error(f"Terjadi kesalahan: {e}")
    st.info("Pastikan koneksi internet stabil dan nama kolom di Google Sheets sudah sesuai.")
