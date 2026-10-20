# TaskFlow API 🚀

> **NIM:** 0110225159 | **Nama:** Rahel Siburian | **Mata Kuliah:** DevSecOps – Pertemuan 5

[![DevSecOps Pipeline](https://github.com/rahelsiburian26-cpu/devsecops-p5-0110225159/actions/workflows/devsecops.yml/badge.svg)](https://github.com/rahelsiburian26-cpu/devsecops-p5-0110225159/actions/workflows/devsecops.yml)

---

## 1. Nama Aplikasi & Fungsinya

**TaskFlow API** adalah aplikasi RESTful Task Management berbasis Python/Flask. Aplikasi ini memungkinkan pengguna untuk:

- **Mengelola tugas (task)**: membuat, membaca, memperbarui, dan menghapus tugas (CRUD penuh)
- **Memfilter & mengurutkan** tugas berdasarkan status (*pending*, *in_progress*, *done*, *cancelled*) dan prioritas (*low*, *medium*, *high*)
- **Mengelola tag** pada setiap tugas untuk kategorisasi
- **Health check endpoint** untuk monitoring ketersediaan layanan
- **Auth stub endpoint** sebagai fondasi integrasi autentikasi di masa depan

Aplikasi dirancang dengan pola *application factory*, memisahkan konfigurasi per-environment (development, testing, production) dan mendukung pengujian otomatis penuh.

---

## 2. Bahasa & Framework

| Komponen | Teknologi |
|---|---|
| Bahasa Pemrograman | Python 3.11 |
| Web Framework | Flask 2.3+ |
| Database | SQLite (via modul `sqlite3` built-in) |
| Testing | pytest + pytest-cov |
| SAST Tool | Bandit 1.7.5+ |
| CI/CD | GitHub Actions |

### Struktur File Source Code

```
devsecops-p5-0110225159/
├── app/
│   ├── __init__.py      # Application factory (create_app)
│   ├── config.py        # Environment configurations (Dev/Test/Prod)
│   ├── database.py      # SQLite CRUD operations untuk tasks & users
│   ├── routes.py        # REST API endpoints (Tasks, Auth, Health)
│   └── utils.py         # Helper: validasi, response formatter, paginasi
├── tests/
│   └── test_app.py      # Unit & integration tests (30+ test cases)
├── .github/
│   └── workflows/
│       └── devsecops.yml  # CI/CD Pipeline GitHub Actions
├── main.py              # Entry point aplikasi
├── requirements.txt     # Python dependencies
└── pyproject.toml       # Konfigurasi Bandit & pytest
```

---

## 3. Cara Menjalankan Aplikasi

### Prasyarat
- Python 3.11+
- pip

### Langkah Instalasi

```bash
# 1. Clone repository
git clone https://github.com/rahelsiburian26-cpu/devsecops-p5-0110225159.git
cd devsecops-p5-0110225159

# 2. Buat & aktifkan virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Jalankan aplikasi
python main.py
```

Aplikasi akan berjalan di `http://localhost:5000`.

### Contoh API Endpoints

```bash
# Health check
curl http://localhost:5000/api/health

# Buat task baru
curl -X POST http://localhost:5000/api/tasks/ \
  -H "Content-Type: application/json" \
  -d '{"title": "Belajar DevSecOps", "priority": "high", "tags": ["kuliah"]}'

# Lihat semua task
curl http://localhost:5000/api/tasks/

# Update status task
curl -X PATCH http://localhost:5000/api/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "done"}'

# Hapus task
curl -X DELETE http://localhost:5000/api/tasks/1
```

### Menjalankan Unit Tests

```bash
pytest tests/ -v --cov=app --cov-report=term-missing
```

### Menjalankan SAST Scan (Bandit)

```bash
bandit -r app/ -f txt --severity-level medium
```

---

## 4. Overview Pipeline CI/CD

Pipeline DevSecOps diimplementasikan menggunakan **GitHub Actions** dan terdiri dari **2 job** yang berjalan secara berurutan:

```
Push / Pull Request ke main
         │
         ▼
┌─────────────────────────┐
│   JOB 1: build          │   runner: ubuntu-latest
│                         │
│  • Checkout kode        │
│  • Setup Python 3.11    │
│  • Install dependencies │
│  • Run pytest (30+ tes) │
│  • Coverage ≥ 70%       │
│  • Upload coverage.xml  │
└──────────┬──────────────┘
           │  needs: build (Quality Gate #1)
           ▼
┌─────────────────────────┐
│   JOB 2: sast-scan      │   runner: ubuntu-latest
│   (SAST: Bandit)        │
│                         │
│  • Checkout kode        │
│  • Install Bandit       │
│  • Scan folder app/     │
│  • Generate JSON report │
│  • Quality Gate #2:     │
│    Gagal jika ada isu   │
│    severity HIGH        │
│  • Upload bandit report │
└─────────────────────────┘
```

### Trigger Kondisi

| Event | Branch | Keterangan |
|---|---|---|
| `push` | `main` | Setiap push ke branch utama |
| `pull_request` | `main` | Setiap PR yang menarget main |

### Quality Gates

| Gate | Kondisi Lulus |
|---|---|
| **Unit Test** | Semua test case harus pass |
| **Code Coverage** | Coverage ≥ 70% (via pytest-cov) |
| **SAST Severity** | Tidak ada isu **HIGH** severity dari Bandit |

### Artifacts yang Di-upload

- `coverage.xml` — laporan coverage kode (disimpan 7 hari)
- `bandit-report.json` — laporan SAST lengkap dalam JSON (disimpan 30 hari)

---

## Referensi

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Bandit – Python SAST Tool](https://bandit.readthedocs.io/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [OWASP DevSecOps Guideline](https://owasp.org/www-project-devsecops-guideline/)