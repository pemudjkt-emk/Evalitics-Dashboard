import streamlit as st
import pandas as pd
from scipy import stats
import google.generativeai as genai  # Library Tambahan
import plotly.express as px
import streamlit as st

# 1. Konfigurasi Halaman Dashboard
st.set_page_config(page_title="Smart Evaluation Analytics UPDL Jakarta", page_icon="⚡", layout="wide")
# Kode CSS untuk memodifikasi Tab
st.markdown("""
    <style>
    /* Mengubah ukuran font dan warna teks tab secara umum */
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 30px; /* Ubah ukuran sesuai keinginan */
        font-weight: bold;
    }

    /* Mengatur warna teks tab yang sedang tidak aktif */
    .stTabs [data-baseweb="tab"] {
        color: #666666; /* Abu-abu */
    }

    /* Mengatur warna teks tab yang sedang AKTIF */
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #005b9f !important; /* Biru PLN */
    }

    /* Mengatur warna garis bawah tab yang sedang AKTIF */
    .stTabs [data-baseweb="tab-highlight"] {
        background-color: #ffc107 !important;
    }
    </style>
    """, unsafe_allow_html=True)

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
        # FITUR BARU: IMPORTANCE-PERFORMANCE ANALYSIS (IPA)
        # ==========================================
        st.markdown("---")
        st.markdown("### 🎯 Analisis Kuadran Strategi (Importance-Performance Analysis)")
        st.write("Grafik ini memetakan 8 indikator utama berdasarkan **Kinerja** (Skor Rata-rata) dan **Kepentingan** (Korelasi dengan Skor Akhir). Fokuskan perbaikan pada indikator yang jatuh di **Kuadran 1 (Kiri Atas)**.")

        try:
            # 1. Persiapan & Pembersihan Data (Memastikan format angka)
            kolom_ipa = ['INS1', 'INS2', 'INS3', 'INS4', 'INS5', 'INS6', 'INS7', 'INS8',
                         'MAT1', 'MAT2', 'MAT3', 'MAT4', 'MAT5', 'MAT6',
                         'RATA DS', 'RATA SP', 'RATA-RATA KESELURUHAN']
            
            # Buat copy data khusus untuk IPA
            df_ipa = df.copy()
            
            # Paksa konversi ke angka (jika ada spasi/teks tidak sengaja di Sheets, akan diubah jadi NaN)
            for col in kolom_ipa:
                if col in df_ipa.columns:
                    df_ipa[col] = pd.to_numeric(df_ipa[col], errors='coerce')

            # Hapus baris yang nilai akhirnya kosong agar hitungan korelasi tidak error
            df_ipa = df_ipa.dropna(subset=['RATA-RATA KESELURUHAN'])

            # 2. Menggabungkan Menjadi 8 Kategori Utama
            df_ipa['Engagement Instruktur'] = df_ipa[['INS1', 'INS2']].mean(axis=1)
            df_ipa['Relevance Instruktur'] = df_ipa[['INS3', 'INS4']].mean(axis=1)
            df_ipa['Satisfaction Instruktur'] = df_ipa[['INS5', 'INS6', 'INS7', 'INS8']].mean(axis=1)
            df_ipa['Engagement Materi'] = df_ipa[['MAT1', 'MAT2']].mean(axis=1)
            df_ipa['Relevance Materi'] = df_ipa[['MAT3', 'MAT4']].mean(axis=1)
            df_ipa['Satisfaction Materi'] = df_ipa[['MAT5', 'MAT6']].mean(axis=1)
            df_ipa['Satisfaction Sarana Digital'] = df_ipa['RATA DS']
            df_ipa['Satisfaction Sarana In Class'] = df_ipa['RATA SP']

            kategori_list = [
                'Engagement Instruktur', 'Relevance Instruktur', 'Satisfaction Instruktur',
                'Engagement Materi', 'Relevance Materi', 'Satisfaction Materi',
                'Satisfaction Sarana Digital', 'Satisfaction Sarana In Class'
            ]

            # 3. Menghitung X (Kinerja) dan Y (Kepentingan)
            kinerja = []
            kepentingan = []

            for kat in kategori_list:
                # Sumbu X: Rata-rata Skor dari tiap kategori
                kinerja.append(df_ipa[kat].mean())
                # Sumbu Y: Korelasi kategori tersebut dengan Skor Keseluruhan
                kepentingan.append(df_ipa[kat].corr(df_ipa['RATA-RATA KESELURUHAN']))

            # Memasukkan ke dalam DataFrame khusus untuk grafik
            df_plot_ipa = pd.DataFrame({
                'Kategori': kategori_list,
                'Kinerja': kinerja,
                'Kepentingan': kepentingan
            })

            # Menghapus data jika ada perhitungan yang gagal (NaN)
            df_plot_ipa = df_plot_ipa.dropna()

            # Menghitung Garis Potong Tengah (Crosshair) dari nilai rata-rata X dan Y
            x_cross = df_plot_ipa['Kinerja'].mean()
            y_cross = df_plot_ipa['Kepentingan'].mean()

            # 4. Visualisasi Scatter Plot 4 Kuadran dengan Plotly
            import plotly.express as px

            fig_ipa = px.scatter(
                df_plot_ipa,
                x='Kinerja',
                y='Kepentingan',
                text='Kategori', # Memunculkan nama kategori di titik
                size_max=60
            )

            # Mempercantik titik dan posisi teks agar tidak menimpa titik
            fig_ipa.update_traces(
                textposition='top center',
                marker=dict(size=14, color='#005b9f', line=dict(width=2, color='DarkSlateGrey'))
            )

            # Menambahkan Garis Silang Pembagi Kuadran
            fig_ipa.add_hline(y=y_cross, line_dash="dash", line_color="#FFC000")
            fig_ipa.add_vline(x=x_cross, line_dash="dash", line_color="#FFC000")

            # Menambahkan Label Kuadran Statis di Sudut-sudut Grafik
            fig_ipa.add_annotation(xref="paper", yref="paper", x=0.01, y=0.99, text="<b>KUADRAN 1</b><br>🚨 Prioritas Utama", showarrow=False, font=dict(color="#d32f2f", size=14), align="left")
            fig_ipa.add_annotation(xref="paper", yref="paper", x=0.99, y=0.99, text="<b>KUADRAN 2</b><br>🌟 Pertahankan", showarrow=False, font=dict(color="#2e7d32", size=14), align="right")
            fig_ipa.add_annotation(xref="paper", yref="paper", x=0.01, y=0.01, text="<b>KUADRAN 3</b><br>📉 Prioritas Rendah", showarrow=False, font=dict(color="#757575", size=14), align="left")
            fig_ipa.add_annotation(xref="paper", yref="paper", x=0.99, y=0.01, text="<b>KUADRAN 4</b><br>⚠️ Berlebihan", showarrow=False, font=dict(color="#f57c00", size=14), align="right")

            # Merapikan sumbu grafik agar proporsional
            fig_ipa.update_layout(
                xaxis_title="Kinerja (Sumbu X) →",
                yaxis_title="Kepentingan / Korelasi (Sumbu Y) ↑",
                height=600,
                margin=dict(t=40, b=40, l=40, r=40)
            )

            # Menampilkan Grafik
            st.plotly_chart(fig_ipa, use_container_width=True)
            
            # Membuat Insight Teks Otomatis di bawah grafik
            q1_items = df_plot_ipa[(df_plot_ipa['Kinerja'] < x_cross) & (df_plot_ipa['Kepentingan'] > y_cross)]['Kategori'].tolist()
            
            if q1_items:
                st.error(f"**Rekomendasi Manajemen:** Indikator **{', '.join(q1_items)}** jatuh di Kuadran 1. Ini sangat penting bagi peserta namun kinerjanya masih di bawah rata-rata. Fokuskan perbaikan bulan ini di area tersebut!")
            else:
                st.success("**Rekomendasi Manajemen:** Saat ini tidak ada indikator yang jatuh di Kuadran 1 (Prioritas Utama). Pertahankan kinerja yang sudah ada!")

        except Exception as e:
            st.error(f"⚠️ Gagal memproses data IPA. Pastikan ejaan nama kolom (INS1, MAT1, dll) persis sama dengan di Sheets. Detail Error: {e}")

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
            
            # UPDATE: Ubah perbandingan kolom menjadi [2, 1] 
            # Kolom pertama (col_chart) untuk grafik, kolom kedua (col_spacer) dibiarkan kosong di kanan
            col_chart, col_spacer = st.columns([2, 1])

            with col_chart:
                # Mengelompokkan data berdasarkan strategi, lalu menghitung rata-ratanya
                df_grafik = df_filtered.groupby('Strategi Pelaksanaan')['RATA-RATA KESELURUHAN'].mean().reset_index()

                # Membuat Bar Chart
                fig = px.bar(
                    df_grafik, 
                    x='Strategi Pelaksanaan', 
                    y='RATA-RATA KESELURUHAN',
                    text='RATA-RATA KESELURUHAN', # Memunculkan angka di atas bar
                    color_discrete_sequence=['#005b9f'] # Warna Biru khas BUMN/PLN
                )

                # Modifikasi tampilan teks angka dan letaknya
                fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
                
                # Menambahkan garis horizontal (Standar TMP) -> Sesuaikan angkanya jika bukan 4.5
                fig.add_hline(y=4.5, line_dash="dash", line_color="#FFC000", 
                              annotation_text="Standar TMP (4.5)", annotation_position="top left")

                # Merapikan sumbu Y, memperpendek tinggi grafik, dan menipiskan batang
                fig.update_layout(
                    height=350,       # [BARU] Memperpendek tinggi grafik menjadi 350 pixel
                    bargap=0.5,       # [BARU] Menipiskan ukuran batang (0.5 = 50% jarak antar batang)
                    yaxis_range=[0, 5],
                    yaxis_title="Rata-rata Skor",
                    xaxis_title="",
                    margin=dict(t=40, b=0, l=0, r=0) # Mengurangi margin berlebih
                )

                # Menampilkan grafik ke layar (di dalam batas kolom tengah)
                st.plotly_chart(fig, use_container_width=True)

            st.markdown("---")
            
            # --- TABEL DETAIL ---
            st.write(f"**Menampilkan detail dari {len(df_filtered)} baris data:**")
            st.dataframe(df_filtered, use_container_width=True)

        else:
            # Posisi 'else' sejajar lurus ke atas dengan 'if not df_filtered.empty:'
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
