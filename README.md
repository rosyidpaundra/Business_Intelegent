# WebGIS Business Intelligence — Kota Yogyakarta

## Struktur Proyek
```
webgis-bi/
├── backend/
│   ├── main.py          ← FastAPI app (semua endpoint)
│   └── requirements.txt
└── frontend/
    └── index.html       ← Single-file WebGIS BI app
```

## Prasyarat Database (PostGIS)

```sql
-- Tabel jalan (dari data OSM / database jalan Jogja)
CREATE TABLE roads (
    id       SERIAL PRIMARY KEY,
    name     TEXT,
    type     TEXT,       -- primary, secondary, residential, dst.
    oneway   BOOLEAN DEFAULT false,
    maxspeed INTEGER,
    geom     GEOMETRY(LineString, 4326)
);
CREATE INDEX ON roads USING GIST(geom);

-- Tabel POI bisnis
CREATE TABLE poi (
    id         SERIAL PRIMARY KEY,
    nama       TEXT NOT NULL,
    kategori   TEXT,
    alamat     TEXT,
    kecamatan  TEXT,
    metadata   JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    geom       GEOMETRY(Point, 4326)
);
CREATE INDEX ON poi USING GIST(geom);
```

## Menjalankan Backend

```bash
cd backend
pip install -r requirements.txt

# Salin dan isi environment
cp .env.example .env

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

File `.env`:
```
ORS_BASE_URL=http://localhost:8080/ors
ORS_API_KEY=
DB_HOST=localhost
DB_PORT=5432
DB_NAME=jogja_roads
DB_USER=postgres
DB_PASS=postgres
```

Jika menggunakan ORS cloud (openrouteservice.org):
```
ORS_BASE_URL=https://api.openrouteservice.org
ORS_API_KEY=<api_key_anda>
```

## Dokumentasi API Otomatis

Setelah server berjalan, buka:
- Swagger UI : http://localhost:8000/docs
- ReDoc      : http://localhost:8000/redoc

## Menjalankan Frontend

Buka `frontend/index.html` langsung di browser,
atau serve via HTTP (disarankan untuk CORS):

```bash
cd frontend
python -m http.server 3000
# buka http://localhost:3000
```

## Ringkasan Endpoint

| Method | Path | Fungsi |
|--------|------|--------|
| GET | /api/v1/geo/roads | Segmen jalan dalam bbox |
| GET | /api/v1/geo/isochrone | Area jangkauan dari titik |
| POST | /api/v1/geo/route | Rute A→B |
| POST | /api/v1/geo/matrix | Matriks jarak N titik |
| GET | /api/v1/geo/tiles/{z}/{x}/{y} | Vector tiles MVT |
| GET | /api/v1/business/poi | Daftar POI |
| POST | /api/v1/business/poi | Tambah POI |
| GET | /api/v1/business/poi/{id}/catchment | Catchment POI |
| GET | /api/v1/business/competitors | Kompetitor terdekat |
| GET | /api/v1/business/heatmap | Density heatmap |
| GET | /api/v1/analytics/accessibility | Skor aksesibilitas |
| GET | /api/v1/analytics/market-area | Market area POI |
| GET | /api/v1/analytics/demand-score | Demand score lokasi |
| POST | /api/v1/analytics/site-analysis | Analisis kelayakan lokasi |
| GET | /api/v1/analytics/gap-analysis | Temukan area gap |
| GET | /api/v1/report/dashboard | KPI dashboard |
| GET | /api/v1/report/summary | Ringkasan agregat |
| GET | /api/v1/report/export | Export GeoJSON / CSV |
| POST | /api/v1/report/compare | Bandingkan N POI |
