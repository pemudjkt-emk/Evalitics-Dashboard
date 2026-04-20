import streamlit as st
import pandas as pd
from scipy import stats
import google.generativeai as genai
import plotly.express as px

# 1. Konfigurasi Halaman Dashboard
st.set_page_config(page_title="Smart Evaluation Analytics UPDL Jakarta", page_icon="⚡", layout="wide")

# Kode CSS untuk memodifikasi Tab
st.markdown("""
    <style>
    /* Mengubah ukuran font dan warna teks tab secara umum */
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 30px; 
        font-weight: bold;
    }
    /* Mengatur warna teks tab yang sedang tidak aktif */
    .stTabs [data-baseweb="tab"] {
        color: #666666; 
    }
    /* Mengatur warna teks tab yang sedang AKTIF */
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #005b9f !important; 
    }
    /* Mengatur warna garis bawah tab yang sedang AKTIF */
    .stTabs [data-baseweb="tab-highlight"] {
        background-color: #ffc107 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- KONFIGURASI GEMINI ---
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

st.write("Dashboard interaktif untuk menganalisis data evaluasi pembelajaran di UPDL Jakarta.")
st.markdown("---")

col_button, col_empty = st.columns([0.5, 4])
with col_button:
    if st.button("🔄 Update Data", use_container_width=True):
        st.toast("Menarik data terbaru dari Google Sheets...") 

# ==========================================
# MENARIK DATA
# ==========================================
sheet_id = '1RitrlhPmYvxAax2gmZHyhyLX5a8j4xEjwpytlBMxvs8'
url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv'

try:
    df = pd.read_csv(url)

    # ==========================================
    # FILTER GLOBAL & PRA-PEMROSESAN (BERLAKU UNTUK SEMUA TAB)
    # ==========================================
    st.markdown("### 🎛️ FILTER DATA")
    
    opsi_bulan = list(df['Laporan Bulan'].dropna().unique())
    opsi_strategi = list(df['Strategi Pelaksanaan'].dropna().unique())
    opsi_valid = ["Semua Status"] + list(df['% Valid'].dropna().unique())

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        filter_bulan = st.multiselect("Laporan Bulanan", options=opsi_bulan, default=opsi_bulan)
    with col_f2:
        filter_strategi = st.multiselect("Strategi Pelaksanaan", options=opsi_strategi, default=opsi_strategi)
    with col_f3:
        filter_valid = st.selectbox("Validitas", opsi_valid)

    # Logika Memfilter Data
    df_filtered = df.copy()

    if filter_bulan:
        df_filtered = df_filtered[df_filtered['Laporan Bulan'].isin(filter_bulan)]
    else:
        df_filtered = pd.DataFrame(columns=df.columns) 

    if filter_strategi:
        df_filtered = df_filtered[df_filtered['Strategi Pelaksanaan'].isin(filter_strategi)]
    else:
        df_filtered = pd.DataFrame(columns=df.columns)

    if filter_valid != "Semua Status":
        df_filtered = df_filtered[df_filtered['% Valid'] == filter_valid]

    # -- [BARU] KONVERSI ANGKA DAN PENGGABUNGAN KATEGORI SECARA GLOBAL --
    kolom_mentah = ['INS1', 'INS2', 'INS3', 'INS4', 'INS5', 'INS6', 'INS7', 'INS8',
                    'MAT1', 'MAT2', 'MAT3', 'MAT4', 'MAT5', 'MAT6',
                    'RATA DS', 'RATA SP', 'RATA-RATA KESELURUHAN']
    
    for col in kolom_mentah:
        if col in df_filtered.columns:
            df_filtered[col] = pd.to_numeric(df_filtered[col], errors='coerce')

    # Membentuk Kategori Gabungan langsung di df_filtered
    if not df_filtered.empty and 'INS1' in df_filtered.columns:
        df_filtered['Engagement Instruktur'] = df_filtered[['INS1', 'INS2']].mean(axis=1)
        df_filtered['Relevance Instruktur'] = df_filtered[['INS3', 'INS4']].mean(axis=1)
        df_filtered['Satisfaction Instruktur'] = df_filtered[['INS5', 'INS6', 'INS7', 'INS8']].mean(axis=1)
        df_filtered['Engagement Materi'] = df_filtered[['MAT1', 'MAT2']].mean(axis=1)
        df_filtered['Relevance Materi'] = df_filtered[['MAT3', 'MAT4']].mean(axis=1)
        df_filtered['Satisfaction Materi'] = df_filtered[['MAT5', 'MAT6']].mean(axis=1)
        df_filtered['Satisfaction Sarana Digital'] = df_filtered['RATA DS']
        df_filtered['Satisfaction Sarana In Class'] = df_filtered['RATA SP']

    # Update kolom yang tersedia setelah penambahan kategori
    kolom_tersedia = df_filtered.columns.tolist()

    st.success(f"Terdapat **{len(df_filtered)}** baris data yang sesuai dengan filter di atas.")
    st.markdown("---")

    # ==========================================
    # INISIALISASI TABS
    # ==========================================
    tab_statistik, tab_dashboard, tab_ai = st.tabs(["ANALYTICS", "DASHBOARD", "🤖 AI ASSISTANT"])

    # ==========================================
    # ISI TAB 1: ANALISA STATISTIK
    # ==========================================
    with tab_statistik:
        if not df_filtered.empty:
            st.subheader("📋 Raw Data")
            st.dataframe(df_filtered, use_container_width=True)

            st.markdown("### 🔍 Analisis Korelasi")
            col1, col2 = st.columns(2)
            with col1:
                var_x = st.selectbox("Pilih Variabel Independen (X):", kolom_tersedia, index=0)
            with col2:
                var_y = st.selectbox("Pilih Variabel Dependen (Y):", kolom_tersedia, index=min(1, len(kolom_tersedia)-1))

            st.markdown("---")

            if pd.api.types.is_numeric_dtype(df_filtered[var_x]) and pd.api.types.is_numeric_dtype(df_filtered[var_y]):
                st.markdown("### 🛠️ Pra-Pemrosesan & Uji Asumsi")
                hapus_outlier = st.checkbox("🧹 Buang Data Pencilan (Outlier) menggunakan metode IQR")
                uji_normalitas = st.checkbox("⚖️ Uji Distribusi Normal (Shapiro-Wilk Test)")
                
                df_clean = df_filtered.copy()

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
                    st.info(f"Tersisa **{len(df_clean)}** baris data setelah Outlier dihapus.")

                if uji_normalitas and len(df_clean) >= 3:
                    stat_x, p_value_x = stats.shapiro(df_clean[var_x].dropna())
                    stat_y, p_value_y = stats.shapiro(df_clean[var_y].dropna())
                    
                    col_n1, col_n2 = st.columns(2)
                    with col_n1:
                        if p_value_x > 0.05: st.success(f"✅ {var_x}: Normal (p = {p_value_x:.3f})")
                        else: st.error(f"❌ {var_x}: Tidak Normal (p = {p_value_x:.3f})")
                    with col_n2:
                        if p_value_y > 0.05: st.success(f"✅ {var_y}: Normal (p = {p_value_y:.3f})")
                        else: st.error(f"❌ {var_y}: Tidak Normal (p = {p_value_y:.3f})")
                
                if len(df_clean) > 1:
                    st.markdown("---")
                    korelasi = df_clean[var_x].corr(df_clean[var_y])
                    
                    col3, col4 = st.columns([1, 2])
                    with col3:
                        st.metric(label="Koefisien Korelasi (r)", value=round(korelasi, 3))
                    with col4:
                        st.write(f"**Sebaran Titik Data (Clean): {var_x} vs {var_y}**")
                        st.scatter_chart(data=df_clean, x=var_x, y=var_y)
                else:
                    st.warning("Data tidak cukup untuk menghitung korelasi setelah difilter/outlier dihapus.")
            else:
                st.error("⚠️ Analisis terhenti: Kolom yang dipilih bukan format angka.")

            # ==========================================
            # FITUR IPA (Importance-Performance Analysis)
            # ==========================================
            st.markdown("---")
            st.markdown("### 🎯 Analisis Kuadran Strategi (Importance-Performance Analysis)")
            st.write("Grafik ini memetakan 8 indikator utama berdasarkan **Kinerja** (Skor Rata-rata) dan **Kepentingan** (Korelasi dengan Skor Akhir). Fokuskan perbaikan pada indikator yang jatuh di **Kuadran 1 (Kiri Atas)**.")

            try:
                df_ipa = df_filtered.dropna(subset=['RATA-RATA KESELURUHAN']).copy()

                if len(df_ipa) > 2:
                    kategori_list = [
                        'Engagement Instruktur', 'Relevance Instruktur', 'Satisfaction Instruktur',
                        'Engagement Materi', 'Relevance Materi', 'Satisfaction Materi',
                        'Satisfaction Sarana Digital', 'Satisfaction Sarana In Class'
                    ]

                    kinerja, kepentingan = [], []
                    for kat in kategori_list:
                        if kat in df_ipa.columns:
                            kinerja.append(df_ipa[kat].mean())
                            kepentingan.append(df_ipa[kat].corr(df_ipa['RATA-RATA KESELURUHAN']))
                        else:
                            kinerja.append(None)
                            kepentingan.append(None)

                    df_plot_ipa = pd.DataFrame({'Kategori': kategori_list, 'Kinerja': kinerja, 'Kepentingan': kepentingan}).dropna()

                    if not df_plot_ipa.empty:
                        x_cross = df_plot_ipa['Kinerja'].mean()
                        y_cross = df_plot_ipa['Kepentingan'].mean()

                        fig_ipa = px.scatter(df_plot_ipa, x='Kinerja', y='Kepentingan', text='Kategori', size_max=60)
                        fig_ipa.update_traces(textposition='top center', marker=dict(size=14, color='#005b9f', line=dict(width=2, color='DarkSlateGrey')))
                        fig_ipa.add_hline(y=y_cross, line_dash="dash", line_color="#FFC000")
                        fig_ipa.add_vline(x=x_cross, line_dash="dash", line_color="#FFC000")

                        fig_ipa.add_annotation(xref="paper", yref="paper", x=0.01, y=0.99, text="<b>KUADRAN 1</b><br>🚨 Prioritas Utama", showarrow=False, font=dict(color="#d32f2f", size=14), align="left")
                        fig_ipa.add_annotation(xref="paper", yref="paper", x=0.99, y=0.99, text="<b>KUADRAN 2</b><br>🌟 Pertahankan", showarrow=False, font=dict(color="#2e7d32", size=14), align="right")
                        fig_ipa.add_annotation(xref="paper", yref="paper", x=0.01, y=0.01, text="<b>KUADRAN 3</b><br>📉 Prioritas Rendah", showarrow=False, font=dict(color="#757575", size=14), align="left")
                        fig_ipa.add_annotation(xref="paper", yref="paper", x=0.99, y=0.01, text="<b>KUADRAN 4</b><br>⚠️ Berlebihan", showarrow=False, font=dict(color="#f57c00", size=14), align="right")

                        fig_ipa.update_layout(xaxis_title="Kinerja (Sumbu X) →", yaxis_title="Kepentingan / Korelasi (Sumbu Y) ↑", height=600, margin=dict(t=40, b=40, l=40, r=40))

                        st.plotly_chart(fig_ipa, use_container_width=True)
                        
                        q1_items = df_plot_ipa[(df_plot_ipa['Kinerja'] < x_cross) & (df_plot_ipa['Kepentingan'] > y_cross)]['Kategori'].tolist()
                        
                        if q1_items:
                            st.error(f"**Rekomendasi Manajemen:** Indikator **{', '.join(q1_items)}** jatuh di Kuadran 1. Ini sangat penting bagi peserta namun kinerjanya masih di bawah rata-rata. Fokuskan perbaikan bulan ini di area tersebut!")
                        else:
                            st.success("**Rekomendasi Manajemen:** Saat ini tidak ada indikator yang jatuh di Kuadran 1 (Prioritas Utama). Pertahankan kinerja yang sudah ada!")
                    else:
                        st.warning("Data tidak cukup untuk menampilkan grafik IPA.")
                else:
                    st.warning("Data tidak cukup untuk analisis IPA (butuh minimal 3 baris data yang valid).")

            except Exception as e:
                st.error(f"⚠️ Gagal memproses data IPA. Pastikan ejaan nama kolom (INS1, dll) sesuai. Detail Error: {e}")

            # ==========================================
            # FITUR BARU: ANALISIS KOMPARATIF (ANOVA / T-TEST)
            # ==========================================
            st.markdown("---")
            st.markdown("### ⚖️ Analisis Komparatif (Uji Signifikansi)")
            st.write("Gunakan fitur ini untuk menguji apakah perbedaan skor antar metode/bulan benar-benar berbeda secara statistik (nyata), atau sekadar kebetulan.")

            opsi_grup = ['Strategi Pelaksanaan', 'Laporan Bulan']
            
            # [UPDATE] Daftar opsi Skor Y yang disesuaikan secara khusus sesuai permintaan
            opsi_skor_tersedia = [
                'RATA-RATA KESELURUHAN',
                'Engagement Instruktur', 'INS1', 'INS2',
                'Relevance Instruktur', 'INS3', 'INS4',
                'Satisfaction Instruktur', 'INS5', 'INS6', 'INS7', 'INS8',
                'Engagement Materi', 'MAT1', 'MAT2',
                'Relevance Materi', 'MAT3', 'MAT4',
                'Satisfaction Materi', 'MAT5', 'MAT6',
                'Satisfaction Sarana Digital', 'RATA DS',
                'Satisfaction Sarana In Class', 'RATA SP'
            ]
            
            # Memastikan hanya kolom yang benar-benar ada di dataframe yang dimunculkan di dropdown
            opsi_skor_final = [col for col in opsi_skor_tersedia if col in df_filtered.columns]

            col_c1, col_c2 = st.columns(2)
            with col_c1:
                var_grup = st.selectbox("Pilih Kategori Pembanding (Sumbu X):", opsi_grup)
            with col_c2:
                var_skor = st.selectbox("Pilih Skor yang Dinilai (Sumbu Y):", opsi_skor_final)

            df_comp = df_filtered.dropna(subset=[var_grup, var_skor])

            if len(df_comp) > 0:
                grup_unik = df_comp[var_grup].unique()
                data_grup = [df_comp[df_comp[var_grup] == grup][var_skor] for grup in grup_unik]

                fig_box = px.box(
                    df_comp, 
                    x=var_grup, 
                    y=var_skor, 
                    color=var_grup,
                    points="all", 
                    title=f"Distribusi {var_skor} berdasarkan {var_grup}"
                )
                fig_box.update_layout(height=400, showlegend=False, xaxis_title="", yaxis_title="Skor")

                if len(grup_unik) < 2:
                    st.warning("⚠️ Tidak bisa melakukan uji komparasi statistik. Filter data Anda saat ini hanya menyisakan 1 kelompok.")
                    st.plotly_chart(fig_box, use_container_width=True)
                elif len(grup_unik) == 2:
                    stat_val, p_value = stats.ttest_ind(data_grup[0], data_grup[1], nan_policy='omit')
                    jenis_uji = "Independent T-Test"
                else:
                    stat_val, p_value = stats.f_oneway(*data_grup)
                    jenis_uji = "One-Way ANOVA"

                if len(grup_unik) >= 2:
                    st.plotly_chart(fig_box, use_container_width=True)
                    st.write(f"**Hasil Uji Statistik ({jenis_uji}):** P-Value = {p_value:.4f}")
                    
                    if p_value < 0.05:
                        st.success(f"**Kesimpulan:** Terdapat **PERBEDAAN SIGNIFIKAN** pada {var_skor} antar kelompok di {var_grup}. Perbedaan rata-rata yang terlihat pada grafik bukanlah sebuah kebetulan.")
                    else:
                        st.info(f"**Kesimpulan:** **TIDAK ADA PERBEDAAN SIGNIFIKAN** pada {var_skor} antar kelompok di {var_grup}. Secara statistik, performa antar kelompok tersebut dianggap sama (perbedaan angka rata-rata diakibatkan oleh sebaran data yang wajar).")
            else:
                st.warning("Data tidak cukup untuk melakukan komparasi.")

        else:
            st.warning("⚠️ Tidak ada data untuk dianalisis. Silakan sesuaikan filter Anda.")


    # ==========================================
    # ISI TAB 2: DASHBOARD
    # ==========================================
    with tab_dashboard:
        st.subheader("📊 Dashboard Utama")
        
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
            col_chart, col_spacer = st.columns([2, 1])

            with col_chart:
                df_grafik = df_filtered.groupby('Strategi Pelaksanaan')['RATA-RATA KESELURUHAN'].mean().reset_index()

                fig = px.bar(
                    df_grafik, 
                    x='Strategi Pelaksanaan', 
                    y='RATA-RATA KESELURUHAN',
                    text='RATA-RATA KESELURUHAN', 
                    color_discrete_sequence=['#005b9f'] 
                )

                fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
                fig.add_hline(y=4.5, line_dash="dash", line_color="#FFC000", 
                              annotation_text="Standar TMP (4.5)", annotation_position="top left")

                fig.update_layout(
                    height=350,       
                    bargap=0.5,       
                    yaxis_range=[0, 5],
                    yaxis_title="Rata-rata Skor",
                    xaxis_title="",
                    margin=dict(t=40, b=0, l=0, r=0) 
                )

                st.plotly_chart(fig, use_container_width=True)

            st.markdown("---")
            st.write(f"**Menampilkan detail dari {len(df_filtered)} baris data:**")
            st.dataframe(df_filtered, use_container_width=True)

        else:
            st.warning("⚠️ Tidak ada data yang ditampilkan. Silakan sesuaikan filter Anda.")


    # ==========================================
    # ISI TAB 3: ASISTEN AI 
    # ==========================================
    with tab_ai:
        st.subheader("🤖 Tanya Asisten EVALYTICS")
        st.write("Gunakan AI untuk menganalisis tren atau meminta saran perbaikan program berdasarkan data yang sedang difilter.")
        
        user_question = st.chat_input("Tanya sesuatu tentang data evaluasi Anda...")
        
        if user_question:
            with st.chat_message("user"):
                st.write(user_question)
            
            with st.chat_message("assistant"):
                with st.spinner("Gemini sedang berpikir..."):
                    context = f"Data evaluasi UPDL Jakarta. Total Data: {len(df_filtered)} baris. Ringkasan data saat ini: {df_filtered.describe().to_string()}"
                    full_prompt = f"Konteks Data:\n{context}\n\nPertanyaan: {user_question}\n\nJawablah dengan ringkas, profesional, dan dalam Bahasa Indonesia."
                    
                    try:
                        response = model.generate_content(full_prompt)
                        st.markdown(response.text)
                    except Exception as ai_err:
                        st.error(f"Gagal mendapatkan respon AI: Pastikan API Key di st.secrets sudah benar. Error: {ai_err}")

# ==========================================
# PENUTUP TRY-EXCEPT
# ==========================================
except Exception as e:
    st.error("Gagal memuat atau memproses data dari Google Sheets.")
    st.error(f"Detail Error Teknis: {e}")
