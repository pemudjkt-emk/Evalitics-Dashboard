import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Konfigurasi Halaman Dashboard
st.set_page_config(page_title="Smart Evaluation Analytics UPDL Jakarta", page_icon="⚡", layout="wide")

# Membuat 2 kolom dengan rasio lebar 1 : 8
col_logo, col_judul = st.columns([2, 8])

with col_logo:
   # GANTI URL dengan NAMA FILE lokal Anda. 
    # Pastikan nama file dan ekstensinya (.png/.jpg) diketik persis sama.
    st.image("Logo PLN.png", width=260)

with col_judul:
    # Menaruh judul di kolom kedua
    st.title("Smart Evaluation Analytics UPDL JAKARTA")

st.write("Dashboard interaktif untuk menganalisis data evaluasi pembelajaran.")
st.markdown("---")

# MENAMBAHKAN TOMBOL REFRESH INTERNAL
col_button, col_empty = st.columns([0.5, 4])
with col_button:
    # Jika tombol diklik, Streamlit akan otomatis memuat ulang halaman
    if st.button("🔄 Perbarui Data", use_container_width=True):
        st.toast("Menarik data terbaru dari Google Sheets...") # Memunculkan notifikasi pop-up kecil


# 2. Menarik Data dari Google Sheets Anda
# ID ini diambil dari link yang Anda berikan
sheet_id = '1RitrlhPmYvxAax2gmZHyhyLX5a8j4xEjwpytlBMxvs8'
url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv'

try:
    # Membaca data CSV ke dalam Pandas DataFrame
    df = pd.read_csv(url)
    
    st.subheader("📋 Data Evaluasi Mentah")
    # Menampilkan dataframe agar interaktif di layar pengguna
    st.dataframe(df, use_container_width=True)

    # Deteksi kolom secara otomatis
    kolom_tersedia = df.columns.tolist()
    
    st.markdown("### 🔍 Pengaturan Analisis Korelasi")
    st.write("Pilih kolom yang berisi data numerik (angka) untuk melihat hubungannya.")
    
    # Membuat 2 kolom untuk menu dropdown
    col1, col2 = st.columns(2)
    with col1:
        var_x = st.selectbox("Pilih Variabel Independen (X):", kolom_tersedia, index=0)
    with col2:
        var_y = st.selectbox("Pilih Variabel Dependen (Y):", kolom_tersedia, index=min(1, len(kolom_tersedia)-1))

    st.markdown("---")

    # Memastikan kolom yang dipilih adalah angka sebelum dihitung
    if pd.api.types.is_numeric_dtype(df[var_x]) and pd.api.types.is_numeric_dtype(df[var_y]):
        
        # 3. Analisis Statistik (Korelasi Pearson)
        korelasi = df[var_x].corr(df[var_y])
        
        col3, col4 = st.columns([1, 2])
        
        with col3:
            # 4. Menampilkan Metrik Utama
            st.metric(label="Koefisien Korelasi (r)", value=round(korelasi, 3))
            
            # Logika Interpretasi Naratif Otomatis
            if korelasi > 0.7:
                st.success("Interpretasi: Hubungan Positif SANGAT KUAT. Kenaikan variabel X sangat sejalan dengan variabel Y.")
            elif korelasi > 0.3:
                st.info("Interpretasi: Hubungan Positif MODERAT. Terdapat tren yang cukup sejalan.")
            elif korelasi > 0:
                st.info("Interpretasi: Hubungan Positif LEMAH. Tren searah namun tidak terlalu kuat.")
            elif korelasi < -0.3:
                st.warning("Interpretasi: Hubungan Negatif. Kenaikan variabel X diikuti penurunan variabel Y.")
            else:
                st.warning("Interpretasi: Tidak terdapat hubungan linier yang berarti.")
                
        with col4:
            # 5. Visualisasi Scatter Plot
            st.write(f"**Sebaran Titik Data: {var_x} vs {var_y}**")
            st.scatter_chart(data=df, x=var_x, y=var_y)
            
    else:
        st.error(f"⚠️ Analisis terhenti: Kolom '{var_x}' atau '{var_y}' bukan format angka. Pastikan data di Google Sheets tidak mengandung huruf.")

except Exception as e:
    st.error("Gagal memuat data. Pastikan akses Google Sheets sudah diubah menjadi 'Anyone with the link can view'.")
    st.error(f"Detail Error Teknis: {e}")

# ==========================================
# 1. KONFIGURASI HALAMAN & CSS
# ==========================================
st.set_page_config(page_title="Overview Evaluasi UPDL", layout="wide")

st.markdown("""
<style>
    .metric-box { padding: 15px; border-radius: 5px; text-align: center; color: white; margin-bottom: 15px;}
    .box-blue { background-color: #0B5394; }
    .box-green { background-color: #27AE60; }
    .box-red { background-color: #E74C3C; }
    .metric-title { font-size: 14px; font-weight: bold; margin-bottom: 5px;}
    .metric-value { font-size: 32px; font-weight: bold; margin: 0;}
    .metric-delta { font-size: 12px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. PENARIKAN DATA GOOGLE SHEETS (CACHED)
# ==========================================
# ID Spreadsheet Anda
sheet_id = '1RitrlhPmYvxAax2gmZHyhyLX5a8j4xEjwpytlBMxvs8'
url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv'

# Fungsi untuk menarik data, di-cache selama 10 menit (600 detik)
@st.cache_data(ttl=600)
def load_data(csv_url):
    data = pd.read_csv(csv_url)
    return data

try:
    # Eksekusi penarikan data
    df = load_data(url)
    
    # (Opsional) Tombol untuk refresh data manual mengabaikan cache
    if st.button("🔄 Perbarui Data Sekarang"):
        st.cache_data.clear() # Membersihkan memori cache
        st.rerun()            # Memuat ulang halaman
        
    # ==========================================
    # 3. HEADER & TATA LETAK UTAMA
    # ==========================================
    st.markdown("<h2 style='text-align: center; color: #0B5394;'>OVERVIEW EVALUASI LEVEL 1 & 2 UPDL JAKARTA</h2>", unsafe_allow_html=True)
    st.markdown("---")

    col_left, col_mid, col_right = st.columns([1.2, 1, 1.2], gap="large")

    # FILTER DASHBOARD
    # ==========================================
    # Membagi layout menjadi 4 kolom (3 untuk filter, 1 untuk ruang kosong di kanan agar tidak terlalu lebar)
    col_f1, col_f2, col_f3, _ = st.columns([2, 2, 2, 4]) 
    
    with col_f1:
        # Mengambil nilai unik dari kolom untuk pilihan dropdown, ditambah opsi "Semua" di urutan pertama
        opsi_bulan = ["Semua Bulan"] + list(df['Laporan Bulan'].dropna().unique())
        filter_bulan = st.selectbox("Laporan Bulan", opsi_bulan)

    with col_f2:
        opsi_strategi = ["Semua Strategi"] + list(df['Strategi Pelaksanaan'].dropna().unique())
        filter_strategi = st.selectbox("Strategi Pelaksanaan", opsi_strategi)

    with col_f3:
        opsi_validitas = ["Semua"] + list(df['% Valid'].dropna().unique())
        filter_validitas = st.selectbox("Validitas", opsi_validitas)

    st.markdown("<br>", unsafe_allow_html=True) # Memberi sedikit jarak/spasi ke bawah
