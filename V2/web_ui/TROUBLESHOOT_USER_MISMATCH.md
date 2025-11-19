# Troubleshooting: Data User Tidak Matching antara Web UI dan Database

## 🔍 Masalah

Data yang ditampilkan di Web UI User Management tidak sesuai dengan data di tabel `web_users` di database.

## 📋 Langkah-langkah Debug

### 1. Verifikasi Data di Database

Jalankan query berikut di DBeaver atau terminal:

```sql
SELECT id, username, full_name, email, role, is_active, created_at, last_login 
FROM web_users 
ORDER BY created_at DESC;
```

Atau gunakan script Python:

```bash
cd web_ui/
python debug_user_mismatch.py
```

### 2. Test API Endpoint

Buka browser dan akses (setelah login sebagai admin):
```
http://localhost:5000/api/admin/web_users
```

Atau gunakan script:

```bash
cd web_ui/
python test_api_users.py
```

**Yang harus dicek:**
- Apakah jumlah user sama?
- Apakah semua user muncul?
- Apakah data setiap user sama?

### 3. Cek Browser Console

1. Buka Web UI di browser
2. Tekan **F12** untuk membuka Developer Tools
3. Buka tab **Console**
4. Refresh halaman Admin
5. Cari error atau warning yang terkait dengan `loadWebUsers`

**Error yang mungkin muncul:**
- `HTTP error! status: 403` - Tidak punya akses admin
- `HTTP error! status: 500` - Error di server
- `API returned invalid data format` - Response tidak valid
- `User at index X missing required fields` - Data user tidak lengkap

### 4. Cek Network Tab

1. Di Developer Tools, buka tab **Network**
2. Refresh halaman Admin
3. Cari request ke `/api/admin/web_users`
4. Klik request tersebut
5. Cek:
   - **Status Code** (harus 200)
   - **Response** (data JSON yang dikembalikan)
   - **Headers** (apakah ada error)

### 5. Cek Log Flask App

Jika menggunakan Docker:

```bash
docker logs whac-web-ui --tail 100
```

Atau jika running lokal, cek terminal tempat Flask app berjalan.

## 🔧 Solusi Umum

### Solusi 1: Clear Browser Cache

1. Tekan **Ctrl+Shift+Delete** (Windows/Linux) atau **Cmd+Shift+Delete** (Mac)
2. Pilih "Cached images and files"
3. Klik "Clear data"
4. Refresh halaman dengan **Ctrl+F5** (hard refresh)

### Solusi 2: Restart Flask App

Jika menggunakan Docker:

```bash
cd web_ui/
docker-compose restart web-ui
```

Jika running lokal, restart aplikasi Flask.

### Solusi 3: Verifikasi Koneksi Database

Pastikan Web UI menggunakan database yang sama:

1. Cek file `.env` di folder `web_ui/`:
   ```env
   DB_HOST=postgres
   DB_NAME=whac_master
   DB_USER=postgres
   DB_PASSWORD=Admin123
   DB_PORT=5432
   ```

2. Pastikan nilai ini sama dengan database yang Anda akses di DBeaver

### Solusi 4: Cek Session/Login

Pastikan Anda login sebagai **admin**:

1. Logout dari Web UI
2. Login kembali dengan user yang memiliki role `admin`
3. Cek apakah user yang login punya akses ke `/admin`

### Solusi 5: Cek Error di Frontend

Jika ada error di console browser:

1. Buka Developer Tools (F12)
2. Tab Console
3. Cari error yang terkait dengan:
   - `loadWebUsers`
   - `webUsersTable`
   - `fetch('/api/admin/web_users')`

## 🐛 Masalah yang Ditemukan dan Perbaikan

### Perbaikan yang Sudah Dilakukan

1. **Error Handling yang Lebih Baik**
   - Menambahkan validasi data user
   - Menampilkan error yang lebih jelas
   - Skip user yang tidak valid (tidak crash seluruh tabel)

2. **Logging untuk Debug**
   - Console log jumlah user yang diterima
   - Console log setiap user yang di-render
   - Warning untuk user yang tidak valid

3. **XSS Protection**
   - Escape username di onclick handler
   - Mencegah injection melalui username

4. **Format Date yang Lebih Aman**
   - Try-catch untuk parsing date
   - Fallback ke 'Never' jika date tidak valid

## 📊 Script Debug

### Script 1: debug_user_mismatch.py

Membandingkan data langsung dari database dengan apa yang seharusnya dikembalikan API.

```bash
cd web_ui/
python debug_user_mismatch.py
```

### Script 2: test_api_users.py

Test API endpoint dan bandingkan dengan database (memerlukan authentication).

```bash
cd web_ui/
python test_api_users.py
```

## 🔍 Checklist Debugging

- [ ] Data di database sudah dicek (5 user: admin, User, Mamat, Greyoungter, Ramadhan)
- [ ] API endpoint `/api/admin/web_users` sudah di-test
- [ ] Browser console sudah dicek untuk error
- [ ] Network tab sudah dicek untuk response API
- [ ] Browser cache sudah di-clear
- [ ] Flask app sudah di-restart
- [ ] Login sebagai admin sudah diverifikasi
- [ ] Koneksi database sudah diverifikasi (sama dengan DBeaver)

## 💡 Tips

1. **Gunakan Incognito/Private Mode**
   - Buka browser dalam mode incognito
   - Login sebagai admin
   - Cek apakah masalah masih ada
   - Ini membantu mengeliminasi masalah cache

2. **Test di Browser Lain**
   - Coba akses dari browser yang berbeda
   - Ini membantu mengeliminasi masalah browser-specific

3. **Cek Database Connection Pool**
   - Jika menggunakan connection pooling, mungkin ada stale connection
   - Restart aplikasi untuk reset connection pool

4. **Cek Transaction Isolation**
   - Pastikan tidak ada transaction yang belum commit
   - Cek apakah ada lock di database

## 📞 Jika Masalah Masih Berlanjut

Jika setelah melakukan semua langkah di atas masalah masih ada:

1. **Kumpulkan informasi:**
   - Screenshot dari Web UI
   - Screenshot dari DBeaver (query result)
   - Screenshot dari browser console (error)
   - Screenshot dari Network tab (API response)
   - Log dari Flask app

2. **Test dengan script:**
   ```bash
   python debug_user_mismatch.py
   python test_api_users.py
   ```

3. **Cek apakah ada perubahan di database:**
   - Apakah ada trigger yang mengubah data?
   - Apakah ada view yang digunakan?
   - Apakah ada permission issue?

---

**Terakhir diupdate:** Setelah perbaikan error handling di frontend



