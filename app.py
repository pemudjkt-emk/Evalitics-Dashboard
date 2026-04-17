import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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

