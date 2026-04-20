import streamlit as st
import pandas as pd
from scipy import stats
import google.generativeai as genai  # Library Tambahan

# 1. Konfigurasi Halaman Dashboard
st.set_page_config(page_title="Smart Evaluation Analytics UPDL Jakarta", page_icon="⚡", layout="wide")

# --- KONFIGURASI GEMINI ---
# Ambil API Key dari st.secrets (Atur di Dashboard Streamlit Cloud > Settings > Secrets)
# Jika running lokal, pastikan sudah set API Key atau ganti dengan string langsung (tidak disarankan)
try:
    genai.configure(api_key=st.secrets["AIzaSyBDDEP8i_OXt6Ray2z_q11AVRsysL1QMNI"])
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.sidebar.error("⚠️ API Key Gemini belum terpasang di Secrets.")

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
# MENARIK DATA
# ==========================================
sheet_id = '1RitrlhPmYvxAax2gmZHyhyLX5a8j4xEjwpytlBMxvs8'
url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv'

try:
    df = pd.read_csv(url)
    kolom_tersedia = df.columns.tolist()

    # ==========================================
    # INISIALISASI TABS
    # ==========================================
    tab_statistik, tab_dashboard, tab_ai = st.tabs(["Analisa Statistik", "Dashboard", "🤖 Asisten AI"])

    # ==========================================
    # ISI TAB 1: ANALISA STATISTIK
    # ==========================================
    with tab_statistik:
        st.subheader("📋 Data Evaluasi Mentah")
        st.dataframe(df, use_container_width=True)

        st.markdown("### 🔍 Pengaturan Analisis Korelasi")
        col1, col2 = st.columns(2)
        with col1:
            var_x = st.selectbox("Pilih Variabel Independen (X):", kolom_tersedia, index=0)
        with col2:
            var_y = st.selectbox("Pilih Variabel Dependen (Y):", kolom_tersedia, index=min(1, len(kolom_tersedia)-1))

        st.markdown("---")

        if pd.api.types.is_numeric_dtype(df[var_x]) and pd.api.types.is_numeric_dtype(df[var_y]):
            st.markdown("### 🛠️ Pra-Pemrosesan & Uji Asumsi")
            hapus_outlier = st.checkbox("🧹 Buang Data Pencilan (Outlier) menggunakan metode IQR")
            uji_normalitas = st.checkbox("⚖️ Uji Distribusi Normal (Shapiro-Wilk Test)")
            
            df_clean = df.copy()

            if hapus_outlier:
                Q1_x = df_clean[var_x].quantile(0.25)
                Q3_x = df_clean[var_x].quantile(0.75)
                IQR_x = Q3_x - Q1_x
                batas_bawah_x = Q1_x - 1.5 * IQR_x
                batas_atas_x = Q3_x + 1.5 * IQR_x

                Q1_y = df_clean[var_y].quantile(0.25)
                Q3_y = df_clean[var_y].quantile(0.75)
                IQR_y = Q3_y - Q1_y
                batas_bawah_y = Q1_y - 1.5 * IQR_y
                batas_atas_y = Q3_y + 1.5 * IQR_y

                df_clean = df_clean[(df_clean[var_x] >= batas_bawah_x) & (df_clean[var_x] <= batas_atas_x)]
                df_clean = df_clean[(df_clean[var_y] >= batas_bawah_y) & (df_clean[var_y] <= batas_atas_y)]
                st.success(f"Tersisa **{len(df_clean)}** baris data setelah Outlier dihapus.")

            if uji_normalitas:
                stat_x, p_value_x = stats.shapiro(df_clean[var_x].dropna())
                stat_y, p_value_y = stats.shapiro(df_clean[var_y].dropna())
                
                col_n1, col_n2 = st.columns(2)
                with col_n1:
                    if p_value_x > 0.05: st.info(f"✅ {var_x}: Normal (p = {p_value_x:.3f})")
                    else: st.error(f"❌ {var_x}: Tidak Normal (p = {p_value_x:.3f})")
                with col_n2:
                    if p_value_y > 0.05: st.info(f"✅ {var_y}: Normal (p = {p_value_y:.3f})")
                    else: st.error(f"❌ {var_y}: Tidak Normal (p = {p_value_y:.3f})")
            
            st.markdown("---")
            korelasi = df_clean[var_x].corr(df_clean[var_y])
            
            col3, col4 = st.columns([1, 2])
            with col3:
                st.metric(label="Koefisien Korelasi (r)", value=round(korelasi, 3))
            with col4:
                st.write(f"**Sebaran Titik Data (Clean): {var_x} vs {var_y}**")
                st.scatter_chart(data=df_clean, x=var_x, y=var_y)
        else:
            st.error(f"⚠️ Analisis terhenti: Kolom bukan format angka.")

    # ==========================================
    # ISI TAB 2: DASHBOARD
    # ==========================================
    with tab_dashboard:
        st.subheader("📊 Dashboard Utama")
        
        # 1. Pilihan Dropdown Filter
        opsi_bulan = ["Semua Bulan"] + list(df['Laporan Bulan'].dropna().unique())
        opsi_strategi = ["Semua Strategi"] + list(df['Strategi Pelaksanaan'].dropna().unique())
        opsi_valid = ["Semua Status"] + list(df['% Valid'].dropna().unique())

        # 2. Layout Tombol Filter
        col_f1, col_f2, col_f3, col_kosong = st.columns([2, 2, 2, 4])
        with col_f1:
            filter_bulan = st.selectbox("Laporan Bulanan", opsi_bulan)
        with col_f2:
            filter_strategi = st.selectbox("Strategi Pelaksanaan", opsi_strategi)
        with col_f3:
            filter_valid = st.selectbox("Validitas", opsi_valid)

        st.markdown("---")

        # 3. Logika Memfilter Data
        df_filtered = df.copy()

        if filter_bulan != "Semua Bulan":
            df_filtered = df_filtered[df_filtered['Laporan Bulan'] == filter_bulan]
        if filter_strategi != "Semua Strategi":
            df_filtered = df_filtered[df_filtered['Strategi Pelaksanaan'] == filter_strategi]
        if filter_valid != "Semua Status":
            df_filtered = df_filtered[df_filtered['% Valid'] == filter_valid]

       # ==========================================
        # FITUR BARU: SCORECARD / KPI METRICS
        # ==========================================
        if not df_filtered.empty:
            # BAGIAN INI HARUS MENJOROK KE DALAM (Tekan Tab 1x dari posisi 'if')
            # Mengagregasi angka dari data yang sudah difilter
            # Gunakan .mean() untuk rata-rata skor, dan .sum() untuk menjumlahkan indikator
            skor_evaluasi = df_filtered['RATA-RATA KESELURUHAN'].mean()
            ind_kurang = df_filtered['Jumlah Indikator dibawah 4.5'].sum()
            ind_lebih = df_filtered['Jumlah Indikator diatas 4.5'].sum()

            # Membuat 3 kolom sejajar untuk Scorecard
            col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
            
            with col_kpi1:
                # BAGIAN INI MENJOROK LAGI (Tekan Tab di bawah 'with')
                st.metric(label="🌟 Skor Evaluasi Level 1", value=f"{skor_evaluasi:.2f}")
            with col_kpi2:
                st.metric(label="⚠️ Indikator < 4.5", value=int(ind_kurang))
            with col_kpi3:
                st.metric(label="✅ Indikator > 4.5", value=int(ind_lebih))
        
        else:
            # Posisi 'else' HARUS sejajar lurus ke atas dengan huruf 'i' pada 'if'
            st.warning("⚠️ Tidak ada data yang cocok dengan kombinasi filter Anda.")

# --- ISI TAB 3: ASISTEN AI (FITUR BARU) ---
    with tab_ai:
        st.subheader("🤖 Tanya Asisten EVALYTICS")
        st.write("Gunakan AI untuk menganalisis tren atau meminta saran perbaikan program.")
        
        # Kotak input pertanyaan
        user_question = st.chat_input("Tanya sesuatu tentang data evaluasi Anda...")
        
        if user_question:
            with st.chat_message("user"):
                st.write(user_question)
            
            with st.chat_message("assistant"):
                with st.spinner("Gemini sedang berpikir..."):
                    # Memberikan konteks data agar Gemini tahu apa yang dianalisis
                    # Kita kirimkan ringkasan data (5 baris pertama) sebagai konteks
                    context = f"Data ini adalah hasil evaluasi UPDL Jakarta. Kolom yang tersedia: {kolom_tersedia}. Ringkasan data: {df.describe().to_string()}"
                    full_prompt = f"Konteks: {context}\n\nPertanyaan: {user_question}"
                    
                    try:
                        response = model.generate_content(full_prompt)
                        st.markdown(response.text)
                    except Exception as ai_err:
                        st.error(f"Gagal mendapatkan respon AI: {ai_err}")
# ==========================================
# PENUTUP TRY-EXCEPT (WAJIB ADA DI PALING BAWAH & RATA KIRI)
# ==========================================
except Exception as e:
    st.error("Gagal memuat atau memproses data dari Google Sheets.")
    st.error(f"Detail Error Teknis: {e}")
