"""
IMPORT CSV KE DATABASE IKLIM INDONESIA
Versi minimalis - hanya import
"""

import pandas as pd
import mysql.connector
import os

def import_csv_sederhana():
    """Import CSV ke database iklim_indonesia (versi sederhana)"""
    
    print("Memulai import data...")
    
    # Koneksi database
    conn = mysql.connector.connect(
        host='localhost',
        database='iklim_indonesia',
        user='root',
        password=''
    )
    cur = conn.cursor()
    
    # File CSV yang akan diimport
    file_provinsi = 'province_detail.csv'
    file_stasiun = 'station_detail.csv'
    file_cuaca = 'climate_data.csv'
    file_cuaca2 = '2021_2025.csv'
    
    total_data = 0
    
    # 1. IMPORT PROVINSI
    if os.path.exists(file_provinsi):
        print(f"Mengimport {file_provinsi}...")
        df_provinsi = pd.read_csv(file_provinsi)
        
        for _, baris in df_provinsi.iterrows():
            cur.execute("""
                INSERT IGNORE INTO provinsi (id_provinsi, nama_provinsi)
                VALUES (%s, %s)
            """, (baris['province_id'], baris['province_name']))
        
        print(f"✅ {len(df_provinsi)} provinsi diimport")
    
    # 2. IMPORT WILAYAH & STASIUN
    if os.path.exists(file_stasiun):
        print(f"\nMengimport {file_stasiun}...")
        df_stasiun = pd.read_csv(file_stasiun)
        
        # Import wilayah
        wilayah_unik = df_stasiun[['region_id', 'region_name', 'province_id']].drop_duplicates()
        for _, baris in wilayah_unik.iterrows():
            cur.execute("""
                INSERT IGNORE INTO wilayah (id_wilayah, nama_wilayah, id_provinsi)
                VALUES (%s, %s, %s)
            """, (baris['region_id'], baris['region_name'], baris['province_id']))
        
        # Import stasiun
        for _, baris in df_stasiun.iterrows():
            cur.execute("""
                INSERT IGNORE INTO stasiun 
                (id_stasiun, nama_stasiun, id_wilayah, lintang, bujur)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                baris['station_id'],
                baris['station_name'],
                baris['region_id'],
                baris.get('latitude', 0),
                baris.get('longitude', 0)
            ))
        
        print(f"✅ {len(wilayah_unik)} wilayah diimport")
        print(f"✅ {len(df_stasiun)} stasiun diimport")
    
    # 3. IMPORT DATA CUACA
    for file_cuaca_nama in [file_cuaca, file_cuaca2]:
        if os.path.exists(file_cuaca_nama):
            print(f"\nMengimport {file_cuaca_nama}...")
            df_cuaca = pd.read_csv(file_cuaca_nama)
            
            baris_diimport = 0
            for idx, baris in df_cuaca.iterrows():
                try:
                    # Format tanggal
                    tanggal = str(baris.get('date', ''))
                    
                    # Konversi format tanggal
                    if '/' in tanggal:
                        parts = tanggal.split('/')
                        if len(parts) == 3:
                            hari, bulan, tahun = parts
                            if len(tahun) == 2:
                                tahun = '20' + tahun
                            tanggal_fix = f"{tahun}-{bulan.zfill(2)}-{hari.zfill(2)}"
                        else:
                            continue
                    else:
                        tanggal_fix = tanggal
                    
                    # Insert data
                    cur.execute("""
                        INSERT IGNORE INTO observasi_cuaca 
                        (id_stasiun, tanggal, suhu_minimum, suhu_maksimum, suhu_rata_rata,
                         kelembaban_rata_rata, curah_hujan, durasi_sinar_matahari,
                         kecepatan_angin_maksimum, arah_angin_maksimum,
                         kecepatan_angin_rata_rata, kode_arah_angin)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        baris.get('station_id'),
                        tanggal_fix,
                        baris.get('Tn'),
                        baris.get('Tx'),
                        baris.get('Tavg'),
                        baris.get('RH_avg'),
                        baris.get('RR'),
                        baris.get('ss'),
                        baris.get('ff_x'),
                        baris.get('ddd_x'),
                        baris.get('ff_avg'),
                        baris.get('ddd_car')
                    ))
                    
                    baris_diimport += 1
                    total_data += 1
                    
                    if baris_diimport % 10000 == 0:
                        print(f"  Diproses: {baris_diimport:,} baris")
                        
                except Exception as e:
                    continue
            
            print(f"✅ {baris_diimport:,} observasi cuaca diimport")
    
    conn.commit()
    
    # Tampilkan ringkasan
    print("\n" + "=" * 50)
    print("RINGKASAN IMPORT:")
    print("=" * 50)
    
    tabel_tampil = ['provinsi', 'wilayah', 'stasiun', 'observasi_cuaca']
    for tabel in tabel_tampil:
        cur.execute(f"SELECT COUNT(*) FROM {tabel}")
        jumlah = cur.fetchone()[0]
        print(f"{tabel.upper():20} : {jumlah:>10,}")
    
    print("=" * 50)
    print(f"TOTAL DATA DIREKAM: {total_data:,}")
    print("=" * 50)
    
    cur.close()
    conn.close()
    print("\n✅ IMPORT SELESAI!")

if __name__ == "__main__":
    import_csv_sederhana()