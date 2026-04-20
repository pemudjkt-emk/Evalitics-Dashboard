import streamlit as st
import pandas as pd
from scipy import stats
import google.generativeai as genai  # Library Tambahan
import plotly.express as px

# 1. Konfigurasi Halaman Dashboard
st.set_page_config(page_title="Smart Evaluation Analytics UPDL Jakarta", page_icon="⚡", layout="wide")

# --- KONFIGURASI GEMINI (YANG BENAR) ---
@st.cache_resource
def load_gemini_model():
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    return genai.GenerativeModel('gemini-1.5-flash')

model = load_gemini_model()

# ==========================================
# HEADER GLOBAL
# ==========================================
col_logo, col_judul = st.columns([2, 8])

with col_logo:
    st.image("Logo PLN.png", width=200)

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
        
        # 1. Pilihan Filter (Ambil nilai unik asli dari dataset)
        opsi_bulan = list(df['Laporan Bulan'].dropna().unique())
        opsi_strategi = list(df['Strategi Pelaksanaan'].dropna().unique())
        opsi_valid = ["Semua Status"] + list(df['% Valid'].dropna().unique())

        # 2. Layout Tombol Filter
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            # Menggunakan multiselect, defaultnya semua bulan terpilih
            filter_bulan = st.multiselect("Laporan Bulanan", options=opsi_bulan, default=opsi_bulan)
        with col_f2:
            # Menggunakan multiselect, defaultnya semua strategi terpilih
            filter_strategi = st.multiselect("Strategi Pelaksanaan", options=opsi_strategi, default=opsi_strategi)
        with col_f3:
            filter_valid = st.selectbox("Validitas", opsi_valid)

        st.markdown("---")

        # 3. Logika Memfilter Data (Disesuaikan untuk Multiselect)
        df_filtered = df.copy()

        # Gunakan fungsi .isin() untuk mengecek apakah data ada di dalam daftar pilihan
        if filter_bulan:
            df_filtered = df_filtered[df_filtered['Laporan Bulan'].isin(filter_bulan)]
        else:
            # Jika user menghapus semua pilihan (kosong), tabel dibuat kosong sementara
            df_filtered = pd.DataFrame(columns=df.columns) 

        if filter_strategi:
            df_filtered = df_filtered[df_filtered['Strategi Pelaksanaan'].isin(filter_strategi)]
        else:
            df_filtered = pd.DataFrame(columns=df.columns)

        if filter_valid != "Semua Status":
            df_filtered = df_filtered[df_filtered['% Valid'] == filter_valid]

        # ==========================================
        # SCORECARD & GRAFIK
        # ==========================================
        if not df_filtered.empty:
            
            # --- BAGIAN SCORECARD ---
            skor_evaluasi = df_filtered['RATA-RATA KESELURUHAN'].mean()
            ind_kurang = df_filtered['Jumlah Indikator dibawah 4.5'].sum()
            ind_lebih = df_filtered['Jumlah Indikator diatas 4.5'].sum()

            col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
            with col_kpi1:
                st.metric(label="🌟 Skor Evaluasi Level 1", value=f"{skor_evaluasi:.2f}")
            with col_kpi2:
                st.metric(label="⚠️ Indikator < 4.5", value=int(ind_kurang))
            with col_kpi3:
                st.metric(label="✅ Indikator > 4.5", value=int(ind_lebih))
            
            st.markdown("---")

            # --- BAGIAN GRAFIK RATA-RATA ---
            st.markdown("### 📈 Skor Evaluasi L1 Berdasarkan Strategi Pelaksanaan")
            
            # Mengelompokkan data berdasarkan strategi, lalu menghitung rata-ratanya
            df_grafik = df_filtered.groupby('Strategi Pelaksanaan')['RATA-RATA KESELURUHAN'].mean().reset_index()

            # Membuat Bar Chart
            fig = px.bar(
                df_grafik, 
                x='Strategi Pelaksanaan', 
                y='RATA-RATA KESELURUHAN',
                text='RATA-RATA KESELURUHAN', # Memunculkan angka di dalam chart
                color_discrete_sequence=['#005b9f'] # Warna Biru khas BUMN/PLN
            )

            # Modifikasi tampilan teks angka dan garis standar
            fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
            
            # Menambahkan garis horizontal (Standar TMP) -> Sesuaikan angkanya jika bukan 4.5
            fig.add_hline(y=4.5, line_dash="dash", line_color="#FFC000", 
                          annotation_text="Standar TMP (4.5)", annotation_position="top left")

            # Merapikan sumbu Y agar skalanya wajar (0 sampai 5)
            fig.update_layout(
                yaxis_range=[0, 5],
                yaxis_title="Rata-rata Skor",
                xaxis_title="",
                margin=dict(t=40, b=0, l=0, r=0) # Mengurangi margin berlebih
            )

            # Menampilkan grafik ke layar
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("---")
            
            # --- TABEL DETAIL ---
            st.write(f"**Menampilkan detail dari {len(df_filtered)} baris data:**")
            st.dataframe(df_filtered, use_container_width=True)

        else:
            st.warning("⚠️ Tidak ada data yang ditampilkan. Silakan pilih minimal satu opsi pada filter di atas.")

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
