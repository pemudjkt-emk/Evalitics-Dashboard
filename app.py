import streamlit as st
import pandas as pd

# 1. Konfigurasi Halaman Dashboard (Harus di baris pertama)
st.set_page_config(page_title="Smart Evaluation Analytics UPDL Jakarta", page_icon="⚡", layout="wide")

# ==========================================
# HEADER GLOBAL (Akan selalu muncul di semua tab)
# ==========================================
col_logo, col_judul = st.columns([2, 8])

with col_logo:
    # GANTI URL dengan NAMA FILE lokal Anda. 
    # Pastikan nama file dan ekstensinya (.png/.jpg) diketik persis sama.
    st.image("Logo PLN.png", width=260)

with col_judul:
    st.title("Smart Evaluation Analytics UPDL JAKARTA")

st.write("Dashboard interaktif untuk menganalisis data evaluasi pembelajaran.")
st.markdown("---")

# Tombol Refresh Global
col_button, col_empty = st.columns([0.5, 4])
with col_button:
    if st.button("🔄 Perbarui Data", use_container_width=True):
        st.toast("Menarik data terbaru dari Google Sheets...") 


# ==========================================
# 2. INISIALISASI TABS
# ==========================================
# Membuat variabel penampung untuk 2 tab
tab_statistik, tab_dashboard = st.tabs(["Analisa Statistik", "Dashboard"])


# ==========================================
# 3. ISI TAB 1: ANALISA STATISTIK
# ==========================================
# Perhatikan indentasi (spasi ke dalam) di bawah baris 'with' ini
with tab_statistik:
    
    # Menarik Data dari Google Sheets Anda
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
        
        # Membuat 2 kolom untuk menu dropdown filter
        col1, col2 = st.columns(2)
        with col1:
            var_x = st.selectbox("Pilih Variabel Independen (X):", kolom_tersedia, index=0)
        with col2:
            var_y = st.selectbox("Pilih Variabel Dependen (Y):", kolom_tersedia, index=min(1, len(kolom_tersedia)-1))

        st.markdown("---")

        # Memastikan kolom yang dipilih adalah angka sebelum dihitung
        if pd.api.types.is_numeric_dtype(df[var_x]) and pd.api.types.is_numeric_dtype(df[var_y]):
            
            # Analisis Statistik (Korelasi Pearson)
            korelasi = df[var_x].corr(df[var_y])
            
            col3, col4 = st.columns([1, 2])
            
            with col3:
                # Menampilkan Metrik Utama
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
                # Visualisasi Scatter Plot
                st.write(f"**Sebaran Titik Data: {var_x} vs {var_y}**")
                st.scatter_chart(data=df, x=var_x, y=var_y)
                
        else:
            st.error(f"⚠️ Analisis terhenti: Kolom '{var_x}' atau '{var_y}' bukan format angka. Pastikan data di Google Sheets tidak mengandung huruf.")

    except Exception as e:
        st.error("Gagal memuat data. Pastikan akses Google Sheets sudah diubah menjadi 'Anyone with the link can view'.")
        st.error(f"Detail Error Teknis: {e}")


# ==========================================
# 4. ISI TAB 2: DASHBOARD
# ==========================================
with tab_dashboard:
    st.subheader("📊 Dashboard Utama")
    st.info("Ruang ini siap digunakan untuk Dashboard Anda. Anda bisa memasukkan grafik Plotly, metrik scorecard tambahan, atau meng-embed Looker Studio di sini.")
