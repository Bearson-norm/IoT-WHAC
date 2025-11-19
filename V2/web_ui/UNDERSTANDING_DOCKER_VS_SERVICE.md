# Memahami Perbedaan Docker Container vs Windows Service

## 🔍 Mengapa PostgreSQL di Docker Masih Bisa Diakses?

### Penjelasan Singkat

**Docker container dan Windows Service adalah dua hal yang berbeda dan berjalan secara independen!**

## 📊 Perbedaan Docker Container vs Windows Service

### 1. PostgreSQL Lokal (Windows Service)

- **Cara berjalan**: Sebagai Windows Service
- **Service name**: `postgresql-x64-17`
- **Port**: 5432 (di host machine)
- **Data**: Disimpan di folder lokal Windows (misalnya `C:\Program Files\PostgreSQL\17\data`)
- **Control**: Dikontrol melalui Windows Services Manager
- **Status**: Sudah di-stop ✅

### 2. PostgreSQL di Docker Container

- **Cara berjalan**: Sebagai Docker container
- **Container name**: `whac-postgres`
- **Port**: 5432 (di-expose dari container ke host)
- **Data**: Disimpan di Docker volume (`postgres_data`)
- **Control**: Dikontrol melalui Docker commands
- **Status**: Masih berjalan ✅ (karena tidak terpengaruh oleh Windows Service)

## 🎯 Mengapa Ini Terjadi?

### Docker Container Berjalan Secara Terpisah

```
┌─────────────────────────────────────────┐
│         Windows Host Machine            │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  PostgreSQL Windows Service      │  │
│  │  (postgresql-x64-17)             │  │
│  │  Status: STOPPED ❌               │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  Docker Engine                   │  │
│  │  ┌────────────────────────────┐  │  │
│  │  │  Container: whac-postgres  │  │  │
│  │  │  PostgreSQL di dalam       │  │  │
│  │  │  Status: RUNNING ✅         │  │  │
│  │  └────────────────────────────┘  │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### Docker Menggunakan Containerization

1. **Isolated Environment**: Docker container berjalan di environment yang terisolasi
2. **Own Process Space**: Container memiliki process space sendiri
3. **Independent Lifecycle**: Container tidak tergantung pada Windows Services
4. **Port Mapping**: Docker mem-map port container ke host (`5432:5432`)

## ✅ Ini Adalah Perilaku yang Benar!

### Yang Seharusnya Terjadi:

1. ✅ **PostgreSQL lokal (Windows Service) di-stop** → Tidak bisa diakses
2. ✅ **PostgreSQL Docker container masih berjalan** → Masih bisa diakses
3. ✅ **DBeaver connect ke `localhost:5432`** → Sekarang hanya connect ke Docker

### Verifikasi

```powershell
# Cek Windows Service (harusnya STOPPED)
Get-Service -Name "postgresql-x64-17"

# Cek Docker Container (harusnya RUNNING)
docker ps | Select-String postgres

# Cek port 5432 (harusnya hanya 1 process - Docker)
netstat -ano | findstr :5432 | findstr LISTENING
```

## 🎯 Keuntungan Setelah Stop Service Lokal

### Sebelum Stop Service:
- Port 5432 digunakan oleh 2 proses:
  - PostgreSQL lokal (Windows Service)
  - PostgreSQL Docker container
- DBeaver mungkin connect ke database lokal (bukan Docker)
- Data tidak sinkron antara Web UI dan DBeaver

### Setelah Stop Service:
- Port 5432 hanya digunakan oleh Docker container
- DBeaver pasti connect ke database Docker
- Data sinkron antara Web UI dan DBeaver ✅

## 🔧 Cara Mengontrol Docker Container

### Stop Docker Container (jika perlu):
```powershell
cd web_ui
docker-compose stop postgres
# atau
docker stop whac-postgres
```

### Start Docker Container:
```powershell
cd web_ui
docker-compose start postgres
# atau
docker start whac-postgres
```

### Restart Docker Container:
```powershell
cd web_ui
docker-compose restart postgres
```

### Cek Status Docker Container:
```powershell
docker ps | Select-String postgres
```

## 💡 Kesimpulan

**Ini adalah perilaku yang benar dan diharapkan!**

- ✅ PostgreSQL lokal di-stop → Tidak mengganggu
- ✅ PostgreSQL Docker masih berjalan → Web UI tetap berfungsi
- ✅ DBeaver sekarang hanya connect ke Docker → Data sinkron

**Docker container tidak terpengaruh oleh Windows Service karena mereka adalah dua sistem yang berbeda dan berjalan secara independen.**

## 📋 Checklist

- [x] PostgreSQL lokal (Windows Service) sudah di-stop
- [x] Docker container masih berjalan
- [x] Port 5432 hanya digunakan oleh Docker
- [x] DBeaver connect ke database Docker
- [x] Data sinkron antara Web UI dan DBeaver

---

**Catatan**: Jika Anda ingin stop PostgreSQL Docker juga, gunakan:
```powershell
docker-compose stop postgres
```

Tapi ini akan membuat Web UI tidak bisa connect ke database!



