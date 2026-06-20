# 🩺 Diabetes Social Media Sentiment & Trend Analysis Dataset

> **Analisis Big Data Komprehensif tentang Persepsi, Sentimen, dan Tren Diskusi Diabetes di Media Sosial Indonesia**

[![Platform](https://img.shields.io/badge/Platforms-YouTube%20%7C%20X%20%7C%20Threads%20%7C%20Google%20Trends-blue)](#dataset-description)
[![Period](https://img.shields.io/badge/Period-2015–2026-green)](#dataset-description)
[![Framework](https://img.shields.io/badge/Framework-Big%20Data%208V-orange)](#big-data-characteristics-8v)
[![Records](https://img.shields.io/badge/Total%20Records-16.632-red)](#dataset-description)

---

## 📋 Daftar Isi

- [Project Overview](#-project-overview)
- [Sumber Data](#-sumber-data)
- [Tujuan Penelitian](#-tujuan-penelitian)
- [Dataset Description](#-dataset-description)
- [Big Data Characteristics (8V)](#-big-data-characteristics-8v)
- [Key Insights](#-key-insights)
- [Analysis Pipeline](#-analysis-pipeline)
- [Getting Started](#-getting-started)
- [Limitasi & Etika Data](#-limitasi--etika-data)
- [Citation](#-citation)

---

## 🎯 Project Overview

Proyek ini adalah **analisis infodemiology multi-platform** tentang persepsi, sentimen, dan tren diskusi diabetes di ruang digital Indonesia. Dataset mengintegrasikan data dari **YouTube, X (Twitter), Threads, dan Google Trends** untuk menghasilkan gambaran holistik tentang bagaimana masyarakat Indonesia berbicara dan berinteraksi dengan topik kesehatan diabetes selama periode **2015–2026**.

Pendekatan **infodemiology** (information + epidemiology) digunakan sebagai kerangka utama — sebuah pendekatan yang diakui secara internasional untuk analisis data digital terkait kesehatan publik, tanpa memerlukan ground truth klinis secara langsung.

**Tujuan Utama:**
- Memahami pola diskusi diabetes di era digital Indonesia
- Menganalisis sentimen publik terhadap topik diabetes dari berbagai platform
- Mengidentifikasi tren topik yang viral dan momen pemicunya
- Mengkorelasikan tren pencarian (Google Trends) dengan volume diskusi sosial media
- Memberikan insights berbasis data untuk edukasi dan kampanye kesehatan

---

## 📊 Sumber Data

### Multi-Platform Data Sources

| Platform | Deskripsi | Metode Pengumpulan | Periode |
|----------|-----------|-------------------|---------|
| **YouTube** | Komentar video bertopik diabetes | YouTube Data API v3 | 2018–2026 |
| **X (Twitter)** | Tweet dan diskusi tentang diabetes | X API v2 & Web Scraping | 2016–2026 |
| **Threads** | Unggahan dan diskusi kesehatan diabetes | Web Scraping | Feb 2024–Mei 2026 |
| **Google Trends** | Indeks pencarian 20 kata kunci diabetes | pytrends (Google Trends API) | 2015–2026 |

> **Catatan metodologis:** Google Trends diperlakukan sebagai *exogenous signal variable* (sinyal indikator eksternal), bukan sebagai dokumen teks. Data ini dikorelasikan dengan volume diskusi sosial media untuk analisis Granger causality.

---

## 🎯 Tujuan Penelitian

### 1. Sentiment Analysis
- Menganalisis sentimen positif, negatif, dan netral dari diskusi diabetes menggunakan model IndoBERT
- Membandingkan distribusi sentimen antar platform
- Mengidentifikasi faktor pemicu emosi dalam diskusi kesehatan

### 2. Trend Detection
- Menemukan topik-topik yang trending tentang diabetes
- Melacak evolusi diskusi dari waktu ke waktu (2015–2026)
- Mengidentifikasi seasonal patterns (Ramadan, Hari Diabetes Sedunia 14 November)

### 3. Topic Modeling
- Mengklasifikasikan diskusi berdasarkan kategori topik menggunakan LDA
- Memahami sub-topik utama dalam wacana diabetes digital
- Mendeteksi narasi misinformasi yang beredar

### 4. Cross-Platform Analysis
- Menguji korelasi volume diskusi antar platform
- Menganalisis apakah Google Trends mendahului diskusi sosial media (Granger causality)
- Membandingkan karakteristik wacana per platform

### 5. Public Health Implications
- Memetakan literasi kesehatan masyarakat tentang diabetes
- Memberikan rekomendasi waktu optimal kampanye edukasi kesehatan
- Mengidentifikasi gap informasi yang perlu dijawab tenaga kesehatan

---

## 📚 Dataset Description

### Ringkasan Dataset per Platform

| Platform | Jumlah Data | Kolom Utama | Keterangan |
|----------|-------------|-------------|------------|
| **Google Trends** | 4.179 hari × 20 keyword | date, keyword, trend_score | Skala relatif 0–100 harian |
| **X (Twitter)** | 10.782 tweet | id, date, text_clean | 2016–2026 |
| **YouTube** | 3.640 komentar | comment, like, engagement_score, topic | 25 topik video, 5 kategori |
| **Threads** | 1.362 unggahan | username, date, comment | Feb 2024–Mei 2026 |
| **Total** | **~99.564 baris data** | | Termasuk 83.780 data poin Trends |

### Unified Schema (Dataset Gabungan)

Dataset gabungan menggunakan skema berikut untuk analisis lintas platform:

| Kolom | Tipe | Keterangan |
|-------|------|------------|
| `record_id` | String | ID unik: `PLATFORM_YYYYMMDD_NNNN` |
| `platform` | Category | `google_trends`, `twitter`, `youtube`, `threads` |
| `date` | Date | Format standar YYYY-MM-DD |
| `text_raw` | Text | Teks asli (NULL untuk Trends) |
| `text_clean` | Text | Hasil preprocessing NLP |
| `trend_score` | Float | 0–100 (NULL untuk platform non-Trends) |
| `trend_keyword` | String | Nama keyword Trends (NULL untuk lain) |
| `engagement_score` | Float | Normalized 0–1 (YouTube & Threads) |
| `sentiment_score` | Float | Output model IndoBERT |
| `sentiment_label` | String | Positif / Negatif / Netral |
| `topic_label` | String | Hasil LDA topic modeling |
| `is_event_day` | Boolean | TRUE jika tanggal event kesehatan nasional |

### Statistik Deskriptif (YouTube)

```
📈 ENGAGEMENT (Likes):
   - Mean:      1.82 likes per komentar
   - Median:    0 likes
   - Max:       565 likes
   - Total:     6.637 likes
   - Std Dev:   ~15 (distribusi sangat skewed)

📊 PANJANG KOMENTAR:
   - Median:    58 karakter
   - Rata-rata: 102 karakter
   - Maksimum:  3.493 karakter
```

### Kategori Topik Video YouTube

| Topik | Jumlah Komentar |
|-------|----------------|
| Penjelasan Diabetes Mellitus | 1.500 |
| Gejala & Penyebab | 724 |
| Penjelasan Klinis | 696 |
| Pencegahan & Penanganan | 470 |
| Jenis Tipe 1 & 2 | 250 |

### Google Trends Keywords (20 Kata Kunci)

```
Kategori Gejala:    diabetes, sering haus, sering buang air kecil,
                    badan lemas, penglihatan kabur, luka sulit sembuh

Kategori Pengelolaan: gula darah tinggi, cek gula darah, diet diabetes,
                      insulin, prediabetes, kadar gula normal

Kategori Lifestyle: obesitas, minuman manis, makanan manis

Kategori Komplikasi: neuropati, retinopati, gagal ginjal, kaki diabetes,
                     hiperglikemia
```

---

## 🔥 Big Data Characteristics (8V)

Dataset ini mendemonstrasikan delapan dimensi karakteristik Big Data:

### V1 — Volume 📊

```
✓ Total baris data:   ~99.564 (termasuk 83.780 data poin Trends)
✓ Rekaman teks:       16.632 komentar dari 3 platform sosial
✓ Rentang waktu:      11 tahun (2015–2026)
✓ Multi-platform:     4 sumber data terintegrasi
✓ Keyword Trends:     20 kata kunci × 4.179 hari
```

**Catatan:** Volume Google Trends (83.780 data poin) dihitung sebagai time-series numerik, bukan dokumen teks, sesuai dengan pendekatan metodologis yang digunakan.

---

### V2 — Velocity ⚡

```
✓ Google Trends:      Granularitas harian (daily) — paling cepat
✓ X (Twitter):        Rata-rata ~63 tweet/bulan (2025); puncak Jan 2025: 93 tweet
✓ Threads:            Puncak aktivitas Feb 2026: 558 unggahan
✓ YouTube:            Puncak komentar Mar 2024: 33 komentar/hari
```

**Insight Velocity:** Diabetes adalah topik yang terus diperbincangkan secara konsisten, bukan musiman semata. Terdapat pola lonjakan yang berulang setiap November (Hari Diabetes Sedunia) dan April/Mei (pasca Lebaran).

---

### V3 — Variety 🎨

```
✓ Format data:
   - Teks pendek (<280 karakter): Tweet X/Twitter
   - Teks menengah: Unggahan Threads
   - Teks panjang (rata-rata 102 karakter): Komentar YouTube
   - Data numerik time-series: Google Trends (0–100)

✓ Tipe konten:
   - Opini & ekspresi emosi (Twitter)
   - Narasi pengalaman pribadi (Threads)
   - Respons konten video (YouTube)
   - Sinyal minat pencarian (Google Trends)
```

---

### V4 — Veracity ✅

```
✓ Strategi validasi multi-lapis:
   1. Ecological Validity:  Korelasi tren keyword dengan data Riskesdas
                            Kemenkes RI 2013 (6.9%), 2018 (8.5%), 2023 (10.9%)
   2. Event Validation:     Verifikasi spike 14 November (Hari Diabetes Sedunia)
                            setiap tahun di semua platform
   3. Cross-Platform:       Concordance rate spike antar platform dalam ±7 hari
   4. Annotation-Based:     Anotasi manual 300–500 sampel, 2 anotator independen
                            Target Cohen's Kappa ≥ 0.6

✓ Kualitas data YouTube:
   - Duplikat dihapus (7 duplikat teridentifikasi)
   - HTML tags dibersihkan
   - Data dari kanal bersubscriber 50K–2M (terverifikasi)

⚠ Keterbatasan Veracity:
   - Tidak ada ground truth klinis langsung
   - 31.2% missing dates pada dataset awal (sudah diimputasi)
   - Bahasa campuran (id/en/slang) memerlukan model multilingual
```

---

### V5 — Value 💎

```
✓ Nilai akademik:
   - Dataset longitudinal terpanjang diskusi diabetes Indonesia (11 tahun)
   - Kontribusi model IndoBERT fine-tuned untuk domain kesehatan
   - Metodologi infodemiology yang reproducible

✓ Nilai kebijakan:
   - Kalender optimal kampanye edukasi diabetes berbasis data historis
   - Profil narasi misinformasi untuk dijawab tenaga kesehatan
   - Rekomendasi platform & framing pesan untuk Kemenkes RI

✓ Nilai riset:
   - Baseline monitoring infodemiologi diabetes nasional
   - Dataset NLP teranotasi Bahasa Indonesia untuk penelitian lanjutan
```

---

### V6 — Variability 📈

```
✓ Temuan variabilitas utama:
   - Panjang komentar YouTube: 1–3.493 karakter (sangat bervariasi)
   - Distribusi like: 75% mendapat 0 like; maksimum 565 like (highly skewed)
   - Trend score Trends: rata-rata 17.55, median 18.9, max 100

✓ Pola temporal yang teridentifikasi:
   1. Efek Domino:     Viral X → lonjakan Trends (1-2 hari) → YouTube (1 minggu)
   2. Siklus Lebaran:  Lonjakan April/Mei tiap tahun (gula darah pasca-Lebaran)
   3. Jam 2 Pagi:      Volume "gejala diabetes" tertinggi pukul 01:00–04:00
   4. Evolusi Topik:   2018–2021 dominasi "obat herbal" → 2024–2026 dominasi
                       "glucose spike" dan CGM (sensor gula darah)
```

---

### V7 — Visualization 📊

Dashboard interaktif tersedia di: **https://fabbbios.github.io/Big-Data/**

```
✓ Komponen visualisasi:
   - Timeline multi-platform 2015–2026 dengan event markers
   - Radar chart skor 8V (kematangan big data)
   - Bar chart distribusi topik per platform
   - Line chart tren temporal dan volume bulanan
   - Heatmap aktivitas per bulan (Mar–Jun 2025)
   - Distribusi panjang komentar dan engagement
   - Scatter plot engagement lintas platform
```

---

### V8 — Vulnerability 🔒

```
✓ Risiko yang diidentifikasi:
   1. Privasi pengguna:    Data komentar publik mengandung informasi
                           kesehatan sensitif yang berpotensi re-identification
   2. Misinformasi:        Beredarnya klaim pengobatan tidak terverifikasi
                           (obat herbal, pengobatan alternatif) di komentar
   3. Bias platform:       Pengguna YouTube cenderung lebih tua; Threads
                           didominasi Gen Z; Twitter campuran

✓ Mitigasi yang diterapkan:
   - Semua username dianonimisasi sebelum penyimpanan
   - URL profil tidak disimpan dalam dataset
   - Data diproses sesuai Terms of Service masing-masing platform
   - Tidak ada data yang memerlukan IRB (data publik, observasional)
```

---

## 🎬 Key Insights

### 1. Efek Domino Lintas Platform
Terdapat pola migrasi audiens yang konsisten: konten viral di X/Twitter memicu lonjakan pencarian di Google Trends (1–2 hari kemudian), diikuti peningkatan komentar di YouTube (sekitar 1 minggu setelah viral). Ini mengkonfirmasi bahwa **X berfungsi sebagai leading indicator** dalam ekosistem diskusi diabetes digital.

### 2. Siklus Penyesalan Pasca-Lebaran
Volume diskusi gejala diabetes ("sering haus", "gula darah naik") melonjak secara konsisten pada April/Mei (pasca-Idul Fitri) dan awal Januari setiap tahunnya — mengindikasikan hubungan kuat antara konsumsi gula tinggi musiman dengan kesadaran kesehatan reaktif.

### 3. Health Anxiety Dini Hari
Cuitan berisi kata kunci "kesemutan", "takut kena diabetes", dan keluhan gejala mencapai volume tertinggi pada pukul 01:00–04:00. Ini mengindikasikan *health anxiety* yang mendorong pencarian informasi di luar jam layanan medis.

### 4. Polarisasi Herbal vs. Medis
Terdapat polarisasi kuat dalam diskusi pengobatan: sebagian besar pengguna X dan YouTube mengagungkan obat herbal sambil menolak obat medis konvensional. Topik ini berpotensi memuat narasi misinformasi yang perlu direspons konten edukasi.

### 5. Demokratisasi Alat Medis
Peningkatan diskusi CGM (Continuous Glucose Monitor) dan alat cek gula mandiri di kalangan non-penderita muda mencerminkan tren *wellness tech* yang baru — peluang sekaligus risiko *health anxiety* berlebihan.

### 6. Dominasi Narasi Gejala
Mayoritas diskusi berfokus pada gejala awal dan diagnosis mandiri sebelum ke dokter — mengindikasikan gap literasi kesehatan yang bisa diisi kampanye edukasi berbasis platform.

---

## 📊 Analysis Pipeline

```
Fase 1: Data Collection & Audit
├── Scraping & API data collection dari 4 platform
├── Data quality audit (missing values, duplikat, distribusi)
└── Output: Data Quality Report per platform

Fase 2: Preprocessing & Unified Schema
├── Normalisasi teks (PySastrawi stemming, stopword removal)
├── Normalisasi singkatan Bahasa Indonesia
├── Deteksi bahasa (langdetect)
├── Penggabungan ke unified schema
└── Output: unified_dataset.parquet

Fase 3: Temporal Analysis
├── STL decomposition Google Trends (20 keyword)
├── Event study analysis (Hari Diabetes Sedunia 14 Nov)
├── Korelasi Granger: Trends vs volume sosial media
└── Output: temporal_insights.csv

Fase 4: NLP Analysis
├── Anotasi manual (500 sampel, 2 anotator, Cohen's Kappa)
├── Fine-tuning IndoBERT untuk sentimen diabetes
├── LDA topic modeling (K optimal via coherence score)
└── Output: dataset_with_nlp.parquet, lda_model/

Fase 5: Cross-Platform Analysis
├── Spearman correlation matrix antar platform
├── Heatmap topik × platform
├── Perbandingan distribusi sentimen (Chi-square test)
└── Output: cross_platform_analysis.ipynb

Fase 6: Validation
├── Ecological validation (korelasi vs Riskesdas)
├── Event-based validation (spike 14 November)
├── Cross-platform concordance
└── Output: validation_report.md

Fase 7: Visualization & Reporting
├── Dashboard interaktif (Plotly Dash / GitHub Pages)
├── Draft manuscript (target: JMIR / BMC Public Health)
└── Policy brief untuk Kemenkes RI
```

---

## 🚀 Getting Started

### Prerequisites

```bash
pip install pandas numpy pytrends PySastrawi gensim transformers
pip install torch statsmodels scikit-learn plotly langdetect scipy
```

### Struktur Direktori

```
diabetes_bigdata_project/
├── data/
│   ├── raw/              # Dataset asli (read-only)
│   ├── processed/        # Hasil preprocessing per platform
│   └── unified/          # Unified schema final
├── notebooks/
│   ├── 01_data_audit.ipynb
│   ├── 02_preprocessing.ipynb
│   ├── 03_temporal_analysis.ipynb
│   ├── 04_sentiment_analysis.ipynb
│   ├── 05_topic_modeling.ipynb
│   ├── 06_cross_platform.ipynb
│   └── 07_validation.ipynb
├── models/               # IndoBERT fine-tuned checkpoint
├── outputs/
│   ├── figures/          # Semua visualisasi PNG/SVG
│   └── reports/          # Laporan per fase
├── dashboard/            # Source code dashboard
└── annotation/           # Gold standard & annotation guidelines
```

### Quick Start

```python
import pandas as pd

# Load unified dataset
df = pd.read_parquet('data/unified/diabetes_unified.parquet')

# Basic stats per platform
print(df.groupby('platform').agg({
    'record_id': 'count',
    'sentiment_score': 'mean',
    'engagement_score': 'mean'
}))

# Filter by date range
df_2024 = df[df['date'] >= '2024-01-01']

# Analisis topik per platform
topic_dist = df.groupby(['platform', 'topic_label']).size().unstack(fill_value=0)
print(topic_dist)
```

---

## ⚠️ Limitasi & Etika Data

### Limitasi Metodologis

1. **Sampling bias:** Pengguna media sosial tidak representatif untuk seluruh populasi Indonesia — cenderung urban, terdidik, dan muda.
2. **Platform bias:** Setiap platform memiliki demografi dan norma komunikasi berbeda yang memengaruhi pola sentimen.
3. **Validasi proxy:** Tidak ada ground truth klinis langsung; validasi menggunakan pendekatan ekologis dan berbasis event.
4. **Skala relatif Trends:** Google Trends menggunakan skala 0–100 relatif, bukan volume absolut pencarian.
5. **Coverage Threads:** Hanya 2 tahun (2024–2026); tidak memungkinkan analisis longitudinal setara platform lain.

### Pernyataan Etika

> Penelitian ini menganalisis data yang tersedia secara publik. Tidak ada informasi yang dapat mengidentifikasi individu yang dikumpulkan atau disimpan. Semua username telah dianonimisasi. Penelitian dilakukan sesuai dengan Terms of Service masing-masing platform. Sebagai penelitian observasional atas data publik, persetujuan formal IRB tidak diperlukan.

---

## 🔮 Future Enhancements

- [ ] Implementasi pipeline analisis sentimen real-time dengan IndoBERT
- [ ] Ekspansi ke platform TikTok dan Instagram Reels
- [ ] Integrasi data klaim BPJS Kesehatan untuk validasi klinis
- [ ] Studi komparatif lintas negara ASEAN
- [ ] API publik untuk akses dataset yang teranonimisasi
- [ ] Model prediksi tren diskusi berbasis ARIMA/Prophet

---

## 📝 Citation

Jika Anda menggunakan dataset ini dalam penelitian atau publikasi, harap sitasi sebagai:

```bibtex
@dataset{diabetes_social_media_2026,
  title     = {Diabetes Social Media Sentiment \& Trend Analysis Dataset:
               A Multi-Platform Infodemiological Study (2015–2026)},
  year      = {2026},
  platforms = {YouTube, X (Twitter), Threads, Google Trends},
  records   = {16632 social media records + 83780 trend data points},
  period    = {2015--2026},
  approach  = {Infodemiology, NLP, Big Data 8V Framework},
  url       = {https://github.com/[username]/BIG-DATA}
}
```

---

## 🙏 Acknowledgments

Terima kasih kepada:
- Platform YouTube, X (Twitter), Threads, dan Google Trends atas data access
- Komunitas open-source: pandas, PySastrawi, Gensim, Hugging Face Transformers
- IndoBERT team (Koto et al., 2020) untuk model pre-trained Bahasa Indonesia
- Kementerian Kesehatan RI atas data Riskesdas yang digunakan sebagai proxy validasi

---

<div align="center">

**📊 Total Data: ~99.564 baris · 4 Platform · 11 Tahun (2015–2026)**

YouTube: 3.640 · X/Twitter: 10.782 · Threads: 1.362 · Google Trends: 83.780 data poin

*Pendekatan: Infodemiology — Big Data 8V Framework*

[🔝 Kembali ke Atas](#-diabetes-social-media-sentiment--trend-analysis-dataset)

</div>
