# Program Manajemen User Sensor AS608

Program untuk mengelola user yang tersimpan di sensor AS608 pada port `/dev/serial0` (ttySerial 0).

## Fitur

1. **Tampilkan Daftar User** - Melihat semua user yang tersimpan di sensor
2. **Daftarkan User Baru** - Mendaftarkan fingerprint baru ke sensor
3. **Hapus User** - Menghapus user dari sensor dan database
4. **Sinkronisasi Database** - Menyamakan database dengan data di sensor
5. **Hapus Semua User** - Menghapus semua user dari sensor dan database
6. **Informasi Sensor** - Menampilkan informasi detail sensor

## Instalasi

Pastikan library yang diperlukan sudah terinstall:

```bash
pip3 install adafruit-circuitpython-fingerprint pyserial
```

Atau install dari requirements.txt:
```bash
pip3 install -r requirements.txt
```

## Penggunaan

### Menjalankan Program

```bash
python3 manage_users_as608.py
```

Atau jika memerlukan akses root (untuk akses serial port):

```bash
sudo python3 manage_users_as608.py
```

### Menambahkan User ke Grup dialout (Linux)

Jika mendapat error "Permission denied", tambahkan user ke grup dialout:

```bash
sudo usermod -a -G dialout $USER
```

Setelah itu, logout dan login lagi, atau jalankan:
```bash
newgrp dialout
```

## Menu Program

### 1. Tampilkan Daftar User

Menampilkan semua user yang tersimpan di sensor dengan informasi:
- ID fingerprint
- Nama user
- Status (terdaftar di database atau belum)

### 2. Daftarkan User Baru

Proses pendaftaran user baru:
1. Pilih ID manual (opsional) atau gunakan ID otomatis
2. Masukkan nama user
3. Scan jari pertama
4. Angkat jari
5. Scan jari kedua (harus sama dengan yang pertama)
6. Model fingerprint dibuat dan disimpan

**Catatan:**
- ID harus antara 1-128
- Jika slot sudah terisi, akan ditanya apakah ingin menimpa
- Jika tidak menentukan ID, akan menggunakan slot kosong pertama

### 3. Hapus User

Menghapus user dari sensor dan database:
1. Tampilkan daftar user
2. Masukkan ID user yang akan dihapus
3. Konfirmasi penghapusan

### 4. Sinkronisasi Database

Menyamakan database dengan data di sensor:
- Menambahkan user yang ada di sensor tapi tidak di database
- Menghapus user yang tidak ada di sensor tapi ada di database

### 5. Hapus Semua User

**PERINGATAN:** Operasi ini akan menghapus SEMUA user dari sensor dan database!

Untuk konfirmasi, ketik `HAPUS SEMUA` (huruf besar).

### 6. Informasi Sensor

Menampilkan informasi detail sensor:
- Jumlah template tersimpan
- Kapasitas maksimal
- Security level
- System ID
- Device address
- Packet size
- Baud rate

## Database

Program menggunakan database SQLite (`fingerprints_multi.db`) untuk menyimpan informasi user:
- `fingerprint_id` - ID fingerprint di sensor (1-128)
- `user_name` - Nama user
- `device_id` - ID device (default: AS608_001)
- `created_at` - Waktu pembuatan
- `updated_at` - Waktu update terakhir

## Troubleshooting

### Port tidak ditemukan

Jika mendapat error "Port /dev/serial0 tidak ditemukan":

1. Cek apakah port ada:
   ```bash
   ls -l /dev/serial0
   ```

2. Cek port serial yang tersedia:
   ```bash
   ls -l /dev/tty*
   ```

3. Jika menggunakan Raspberry Pi, pastikan UART diaktifkan di `/boot/config.txt`:
   ```
   enable_uart=1
   ```

### Sensor tidak merespon

1. Pastikan koneksi hardware benar
2. Cek baud rate (default: 57600)
3. Coba restart sensor
4. Cek apakah port digunakan program lain:
   ```bash
   lsof /dev/serial0
   ```

### Permission denied

1. Tambahkan user ke grup dialout:
   ```bash
   sudo usermod -a -G dialout $USER
   ```

2. Atau jalankan dengan sudo:
   ```bash
   sudo python3 manage_users_as608.py
   ```

## Contoh Output

```
======================================================================
PROGRAM MANAJEMEN USER SENSOR AS608
Port: /dev/serial0 (ttySerial 0)
======================================================================
🔌 Menghubungkan ke sensor AS608 pada /dev/serial0 (percobaan 1/3)...
✅ Sensor terhubung! Template tersimpan: 5

📊 Informasi Sensor:
   Template tersimpan: 5
   Kapasitas maksimal: 256
   Security level: 3

======================================================================
MENU UTAMA
======================================================================
1. Tampilkan daftar user
2. Daftarkan user baru
3. Hapus user
4. Sinkronisasi database dengan sensor
5. Hapus semua user
6. Informasi sensor
7. Keluar
======================================================================

Pilih opsi (1-7):
```

## Catatan Penting

1. **Backup Data**: Sebelum menghapus semua user, pastikan sudah melakukan backup
2. **ID Unik**: Setiap fingerprint ID harus unik (1-128)
3. **Kualitas Fingerprint**: Pastikan jari bersih dan kering saat enrollment
4. **Konsistensi**: Gunakan jari yang sama untuk kedua scan saat enrollment

## File Terkait

- `fingerprint_multi_client.py` - Client MQTT untuk multi-sensor
- `fingerprint_manager.py` - Program backup/restore fingerprint
- `config.py` - File konfigurasi

