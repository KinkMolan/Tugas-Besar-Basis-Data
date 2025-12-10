"""
config.py - KONEKSI DATABASE BAHASA INDONESIA
Fungsi untuk mengelola koneksi dan query database iklim_indonesia
VERSI DIPERBAIKI: Mendukung filter rentang tanggal dengan benar
"""

import mysql.connector
from mysql.connector import Error
import streamlit as st
import pandas as pd
from datetime import datetime

class KonektorDatabase:
    """Class untuk mengelola koneksi database"""
    
    def __init__(self):
        self.host = "localhost"
        self.port = 3306
        self.user = "root"
        self.password = ""  # Kosong untuk Laragon
        self.database = "iklim_indonesia"  # Database baru
    
    def buat_koneksi(self):
        """Membuat koneksi ke database"""
        try:
            koneksi = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database
            )
            return koneksi
        except Error as e:
            st.error(f"❌ Error menghubungkan ke MySQL: {e}")
            return None
    
    def uji_koneksi(self):
        """Testing koneksi database"""
        try:
            koneksi = self.buat_koneksi()
            if koneksi:
                koneksi.close()
                return True
        except:
            return False

# ===== FUNGSI UTAMA BAHASA INDONESIA =====

def ambil_data_cuaca(tanggal_mulai=None, tanggal_selesai=None, id_wilayah=None, id_stasiun=None, batas=10000):
    """
    Ambil data observasi_cuaca dengan struktur BAHASA INDONESIA
    SUDAH DIPERBAIKI: Mendukung filter rentang tanggal lengkap
    
    Args:
        tanggal_mulai (str): Format 'YYYY-MM-DD'. Jika None, ambil semua.
        tanggal_selesai (str): Format 'YYYY-MM-DD'. Jika None, ambil dari tanggal_mulai hingga data terbaru.
        id_wilayah (int): Filter berdasarkan wilayah.
        id_stasiun (int): Filter berdasarkan stasiun.
        batas (int): Batas jumlah baris.
    
    Returns:
        DataFrame: Data cuaca yang telah difilter.
    """
    db = KonektorDatabase()
    koneksi = db.buat_koneksi()
    
    if koneksi is None:
        return pd.DataFrame()
    
    try:
        # Query dengan nama tabel dan kolom Bahasa Indonesia
        query = """
        SELECT 
            oc.id_observasi,
            oc.id_stasiun,
            oc.tanggal,
            oc.suhu_minimum,
            oc.suhu_maksimum,
            oc.suhu_rata_rata,
            oc.kelembaban_rata_rata,
            oc.curah_hujan,
            oc.durasi_sinar_matahari,
            oc.kecepatan_angin_maksimum,
            oc.arah_angin_maksimum,
            oc.kecepatan_angin_rata_rata,
            oc.kode_arah_angin,
            s.nama_stasiun,
            s.lintang,
            s.bujur,
            w.nama_wilayah,
            p.nama_provinsi,
            aa.nama_arah AS nama_arah_angin
        FROM observasi_cuaca oc
        JOIN stasiun s ON oc.id_stasiun = s.id_stasiun
        LEFT JOIN wilayah w ON s.id_wilayah = w.id_wilayah
        LEFT JOIN provinsi p ON w.id_provinsi = p.id_provinsi
        LEFT JOIN arah_angin aa ON oc.kode_arah_angin = aa.kode_arah
        WHERE 1=1
        """
        
        parameter = []
        
        # ===== FILTER TANGGAL YANG SUDAH DIPERBAIKI =====
        if tanggal_mulai and tanggal_selesai:
            # Jika kedua tanggal diberikan, gunakan BETWEEN
            query += " AND oc.tanggal BETWEEN %s AND %s"
            parameter.append(tanggal_mulai)
            parameter.append(tanggal_selesai)
        elif tanggal_mulai:
            # Jika hanya tanggal mulai, gunakan >=
            query += " AND oc.tanggal >= %s"
            parameter.append(tanggal_mulai)
        elif tanggal_selesai:
            # Jika hanya tanggal selesai, gunakan <=
            query += " AND oc.tanggal <= %s"
            parameter.append(tanggal_selesai)
        # Jika tidak ada tanggal, ambil semua data
        # ============================================
        
        if id_wilayah:
            query += " AND w.id_wilayah = %s"
            parameter.append(id_wilayah)
        
        if id_stasiun:
            query += " AND s.id_stasiun = %s"
            parameter.append(id_stasiun)
        
        query += " ORDER BY oc.tanggal DESC LIMIT %s"
        parameter.append(batas)
        
        # Eksekusi query
        df = pd.read_sql(query, koneksi, params=parameter)
        
        return df
    
    except Error as e:
        st.error(f"❌ Error SQL: {str(e)[:200]}")
        return pd.DataFrame()
    
    finally:
        if koneksi and koneksi.is_connected():
            koneksi.close()

def ambil_data_stasiun():
    """Ambil data stasiun dengan lokasi"""
    db = KonektorDatabase()
    koneksi = db.buat_koneksi()
    
    if koneksi is None:
        return pd.DataFrame()
    
    try:
        query = """
        SELECT 
            s.id_stasiun,
            s.nama_stasiun,
            s.lintang,
            s.bujur,
            w.nama_wilayah,
            p.nama_provinsi
        FROM stasiun s
        LEFT JOIN wilayah w ON s.id_wilayah = w.id_wilayah
        LEFT JOIN provinsi p ON w.id_provinsi = p.id_provinsi
        WHERE s.lintang IS NOT NULL 
        AND s.bujur IS NOT NULL
        ORDER BY s.nama_stasiun
        """
        
        df = pd.read_sql(query, koneksi)
        return df
    
    except Error as e:
        st.error(f"Error mengambil data stasiun: {e}")
        return pd.DataFrame()
    
    finally:
        if koneksi and koneksi.is_connected():
            koneksi.close()

def ambil_daftar_wilayah():
    """Ambil daftar wilayah"""
    db = KonektorDatabase()
    koneksi = db.buat_koneksi()
    
    if koneksi is None:
        return []
    
    try:
        query = "SELECT id_wilayah, nama_wilayah FROM wilayah ORDER BY nama_wilayah"
        kursor = koneksi.cursor(dictionary=True)
        kursor.execute(query)
        hasil = kursor.fetchall()
        return hasil
    except:
        return []
    finally:
        if koneksi and koneksi.is_connected():
            koneksi.close()

def ambil_arah_angin():
    """Ambil data arah angin"""
    db = KonektorDatabase()
    koneksi = db.buat_koneksi()
    
    if koneksi is None:
        return pd.DataFrame()
    
    try:
        query = """
        SELECT 
            kode_arah,
            nama_arah,
            nama_arah_id
        FROM arah_angin 
        ORDER BY nama_arah
        """
        df = pd.read_sql(query, koneksi)
        return df
    except:
        return pd.DataFrame()
    finally:
        if koneksi and koneksi.is_connected():
            koneksi.close()

def ambil_statistik_database():
    """Ambil statistik database"""
    db = KonektorDatabase()
    koneksi = db.buat_koneksi()
    
    if koneksi is None:
        return {}
    
    try:
        statistik = {}
        kursor = koneksi.cursor()
        
        # Hitung total observasi cuaca
        kursor.execute("SELECT COUNT(*) FROM observasi_cuaca")
        statistik['total_observasi'] = kursor.fetchone()[0]
        
        # Hitung total stasiun
        kursor.execute("SELECT COUNT(*) FROM stasiun")
        statistik['total_stasiun'] = kursor.fetchone()[0]
        
        # Hitung rentang tanggal
        kursor.execute("SELECT MIN(tanggal), MAX(tanggal) FROM observasi_cuaca")
        tanggal_min, tanggal_maks = kursor.fetchone()
        if tanggal_min and tanggal_maks:
            statistik['rentang_tanggal'] = f"{tanggal_min.strftime('%Y-%m-%d')} sampai {tanggal_maks.strftime('%Y-%m-%d')}"
        else:
            statistik['rentang_tanggal'] = "Data tidak tersedia"
        
        # Hitung data terbaru
        kursor.execute("SELECT COUNT(*) FROM observasi_cuaca WHERE tanggal >= DATE_SUB(NOW(), INTERVAL 30 DAY)")
        statistik['terbaru_30_hari'] = kursor.fetchone()[0]
        
        # Hitung jumlah wilayah
        kursor.execute("SELECT COUNT(*) FROM wilayah")
        statistik['total_wilayah'] = kursor.fetchone()[0]
        
        # Hitung jumlah provinsi
        kursor.execute("SELECT COUNT(*) FROM provinsi")
        statistik['total_provinsi'] = kursor.fetchone()[0]
        
        return statistik
    
    except Error as e:
        st.error(f"Error mengambil statistik: {e}")
        return {}
    
    finally:
        if koneksi and koneksi.is_connected():
            koneksi.close()

def ambil_data_contoh(batas=100):
    """Ambil sample data untuk testing"""
    db = KonektorDatabase()
    koneksi = db.buat_koneksi()
    
    if koneksi is None:
        return pd.DataFrame()
    
    try:
        query = f"""
        SELECT * FROM observasi_cuaca 
        ORDER BY tanggal DESC 
        LIMIT {batas}
        """
        df = pd.read_sql(query, koneksi)
        return df
    except:
        return pd.DataFrame()
    finally:
        if koneksi and koneksi.is_connected():
            koneksi.close()

def ambil_tahun_tersedia():
    """Dapatkan tahun-tahun yang tersedia di data"""
    db = KonektorDatabase()
    koneksi = db.buat_koneksi()
    
    if koneksi is None:
        return []
    
    try:
        query = "SELECT DISTINCT YEAR(tanggal) as tahun FROM observasi_cuaca ORDER BY tahun DESC"
        kursor = koneksi.cursor()
        kursor.execute(query)
        hasil = [baris[0] for baris in kursor.fetchall() if baris[0]]
        return hasil
    except:
        return []
    finally:
        if koneksi and koneksi.is_connected():
            koneksi.close()

def ambil_statistik_cuaca_stasiun(id_stasiun):
    """Dapatkan statistik cuaca untuk stasiun tertentu"""
    db = KonektorDatabase()
    koneksi = db.buat_koneksi()
    
    if koneksi is None:
        return {}
    
    try:
        query = """
        SELECT 
            COUNT(*) as total_hari,
            AVG(suhu_rata_rata) as suhu_rata,
            MIN(suhu_rata_rata) as suhu_minimum,
            MAX(suhu_rata_rata) as suhu_maksimum,
            SUM(curah_hujan) as total_hujan,
            AVG(kelembaban_rata_rata) as kelembaban_rata,
            AVG(kecepatan_angin_rata_rata) as angin_rata
        FROM observasi_cuaca 
        WHERE id_stasiun = %s
        """
        
        kursor = koneksi.cursor(dictionary=True)
        kursor.execute(query, (id_stasiun,))
        hasil = kursor.fetchone()
        return hasil
    except:
        return {}
    finally:
        if koneksi and koneksi.is_connected():
            koneksi.close()

# Fungsi tambahan untuk kenyamanan
def ambil_nama_kolom():
    """Ambil daftar nama kolom dalam Bahasa Indonesia"""
    return {
        'id_observasi': 'ID Observasi',
        'id_stasiun': 'ID Stasiun',
        'tanggal': 'Tanggal',
        'suhu_minimum': 'Suhu Minimum',
        'suhu_maksimum': 'Suhu Maksimum',
        'suhu_rata_rata': 'Suhu Rata-rata',
        'kelembaban_rata_rata': 'Kelembaban Rata-rata',
        'curah_hujan': 'Curah Hujan',
        'durasi_sinar_matahari': 'Durasi Sinar Matahari',
        'kecepatan_angin_maksimum': 'Kecepatan Angin Maksimum',
        'arah_angin_maksimum': 'Arah Angin Maksimum',
        'kecepatan_angin_rata_rata': 'Kecepatan Angin Rata-rata',
        'kode_arah_angin': 'Kode Arah Angin',
        'nama_stasiun': 'Nama Stasiun',
        'lintang': 'Lintang',
        'bujur': 'Bujur',
        'nama_wilayah': 'Nama Wilayah',
        'nama_provinsi': 'Nama Provinsi',
        'nama_arah_angin': 'Nama Arah Angin'
    }

# Fungsi khusus untuk dashboard
def ambil_data_periode(tanggal_mulai, tanggal_selesai, batas=50000):
    """Fungsi khusus untuk mengambil data dalam periode tertentu (untuk dashboard)"""
    return ambil_data_cuaca(
        tanggal_mulai=tanggal_mulai,
        tanggal_selesai=tanggal_selesai,
        batas=batas
    )