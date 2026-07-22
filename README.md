

```markdown
# WebGIS Business Intelligence — Yogyakarta City

A location-based WebGIS application for business analysis in Yogyakarta City. It combines interactive maps, coverage area isochrones, business location analysis, and KPI dashboards into a single platform.

**Live Demo:** https://business-intelegent.vercel.app  
**Backend API:** https://businessintelegent-production.up.railway.app/docs

---

## Deployment Architecture


```
<img width="300" height="301" alt="image" src="https://github.com/user-attachments/assets/72f0e8e9-a16e-4ae4-a3d4-13c5af057390" />

```

---

## Technology Stack

| Component | Technology | Platform |
|-----------|------------|----------|
| Frontend | HTML, CSS, JavaScript | Vercel |
| Map | Leaflet.js 1.9.4 | CDN |
| Heatmap | Leaflet.heat | CDN |
| Chart | Chart.js 4.4.2 | CDN |
| Backend | FastAPI + Python 3.11 | Railway |
| Database | PostgreSQL 15 + PostGIS | Supabase |
| Routing | OpenRouteService API | Cloud |
| Repo | Git | GitHub |

---

## Repository Structure


```

<img width="439" height="237" alt="image" src="https://github.com/user-attachments/assets/a10b227b-a5ed-4c79-8682-5d75c3e8e0aa" />


```

---

## API Endpoints

### Geo
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/geo/roads` | Road segments within bounding box (bbox) |
| GET | `/api/v1/geo/isochrone` | Coverage area from a point |
| POST | `/api/v1/geo/route` | Route A→B |
| POST | `/api/v1/geo/matrix` | Distance matrix for N points |
| GET | `/api/v1/geo/tiles/{z}/{x}/{y}` | MVT vector tiles |

### Business
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/business/poi` | List of POIs |
| POST | `/api/v1/business/poi` | Add POI |
| GET | `/api/v1/business/poi/{id}` | POI details |
| GET | `/api/v1/business/poi/{id}/catchment` | Catchment area |
| GET | `/api/v1/business/competitors` | Nearby competitors |
| GET | `/api/v1/business/heatmap` | Density heatmap |

### Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/analytics/accessibility` | Accessibility score |
| GET | `/api/v1/analytics/market-area` | POI market area |
| GET | `/api/v1/analytics/demand-score` | Location demand score |
| POST | `/api/v1/analytics/site-analysis` | Location feasibility analysis |
| GET | `/api/v1/analytics/gap-analysis` | Find gap areas |

### Report
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/report/dashboard` | KPI dashboard |
| GET | `/api/v1/report/summary` | Aggregate summary |
| GET | `/api/v1/report/export` | Export GeoJSON / CSV |
| POST | `/api/v1/report/compare` | Compare N POIs |

---

## Local Setup

### Prerequisites
- Python 3.11
- PostgreSQL + PostGIS
- Git

### Steps

**1. Clone the repository**
```bash
git clone [https://github.com/rosyidpaundra/Business_Intelegent.git](https://github.com/rosyidpaundra/Business_Intelegent.git)
cd Business_Intelegent

```

**2. Set up the backend**

```bash
cd backend
python -m venv venv311
venv311\Scripts\activate        # Windows
# source venv311/bin/activate  # macOS/Linux
pip install -r requirements.txt

```

**3. Create a `.env` file in the `backend/` folder**

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=database_name
DB_USER=postgres
DB_PASS=postgres_password
ORS_BASE_URL=[https://api.openrouteservice.org](https://api.openrouteservice.org)
ORS_API_KEY=ors_api_key

```

**4. Create database and tables**

```sql
CREATE DATABASE database_name;
-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

```

**5. Run the application**

```bash
uvicorn main:app --reload

```

---

## License

Distributed under the MIT License. See `LICENSE` for more information.

```

```
