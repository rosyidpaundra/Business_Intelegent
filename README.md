# Business_Intelegent
Kami membantu bisnis mengambil keputusan lebih cepat dan lebih cerdas dengan dukungan Location Intelligence dan data geospasial.


Tentu, ini adalah draf deskripsi `README.md` yang profesional dan informatif untuk repositori **Business_Intelegent** kamu. Deskripsi ini mencakup panduan instalasi lokal serta tautan ke versi demo yang sudah di-deploy.

---

# Business Intelligence - Location Intelligence & Geospatial Data

Repositori ini berisi solusi **Business Intelligence** yang berfokus pada pengambilan keputusan berbasis data geospasial. Kami membantu bisnis menganalisis lokasi secara lebih cerdas dan cepat menggunakan teknologi *Location Intelligence*.

**Live Demo:** [business-intelegent.vercel.app](https://business-intelegent.vercel.app/)

---

## 🚀 Fitur Utama

* **Location Intelligence:** Analisis mendalam berbasis titik koordinat dan wilayah.
* **Geospatial Visualization:** Visualisasi data peta yang interaktif.
* **Fast Decision Making:** Dashboard yang dirancang untuk mempercepat proses pengambilan keputusan bisnis.

## 🛠️ Arsitektur Teknologi

* **Frontend:** HTML5 (Deployed via Vercel)
* **Backend:** Python 3.11+
* **Database Integration:** PostgreSQL (via `test_db.py`)

---

## 💻 Panduan Menjalankan di Komputer Lokal

Ikuti langkah-langkah di bawah ini untuk menjalankan proyek ini di mesin lokal Anda:

### 1. Persyaratan Sistem

Pastikan Anda sudah menginstal:

* [Python 3.11 atau lebih baru](https://www.python.org/downloads/)
* Git

### 2. Kloning Repositori

```bash
git clone https://github.com/rosyidpaundra/Business_Intelegent.git
cd Business_Intelegent

```

### 3. Setup Lingkungan Virtual (Opsional tapi Disarankan)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate

```

### 4. Instalasi Dependensi

Instal semua pustaka Python yang diperlukan:

```bash
pip install -r requirements.txt

```

### 5. Konfigurasi Environment

Buat file `.env` (atau edit file yang sudah ada) dan sesuaikan kredensial database atau API key yang diperlukan:

```env
# Contoh isi .env
DB_URL=your_database_url
API_KEY=your_api_key

```

### 6. Menjalankan Aplikasi

Untuk menjalankan backend (Python):

```bash
python main.py

```

Untuk melihat tampilan frontend, Anda dapat membuka file `index.html` langsung di browser atau menggunakan ekstensi *Live Server* di VS Code.

---

## 📂 Struktur Folder

* `main.py`: Entry point utama untuk logika backend.
* `index.html`: File utama untuk antarmuka pengguna (frontend).
* `test_db.py`: Skrip untuk pengujian koneksi database.
* `requirements.txt`: Daftar pustaka Python yang digunakan.

## 🤝 Kontribusi

Kontribusi selalu terbuka! Silakan lakukan *fork* pada repositori ini dan kirimkan *pull request* untuk fitur-fitur baru atau perbaikan bug.

---

**Author:** [Rosyid Paundra](https://github.com/rosyidpaundra)
