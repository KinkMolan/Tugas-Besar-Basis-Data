# main.py - DASHBOARD IKLIM INDONESIA BAHASA INDONESIA
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import folium_static
from datetime import datetime, timedelta
import numpy as np

# Import fungsi dari config BAHASA INDONESIA
from config import (
    KonektorDatabase,
    ambil_data_cuaca,
    ambil_data_stasiun,
    ambil_daftar_wilayah,
    ambil_arah_angin,
    ambil_statistik_database,
    ambil_data_contoh,
    ambil_tahun_tersedia,
    ambil_statistik_cuaca_stasiun,
    ambil_nama_kolom
)

# Konfigurasi halaman
st.set_page_config(
    page_title="Dashboard Iklim Indonesia",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Custom untuk styling
st.markdown("""
<style>
    .climate-legend {
        position: absolute;
        bottom: 20px;
        left: 20px;
        z-index: 1000;
        background: white;
        padding: 10px;
        border-radius: 5px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.3);
        font-size: 12px;
    }
    .color-box {
        width: 15px;
        height: 15px;
        display: inline-block;
        margin-right: 5px;
        border: 1px solid #ccc;
    }
    .main-title {
        text-align: center;
        color: #1E90FF;
        font-size: 2.5rem;
        margin-bottom: 1rem;
    }
    .subtitle {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card-blue {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card-green {
        background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card-orange {
        background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 1rem;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Header Dashboard
st.markdown('<h1 class="main-title">🌤️ DASHBOARD IKLIM INDONESIA</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Visualisasi Data Cuaca Stasiun BMKG Seluruh Indonesia</p>', unsafe_allow_html=True)

# Sidebar untuk filter
with st.sidebar:

    # Pilih tab utama
    tab_selection = st.radio(
        "Pilih Visualisasi:",
        ["🏠 Dashboard Utama", "🗺️ Peta Stasiun", "📈 Analisis Suhu", 
         "🌧️ Analisis Hujan", "🌀 Analisis Angin", "📋 Data Mentah", "🔍 Info Database"]
    )
    
    st.markdown("---")
    st.markdown("**Rentang Waktu**")
    
    # Method 1: Gunakan value manual dengan tanggal jauh ke depan
    col1, col2 = st.columns(2)
    with col1:
        tanggal_mulai = st.date_input(
            "Dari",
            value=datetime(2010, 1, 1).date(),
            min_value=datetime(2000, 1, 1).date(),
            max_value=datetime(2035, 12, 31).date()
        )
    with col2:
        tanggal_selesai = st.date_input(
            "Sampai",
            value=datetime(2024, 12, 31).date(),
            min_value=datetime(2000, 1, 1).date(),
            max_value=datetime(2035, 12, 31).date()
        )
    
    # Method 2: Slider untuk tahun
    st.markdown("**Filter berdasarkan tahun:**")
    tahun_min, tahun_maks = st.slider(
        "Pilih rentang tahun:",
        min_value=2010,
        max_value=2035,
        value=(2010, 2024),
        step=1
    )
    
    # Konversi ke tanggal
    tanggal_mulai = datetime(tahun_min, 1, 1)
    tanggal_selesai = datetime(tahun_maks, 12, 31)
    
    # Wilayah filter
    try:
        daftar_wilayah = ambil_daftar_wilayah()
        if isinstance(daftar_wilayah, list) and len(daftar_wilayah) > 0:
            nama_wilayah_list = [w.get('nama_wilayah', '') for w in daftar_wilayah if 'nama_wilayah' in w]
            wilayah_terpilih = st.selectbox(
                "Pilih Wilayah:",
                ["Semua Wilayah"] + [w for w in nama_wilayah_list if w]
            )
        else:
            wilayah_terpilih = "Semua Wilayah"
    except Exception as e:
        st.error(f"Error mengambil wilayah: {str(e)[:100]}")
        wilayah_terpilih = "Semua Wilayah"
    
    # Data limit untuk performa
    batas_data = st.slider(
        "Limit Data:",
        min_value=1000,
        max_value=50000,
        value=10000,
        step=1000,
        help="Batasi jumlah data untuk meningkatkan performa"
    )
    
    st.markdown("---")
    
    # Test connection button
    if st.button("🔗 Test Koneksi Database"):
        try:
            db = KonektorDatabase()
            if db.uji_koneksi():
                st.success("✅ Koneksi database berhasil!")
            else:
                st.error("❌ Koneksi database gagal")
        except Exception as e:
            st.error(f"❌ Error: {str(e)[:100]}")

# Cache data untuk performa
# Cache data untuk performa
@st.cache_data(ttl=300)
def muat_data_cuaca(tanggal_mulai, tanggal_selesai, nama_wilayah, batas):
    """Load data dengan error handling"""
    try:
        # Format date untuk query (UBAH DI SINI)
        tanggal_mulai_str = tanggal_mulai.strftime('%Y-%m-%d')
        tanggal_selesai_str = tanggal_selesai.strftime('%Y-%m-%d')
        
        # Get wilayah_id jika wilayah dipilih
        id_wilayah = None
        if nama_wilayah != "Semua Wilayah" and daftar_wilayah and isinstance(daftar_wilayah, list):
            for w in daftar_wilayah:
                if isinstance(w, dict) and w.get('nama_wilayah') == nama_wilayah:
                    id_wilayah = w.get('id_wilayah')
                    break
        
        # Gunakan fungsi yang sudah diperbaiki (UBAH DI SINI)
        # PARAMETER BERUBAH: filter_tanggal -> tanggal_mulai dan tanggal_selesai
        df = ambil_data_cuaca(
            tanggal_mulai=tanggal_mulai_str,
            tanggal_selesai=tanggal_selesai_str,
            id_wilayah=id_wilayah,
            batas=batas
        )
        
        if isinstance(df, pd.DataFrame) and not df.empty:
            # Konversi tipe data
            if 'tanggal' in df.columns:
                df['tanggal'] = pd.to_datetime(df['tanggal'], errors='coerce')
            
            # HAPUS filter manual ini karena sudah ditangani di database:
            # df = df[df['tanggal'] <= pd.to_datetime(tanggal_selesai)]
            
            # Rename kolom untuk tampilan
            nama_kolom = ambil_nama_kolom()
            df = df.rename(columns=nama_kolom)
            
            return df
        else:
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)[:200]}")
        return pd.DataFrame()
            
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)[:200]}")
        return pd.DataFrame()

# Main content berdasarkan tab selection
if tab_selection == "🏠 Dashboard Utama":
    st.markdown("## 📊 Gambaran Umum Data Iklim")
    
    # Load data
    df = muat_data_cuaca(tanggal_mulai, tanggal_selesai, wilayah_terpilih, batas_data)
    
    if df.empty:
        st.markdown('<div class="warning-box"><b>⚠️ Tidak ada data yang ditemukan</b><br>Coba periksa filter tanggal atau koneksi database</div>', unsafe_allow_html=True)
    else:
        # Tampilkan info data
        st.success(f"✅ Data berhasil diambil: {len(df):,} baris")
        
        # Metrics Cards dengan Bahasa Indonesia
        st.markdown("### 📈 Metrik Utama")
        col1, col2, col3, col4 = st.columns(4)
        
        # Helper functions
        def aman_rata_rata(kolom):
            return df[kolom].mean() if kolom in df.columns and not df[kolom].isna().all() else 0
        
        def aman_jumlah(kolom):
            return df[kolom].sum() if kolom in df.columns and not df[kolom].isna().all() else 0
        
        with col1:
            suhu_rata = aman_rata_rata('Suhu Rata-rata')
            st.markdown(f"""
            <div class="metric-card">
                <h3>🌡️ Suhu Rata-rata</h3>
                <h1>{suhu_rata:.1f}°C</h1>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            total_hujan = aman_jumlah('Curah Hujan')
            st.markdown(f"""
            <div class="metric-card-blue">
                <h3>🌧️ Total Hujan</h3>
                <h1>{total_hujan:,.0f} mm</h1>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            kelembaban_rata = aman_rata_rata('Kelembaban Rata-rata')
            st.markdown(f"""
            <div class="metric-card-green">
                <h3>💧 Kelembaban</h3>
                <h1>{kelembaban_rata:.1f}%</h1>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            angin_rata = aman_rata_rata('Kecepatan Angin Rata-rata')
            st.markdown(f"""
            <div class="metric-card-orange">
                <h3>🌀 Angin Rata-rata</h3>
                <h1>{angin_rata:.1f} m/s</h1>
            </div>
            """, unsafe_allow_html=True)
        
        # Visualizations
        st.markdown("### 📊 Visualisasi Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if 'Suhu Rata-rata' in df.columns:
                data_suhu = df['Suhu Rata-rata'].dropna()
                if len(data_suhu) > 0:
                    fig_suhu = px.histogram(
                        data_suhu,
                        nbins=30,
                        title='Distribusi Suhu Rata-rata',
                        labels={'value': 'Suhu (°C)', 'count': 'Jumlah Observasi'},
                        color_discrete_sequence=['#FF6B6B']
                    )
                    fig_suhu.update_layout(
                        xaxis_title="Suhu (°C)",
                        yaxis_title="Jumlah Observasi"
                    )
                    st.plotly_chart(fig_suhu, use_container_width=True)
        
        with col2:
            if 'Curah Hujan' in df.columns:
                data_hujan = df['Curah Hujan'].dropna()
                if len(data_hujan) > 0:
                    fig_hujan = px.histogram(
                        data_hujan,
                        nbins=30,
                        title='Distribusi Curah Hujan',
                        labels={'value': 'Hujan (mm)', 'count': 'Jumlah Observasi'},
                        color_discrete_sequence=['#1E90FF']
                    )
                    fig_hujan.update_layout(
                        xaxis_title="Curah Hujan (mm)",
                        yaxis_title="Jumlah Observasi"
                    )
                    st.plotly_chart(fig_hujan, use_container_width=True)
        
        # Tabel data ringkasan
        st.markdown("### 📋 Ringkasan Data")
        if 'Tanggal' in df.columns:
            df['Bulan'] = df['Tanggal'].dt.month
            ringkasan_bulanan = df.groupby('Bulan').agg({
                'Suhu Rata-rata': 'mean',
                'Curah Hujan': 'sum',
                'Kelembaban Rata-rata': 'mean'
            }).reset_index()
            
            nama_bulan = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
                         'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
            ringkasan_bulanan['Nama Bulan'] = ringkasan_bulanan['Bulan'].apply(lambda x: nama_bulan[x-1] if 1 <= x <= 12 else 'Unknown')
            
            st.dataframe(ringkasan_bulanan[['Nama Bulan', 'Suhu Rata-rata', 'Curah Hujan', 'Kelembaban Rata-rata']].round(2), 
                        use_container_width=True)

elif tab_selection == "🗺️ Peta Stasiun":
    st.markdown("## 🗺️ Peta Interaktif Stasiun BMKG")
    
    # Pilihan jenis visualisasi
    jenis_visualisasi = st.selectbox(
        "Pilih Jenis Visualisasi Peta:",
        ["📍 Lokasi Saja", "🌡️ Berdasarkan Suhu", "🌧️ Berdasarkan Hujan", 
         "🔥 Heatmap Suhu", "💧 Heatmap Hujan", "🌈 Kombinasi Iklim"]
    )
    
    # Load data stasiun
    df_stasiun = ambil_data_stasiun()
    
    if df_stasiun.empty:
        st.error("❌ Tidak ada data stasiun yang ditemukan.")
    else:
        # Rename kolom untuk konsistensi
        df_stasiun = df_stasiun.rename(columns={
            'nama_stasiun': 'Nama Stasiun',
            'lintang': 'Lintang',
            'bujur': 'Bujur',
            'nama_wilayah': 'Wilayah',
            'nama_provinsi': 'Provinsi'
        })
        
        # Load weather data untuk analisis
        df_cuaca = muat_data_cuaca(tanggal_mulai, tanggal_selesai, wilayah_terpilih, 5000)
        
        # Gabungkan data stasiun dengan data cuaca terbaru
        if not df_cuaca.empty and 'ID Stasiun' in df_cuaca.columns:
            # Ambil data terbaru untuk setiap stasiun
            cuaca_terbaru = df_cuaca.sort_values('Tanggal', ascending=False).drop_duplicates('ID Stasiun')
            df_stasiun = df_stasiun.merge(
                cuaca_terbaru[['ID Stasiun', 'Suhu Rata-rata', 'Curah Hujan', 
                              'Kelembaban Rata-rata', 'Kecepatan Angin Rata-rata']],
                left_on='id_stasiun',
                right_on='ID Stasiun',
                how='left'
            )
        
        # Filter by wilayah jika dipilih
        if wilayah_terpilih != "Semua Wilayah" and 'Wilayah' in df_stasiun.columns:
            df_stasiun = df_stasiun[df_stasiun['Wilayah'] == wilayah_terpilih]
        
        # Display metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Stasiun", len(df_stasiun))
        with col2:
            if 'Suhu Rata-rata' in df_stasiun.columns:
                suhu_rata = df_stasiun['Suhu Rata-rata'].mean()
                st.metric("Suhu Rata-rata", f"{suhu_rata:.1f}°C")
        with col3:
            if 'Curah Hujan' in df_stasiun.columns:
                total_hujan = df_stasiun['Curah Hujan'].sum()
                st.metric("Total Hujan", f"{total_hujan:,.0f} mm")
        
        # ====== VISUALISASI PETA ======
        
        # 1. PETA BERDASARKAN SUHU
        if jenis_visualisasi == "🌡️ Berdasarkan Suhu":
            st.markdown("### 🌡️ Peta Berdasarkan Suhu Rata-rata")
            
            if 'Suhu Rata-rata' in df_stasiun.columns:
                # Buat peta
                lintang_tengah = df_stasiun['Lintang'].mean()
                bujur_tengah = df_stasiun['Bujur'].mean()
                
                peta = folium.Map(
                    location=[lintang_tengah, bujur_tengah],
                    zoom_start=5,
                    tiles='CartoDB positron'
                )
                
                # Legend untuk suhu
                legend_html = '''
                <div style="position: fixed; 
                            bottom: 50px; left: 50px; width: 220px; height: 160px; 
                            background-color: white; border:2px solid grey; z-index:9999; 
                            font-size:14px; padding: 10px; border-radius: 5px;">
                    <b>🌡️ Legenda Suhu</b><br>
                    <i style="background: blue; width: 20px; height: 20px; display: inline-block; margin-right: 5px;"></i> < 20°C (Dingin)<br>
                    <i style="background: green; width: 20px; height: 20px; display: inline-block; margin-right: 5px;"></i> 20-25°C (Sejuk)<br>
                    <i style="background: yellow; width: 20px; height: 20px; display: inline-block; margin-right: 5px;"></i> 25-30°C (Hangat)<br>
                    <i style="background: orange; width: 20px; height: 20px; display: inline-block; margin-right: 5px;"></i> 30-35°C (Panas)<br>
                    <i style="background: red; width: 20px; height: 20px; display: inline-block; margin-right: 5px;"></i> > 35°C (Sangat Panas)
                </div>
                '''
                
                peta.get_root().html.add_child(folium.Element(legend_html))
                
                # Tambahkan marker untuk setiap stasiun
                for idx, baris in df_stasiun.iterrows():
                    if pd.notna(baris['Lintang']) and pd.notna(baris['Bujur']):
                        suhu = baris['Suhu Rata-rata'] if pd.notna(baris['Suhu Rata-rata']) else 25
                        
                        # Tentukan warna berdasarkan suhu
                        if suhu < 20:
                            warna = 'blue'
                            deskripsi_suhu = "Dingin"
                        elif suhu < 25:
                            warna = 'green'
                            deskripsi_suhu = "Sejuk"
                        elif suhu < 30:
                            warna = 'yellow'
                            deskripsi_suhu = "Hangat"
                        elif suhu < 35:
                            warna = 'orange'
                            deskripsi_suhu = "Panas"
                        else:
                            warna = 'red'
                            deskripsi_suhu = "Sangat Panas"
                        
                        # Popup info
                        popup_html = f"""
                        <div style="width: 250px;">
                            <h4>{baris['Nama Stasiun']}</h4>
                            <hr>
                            <p><b>Status Suhu:</b> <span style="color:{warna}; font-weight:bold;">{deskripsi_suhu}</span></p>
                            <p><b>Suhu Rata-rata:</b> {suhu:.1f}°C</p>
                            <p><b>Wilayah:</b> {baris.get('Wilayah', 'N/A')}</p>
                            <p><b>Provinsi:</b> {baris.get('Provinsi', 'N/A')}</p>
                            <p><b>Koordinat:</b><br>
                            {baris['Lintang']:.4f}, {baris['Bujur']:.4f}</p>
                        </div>
                        """
                        
                        folium.Marker(
                            location=[baris['Lintang'], baris['Bujur']],
                            popup=folium.Popup(popup_html, max_width=300),
                            tooltip=f"{baris['Nama Stasiun']} - {suhu:.1f}°C ({deskripsi_suhu})",
                            icon=folium.Icon(color=warna, icon='thermometer', prefix='fa')
                        ).add_to(peta)
                
                folium_static(peta, width=1200, height=600)
                
                # Tambahkan grafik distribusi suhu
                st.markdown("#### 📊 Distribusi Suhu di Peta")
                data_suhu = df_stasiun['Suhu Rata-rata'].dropna()
                if len(data_suhu) > 0:
                    fig = px.histogram(
                        data_suhu,
                        nbins=20,
                        title='Distribusi Suhu Stasiun',
                        labels={'value': 'Suhu (°C)', 'count': 'Jumlah Stasiun'},
                        color_discrete_sequence=['orange']
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        # 2. PETA BERDASARKAN HUJAN
        elif jenis_visualisasi == "🌧️ Berdasarkan Hujan":
            st.markdown("### 🌧️ Peta Berdasarkan Curah Hujan")
            
            if 'Curah Hujan' in df_stasiun.columns:
                # Buat peta
                lintang_tengah = df_stasiun['Lintang'].mean()
                bujur_tengah = df_stasiun['Bujur'].mean()
                
                peta = folium.Map(
                    location=[lintang_tengah, bujur_tengah],
                    zoom_start=5,
                    tiles='CartoDB dark_matter'
                )
                
                # Legend untuk hujan
                legend_html = '''
                <div style="position: fixed; 
                            bottom: 50px; left: 50px; width: 220px; height: 160px; 
                            background-color: white; border:2px solid grey; z-index:9999; 
                            font-size:14px; padding: 10px; border-radius: 5px;">
                    <b>🌧️ Legenda Hujan</b><br>
                    <i style="background: white; width: 20px; height: 20px; display: inline-block; margin-right: 5px; border:1px solid grey;"></i> Tidak Hujan (0 mm)<br>
                    <i style="background: lightblue; width: 20px; height: 20px; display: inline-block; margin-right: 5px;"></i> Ringan (< 10 mm)<br>
                    <i style="background: blue; width: 20px; height: 20px; display: inline-block; margin-right: 5px;"></i> Sedang (10-50 mm)<br>
                    <i style="background: darkblue; width: 20px; height: 20px; display: inline-block; margin-right: 5px;"></i> Lebat (50-100 mm)<br>
                    <i style="background: purple; width: 20px; height: 20px; display: inline-block; margin-right: 5px;"></i> Sangat Lebat (> 100 mm)
                </div>
                '''
                
                peta.get_root().html.add_child(folium.Element(legend_html))
                
                # Tambahkan marker untuk setiap stasiun
                for idx, baris in df_stasiun.iterrows():
                    if pd.notna(baris['Lintang']) and pd.notna(baris['Bujur']):
                        hujan = baris['Curah Hujan'] if pd.notna(baris['Curah Hujan']) else 0
                        
                        # Tentukan warna berdasarkan curah hujan
                        if hujan == 0:
                            warna = 'white'
                            deskripsi_hujan = "Tidak Hujan"
                            warna_icon = 'gray'
                        elif hujan < 10:
                            warna = 'lightblue'
                            deskripsi_hujan = "Hujan Ringan"
                            warna_icon = 'blue'
                        elif hujan < 50:
                            warna = 'blue'
                            deskripsi_hujan = "Hujan Sedang"
                            warna_icon = 'blue'
                        elif hujan < 100:
                            warna = 'darkblue'
                            deskripsi_hujan = "Hujan Lebat"
                            warna_icon = 'darkblue'
                        else:
                            warna = 'purple'
                            deskripsi_hujan = "Hujan Sangat Lebat"
                            warna_icon = 'purple'
                        
                        # Popup info
                        popup_html = f"""
                        <div style="width: 250px;">
                            <h4>{baris['Nama Stasiun']}</h4>
                            <hr>
                            <p><b>Status Hujan:</b> <span style="color:{warna_icon}; font-weight:bold;">{deskripsi_hujan}</span></p>
                            <p><b>Curah Hujan:</b> {hujan:.1f} mm</p>
                            <p><b>Wilayah:</b> {baris.get('Wilayah', 'N/A')}</p>
                            <p><b>Provinsi:</b> {baris.get('Provinsi', 'N/A')}</p>
                            <p><b>Koordinat:</b><br>
                            {baris['Lintang']:.4f}, {baris['Bujur']:.4f}</p>
                        </div>
                        """
                        
                        # Buat custom icon dengan warna background
                        icon_html = f"""
                        <div style="background-color: {warna}; 
                                    width: 30px; height: 30px; 
                                    border-radius: 50%; 
                                    border: 2px solid white;
                                    display: flex;
                                    align-items: center;
                                    justify-content: center;">
                            <span style="color: {'black' if warna == 'white' or warna == 'lightblue' else 'white'}; 
                                        font-size: 18px;">💧</span>
                        </div>
                        """
                        
                        icon = folium.DivIcon(
                            html=icon_html,
                            icon_size=(30, 30),
                            icon_anchor=(15, 15)
                        )
                        
                        folium.Marker(
                            location=[baris['Lintang'], baris['Bujur']],
                            popup=folium.Popup(popup_html, max_width=300),
                            tooltip=f"{baris['Nama Stasiun']} - {hujan:.1f} mm ({deskripsi_hujan})",
                            icon=icon
                        ).add_to(peta)
                
                folium_static(peta, width=1200, height=600)
        
        # 3. HEATMAP SUHU
        elif jenis_visualisasi == "🔥 Heatmap Suhu":
            st.markdown("### 🔥 Heatmap Distribusi Suhu")
            
            if 'Suhu Rata-rata' in df_stasiun.columns:
                # Buat peta dengan heatmap
                lintang_tengah = df_stasiun['Lintang'].mean()
                bujur_tengah = df_stasiun['Bujur'].mean()
                
                peta = folium.Map(
                    location=[lintang_tengah, bujur_tengah],
                    zoom_start=5,
                    tiles='CartoDB dark_matter'
                )
                
                # Tambahkan heatmap
                from folium.plugins import HeatMap
                
                data_panas = []
                for idx, baris in df_stasiun.iterrows():
                    if pd.notna(baris['Lintang']) and pd.notna(baris['Bujur']) and pd.notna(baris['Suhu Rata-rata']):
                        # Beri weight berdasarkan suhu (normalisasi 0-1)
                        suhu = baris['Suhu Rata-rata']
                        berat = (suhu - 15) / 20  # Asumsi suhu 15-35°C
                        berat = max(0, min(1, berat))  # Clamp 0-1
                        
                        data_panas.append([baris['Lintang'], baris['Bujur'], berat])
                
                HeatMap(
                    data_panas,
                    radius=20,
                    blur=15,
                    max_zoom=10,
                    gradient={0.2: 'blue', 0.4: 'green', 0.6: 'yellow', 0.8: 'orange', 1: 'red'}
                ).add_to(peta)
                
                folium_static(peta, width=1200, height=600)
                # 4. HEATMAP HUJAN
        elif jenis_visualisasi == "💧 Heatmap Hujan":
            st.markdown("### 💧 Heatmap Distribusi Hujan")
            
            if 'Curah Hujan' in df_stasiun.columns:
                # Buat peta dengan heatmap
                lintang_tengah = df_stasiun['Lintang'].mean()
                bujur_tengah = df_stasiun['Bujur'].mean()
                
                peta = folium.Map(
                    location=[lintang_tengah, bujur_tengah],
                    zoom_start=5,
                    tiles='CartoDB dark_matter'
                )
                
                # Tambahkan heatmap untuk hujan
                from folium.plugins import HeatMap
                
                data_hujan_heat = []
                for idx, baris in df_stasiun.iterrows():
                    if pd.notna(baris['Lintang']) and pd.notna(baris['Bujur']) and pd.notna(baris['Curah Hujan']):
                        # Beri weight berdasarkan curah hujan
                        hujan = baris['Curah Hujan']
                        
                        # Normalisasi: hujan 0-200mm menjadi 0-1
                        # Lebih dari 200mm dianggap sebagai intensitas maksimum
                        berat = min(hujan / 200, 1.0)  # Clamp maksimum 1.0
                        berat = max(0, berat)  # Clamp minimum 0
                        
                        data_hujan_heat.append([baris['Lintang'], baris['Bujur'], berat])
                
                # Jika ada data hujan yang valid
                if data_hujan_heat:
                    HeatMap(
                        data_hujan_heat,
                        radius=25,
                        blur=20,
                        max_zoom=10,
                        gradient={
                            0.1: 'lightblue',    # Hujan ringan
                            0.3: 'blue',         # Hujan sedang
                            0.6: 'darkblue',     # Hujan lebat
                            0.8: 'purple',       # Hujan sangat lebat
                            1.0: 'red'           # Hujan ekstrem
                        },
                        min_opacity=0.3,
                        max_opacity=0.8
                    ).add_to(peta)
                    
                    # Tambahkan legend untuk heatmap hujan
                    legend_html = '''
                    <div style="position: fixed; 
                                bottom: 50px; left: 50px; width: 250px; height: 180px; 
                                background-color: rgba(255, 255, 255, 0.9); border:2px solid grey; z-index:9999; 
                                font-size:12px; padding: 10px; border-radius: 5px;">
                        <b>💧 Legenda Intensitas Hujan</b><br>
                        <i style="background: lightblue; width: 20px; height: 20px; display: inline-block; margin-right: 5px;"></i> Ringan (0-20 mm)<br>
                        <i style="background: blue; width: 20px; height: 20px; display: inline-block; margin-right: 5px;"></i> Sedang (20-60 mm)<br>
                        <i style="background: darkblue; width: 20px; height: 20px; display: inline-block; margin-right: 5px;"></i> Lebat (60-120 mm)<br>
                        <i style="background: purple; width: 20px; height: 20px; display: inline-block; margin-right: 5px;"></i> Sangat Lebat (120-200 mm)<br>
                        <i style="background: red; width: 20px; height: 20px; display: inline-block; margin-right: 5px;"></i> Ekstrem (>200 mm)
                    </div>
                    '''
                    
                    peta.get_root().html.add_child(folium.Element(legend_html))
                    
                    # Tambahkan marker untuk stasiun dengan hujan tertinggi
                    if len(df_stasiun) > 0:
                        # Cari stasiun dengan hujan tertinggi
                        df_stasiun_sorted = df_stasiun.dropna(subset=['Curah Hujan']).sort_values('Curah Hujan', ascending=False)
                        top_stations = df_stasiun_sorted.head(3)
                        
                        for idx, baris in top_stations.iterrows():
                            if pd.notna(baris['Lintang']) and pd.notna(baris['Bujur']):
                                # Marker untuk stasiun dengan hujan tinggi
                                popup_html = f"""
                                <div style="width: 250px;">
                                    <h4>☔ {baris['Nama Stasiun']}</h4>
                                    <hr>
                                    <p><b>Curah Hujan:</b> <span style="color:red; font-weight:bold;">{baris['Curah Hujan']:.1f} mm</span></p>
                                    <p><b>Peringkat:</b> #{idx+1} tertinggi</p>
                                    <p><b>Wilayah:</b> {baris.get('Wilayah', 'N/A')}</p>
                                    <p><b>Koordinat:</b><br>
                                    {baris['Lintang']:.4f}, {baris['Bujur']:.4f}</p>
                                </div>
                                """
                                
                                folium.Marker(
                                    location=[baris['Lintang'], baris['Bujur']],
                                    popup=folium.Popup(popup_html, max_width=300),
                                    tooltip=f"☔ {baris['Nama Stasiun']} - {baris['Curah Hujan']:.1f} mm (Tertinggi #{idx+1})",
                                    icon=folium.Icon(color='red', icon='tint', prefix='fa')
                                ).add_to(peta)
                    
                    folium_static(peta, width=1200, height=600)
                    
                    # Tambahkan analisis distribusi hujan
                    st.markdown("#### 📊 Analisis Distribusi Hujan di Heatmap")
                    
                    # Hitung statistik hujan
                    total_hujan = df_stasiun['Curah Hujan'].sum()
                    rata_hujan = df_stasiun['Curah Hujan'].mean()
                    max_hujan = df_stasiun['Curah Hujan'].max()
                    stasiun_hujan = (df_stasiun['Curah Hujan'] > 0).sum()
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Hujan", f"{total_hujan:,.0f} mm")
                    with col2:
                        st.metric("Rata-rata per Stasiun", f"{rata_hujan:.1f} mm")
                    with col3:
                        st.metric("Hujan Tertinggi", f"{max_hujan:.1f} mm")
                    
                    # Visualisasi distribusi hujan
                    if len(data_hujan_heat) > 0:
                        # Buat histogram distribusi hujan
                        fig_hujan = px.histogram(
                            df_stasiun,
                            x='Curah Hujan',
                            nbins=20,
                            title='Distribusi Curah Hujan di Stasiun',
                            labels={'Curah Hujan': 'Curah Hujan (mm)', 'count': 'Jumlah Stasiun'},
                            color_discrete_sequence=['blue']
                        )
                        fig_hujan.update_layout(
                            xaxis_title="Curah Hujan (mm)",
                            yaxis_title="Jumlah Stasiun"
                        )
                        st.plotly_chart(fig_hujan, use_container_width=True)
                else:
                    st.warning("⚠️ Tidak ada data hujan yang valid untuk membuat heatmap")
                    # Tampilkan peta biasa
                    folium_static(peta, width=1200, height=600)
            else:
                st.error("❌ Kolom 'Curah Hujan' tidak ditemukan dalam data stasiun")
        
        # 4. PETA KOMBINASI IKLIM
        elif jenis_visualisasi == "🌈 Kombinasi Iklim":
            st.markdown("### 🌈 Peta Kombinasi Kondisi Iklim")
            
            if 'Suhu Rata-rata' in df_stasiun.columns and 'Curah Hujan' in df_stasiun.columns:
                # Buat peta
                lintang_tengah = df_stasiun['Lintang'].mean()
                bujur_tengah = df_stasiun['Bujur'].mean()
                
                peta = folium.Map(
                    location=[lintang_tengah, bujur_tengah],
                    zoom_start=5,
                    tiles='OpenStreetMap'
                )
                
                # Buat kategori iklim berdasarkan suhu dan hujan
                def dapatkan_kategori_iklim(suhu, hujan):
                    """Kategorikan kondisi iklim"""
                    if suhu < 22 and hujan < 10:
                        return "Sejuk & Kering", "blue", "❄️"
                    elif suhu < 22 and hujan >= 10:
                        return "Sejuk & Basah", "lightblue", "🌧️❄️"
                    elif suhu < 28 and hujan < 10:
                        return "Hangat & Kering", "green", "🌞"
                    elif suhu < 28 and hujan >= 10:
                        return "Hangat & Lembab", "lightgreen", "🌞💧"
                    elif suhu >= 28 and hujan < 10:
                        return "Panas & Kering", "orange", "🔥"
                    elif suhu >= 28 and hujan >= 10:
                        return "Panas & Basah", "red", "🔥🌧️"
                    else:
                        return "Normal", "gray", "⛅"
                
                # Legend untuk kategori iklim
                legend_html = '''
                <div style="position: fixed; 
                            bottom: 50px; left: 50px; width: 250px; height: 220px; 
                            background-color: white; border:2px solid grey; z-index:9999; 
                            font-size:12px; padding: 10px; border-radius: 5px;">
                    <b>🌈 Kategori Iklim</b><br>
                    <i style="background: blue; width: 15px; height: 15px; display: inline-block; margin-right: 5px;"></i> ❄️ Sejuk & Kering<br>
                    <i style="background: lightblue; width: 15px; height: 15px; display: inline-block; margin-right: 5px;"></i> 🌧️❄️ Sejuk & Basah<br>
                    <i style="background: green; width: 15px; height: 15px; display: inline-block; margin-right: 5px;"></i> 🌞 Hangat & Kering<br>
                    <i style="background: lightgreen; width: 15px; height: 15px; display: inline-block; margin-right: 5px;"></i> 🌞💧 Hangat & Lembab<br>
                    <i style="background: orange; width: 15px; height: 15px; display: inline-block; margin-right: 5px;"></i> 🔥 Panas & Kering<br>
                    <i style="background: red; width: 15px; height: 15px; display: inline-block; margin-right: 5px;"></i> 🔥🌧️ Panas & Basah
                </div>
                '''
                
                peta.get_root().html.add_child(folium.Element(legend_html))
                
                # Tambahkan marker untuk setiap stasiun
                for idx, baris in df_stasiun.iterrows():
                    if pd.notna(baris['Lintang']) and pd.notna(baris['Bujur']):
                        suhu = baris['Suhu Rata-rata'] if pd.notna(baris['Suhu Rata-rata']) else 25
                        hujan = baris['Curah Hujan'] if pd.notna(baris['Curah Hujan']) else 0
                        
                        kategori, warna, emoji = dapatkan_kategori_iklim(suhu, hujan)
                        
                        # Popup info lengkap
                        popup_html = f"""
                        <div style="width: 300px;">
                            <h4>{baris['Nama Stasiun']}</h4>
                            <hr>
                            <p><b>Kategori Iklim:</b> <span style="color:{warna}; font-weight:bold;">{emoji} {kategori}</span></p>
                            <p><b>Suhu:</b> {suhu:.1f}°C</p>
                            <p><b>Curah Hujan:</b> {hujan:.1f} mm</p>
                            <p><b>Kelembaban:</b> {baris.get('Kelembaban Rata-rata', 'N/A'):.1f}%</p>
                            <p><b>Wilayah:</b> {baris.get('Wilayah', 'N/A')}</p>
                            <p><b>Provinsi:</b> {baris.get('Provinsi', 'N/A')}</p>
                        </div>
                        """
                        
                        # Buat custom icon dengan emoji
                        icon_html = f"""
                        <div style="background-color: {warna}; 
                                    width: 40px; height: 40px; 
                                    border-radius: 50%; 
                                    border: 2px solid white;
                                    display: flex;
                                    align-items: center;
                                    justify-content: center;
                                    box-shadow: 2px 2px 5px rgba(0,0,0,0.3);">
                            <span style="color: white; font-size: 20px;">{emoji}</span>
                        </div>
                        """
                        
                        icon = folium.DivIcon(
                            html=icon_html,
                            icon_size=(40, 40),
                            icon_anchor=(20, 20)
                        )
                        
                        folium.Marker(
                            location=[baris['Lintang'], baris['Bujur']],
                            popup=folium.Popup(popup_html, max_width=350),
                            tooltip=f"{baris['Nama Stasiun']} - {kategori}",
                            icon=icon
                        ).add_to(peta)
                
                folium_static(peta, width=1200, height=600)
                
                # Tambahkan analisis iklim
                st.markdown("#### 📊 Analisis Distribusi Kategori Iklim")
                
                # Hitung distribusi kategori
                jumlah_kategori = {}
                for idx, baris in df_stasiun.iterrows():
                    suhu = baris['Suhu Rata-rata'] if pd.notna(baris['Suhu Rata-rata']) else 25
                    hujan = baris['Curah Hujan'] if pd.notna(baris['Curah Hujan']) else 0
                    kategori, _, _ = dapatkan_kategori_iklim(suhu, hujan)
                    jumlah_kategori[kategori] = jumlah_kategori.get(kategori, 0) + 1
                
                if jumlah_kategori:
                    # Buat pie chart
                    kategori_list = list(jumlah_kategori.keys())
                    jumlah_list = list(jumlah_kategori.values())
                    
                    fig_pie = px.pie(
                        values=jumlah_list,
                        names=kategori_list,
                        title='Distribusi Kategori Iklim Stasiun',
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
        
        # 5. PETA LOKASI SAJA (default)
        else:
            st.markdown("### 📍 Peta Lokasi Stasiun")
            
            # Buat peta sederhana
            lintang_tengah = df_stasiun['Lintang'].mean()
            bujur_tengah = df_stasiun['Bujur'].mean()
            
            peta = folium.Map(
                location=[lintang_tengah, bujur_tengah],
                zoom_start=5,
                tiles='OpenStreetMap'
            )
            
            for idx, baris in df_stasiun.iterrows():
                if pd.notna(baris['Lintang']) and pd.notna(baris['Bujur']):
                    folium.Marker(
                        location=[baris['Lintang'], baris['Bujur']],
                        popup=baris['Nama Stasiun'],
                        tooltip=baris['Nama Stasiun'],
                        icon=folium.Icon(color='blue', icon='cloud')
                    ).add_to(peta)
            
            folium_static(peta, width=1200, height=600)
        
        # Tabel data stasiun
        st.markdown("### 📋 Data Stasiun")
        kolom_tampil = ['Nama Stasiun', 'Lintang', 'Bujur', 'Wilayah', 'Provinsi']
        if 'Suhu Rata-rata' in df_stasiun.columns:
            kolom_tampil.extend(['Suhu Rata-rata', 'Curah Hujan'])
        
        st.dataframe(df_stasiun[kolom_tampil].round(4), use_container_width=True, height=400)

elif tab_selection == "📈 Analisis Suhu":
    st.markdown("## 📈 Analisis Data Suhu")
    
    df = muat_data_cuaca(tanggal_mulai, tanggal_selesai, wilayah_terpilih, batas_data)
    
    if df.empty:
        st.warning("Tidak ada data yang ditemukan")
    else:
        if 'Suhu Rata-rata' not in df.columns:
            st.error("Kolom Suhu Rata-rata tidak ditemukan")
        else:
            # Tabs untuk analisis
            tab1, tab2, = st.tabs(["📊 Distribusi", "📈 Trend",])
            
            with tab1:
                col1, col2 = st.columns(2)
                
                with col1:
                    fig_hist = px.histogram(
                        df,
                        x='Suhu Rata-rata',
                        nbins=50,
                        title='Distribusi Suhu Rata-rata',
                        labels={'Suhu Rata-rata': 'Suhu (°C)'},
                        color_discrete_sequence=['#FF6B6B']
                    )
                    fig_hist.update_layout(
                        xaxis_title="Suhu (°C)",
                        yaxis_title="Jumlah Observasi"
                    )
                    st.plotly_chart(fig_hist, use_container_width=True)
                
                with col2:
                    if 'Wilayah' in df.columns:
                        # Ambil top 10 wilayah dengan data terbanyak
                        wilayah_top = df['Wilayah'].value_counts().nlargest(10).index.tolist()
                        df_top = df[df['Wilayah'].isin(wilayah_top)]
                        
                        fig_box = px.box(
                            df_top,
                            x='Wilayah',
                            y='Suhu Rata-rata',
                            title='Distribusi Suhu per Wilayah (Top 10)',
                            color='Wilayah'
                        )
                        fig_box.update_layout(
                            xaxis_title="Wilayah",
                            yaxis_title="Suhu (°C)",
                            xaxis_tickangle=-45,
                            showlegend=False
                        )
                        st.plotly_chart(fig_box, use_container_width=True)
            
            with tab2:
                if 'Tanggal' in df.columns:
                    df['Bulan'] = df['Tanggal'].dt.month
                    rata_bulanan = df.groupby('Bulan').agg({
                        'Suhu Rata-rata': 'mean',
                        'Suhu Minimum': 'min',
                        'Suhu Maksimum': 'max'
                    }).reset_index()
                    
                    nama_bulan = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
                                 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
                    rata_bulanan['Nama Bulan'] = rata_bulanan['Bulan'].apply(lambda x: nama_bulan[x-1] if 1 <= x <= 12 else 'Unknown')
                    
                    fig_trend = go.Figure()
                    
                    fig_trend.add_trace(go.Scatter(
                        x=rata_bulanan['Nama Bulan'],
                        y=rata_bulanan['Suhu Rata-rata'],
                        mode='lines+markers',
                        name='Suhu Rata-rata',
                        line=dict(color='red', width=3)
                    ))
                    
                    fig_trend.add_trace(go.Scatter(
                        x=rata_bulanan['Nama Bulan'],
                        y=rata_bulanan['Suhu Minimum'],
                        mode='lines',
                        name='Suhu Minimum',
                        line=dict(color='blue', width=2, dash='dash')
                    ))
                    
                    fig_trend.add_trace(go.Scatter(
                        x=rata_bulanan['Nama Bulan'],
                        y=rata_bulanan['Suhu Maksimum'],
                        mode='lines',
                        name='Suhu Maksimum',
                        line=dict(color='orange', width=2, dash='dash')
                    ))
                    
                    fig_trend.update_layout(
                        title='Trend Suhu Bulanan',
                        xaxis_title="Bulan",
                        yaxis_title="Suhu (°C)",
                        hovermode='x unified'
                    )
                    
                    st.plotly_chart(fig_trend, use_container_width=True)
            
            

elif tab_selection == "🌧️ Analisis Hujan":
    st.markdown("## 🌧️ Analisis Data Curah Hujan")
    
    df = muat_data_cuaca(tanggal_mulai, tanggal_selesai, wilayah_terpilih, batas_data)
    
    if df.empty:
        st.warning("Tidak ada data yang ditemukan")
    else:
        if 'Curah Hujan' not in df.columns:
            st.error("Kolom Curah Hujan tidak ditemukan")
        else:
            # Metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                total_hujan = df['Curah Hujan'].sum()
                st.metric("Total Hujan", f"{total_hujan:,.0f} mm")
            with col2:
                rata_hujan = df['Curah Hujan'].mean()
                st.metric("Rata-rata Harian", f"{rata_hujan:.1f} mm/hari")
            with col3:
                maks_hujan = df['Curah Hujan'].max()
                st.metric("Hujan Tertinggi", f"{maks_hujan:.1f} mm")
            with col4:
                hari_hujan = (df['Curah Hujan'] > 0).sum()
                total_hari = len(df)
                persen_hujan = (hari_hujan / total_hari * 100) if total_hari > 0 else 0
                st.metric("Hari Hujan", f"{hari_hujan}/{total_hari} ({persen_hujan:.1f}%)")
            
            # Tabs untuk analisis
            tab1, tab2 = st.tabs(["📊 Distribusi", "📍 Spasial"])
            
            with tab1:
                col1, col2 = st.columns(2)
                
                with col1:
                    # Hanya data dengan hujan > 0
                    data_hujan = df[df['Curah Hujan'] > 0]
                    if not data_hujan.empty:
                        fig_hujan_dist = px.histogram(
                            data_hujan,
                            x='Curah Hujan',
                            nbins=30,
                            title='Distribusi Curah Hujan (saat hujan)',
                            labels={'Curah Hujan': 'Hujan (mm)'},
                            color_discrete_sequence=['#1E90FF']
                        )
                        fig_hujan_dist.update_layout(
                            xaxis_title="Curah Hujan (mm)",
                            yaxis_title="Jumlah Hari"
                        )
                        st.plotly_chart(fig_hujan_dist, use_container_width=True)
                
                with col2:
                    if 'Tanggal' in df.columns:
                        df['Hari'] = df['Tanggal'].dt.dayofweek
                        nama_hari = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
                        df['Nama Hari'] = df['Hari'].apply(lambda x: nama_hari[x])
                        
                        hujan_per_hari = df.groupby('Nama Hari')['Curah Hujan'].sum().reindex(nama_hari)
                        
                        fig_hari = px.bar(
                            hujan_per_hari.reset_index(),
                            x='Nama Hari',
                            y='Curah Hujan',
                            title='Total Hujan per Hari dalam Seminggu',
                            color='Curah Hujan',
                            color_continuous_scale='Blues'
                        )
                        fig_hari.update_layout(
                            xaxis_title="Hari",
                            yaxis_title="Total Hujan (mm)"
                        )
                        st.plotly_chart(fig_hari, use_container_width=True)
            
            with tab2:
                # Analisis spasial hujan
                st.markdown("### 📍 Distribusi Spasial Hujan")
                
                if 'Wilayah' in df.columns and 'Provinsi' in df.columns:
                    # Group by wilayah
                    hujan_per_wilayah = df.groupby(['Provinsi', 'Wilayah']).agg({
                        'Curah Hujan': ['sum', 'mean', 'max', 'count']
                    }).reset_index()
                    
                    # Flatten multi-index columns
                    hujan_per_wilayah.columns = ['Provinsi', 'Wilayah', 'Total_Hujan', 'Rata_Hujan', 'Maks_Hujan', 'Jumlah_Data']
                    
                    # Tampilkan top 10 wilayah dengan hujan terbanyak
                    top_hujan = hujan_per_wilayah.nlargest(10, 'Total_Hujan')
                    
                    fig_top = px.bar(
                        top_hujan,
                        x='Wilayah',
                        y='Total_Hujan',
                        color='Provinsi',
                        title='10 Wilayah dengan Hujan Tertinggi',
                        labels={'Total_Hujan': 'Total Hujan (mm)', 'Wilayah': 'Wilayah'}
                    )
                    fig_top.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig_top, use_container_width=True)
                    
                    # Tabel detail
                    st.markdown("### 📋 Detail Hujan per Wilayah")
                    st.dataframe(
                        hujan_per_wilayah.sort_values('Total_Hujan', ascending=False).round(2),
                        use_container_width=True,
                        height=400
                    )

elif tab_selection == "🌀 Analisis Angin":
    st.markdown("## 🌀 Analisis Data Angin")
    
    df = muat_data_cuaca(tanggal_mulai, tanggal_selesai, wilayah_terpilih, batas_data)
    
    if df.empty:
        st.warning("Tidak ada data yang ditemukan")
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            if 'Kecepatan Angin Rata-rata' in df.columns:
                angin_rata = df['Kecepatan Angin Rata-rata'].mean()
                st.metric("Kecepatan Rata-rata", f"{angin_rata:.1f} m/s")
        
        with col2:
            if 'Kecepatan Angin Maksimum' in df.columns:
                angin_maks = df['Kecepatan Angin Maksimum'].max()
                st.metric("Kecepatan Maksimum", f"{angin_maks:.1f} m/s")
        
        with col3:
            if 'Nama Arah Angin' in df.columns:
                arah_terbanyak = df['Nama Arah Angin'].mode()
                if len(arah_terbanyak) > 0:
                    st.metric("Arah Terbanyak", arah_terbanyak[0])
        
        # Visualizations
        st.markdown("### 📊 Visualisasi Data Angin")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if 'Kecepatan Angin Rata-rata' in df.columns:
                fig_angin = px.histogram(
                    df,
                    x='Kecepatan Angin Rata-rata',
                    nbins=30,
                    title='Distribusi Kecepatan Angin Rata-rata',
                    labels={'Kecepatan Angin Rata-rata': 'Kecepatan (m/s)'},
                    color_discrete_sequence=['#00CED1']
                )
                fig_angin.update_layout(
                    xaxis_title="Kecepatan Angin (m/s)",
                    yaxis_title="Jumlah Observasi"
                )
                st.plotly_chart(fig_angin, use_container_width=True)
        
        with col2:
            # Wind rose untuk arah angin
            if 'Nama Arah Angin' in df.columns:
                hitung_arah = df['Nama Arah Angin'].value_counts().reset_index()
                hitung_arah.columns = ['Arah Angin', 'Jumlah']
                
                fig_mawar_angin = px.bar_polar(
                    hitung_arah,
                    r='Jumlah',
                    theta='Arah Angin',
                    title='Distribusi Arah Angin',
                    color='Jumlah',
                    color_continuous_scale='Blues'
                )
                st.plotly_chart(fig_mawar_angin, use_container_width=True)
        
        # Analisis hubungan angin dengan variabel lain
        st.markdown("### 🔗 Hubungan Angin dengan Variabel Lain")
        
        if all(k in df.columns for k in ['Kecepatan Angin Rata-rata', 'Suhu Rata-rata', 'Curah Hujan']):
            col1, col2 = st.columns(2)
            
        with col1:
            try:
                fig_scatter_suhu = px.scatter(
                    df,
                    x='Kecepatan Angin Rata-rata',
                    y='Suhu Rata-rata',
                    title='Hubungan Kecepatan Angin dengan Suhu',
                    trendline='ols',
                    labels={'Kecepatan Angin Rata-rata': 'Kecepatan Angin (m/s)', 
                        'Suhu Rata-rata': 'Suhu (°C)'}
                )
                st.plotly_chart(fig_scatter_suhu, use_container_width=True)
            except Exception as e:
                # Fallback tanpa trendline
                fig_scatter_suhu = px.scatter(
                    df,
                    x='Kecepatan Angin Rata-rata',
                    y='Suhu Rata-rata',
                    title='Hubungan Kecepatan Angin dengan Suhu (tanpa trendline)',
                    labels={'Kecepatan Angin Rata-rata': 'Kecepatan Angin (m/s)', 
                        'Suhu Rata-rata': 'Suhu (°C)'}
                )
                st.plotly_chart(fig_scatter_suhu, use_container_width=True)
                st.info("⚠️ Trendline tidak tersedia. Install statsmodels: `pip install statsmodels`")

        with col2:
            try:
                fig_scatter_hujan = px.scatter(
                    df,
                    x='Kecepatan Angin Rata-rata',
                    y='Curah Hujan',
                    title='Hubungan Kecepatan Angin dengan Curah Hujan',
                    trendline='ols',
                    labels={'Kecepatan Angin Rata-rata': 'Kecepatan Angin (m/s)', 
                        'Curah Hujan': 'Curah Hujan (mm)'}
                )
                st.plotly_chart(fig_scatter_hujan, use_container_width=True)
            except Exception as e:
                # Fallback tanpa trendline
                fig_scatter_hujan = px.scatter(
                    df,
                    x='Kecepatan Angin Rata-rata',
                    y='Curah Hujan',
                    title='Hubungan Kecepatan Angin dengan Curah Hujan (tanpa trendline)',
                    labels={'Kecepatan Angin Rata-rata': 'Kecepatan Angin (m/s)', 
                        'Curah Hujan': 'Curah Hujan (mm)'}
                )
                st.plotly_chart(fig_scatter_hujan, use_container_width=True)

elif tab_selection == "📋 Data Mentah":
    st.markdown("## 📋 Data Mentah dan Ekspor")
    
    df = muat_data_cuaca(tanggal_mulai, tanggal_selesai, wilayah_terpilih, batas_data)
    
    if df.empty:
        st.warning("Tidak ada data yang ditemukan")
    else:
        # Data info
        st.markdown(f"**Total Data:** {len(df):,} baris")
        st.markdown(f"**Jumlah Kolom:** {len(df.columns)} kolom")
        
        if 'Tanggal' in df.columns:
            tanggal_min = df['Tanggal'].min()
            tanggal_maks = df['Tanggal'].max()
            st.markdown(f"**Periode:** {tanggal_min.strftime('%Y-%m-%d')} - {tanggal_maks.strftime('%Y-%m-%d')}")
        
        # Preview dengan pilihan kolom
        st.markdown("### 👁️ Preview Data")
        
        # Pilih kolom untuk ditampilkan
        semua_kolom = df.columns.tolist()
        kolom_pilihan = st.multiselect(
            "Pilih kolom untuk ditampilkan:",
            options=semua_kolom,
            default=semua_kolom[:10] if len(semua_kolom) > 10 else semua_kolom
        )
        
        if kolom_pilihan:
            st.dataframe(df[kolom_pilihan].head(100), use_container_width=True, height=400)
        else:
            st.dataframe(df.head(100), use_container_width=True, height=400)
        
        # Statistik deskriptif
        st.markdown("### 📊 Statistik Deskriptif")
        kolom_numerik = df.select_dtypes(include=[np.number]).columns.tolist()
        if kolom_numerik:
            st.dataframe(df[kolom_numerik].describe().round(2), use_container_width=True)
        
        # Export
        st.markdown("### ⬇️ Ekspor Data")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            csv = df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"data_iklim_{tanggal_mulai}_ke_{tanggal_selesai}.csv",
                mime="text/csv",
                help="Download data dalam format CSV"
            )
        
        with col2:
            try:
                from io import BytesIO
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as penulis:
                    df.to_excel(penulis, index=False, sheet_name='Data Iklim')
                    
                    # Buat sheet statistik juga
                    if kolom_numerik:
                        df[kolom_numerik].describe().to_excel(penulis, sheet_name='Statistik')
                
                st.download_button(
                    label="📊 Download Excel",
                    data=output.getvalue(),
                    file_name=f"data_iklim_{tanggal_mulai}_ke_{tanggal_selesai}.xlsx",
                    mime="application/vnd.ms-excel",
                    help="Download data dalam format Excel dengan multiple sheets"
                )
            except Exception as e:
                st.info("Install xlsxwriter untuk export Excel")
                st.error(f"Error: {str(e)[:100]}")
        
        with col3:
            json_str = df.to_json(orient='records', indent=2, force_ascii=False)
            st.download_button(
                label="📄 Download JSON",
                data=json_str.encode('utf-8'),
                file_name=f"data_iklim_{tanggal_mulai}_ke_{tanggal_selesai}.json",
                mime="application/json",
                help="Download data dalam format JSON"
            )

elif tab_selection == "🔍 Info Database":
    st.markdown("## 🔍 Informasi Database")
    
    # Database stats
    statistik = ambil_statistik_database()
    
    if statistik:
        st.markdown("### 📊 Statistik Database")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Observasi", f"{statistik.get('total_observasi', 0):,}")
        with col2:
            st.metric("Total Stasiun", statistik.get('total_stasiun', 0))
        with col3:
            st.metric("Data 30 Hari Terakhir", f"{statistik.get('terbaru_30_hari', 0):,}")
        with col4:
            st.metric("Total Wilayah", statistik.get('total_wilayah', 0))
        
        col5, col6, col7 = st.columns(3)
        with col5:
            st.metric("Total Provinsi", statistik.get('total_provinsi', 0))
        with col6:
            if 'rentang_tanggal' in statistik:
                st.metric("Rentang Tanggal", "2010-2025")
        
        # Info tambahan
        st.markdown("### ℹ️ Informasi Tambahan")
        
        # Available years
        tahun_tersedia = ambil_tahun_tersedia()
        if tahun_tersedia:
            st.markdown(f"**Tahun yang Tersedia:** {', '.join(map(str, tahun_tersedia))}")
        
        # Info struktur database
        st.markdown("#### 🗃️ Struktur Database")
        st.markdown("""
        - **observasi_cuaca**: Tabel utama berisi data observasi cuaca harian
        - **stasiun**: Data stasiun pengamatan BMKG
        - **wilayah**: Data wilayah administratif
        - **provinsi**: Data provinsi di Indonesia
        - **arah_angin**: Tabel referensi arah angin
        """)
        
        # Sample data dari berbagai tabel
        st.markdown("### 🧪 Sample Data dari Setiap Tabel")
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["Observasi Cuaca", "Stasiun", "Wilayah", "Provinsi", "Arah Angin"])
        
        with tab1:
            if st.button("Tampilkan Sample Observasi Cuaca (10 baris)"):
                sample_observasi = ambil_data_contoh(10)
                if not sample_observasi.empty:
                    st.dataframe(sample_observasi)
                else:
                    st.error("Tidak bisa mengambil sample data")
        
        with tab2:
            if st.button("Tampilkan Data Stasiun"):
                data_stasiun = ambil_data_stasiun()
                if not data_stasiun.empty:
                    st.dataframe(data_stasiun)
                else:
                    st.error("Tidak bisa mengambil data stasiun")
        
        with tab3:
            data_wilayah = ambil_daftar_wilayah()
            if data_wilayah:
                df_wilayah = pd.DataFrame(data_wilayah)
                st.dataframe(df_wilayah)
            else:
                st.info("Tidak ada data wilayah")
        
        with tab4:
            # Query langsung untuk provinsi
            try:
                db = KonektorDatabase()
                koneksi = db.buat_koneksi()
                if koneksi:
                    query = "SELECT * FROM provinsi ORDER BY nama_provinsi"
                    df_provinsi = pd.read_sql(query, koneksi)
                    st.dataframe(df_provinsi)
                    koneksi.close()
            except:
                st.info("Tidak bisa mengambil data provinsi")
        
        with tab5:
            data_arah = ambil_arah_angin()
            if not data_arah.empty:
                st.dataframe(data_arah)
            else:
                st.info("Tidak ada data arah angin")
    else:
        st.error("Tidak bisa mengambil statistik database")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 2rem;">
    <p><strong>🌤️ Dashboard Iklim Indonesia</strong></p>
    <p>Data Sumber: Kaggle Dataset | Database: iklim_indonesia</p>
    <p style="font-size: 0.8rem;">
        Tabel: observasi_cuaca, stasiun, wilayah, provinsi, arah_angin<br>
        Dibangun dengan Streamlit, Plotly, dan Folium
    </p>
    <p style="font-size: 0.7rem; color: #999;">© 2024 Dashboard Iklim Indonesia - Kelompok 4</p>
</div>
""", unsafe_allow_html=True)
