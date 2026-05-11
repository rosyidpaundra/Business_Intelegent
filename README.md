# WebGIS Business Intelligence — Kota Yogyakarta

Aplikasi WebGIS berbasis lokasi untuk analisis bisnis di Kota Yogyakarta. Menggabungkan peta interaktif, isochrone area jangkauan, analisis lokasi usaha, dan dashboard KPI dalam satu platform.

**Demo live:** https://business-intelegent.vercel.app  
**Backend API:** https://businessintelegent-production.up.railway.app/docs

---

## Arsitektur Deployment

```
Browser (Vercel)
    │
    ├── Frontend: HTML/CSS/JS statis
    │   └── Vercel (CDN global, gratis)
    │
    └── Backend: FastAPI Python
        └── Railway (Web Service, gratis $5/bulan)
            │
            ├── Database: PostgreSQL + PostGIS
            │   └── Supabase (500MB gratis)
            │
            └── Routing & Isochrone
                └── OpenRouteService API (gratis)
```

---

## Stack Teknologi

| Komponen | Teknologi | Platform |
|----------|-----------|----------|
| Frontend | HTML, CSS, JavaScript | Vercel |
| Peta | Leaflet.js 1.9.4 | CDN |
| Heatmap | Leaflet.heat | CDN |
| Chart | Chart.js 4.4.2 | CDN |
| Backend | FastAPI + Python 3.11 | Railway |
| Database | PostgreSQL 15 + PostGIS | Supabase |
| Routing | OpenRouteService API | Cloud |
| Repo | Git | GitHub |

---

## Struktur Repository

```
Business_Intelegent/
├── backend/
│   ├── main.py              # FastAPI app — semua endpoint API
│   ├── requirements.txt     # Python dependencies
│   ├── Procfile             # Konfigurasi start command Railway
│   └── runtime.txt          # Versi Python (3.11.0)
├── frontend/
│   └── index.html           # Single-file WebGIS app
├── .gitignore
└── README.md
```

---

## Endpoint API

### Geo
| Method | Endpoint | Fungsi |
|--------|----------|--------|
| GET | `/api/v1/geo/roads` | Segmen jalan dalam bbox |
| GET | `/api/v1/geo/isochrone` | Area jangkauan dari titik |
| POST | `/api/v1/geo/route` | Rute A→B |
| POST | `/api/v1/geo/matrix` | Matriks jarak N titik |
| GET | `/api/v1/geo/tiles/{z}/{x}/{y}` | Vector tiles MVT |

### Business
| Method | Endpoint | Fungsi |
|--------|----------|--------|
| GET | `/api/v1/business/poi` | Daftar POI |
| POST | `/api/v1/business/poi` | Tambah POI |
| GET | `/api/v1/business/poi/{id}` | Detail POI |
| GET | `/api/v1/business/poi/{id}/catchment` | Catchment area |
| GET | `/api/v1/business/competitors` | Kompetitor terdekat |
| GET | `/api/v1/business/heatmap` | Density heatmap |

### Analytics
| Method | Endpoint | Fungsi |
|--------|----------|--------|
| GET | `/api/v1/analytics/accessibility` | Skor aksesibilitas |
| GET | `/api/v1/analytics/market-area` | Market area POI |
| GET | `/api/v1/analytics/demand-score` | Demand score lokasi |
| POST | `/api/v1/analytics/site-analysis` | Analisis kelayakan lokasi |
| GET | `/api/v1/analytics/gap-analysis` | Temukan area gap |

### Report
| Method | Endpoint | Fungsi |
|--------|----------|--------|
| GET | `/api/v1/report/dashboard` | KPI dashboard |
| GET | `/api/v1/report/summary` | Ringkasan agregat |
| GET | `/api/v1/report/export` | Export GeoJSON / CSV |
| POST | `/api/v1/report/compare` | Bandingkan N POI |

---

## Setup Lokal

### Prasyarat
- Python 3.11
- PostgreSQL + PostGIS
- Git

### Langkah

**1. Clone repo**
```bash
git clone https://github.com/rosyidpaundra/Business_Intelegent.git
cd Business_Intelegent
```

**2. Setup backend**
```bash
cd backend
python -m venv venv311
venv311\Scripts\activate        # Windows
pip install -r requirements.txt
```

**3. Buat file `.env` di folder `backend/`**
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=nama_database
DB_USER=postgres
DB_PASS=password_postgres
ORS_BASE_URL=https://api.openrouteservice.org
ORS_API_KEY=api_key_ors
```

**4. Buat database dan tabel**
```sql
CREATE DATABASE nama_database;
\c nama_database
CREATE EXTENSION postgis;

CREATE TABLE roads (
    id SERIAL PRIMARY KEY, name TEXT, type TEXT,
    oneway BOOLEAN DEFAULT false, maxspeed INTEGER,
    geom GEOMETRY(LineString, 4326));
CREATE INDEX ON roads USING GIST(geom);

CREATE TABLE poi (
    id SERIAL PRIMARY KEY, nama TEXT NOT NULL,
    kategori TEXT, alamat TEXT, kecamatan TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    geom GEOMETRY(Point, 4326));
CREATE INDEX ON poi USING GIST(geom);
```

**5. Jalankan backend**
```bash
uvicorn main:app --reload --port 8001
# Swagger: http://localhost:8001/docs
```

**6. Jalankan frontend**
```bash
cd ../frontend
python -m http.server 3000
# Buka: http://localhost:3000
```

---

## Deployment

### Database — Supabase

1. Daftar di [supabase.com](https://supabase.com) pakai GitHub (gratis)
2. New Project → Region: Southeast Asia
3. SQL Editor → aktifkan PostGIS:
   ```sql
   CREATE EXTENSION IF NOT EXISTS postgis;
   ```
4. Buat tabel `roads` dan `poi` (SQL di atas)
5. Catat credentials dari Settings → Database → Connection Pooling:
   ```
   Host : aws-1-ap-northeast-2.pooler.supabase.com
   Port : 6543
   User : postgres.PROJECT_ID
   ```

> **Catatan:** Gunakan Transaction Pooler (port 6543), bukan Direct Connection (port 5432), karena Railway menggunakan IPv4 sedangkan Direct Connection Supabase hanya IPv6.

---

### Backend — Railway

1. Daftar di [railway.app](https://railway.app) pakai GitHub (gratis $5/bulan)
2. New Project → Deploy from GitHub repo → pilih `Business_Intelegent`
3. Settings:
   ```
   Root Directory : backend
   Start Command  : uvicorn main:app --host 0.0.0.0 --port $PORT
   ```
4. Variables → tambahkan:
   ```
   DB_HOST      = aws-1-ap-northeast-2.pooler.supabase.com
   DB_PORT      = 6543
   DB_NAME      = postgres
   DB_USER      = postgres.PROJECT_ID
   DB_PASS      = password_supabase
   ORS_BASE_URL = https://api.openrouteservice.org
   ORS_API_KEY  = api_key_ors
   ```
5. Railway otomatis deploy setiap push ke branch `main`

---

### Frontend — Vercel

1. Daftar di [vercel.com](https://vercel.com) pakai GitHub (gratis)
2. New Project → Import repo `Business_Intelegent`
3. Configure Project:
   ```
   Root Directory : frontend
   ```
4. Deploy → dapat URL: `https://business-intelegent.vercel.app`
5. Vercel otomatis rebuild setiap push ke branch `main`

---

## Update & Deploy Ulang

Setiap perubahan kode cukup push ke GitHub:

```bash
git add .
git commit -m "deskripsi perubahan"
git push
```

- **Railway** otomatis rebuild backend dalam ~2 menit
- **Vercel** otomatis rebuild frontend dalam ~1 menit

---

## Catatan Penting

| Hal | Keterangan |
|-----|------------|
| Supabase free tier | Database dihapus jika tidak aktif 90 hari — login rutin ke dashboard |
| Railway free tier | $5 credit/bulan, cukup untuk ~500 jam runtime |
| Railway sleep | Service tidak sleep (berbeda dengan Render free tier) |
| ORS API | Gratis dengan rate limit — daftar di openrouteservice.org |
| `.env` | Jangan pernah commit file `.env` ke GitHub |


