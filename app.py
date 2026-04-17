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
        st.header("Analisis Hubungan Variabel")
        
        # Masukkan kode filter dan scatter plot Anda di sini
        kolom_numeric = df.select_dtypes(include=['number']).columns
        
        c1, c2 = st.columns(2)
        with c1:
            var_x = st.selectbox("Pilih Variabel X", kolom_numeric, key="x_corr")
        with c2:
            var_y = st.selectbox("Pilih Variabel Y", kolom_numeric, key="y_corr")
            
        fig = px.scatter(df, x=var_x, y=var_y, trendline="ols")
        st.plotly_chart(fig, use_container_width=True)

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
