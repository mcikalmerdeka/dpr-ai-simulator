---
title: DPR AI Simulator
emoji: 🏛️
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 6.4.0
app_file: main.py
pinned: false
license: mit
short_description: Simulate DPR process using AI agents
tags:
  - langchain
  - dpr simulator
  - ai
  - experiment
---

# 🏛️ DPR AI Simulator

![DPR AI Simulator](assets/project_header.png)

**Simulasi berbasis AI untuk proses Dewan Perwakilan Rakyat (DPR) Indonesia**

Proyek eksperimen untuk mensimulasikan fungsi DPR menggunakan AI agents, menunjukkan potensi efisiensi dibandingkan dengan sistem konvensional yang menghabiskan triliunan rupiah APBN setiap tahunnya.

Coba proyeknya disini: [Hugging Face Spaces](https://huggingface.co/spaces/mcikalmerdeka/dpr-simulator)

## 🎯 Tujuan Proyek

Proyek ini mensimulasikan 3 fungsi utama DPR dalam menangani aspirasi rakyat melalui pipeline AI multi-tahap:

1. **Menyerap (Absorb)** - AI agents menyerap dan memahami aspirasi dari perspektif berbagai anggota DPR dengan latar belakang, fraksi, dan daerah pemilihan yang berbeda
2. **Menghimpun (Compile)** - Mengagregasi dan mengkompilasi tanggapan dari banyak anggota menjadi konsensus kolektif
3. **Diskusi Council (Council Discussion)** - Mensimulasikan deliberasi parlemen antar anggota DPR yang relevan, menunjukkan dinamika fraksi dan pembentukan konsensus
4. **Menindaklanjuti (Follow-up)** - Menentukan langkah konkret tindak lanjut, termasuk komisi penanggung jawab, timeline, estimasi anggaran, dan pihak-pihak yang perlu dilibatkan

## ✨ Fitur Utama

- **Interface Gradio Interaktif** - Web UI modern untuk input aspirasi dan visualisasi hasil pemrosesan
- **Simulasi Multi-Agent** - Setiap anggota DPR disimulasikan sebagai AI agent independen dengan karakteristik unik
- **Pemrosesan Paralel dengan Batching** - Efisien memproses puluhan hingga ratusan agent secara bersamaan
- **Pelacakan Biaya Real-time** - Monitoring biaya API OpenAI untuk setiap tahap pemrosesan
- **AI Council Personas** - Anggota DPR memiliki "jiwa" (persona) sesuai ideologi fraksi (Nasionalis, Agamis, Karya, dll) dan memberikan tanggapan lisan (quote) yang natural.
- **Support 13 Komisi (2024-2029)** - Integrasi penuh dengan bidang tugas 13 Komisi DPR RI untuk filtering relevansi yang akurat.
- **Visualisasi Data Komprehensif** - Tabel interaktif menampilkan anggota DPR, relevansi, sikap (sentiment), tanggapan awal, dan partisipasi dalam diskusi council.
- **Council Discussion (NEW!)** - Mensimulasikan deliberasi parlemen antar anggota DPR dengan dinamika fraksi, debat multi-putaran, dan pembentukan konsensus.
- **Konfigurasi Fleksibel** - Pengaturan model, jumlah anggota, dan parameter lainnya melalui environment variables.

## 🚀 Instalasi dan Penggunaan

### Prasyarat

- Python 3.12 atau lebih tinggi
- [uv](https://github.com/astral-sh/uv) - Python package manager (direkomendasikan)
- OpenAI API key

### Langkah Instalasi

```bash
# Clone repository
git clone https://github.com/yourusername/dpr-simulator.git
cd dpr-simulator

# Install dependencies menggunakan uv
uv sync
```

> **Catatan:** Aplikasi ini tidak menggunakan file `.env`. API key OpenAI dimasukkan langsung melalui interface Gradio saat menjalankan aplikasi untuk keamanan.

### Menjalankan Aplikasi

```bash
# Jalankan dengan uv
uv run python main.py

# Atau aktifkan virtual environment terlebih dahulu
.venv\Scripts\activate   # Windows
source .venv/bin/activate  # Linux/Mac

# Kemudian jalankan
python main.py
```

Aplikasi Gradio akan tersedia di `http://127.0.0.1:7860`

## 📁 Struktur Proyek

```
dpr-simulator/
├── src/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py          # Manajemen konfigurasi aplikasi
│   ├── models/
│   │   ├── __init__.py
│   │   ├── dpr_member.py        # Model data anggota DPR
│   │   ├── aspirasi.py          # Model data aspirasi rakyat
│   │   └── responses.py         # Model respons untuk setiap tahap pipeline
│   ├── core/
│   │   ├── __init__.py
│   │   ├── simulator.py         # Orchestrator utama simulator
│   │   ├── member_factory.py    # Factory untuk membuat anggota DPR
│   │   └── agents/
│   │       ├── __init__.py
│   │       ├── base.py                       # Base class untuk semua agent
│   │       ├── absorb_agent.py               # Agent tahap 1: Menyerap
│   │       ├── compile_agent.py              # Agent tahap 2: Menghimpun
│   │       ├── council_discussion_agent.py   # Agent tahap 3: Diskusi Council
│   │       └── followup_agent.py             # Agent tahap 4: Menindaklanjuti
│   └── ui/
│       ├── __init__.py
│       └── app.py               # Gradio web interface
├── main.py                      # Entry point aplikasi
├── pyproject.toml               # Konfigurasi proyek dan dependencies
└── README.md
```

## ⚙️ Konfigurasi

**API Key:** Dimasukkan langsung melalui interface Gradio (tidak menggunakan file `.env`)

**Pengaturan Lainnya:** Dapat dikonfigurasi melalui environment variables (opsional):

| Variable                    | Default        | Deskripsi                             |
| --------------------------- | -------------- | ------------------------------------- |
| `OPENAI_MODEL`              | `gpt-4.1-nano` | Model OpenAI yang digunakan           |
| `PROMPT_COST_PER_1K`        | `0.0001`       | Biaya per 1k prompt tokens (USD)      |
| `COMPLETION_COST_PER_1K`    | `0.0004`       | Biaya per 1k completion tokens (USD)  |
| `DEFAULT_MEMBER_COUNT`      | `50`           | Jumlah default anggota DPR            |
| `BATCH_SIZE`                | `10`           | Ukuran batch untuk pemrosesan paralel |
| `RATE_LIMIT_DELAY`          | `1.0`          | Delay antar batch (detik)             |
| `GRADIO_SERVER_NAME`        | `127.0.0.1`    | Host server Gradio                    |
| `GRADIO_SERVER_PORT`        | `7860`         | Port server Gradio                    |
| `GRADIO_SHARE`              | `False`        | Share aplikasi secara publik          |
| `COUNCIL_DISCUSSION_ROUNDS` | `2`            | Jumlah putaran diskusi council        |

## 💰 Estimasi Biaya

Menggunakan model `gpt-4.1-nano`:

**Formula: Total API Calls = N + 3**

Dimana **N** = sample size (jumlah anggota DPR yang memproses aspirasi)

**Rincian 4 Tahap:**

1. **Menyerap (Absorb):** N API calls - setiap anggota menganalisis aspirasi secara independen
2. **Menghimpun (Compile):** 1 API call - agregasi konsensus dari semua anggota
3. **Diskusi Council:** 1 API call - simulasi deliberasi parlemen antar anggota
4. **Menindaklanjuti (Follow-up):** 1 API call - generate action plan lengkap

**Estimasi Biaya:**

| Sample Size | Stage 1 | Stage 2 | Stage 3 | Stage 4 | **Total API Calls** | **Estimasi Biaya** |
| ----------- | ------- | ------- | ------- | ------- | ------------------- | ------------------ |
| 20 anggota  | 20      | 1       | 1       | 1       | **23**              | ~$0.002-0.005      |
| 50 anggota  | 50      | 1       | 1       | 1       | **53**              | ~$0.005-0.01       |
| 100 anggota | 100     | 1       | 1       | 1       | **103**             | ~$0.01-0.02        |
| 575 anggota | 575     | 1       | 1       | 1       | **578**             | ~$0.05-0.10        |

Bandingkan dengan anggaran DPR aktual: **~Rp 5 Triliun/tahun**!

## 🔧 Tech Stack

- **LangChain** (v1.2.7+) - Framework orkestrasi LLM
- **LangChain OpenAI** (v1.1.7+) - Integrasi OpenAI dengan LangChain
- **OpenAI** (v2.16.0+) - Provider model bahasa
- **Gradio** (v6.4.0+) - Framework UI web modern untuk Python
- **Pydantic** (v2.12.5+) - Validasi data dan settings management
- **uv** - Python package manager yang cepat

## 📝 Contoh Penggunaan Programmatic

Selain menggunakan Gradio UI, Anda juga dapat menggunakan simulator secara programmatic:

```python
import asyncio
from src.core import DPRSimulator
from src.models import Aspirasi
from datetime import datetime

async def main():
    # Inisialisasi simulator
    simulator = DPRSimulator(api_key="sk-your-api-key")

    # Buat anggota DPR (50 anggota dengan berbagai fraksi dan daerah)
    simulator.create_members(50)

    # Buat aspirasi rakyat
    aspirasi = Aspirasi(
        id=1,
        source="Jawa Barat",
        category="Pendidikan",
        content="Penambahan dana BOS untuk sekolah terpencil di daerah pegunungan",
        priority="Tinggi",
        timestamp=datetime.now(),
    )

    # Proses melalui pipeline lengkap
    result = await simulator.process_aspirasi(
        aspirasi,
        sample_size=20  # Gunakan 20 anggota yang paling relevan
    )

    # Tampilkan hasil
    print(result.summary())
    print(f"\nTotal biaya pemrosesan: ${result.total_cost_usd:.6f}")
    print(f"Anggota yang merespons: {result.simulation_details.anggota_merespons}")
    print(f"Komisi penanggung jawab: {result.tindak_lanjut.komisi_penanggung_jawab}")
    print(f"Timeline: {result.tindak_lanjut.timeline}")

    # Tampilkan hasil diskusi council (jika ada)
    if result.council_discussion and result.council_discussion.status == "success":
        print(f"\n=== Diskusi Council ===")
        print(f"Konsensus: {result.council_discussion.konsensus}")
        print(f"Rekomendasi Kolektif: {result.council_discussion.rekomendasi_kolektif}")
        print(f"\nPosisi Fraksi:")
        for fraksi, posisi in result.council_discussion.posisi_fraksi.items():
            print(f"  - {fraksi}: {posisi}")

asyncio.run(main())
```

## 🏗️ Arsitektur Pipeline

```mermaid
sequenceDiagram
    participant User
    participant Gradio UI
    participant DPRSimulator
    participant MemberFactory
    participant AbsorbAgent
    participant CompileAgent
    participant FollowUpAgent
    participant OpenAI API

    Note over User,OpenAI API: Fase Inisialisasi
    User->>Gradio UI: Konfigurasi jumlah anggota DPR
    Gradio UI->>DPRSimulator: create_members(count)
    DPRSimulator->>MemberFactory: Buat anggota DPR
    MemberFactory-->>DPRSimulator: List[DPRMember] (50-575 anggota)
    DPRSimulator-->>Gradio UI: Anggota DPR siap

    Note over User,OpenAI API: Fase Pemrosesan Aspirasi
    User->>Gradio UI: Submit aspirasi rakyat
    Gradio UI->>DPRSimulator: process_aspirasi(aspirasi, sample_size)

    Note over DPRSimulator,OpenAI API: Tahap 1: Menyerap (Absorpsi)
    DPRSimulator->>DPRSimulator: Filter anggota relevan
    loop Batch Processing (10 anggota/batch)
        DPRSimulator->>AbsorbAgent: invoke(member, aspirasi)
        AbsorbAgent->>OpenAI API: Analisis dari perspektif anggota
        OpenAI API-->>AbsorbAgent: Tingkat relevansi + poin kunci
        AbsorbAgent-->>DPRSimulator: AbsorpsiResponse
    end
    DPRSimulator->>Gradio UI: Update: X anggota merespons

    Note over DPRSimulator,OpenAI API: Tahap 2: Menghimpun (Kompilasi)
    DPRSimulator->>CompileAgent: invoke(all_responses)
    CompileAgent->>OpenAI API: Agregasi konsensus dari semua anggota
    OpenAI API-->>CompileAgent: Ringkasan + tema utama + fraksi
    CompileAgent-->>DPRSimulator: KompilasiResponse
    DPRSimulator->>Gradio UI: Update: Kompilasi selesai

    Note over DPRSimulator,OpenAI API: Tahap 3: Diskusi Council
    DPRSimulator->>CouncilDiscussionAgent: invoke(aspirasi, responses, members)
    CouncilDiscussionAgent->>OpenAI API: Simulasi deliberasi parlemen
    OpenAI API-->>CouncilDiscussionAgent: Diskusi multi-putaran + konsensus
    CouncilDiscussionAgent-->>DPRSimulator: CouncilDiscussionResponse
    DPRSimulator->>Gradio UI: Update: Diskusi council selesai

    Note over DPRSimulator,OpenAI API: Tahap 4: Menindaklanjuti
    DPRSimulator->>FollowUpAgent: invoke(kompilasi, aspirasi)
    FollowUpAgent->>OpenAI API: Generate action plan konkret
    OpenAI API-->>FollowUpAgent: Langkah + timeline + anggaran + pihak terlibat
    FollowUpAgent-->>DPRSimulator: TindakLanjutResponse

    DPRSimulator-->>Gradio UI: PipelineResult (lengkap)
    Gradio UI-->>User: Tampilkan hasil + visualisasi + biaya
```

**Alur Pemrosesan:**

### 1. Tahap Absorpsi (Menyerap)

- Setiap anggota DPR (AI agent) menganalisis aspirasi dari perspektif mereka
- Sistem memfilter anggota yang relevan berdasarkan keahlian dan daerah pemilihan
- Pemrosesan paralel dalam batch (default: 10 anggota per batch)
- Menentukan tingkat relevansi: Tinggi/Sedang/Rendah (Prioritas: Komisi > Dapil)
- Mengidentifikasi poin-poin kunci dan memberikan rekomendasi awal
- **Menghasilkan Output Persona:**
  - **Sikap (Sentiment):** Positif/Negatif/Netral/Kritis
  - **Tanggapan Lisan (Quote):** Statement politik sesuai gaya fraksi
- **Output:** `AbsorpsiResponse` untuk setiap anggota

### 2. Tahap Kompilasi (Menghimpun)

- Mengagregasi semua tanggapan anggota menjadi satu konsensus
- Mengidentifikasi tema utama yang muncul dari berbagai perspektif
- Mencatat fraksi-fraksi politik yang terlibat
- Menghitung statistik partisipasi (jumlah anggota, distribusi relevansi)
- **Output:** `KompilasiResponse` dengan ringkasan kolektif dan rekomendasi tindak lanjut

### 3. Tahap Diskusi Council (Council Discussion)

- Mensimulasikan deliberasi parlemen antar anggota DPR yang relevan
- Anggota menyampaikan posisi dan argumen sesuai ideologi fraksi mereka
- Terjadi debat multi-putaran dengan tanggapan antar anggota
- Menunjukkan dinamika fraksi (koalisi vs oposisi)
- Membentuk konsensus atau mengidentifikasi deadlock
- Menghasilkan rekomendasi kolektif berdasarkan hasil diskusi
- **Output:** `CouncilDiscussionResponse` dengan transkrip diskusi, posisi fraksi, dan tingkat konsensus

### 4. Tahap Tindak Lanjut (Menindaklanjuti)

- Menentukan langkah-langkah konkret tindak lanjut berdasarkan kompilasi dan diskusi council
- Menetapkan komisi DPR yang bertanggung jawab
- Membuat timeline realistis untuk implementasi
- Menentukan mekanisme (RDP/Hearing/Kunjungan Kerja/dll)
- Mengestimasi anggaran dengan rincian per item dan sumber dana
- Menetapkan indikator keberhasilan yang terukur
- Mengidentifikasi pihak-pihak yang perlu dilibatkan (Kementerian, Pemda, LSM, dll)
- **Output:** `TindakLanjutResponse` dengan action plan lengkap dan terstruktur

## 🤝 Kontribusi

Kontribusi sangat diterima! Silakan submit Pull Request atau buka Issue untuk diskusi fitur baru.

## 📄 Lisensi

MIT License - bebas digunakan untuk keperluan riset dan edukasi.

---
