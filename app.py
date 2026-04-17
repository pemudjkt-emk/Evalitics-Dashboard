import streamlit as st
import pandas as pd
from scipy import stats # Library baru untuk uji normalitas

# 1. Konfigurasi Halaman Dashboard
st.set_page_config(page_title="Smart Evaluation Analytics UPDL Jakarta", page_icon="⚡", layout="wide")

# ==========================================
# HEADER GLOBAL
# ==========================================
col_logo, col_judul = st.columns([2, 8])

with col_logo:
    st.image("Logo PLN.png", width=260)

with col_judul:
    st.title("Smart Evaluation Analytics UPDL JAKARTA")

st.write("Dashboard interaktif untuk menganalisis data evaluasi pembelajaran.")
st.markdown("---")

col_button, col_empty = st.columns([0.5, 4])
with col_button:
    if st.button("🔄 Perbarui Data", use_container_width=True):
        st.toast("Menarik data terbaru dari Google Sheets...") 

# ==========================================
# 2. INISIALISASI TABS
# ==========================================
tab_statistik, tab_dashboard = st.tabs(["Analisa Statistik", "Dashboard"])

# ==========================================
# 3. ISI TAB 1: ANALISA STATISTIK
# ==========================================
with tab_statistik:
    
    sheet_id = '1RitrlhPmYvxAax2gmZHyhyLX5a8j4xEjwpytlBMxvs8'
    url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv'

    try:
        df = pd.read_csv(url)
        
        st.subheader("📋 Data Evaluasi Mentah")
        st.dataframe(df, use_container_width=True)

        kolom_tersedia = df.columns.tolist()
        
        st.markdown("### 🔍 Pengaturan Analisis Korelasi")
        col1, col2 = st.columns(2)
        with col1:
            var_x = st.selectbox("Pilih Variabel Independen (X):", kolom_tersedia, index=0)
        with col2:
            var_y = st.selectbox("Pilih Variabel Dependen (Y):", kolom_tersedia, index=min(1, len(kolom_tersedia)-1))

        st.markdown("---")

        if pd.api.types.is_numeric_dtype(df[var_x]) and pd.api.types.is_numeric_dtype(df[var_y]):
            
            # ==========================================
            # FITUR BARU: PRA-PEMROSESAN & UJI ASUMSI
            # ==========================================
            st.markdown("### 🛠️ Pra-Pemrosesan & Uji Asumsi")
            
            # Checkbox interaktif
            hapus_outlier = st.checkbox("🧹 Buang Data Pencilan (Outlier) menggunakan metode IQR")
            uji_normalitas = st.checkbox("⚖️ Uji Distribusi Normal (Shapiro-Wilk Test)")
            
            # Membuat salinan dataframe agar data asli tidak rusak
            df_clean = df.copy()

            # Logika Hapus Outlier
            if hapus_outlier:
                # Hitung Batas IQR untuk Variabel X
                Q1_x = df_clean[var_x].quantile(0.25)
                Q3_x = df_clean[var_x].quantile(0.75)
                IQR_x = Q3_x - Q1_x
                batas_bawah_x = Q1_x - 1.5 * IQR_x
                batas_atas_x = Q3_x + 1.5 * IQR_x

                # Hitung Batas IQR untuk Variabel Y
                Q1_y = df_clean[var_y].quantile(0.25)
                Q3_y = df_clean[var_y].quantile(0.75)
                IQR_y = Q3_y - Q1_y
                batas_bawah_y = Q1_y - 1.5 * IQR_y
                batas_atas_y = Q3_y + 1.5 * IQR_y

                # Filter data yang masuk akal (bukan outlier)
                df_clean = df_clean[(df_clean[var_x] >= batas_bawah_x) & (df_clean[var_x] <= batas_atas_x)]
                df_clean = df_clean[(df_clean[var_y] >= batas_bawah_y) & (df_clean[var_y] <= batas_atas_y)]
                
                st.success(f"Berhasil! Tersisa **{len(df_clean)}** baris data dari total awal {len(df)} baris (Outlier telah dihapus).")

            # Logika Uji Normalitas
            if uji_normalitas:
                # Drop NA agar perhitungan shapiro tidak error jika ada sel kosong
                stat_x, p_value_x = stats.shapiro(df_clean[var_x].dropna())
                stat_y, p_value_y = stats.shapiro(df_clean[var_y].dropna())
                
                st.write("**Hasil Uji Shapiro-Wilk (Syarat Normal p-value > 0.05):**")
                col_n1, col_n2 = st.columns(2)
                
                with col_n1:
                    if p_value_x > 0.05:
                        st.info(f"✅ {var_x}: Berdistribusi Normal (p = {p_value_x:.3f})")
                    else:
                        st.error(f"❌ {var_x}: Tidak Normal (p = {p_value_x:.3f})")
                        
                with col_n2:
                    if p_value_y > 0.05:
                        st.info(f"✅ {var_y}: Berdistribusi Normal (p = {p_value_y:.3f})")
                    else:
                        st.error(f"❌ {var_y}: Tidak Normal (p = {p_value_y:.3f})")
            
            st.markdown("---")
            st.markdown("### 📈 Hasil Analisis Korelasi")

            # Analisis Korelasi Pearson (Menggunakan df_clean yang sudah dibersihkan)
            korelasi = df_clean[var_x].corr(df_clean[var_y])
            
            col3, col4 = st.columns([1, 2])
            
            with col3:
                st.metric(label="Koefisien Korelasi (r)", value=round(korelasi, 3))
                
                if korelasi > 0.7:
                    st.success("Interpretasi: Hubungan Positif SANGAT KUAT.")
                elif korelasi > 0.3:
                    st.info("Interpretasi: Hubungan Positif MODERAT.")
                elif korelasi > 0:
                    st.info("Interpretasi: Hubungan Positif LEMAH.")
                elif korelasi < -0.3:
                    st.warning("Interpretasi: Hubungan Negatif.")
                else:
                    st.warning("Interpretasi: Tidak terdapat hubungan linier yang berarti.")
                    
            with col4:
                # Visualisasi Sebaran menggunakan data yang sudah bersih
                st.write(f"**Sebaran Titik Data (Clean): {var_x} vs {var_y}**")
                st.scatter_chart(data=df_clean, x=var_x, y=var_y)
                
        else:
            st.error(f"⚠️ Analisis terhenti: Kolom bukan format angka.")

    except Exception as e:
        st.error("Gagal memuat atau memproses data.")
        st.error(f"Detail Error: {e}")

# ==========================================
# 4. ISI TAB 2: DASHBOARD
# ==========================================
with tab_dashboard:
    st.subheader("📊 Dashboard Utama")
    st.info("Ruang ini siap digunakan untuk elemen Dashboard visual Anda.")
