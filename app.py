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
# 1. KONFIGURASI HALAMAN
# ==========================================
st.set_page_config(page_title="Overview Evaluasi UPDL", layout="wide")

# Custom CSS untuk membuat kotak skor (Scorecards) berwarna seperti di gambar
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
# 2. HEADER & FILTER
# ==========================================
col_logo, col_title = st.columns([1, 8])
with col_title:
    st.markdown("<h2 style='text-align: center; color: #0B5394;'>OVERVIEW EVALUASI LEVEL 1 & 2 UPDL JAKARTA TAHUN 2026</h2>", unsafe_allow_html=True)
st.markdown("---")

# Filter Dropdown
col_f1, col_f2, col_f3, _ = st.columns([2, 2, 2, 4])
with col_f1:
    st.selectbox("Laporan Bulan", ["Semua Bulan", "Januari", "Februari", "Maret", "April", "Mei"])
with col_f2:
    st.selectbox("Strategi Pelaksanaan", ["Semua Strategi", "Tatap Muka", "Online"])
with col_f3:
    st.selectbox("Validitas", ["Semua", "Valid", "Tidak Valid"])

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 3. TATA LETAK UTAMA (GRID 3 KOLOM)
# ==========================================
# Membagi layar menjadi Kiri (Skor & Garis), Tengah (Gauge & Scatter), Kanan (Bar & Line)
col_left, col_mid, col_right = st.columns([1.2, 1, 1.2], gap="large")

# ------------------------------------------
# KOLOM KIRI
# ------------------------------------------
with col_left:
    # Baris Scorecard
    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        st.markdown("<div class='metric-title' style='color:black; text-align:center;'>SKOR EVALUASI L1</div>", unsafe_allow_html=True)
        st.markdown("<div class='metric-box box-blue'><p class='metric-value'>4.22</p><p class='metric-delta'>⬇ -6.2%</p></div>", unsafe_allow_html=True)
    with sc2:
        st.markdown("<div class='metric-title' style='color:black; text-align:center;'>INDIKATOR > 4.5</div>", unsafe_allow_html=True)
        st.markdown("<div class='metric-box box-green'><p class='metric-value'>721</p><p class='metric-delta'><br></p></div>", unsafe_allow_html=True)
    with sc3:
        st.markdown("<div class='metric-title' style='color:black; text-align:center;'>INDIKATOR < 4.5</div>", unsafe_allow_html=True)
        st.markdown("<div class='metric-box box-red'><p class='metric-value'>2,238</p><p class='metric-delta'><br></p></div>", unsafe_allow_html=True)
    
    # Grafik Garis (Line Chart L1)
    st.markdown("<h5 style='text-align: center;'>Grafik Skor Evaluasi L1</h5>", unsafe_allow_html=True)
    # Dummy Data
    df_line = pd.DataFrame({
        "Bulan": ["Januari", "Februari", "Maret", "April", "Mei"],
        "Instruktur": [4.1, 4.3, 4.25, 4.15, 4.0],
        "Materi": [4.2, 4.25, 4.2, 4.1, 4.02]
    })
    fig_line = px.line(df_line, x="Bulan", y=["Instruktur", "Materi"], markers=True)
    # Menambahkan Garis Standar
    fig_line.add_hline(y=4.5, line_dash="dash", line_color="orange", annotation_text="Standar TMP (4.5)", annotation_position="top left")
    fig_line.update_layout(height=400, showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig_line, use_container_width=True)

# ------------------------------------------
# KOLOM TENGAH
# ------------------------------------------
with col_mid:
    # Gauge Chart
    st.markdown("<h6 style='text-align: center;'>% Pembelajaran Sesuai TMP</h6>", unsafe_allow_html=True)
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = 24.4,
        number = {'suffix': "%"},
        gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': "#0B5394"}}
    ))
    fig_gauge.update_layout(height=250, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_gauge, use_container_width=True)

    # Simple KPIs
    st.metric(label="Rata-Rata Pengisian L1", value="71.3%")
    st.metric(label="Rata-Rata Pengisian L2", value="70.7%")
    st.metric(label="Jumlah Temuan L1", value="37")

    # Scatter Plot
    st.markdown("<h6 style='text-align: center;'>Matriks Pengisian Evaluasi</h6>", unsafe_allow_html=True)
    df_scatter = pd.DataFrame({"Pengisian": [25, 50, 75, 80, 90, 100], "Skor": [1.8, 4.2, 4.1, 4.3, 4.0, 4.5]})
    fig_scatter = px.scatter(df_scatter, x="Pengisian", y="Skor")
    fig_scatter.add_hline(y=4.5, line_dash="dash", line_color="orange")
    fig_scatter.add_vline(x=80, line_dash="dash", line_color="red")
    fig_scatter.update_layout(height=250, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_scatter, use_container_width=True)

# ------------------------------------------
# KOLOM KANAN
# ------------------------------------------
with col_right:
    # Bar Chart (Atas)
    st.markdown("<h6 style='text-align: center;'>Skor Evaluasi L1</h6>", unsafe_allow_html=True)
    df_bar1 = pd.DataFrame({"Kategori": ["HL", "IC", "SL", "DL"], "Skor": [4.53, 4.30, 4.26, 4.18]})
    fig_bar1 = px.bar(df_bar1, x="Kategori", y="Skor", text="Skor")
    fig_bar1.add_hline(y=4.5, line_dash="dash", line_color="orange")
    fig_bar1.update_traces(marker_color='#0B5394')
    fig_bar1.update_layout(height=250, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_bar1, use_container_width=True)

    # Line Chart L1 & L2
    st.markdown("<h6 style='text-align: center;'>Persentase Pengisian L1 & L2</h6>", unsafe_allow_html=True)
    df_line2 = pd.DataFrame({"Bulan": ["Feb", "Mar", "Apr"], "L1": [74, 73, 64], "L2": [65, 77, 59]})
    fig_line2 = px.line(df_line2, x="Bulan", y=["L1", "L2"], markers=True)
    fig_line2.update_layout(height=200, margin=dict(l=10, r=10, t=10, b=10), showlegend=False)
    st.plotly_chart(fig_line2, use_container_width=True)

    # Bar Chart Progress
    st.markdown("<h6 style='text-align: center;'>Progress Tindak Lanjut Temuan</h6>", unsafe_allow_html=True)
    df_bar2 = pd.DataFrame({"Status": ["SUDAH", "NOT STARTED", "IN PROGRESS"], "Jumlah": [16, 14, 7]})
    fig_bar2 = px.bar(df_bar2, x="Status", y="Jumlah", text="Jumlah", color="Status", 
                      color_discrete_sequence=["#0B5394", "#4A235A", "#F1C40F"])
    fig_bar2.update_layout(height=200, margin=dict(l=10, r=10, t=10, b=10), showlegend=False)
    st.plotly_chart(fig_bar2, use_container_width=True)
