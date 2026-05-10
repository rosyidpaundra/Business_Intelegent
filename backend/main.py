"""
WebGIS Business Intelligence - Kota Yogyakarta
Backend API menggunakan FastAPI
Menggabungkan ORS API, Isochrone, dan Database Jalan Jogja
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import httpx
import psycopg2
import psycopg2.extras
from typing import Optional
import json
import os
from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path(__file__).parent / ".env")
# ─────────────────────────────────────────
# Konfigurasi
# ─────────────────────────────────────────
ORS_BASE_URL  = os.getenv("ORS_BASE_URL", "http://localhost:8080/ors")
ORS_API_KEY   = ORS_API_KEY = os.getenv("ORS_API_KEY")
DB_HOST       = os.getenv("DB_HOST", "localhost")
DB_PORT       = os.getenv("DB_PORT", "5432")
DB_NAME       = os.getenv("DB_NAME", "webgis")
DB_USER       = os.getenv("DB_USER", "postgres")
DB_PASS       = os.getenv("DB_PASS", "Sukses789")

app = FastAPI(
    title="WebGIS BI Jogja",
    description="API analitik bisnis berbasis lokasi untuk Kota Yogyakarta",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# ─────────────────────────────────────────
# Koneksi Database
# ─────────────────────────────────────────
def get_db():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASS
    )

def build_ors_headers():
    h = {"Content-Type": "application/json", "Accept": "application/geo+json"}
    if ORS_API_KEY:
        h["Authorization"] = ORS_API_KEY
    return h


# ─────────────────────────────────────────
# Models
# ─────────────────────────────────────────
class RouteRequest(BaseModel):
    start: list[float]          # [lng, lat]
    end:   list[float]          # [lng, lat]
    profile: str = "driving-car"

class MatrixRequest(BaseModel):
    locations: list[list[float]] # [[lng,lat], ...]
    profile: str = "driving-car"

class POI(BaseModel):
    nama:      str
    kategori:  str
    lat:       float
    lng:       float
    alamat:    Optional[str] = None
    metadata:  Optional[dict] = {}

class SiteAnalysisRequest(BaseModel):
    lat:       float
    lng:       float
    kategori:  str
    radius_menit: int = 10
    profile:   str = "driving-car"

class CompareRequest(BaseModel):
    poi_ids: list[int]


# ═══════════════════════════════════════════
# 1. ENDPOINT /geo — Geospasial & Jaringan
# ═══════════════════════════════════════════

@app.get("/api/v1/geo/roads", tags=["Geo"])
async def get_roads(
    bbox: str = Query(..., description="minLng,minLat,maxLng,maxLat — contoh: 110.34,-7.84,110.43,-7.75")
):
    """
    Ambil segmen jalan dalam bounding box dari database Jogja.
    Kembalikan GeoJSON FeatureCollection.
    """
    try:
        coords = [float(c) for c in bbox.split(",")]
        minx, miny, maxx, maxy = coords
    except Exception:
        raise HTTPException(400, "Format bbox salah. Gunakan: minLng,minLat,maxLng,maxLat")

    conn = get_db()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT id, name, type, oneway, maxspeed,
               ST_AsGeoJSON(geom)::json AS geometry
        FROM roads
        WHERE geom && ST_MakeEnvelope(%s,%s,%s,%s, 4326)
        LIMIT 5000
    """, (minx, miny, maxx, maxy))
    rows = cur.fetchall()
    cur.close(); conn.close()

    features = [
        {"type": "Feature", "geometry": r["geometry"],
         "properties": {k: v for k, v in r.items() if k != "geometry"}}
        for r in rows
    ]
    return {"type": "FeatureCollection", "features": features}


@app.get("/api/v1/geo/isochrone", tags=["Geo"])
async def get_isochrone(
    lng:    float = Query(...),
    lat:    float = Query(...),
    range_menit: int = Query(10, ge=1, le=60),
    profile: str = Query("driving-car",
                         description="driving-car | cycling-regular | foot-walking")
):
    """
    Hitung isochrone (area jangkauan) dari satu titik koordinat.
    Memanggil ORS Isochrones API → kembalikan GeoJSON Polygon.
    """
    payload = {
        "locations": [[lng, lat]],
        "range":     [range_menit * 60],   # ORS menerima detik
        "range_type": "time",
        "attributes": ["area", "reachfactor"],
        "smoothing": 0.5
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{ORS_BASE_URL}/v2/isochrones/{profile}",
            headers=build_ors_headers(),
            json=payload
        )
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, f"ORS error: {resp.text}")
    return resp.json()


@app.post("/api/v1/geo/route", tags=["Geo"])
async def post_route(body: RouteRequest):
    """
    Hitung rute terpendek / tercepat antara dua titik.
    Mengembalikan GeoJSON LineString + durasi + jarak.
    """
    payload = {
        "coordinates": [body.start, body.end],
        "format": "geojson"
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{ORS_BASE_URL}/v2/directions/{body.profile}/geojson",
            headers=build_ors_headers(),
            json=payload
        )
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, f"ORS error: {resp.text}")
    return resp.json()


@app.post("/api/v1/geo/matrix", tags=["Geo"])
async def post_matrix(body: MatrixRequest):
    """
    Hitung matriks jarak / durasi antar N titik.
    Berguna untuk analisis aksesibilitas multi-titik.
    """
    if len(body.locations) > 50:
        raise HTTPException(400, "Maksimal 50 lokasi per request")
    payload = {
        "locations": body.locations,
        "metrics":   ["duration", "distance"],
        "units":     "km"
    }
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{ORS_BASE_URL}/v2/matrix/{body.profile}",
            headers=build_ors_headers(),
            json=payload
        )
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, f"ORS error: {resp.text}")
    return resp.json()


@app.get("/api/v1/geo/tiles/{z}/{x}/{y}", tags=["Geo"])
async def get_vector_tile(z: int, x: int, y: int):
    """
    Sajikan vector tile (MVT) segmen jalan dari PostGIS.
    Endpoint ini dikonsumsi langsung oleh Leaflet / MapLibre.
    """
    conn = get_db()
    cur  = conn.cursor()
    cur.execute("""
        WITH bounds AS (
            SELECT ST_TileEnvelope(%s, %s, %s) AS geom
        )
        SELECT ST_AsMVT(tile, 'roads', 4096, 'geom') FROM (
            SELECT id, name, type,
                   ST_AsMVTGeom(r.geom, bounds.geom, 4096, 64, true) AS geom
            FROM roads r, bounds
            WHERE r.geom && bounds.geom
        ) tile
    """, (z, x, y))
    tile_data = cur.fetchone()[0]
    cur.close(); conn.close()
    from fastapi.responses import Response
    return Response(content=bytes(tile_data), media_type="application/x-protobuf")


# ═══════════════════════════════════════════
# 2. ENDPOINT /business — Data POI & Usaha
# ═══════════════════════════════════════════

@app.get("/api/v1/business/poi", tags=["Business"])
async def get_poi(
    kategori: Optional[str]  = None,
    bbox:     Optional[str]  = None,
    limit:    int            = Query(200, le=1000)
):
    """
    Daftar POI / titik usaha.
    Filter opsional: kategori dan bounding box.
    """
    conn = get_db()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    where_clauses = []
    params = []

    if kategori:
        where_clauses.append("kategori = %s")
        params.append(kategori)

    if bbox:
        coords = [float(c) for c in bbox.split(",")]
        where_clauses.append(
            "geom && ST_MakeEnvelope(%s,%s,%s,%s, 4326)"
        )
        params.extend(coords)

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
    params.append(limit)

    cur.execute(f"""
        SELECT id, nama, kategori, alamat, metadata,
               ST_X(geom) AS lng, ST_Y(geom) AS lat
        FROM poi {where_sql}
        LIMIT %s
    """, params)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows


@app.post("/api/v1/business/poi", tags=["Business"], status_code=201)
async def create_poi(poi: POI):
    """Tambah titik usaha baru ke database."""
    conn = get_db()
    cur  = conn.cursor()
    cur.execute("""
        INSERT INTO poi (nama, kategori, alamat, metadata, geom)
        VALUES (%s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s,%s), 4326))
        RETURNING id
    """, (poi.nama, poi.kategori, poi.alamat,
          json.dumps(poi.metadata), poi.lng, poi.lat))
    new_id = cur.fetchone()[0]
    conn.commit(); cur.close(); conn.close()
    return {"id": new_id, "message": "POI berhasil ditambahkan"}


@app.get("/api/v1/business/poi/{poi_id}/catchment", tags=["Business"])
async def get_poi_catchment(
    poi_id:       int,
    radius_menit: int  = Query(10, ge=1, le=60),
    profile:      str  = Query("driving-car")
):
    """
    Hitung catchment area (isochrone) untuk satu POI.
    Sekaligus hitung jumlah kompetitor dan POI lain yang masuk ke area tersebut.
    """
    conn = get_db()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT ST_X(geom) AS lng, ST_Y(geom) AS lat, kategori FROM poi WHERE id=%s", (poi_id,))
    poi = cur.fetchone()
    if not poi:
        cur.close(); conn.close()
        raise HTTPException(404, "POI tidak ditemukan")

    # Ambil isochrone
    iso_resp = await get_isochrone(poi["lng"], poi["lat"], radius_menit, profile)
    iso_geom = json.dumps(iso_resp["features"][0]["geometry"])

    # Hitung kompetitor dalam area
    cur.execute("""
        SELECT COUNT(*) AS total_kompetitor
        FROM poi
        WHERE kategori = %s AND id != %s
          AND ST_Within(geom, ST_GeomFromGeoJSON(%s))
    """, (poi["kategori"], poi_id, iso_geom))
    kompetitor = cur.fetchone()["total_kompetitor"]

    # Panjang jalan dalam catchment (km)
    cur.execute("""
        SELECT COALESCE(ROUND(SUM(ST_Length(geom::geography))/1000, 2), 0) AS panjang_jalan_km
        FROM roads
        WHERE ST_Intersects(geom, ST_GeomFromGeoJSON(%s))
    """, (iso_geom,))
    panjang_jalan = cur.fetchone()["panjang_jalan_km"]

    cur.close(); conn.close()
    return {
        "poi_id":          poi_id,
        "radius_menit":    radius_menit,
        "isochrone":       iso_resp,
        "kompetitor":      kompetitor,
        "panjang_jalan_km": float(panjang_jalan)
    }


@app.get("/api/v1/business/competitors", tags=["Business"])
async def get_competitors(
    lat:       float,
    lng:       float,
    kategori:  str,
    radius_km: float = Query(1.0, ge=0.1, le=20)
):
    """Cari kompetitor dalam radius tertentu dari suatu titik."""
    conn = get_db()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT id, nama, alamat,
               ST_X(geom) AS lng, ST_Y(geom) AS lat,
               ROUND(ST_Distance(geom::geography,
                     ST_SetSRID(ST_MakePoint(%s,%s),4326)::geography)/1000, 3) AS jarak_km
        FROM poi
        WHERE kategori = %s
          AND ST_DWithin(geom::geography,
              ST_SetSRID(ST_MakePoint(%s,%s),4326)::geography,
              %s * 1000)
        ORDER BY jarak_km
    """, (lng, lat, kategori, lng, lat, radius_km))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return {"total": len(rows), "items": rows}


@app.get("/api/v1/business/heatmap", tags=["Business"])
async def get_heatmap(
    kategori:  Optional[str] = None,
    resolution: int = Query(8, description="H3 resolution 6-10")
):
    """
    Kembalikan GeoJSON point density untuk heat layer di peta.
    Setiap titik memiliki properti 'weight' = jumlah POI di sel H3.
    """
    conn = get_db()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    where = "WHERE kategori = %s" if kategori else ""
    params = (kategori,) if kategori else ()
    cur.execute(f"""
        SELECT ST_X(geom) AS lng, ST_Y(geom) AS lat, COUNT(*) AS weight
        FROM poi {where}
        GROUP BY
            ROUND(ST_X(geom)::numeric, {11 - resolution}),
            ROUND(ST_Y(geom)::numeric, {11 - resolution}),
            ST_X(geom), ST_Y(geom)
        ORDER BY weight DESC
        LIMIT 2000
    """, params)
    rows = cur.fetchall()
    cur.close(); conn.close()

    features = [
        {"type": "Feature",
         "geometry": {"type": "Point", "coordinates": [r["lng"], r["lat"]]},
         "properties": {"weight": r["weight"]}}
        for r in rows
    ]
    return {"type": "FeatureCollection", "features": features}


# ═══════════════════════════════════════════
# 3. ENDPOINT /analytics — BI Spasial
# ═══════════════════════════════════════════

@app.get("/api/v1/analytics/accessibility", tags=["Analytics"])
async def get_accessibility(
    lat:     float,
    lng:     float,
    profile: str = "driving-car"
):
    """
    Nilai aksesibilitas suatu titik: berapa banyak jalan yang terhubung,
    panjang total jalan dalam radius 500 m, dan node intersection terdekat.
    """
    conn = get_db()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT
            COUNT(*)                                              AS jumlah_segmen,
            ROUND(CAST(SUM(ST_Length(geom::geography))/1000 AS numeric), 3)     AS total_km,
            COUNT(DISTINCT type)                                  AS tipe_jalan
        FROM roads
        WHERE ST_DWithin(geom::geography,
              ST_SetSRID(ST_MakePoint(%s,%s),4326)::geography, 500)
    """, (lng, lat))
    road_stats = cur.fetchone()
    cur.close(); conn.close()

    # Skor 0-100 sederhana berbasis panjang jalan
    skor = min(100, int((road_stats["total_km"] or 0) / 5 * 100))

    return {
        "koordinat":      {"lat": lat, "lng": lng},
        "radius_meter":   500,
        **road_stats,
        "skor_aksesibilitas": skor,
        "interpretasi":   "Tinggi" if skor >= 70 else ("Sedang" if skor >= 40 else "Rendah")
    }


@app.get("/api/v1/analytics/market-area", tags=["Analytics"])
async def get_market_area(
    poi_id: int,
    profile: str = "driving-car",
    range_menit: int = Query(15, ge=5, le=60)
):
    """
    Hitung market area (isochrone) dan statistik demografis / kompetisi
    untuk sebuah POI.
    """
    conn = get_db()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT ST_X(geom) AS lng, ST_Y(geom) AS lat, kategori FROM poi WHERE id=%s", (poi_id,))
    poi = cur.fetchone()
    if not poi:
        cur.close(); conn.close()
        raise HTTPException(404, "POI tidak ditemukan")

    iso = await get_isochrone(poi["lng"], poi["lat"], range_menit, profile)
    iso_geom = json.dumps(iso["features"][0]["geometry"])

    cur.execute("""
        SELECT COUNT(*) AS total_kompetitor
        FROM poi
        WHERE kategori = %s AND id != %s
          AND ST_Within(geom, ST_GeomFromGeoJSON(%s))
    """, (poi["kategori"], poi_id, iso_geom))
    n_kompetitor = cur.fetchone()["total_kompetitor"]

    area_km2 = iso["features"][0]["properties"].get("area", 0) / 1_000_000

    cur.close(); conn.close()
    return {
        "poi_id":         poi_id,
        "range_menit":    range_menit,
        "market_area_km2": round(area_km2, 3),
        "total_kompetitor": n_kompetitor,
        "isochrone":      iso
    }


@app.get("/api/v1/analytics/demand-score", tags=["Analytics"])
async def get_demand_score(
    lat:      float,
    lng:      float,
    kategori: str,
    radius_menit: int = Query(10, ge=1, le=30)
):
    """
    Hitung demand score (0-100) berbasis:
    - Aksesibilitas jalan
    - Kepadatan POI serupa (saturasi)
    - Ukuran catchment area
    """
    iso = await get_isochrone(lng, lat, radius_menit, "driving-car")
    iso_geom = json.dumps(iso["features"][0]["geometry"])
    area_km2  = iso["features"][0]["properties"].get("area", 0) / 1_000_000

    conn = get_db()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Kepadatan kompetitor
    cur.execute("""
        SELECT COUNT(*) AS n FROM poi
        WHERE kategori = %s
          AND ST_Within(geom, ST_GeomFromGeoJSON(%s))
    """, (kategori, iso_geom))
    n_kompetitor = cur.fetchone()["n"]

    # Panjang jalan
    cur.execute("""
        SELECT COALESCE(SUM(ST_Length(geom::geography))/1000, 0) AS km
        FROM roads WHERE ST_Intersects(geom, ST_GeomFromGeoJSON(%s))
    """, (iso_geom,))
    km_jalan = float(cur.fetchone()["km"])

    cur.close(); conn.close()

    skor_akses    = min(40, km_jalan * 4)
    skor_area     = min(30, area_km2 * 10)
    skor_saturasi = max(0, 30 - n_kompetitor * 5)   # makin banyak kompetitor, makin rendah
    total         = round(skor_akses + skor_area + skor_saturasi)

    return {
        "koordinat":        {"lat": lat, "lng": lng},
        "demand_score":     total,
        "komponen": {
            "aksesibilitas":   round(skor_akses),
            "luas_catchment":  round(skor_area),
            "saturasi_pasar":  round(skor_saturasi),
        },
        "rekomendasi": "Sangat Potensial" if total >= 70
                       else ("Potensial" if total >= 50 else "Kurang Disarankan")
    }


@app.post("/api/v1/analytics/site-analysis", tags=["Analytics"])
async def post_site_analysis(body: SiteAnalysisRequest):
    """
    Analisis lengkap kelayakan lokasi bisnis baru.
    Menggabungkan aksesibilitas + market area + demand score.
    """
    aksesibilitas = await get_accessibility(body.lat, body.lng, body.profile)
    demand        = await get_demand_score(body.lat, body.lng, body.kategori, body.radius_menit)

    return {
        "kandidat":        {"lat": body.lat, "lng": body.lng},
        "kategori":        body.kategori,
        "aksesibilitas":   aksesibilitas,
        "demand":          demand,
        "skor_total":      round(
            aksesibilitas["skor_aksesibilitas"] * 0.4 + demand["demand_score"] * 0.6
        ),
        "rekomendasi":     demand["rekomendasi"]
    }


@app.get("/api/v1/analytics/gap-analysis", tags=["Analytics"])
async def get_gap_analysis(
    kategori:    str,
    grid_size:   float = Query(0.01, description="Ukuran grid derajat (≈1 km = 0.009)")
):
    """
    Temukan area di Jogja yang kekurangan POI kategori tertentu
    (gap pada grid kota). Kembalikan titik-titik berpotensi.
    """
    conn = get_db()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Bounding box Kota Yogyakarta
    MINX, MINY, MAXX, MAXY = 110.34, -7.84, 110.43, -7.76

    cur.execute("""
        WITH grid AS (
            SELECT
                ST_Centroid(cell) AS geom,
                ST_X(ST_Centroid(cell)) AS lng,
                ST_Y(ST_Centroid(cell)) AS lat
            FROM (
                SELECT (ST_SquareGrid(%s,
                    ST_MakeEnvelope(%s,%s,%s,%s,4326))).geom AS cell
            ) g
        ),
        existing AS (
            SELECT geom FROM poi WHERE kategori = %s
        )
        SELECT grid.lng, grid.lat
        FROM grid
        WHERE NOT EXISTS (
            SELECT 1 FROM existing
            WHERE ST_DWithin(existing.geom::geography,
                             grid.geom::geography, %s * 111000)
        )
        LIMIT 100
    """, (grid_size, MINX, MINY, MAXX, MAXY, kategori, grid_size))
    rows = cur.fetchall()
    cur.close(); conn.close()

    features = [
        {"type": "Feature",
         "geometry": {"type": "Point", "coordinates": [r["lng"], r["lat"]]},
         "properties": {"gap": True, "kategori": kategori}}
        for r in rows
    ]
    return {"type": "FeatureCollection", "features": features,
            "total_gap_points": len(features)}


# ═══════════════════════════════════════════
# 4. ENDPOINT /report — Dashboard & Export
# ═══════════════════════════════════════════

@app.get("/api/v1/report/dashboard", tags=["Report"])
async def get_dashboard():
    """
    KPI ringkasan untuk halaman utama dashboard BI.
    Satu request → semua angka kunci.
    """
    conn = get_db()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute("SELECT COUNT(*) AS total FROM poi")
    total_poi = cur.fetchone()["total"]

    cur.execute("SELECT kategori, COUNT(*) AS n FROM poi GROUP BY kategori ORDER BY n DESC LIMIT 10")
    by_kategori = cur.fetchall()

    cur.execute("SELECT COUNT(*) AS total FROM roads")
    total_roads = cur.fetchone()["total"]

    cur.execute("SELECT ROUND(CAST(SUM(ST_Length(geom::geography))/1000 AS numeric),2) AS km FROM roads")
    total_km = cur.fetchone()["km"]

    cur.close(); conn.close()

    return {
        "kpi": {
            "total_poi":       total_poi,
            "total_segmen_jalan": total_roads,
            "total_km_jalan":  float(total_km or 0),
        },
        "distribusi_kategori": list(by_kategori),
    }


@app.get("/api/v1/report/summary", tags=["Report"])
async def get_summary(
    date_from: Optional[str] = None,
    date_to:   Optional[str] = None,
    group_by:  str = Query("kategori", description="kategori | kecamatan")
):
    """Ringkasan agregat POI dengan pengelompokan fleksibel."""
    conn = get_db()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    where_parts = []
    params = []
    if date_from:
        where_parts.append("created_at >= %s"); params.append(date_from)
    if date_to:
        where_parts.append("created_at <= %s"); params.append(date_to)
    where_sql = ("WHERE " + " AND ".join(where_parts)) if where_parts else ""

    col = "kategori" if group_by == "kategori" else "kecamatan"
    cur.execute(f"""
        SELECT {col} AS label, COUNT(*) AS jumlah
        FROM poi {where_sql}
        GROUP BY {col}
        ORDER BY jumlah DESC
    """, params)
    rows = cur.fetchall()
    cur.close(); conn.close()
    return {"group_by": group_by, "data": list(rows)}


@app.get("/api/v1/report/export", tags=["Report"])
async def get_export(
    kategori: Optional[str] = None,
    format:   str = Query("geojson", description="geojson | csv")
):
    """Export data POI dalam format GeoJSON atau CSV."""
    conn = get_db()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    where = "WHERE kategori = %s" if kategori else ""
    params = (kategori,) if kategori else ()
    cur.execute(f"""
        SELECT id, nama, kategori, alamat, metadata,
               ST_X(geom) AS lng, ST_Y(geom) AS lat
        FROM poi {where}
    """, params)
    rows = cur.fetchall()
    cur.close(); conn.close()

    if format == "csv":
        import io, csv
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=["id","nama","kategori","alamat","lat","lng"])
        writer.writeheader()
        writer.writerows(rows)
        from fastapi.responses import StreamingResponse
        buf.seek(0)
        return StreamingResponse(buf, media_type="text/csv",
                                 headers={"Content-Disposition": "attachment; filename=poi_jogja.csv"})

    features = [
        {"type": "Feature",
         "geometry": {"type": "Point", "coordinates": [r["lng"], r["lat"]]},
         "properties": {k: v for k, v in r.items() if k not in ("lng","lat")}}
        for r in rows
    ]
    return {"type": "FeatureCollection", "features": features}


@app.post("/api/v1/report/compare", tags=["Report"])
async def post_compare(body: CompareRequest):
    """Bandingkan N titik POI secara side-by-side."""
    if len(body.poi_ids) < 2 or len(body.poi_ids) > 5:
        raise HTTPException(400, "Masukkan 2-5 POI ID")
    results = []
    for pid in body.poi_ids:
        conn = get_db()
        cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("""
            SELECT id, nama, kategori, ST_X(geom) AS lng, ST_Y(geom) AS lat
            FROM poi WHERE id=%s
        """, (pid,))
        poi = cur.fetchone()
        cur.close(); conn.close()
        if poi:
            score = await get_demand_score(poi["lat"], poi["lng"], poi["kategori"])
            results.append({**poi, "demand_score": score["demand_score"],
                            "rekomendasi": score["rekomendasi"]})
    results.sort(key=lambda x: x["demand_score"], reverse=True)
    return {"perbandingan": results}


# ─────────────────────────────────────────
# Jalankan
# ─────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
