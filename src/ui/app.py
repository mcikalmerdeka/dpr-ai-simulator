"""Gradio UI for DPR Simulator."""

import asyncio
import json
from datetime import datetime
from typing import List, Generator, Tuple, Any

import gradio as gr
import pandas as pd

from ..config import settings
from ..core import DPRSimulator, DPRMemberFactory
from ..models import Aspirasi, DPRMember


# Custom CSS for modern look
CUSTOM_CSS = """
:root {
    --primary-color: #1a365d;
    --secondary-color: #2c5282;
    --accent-color: #ed8936;
    --bg-dark: #0f172a;
    --bg-card: #1e293b;
    --text-primary: #f1f5f9;
    --text-secondary: #94a3b8;
}

.gradio-container {
    font-family: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    background: linear-gradient(135deg, var(--bg-dark) 0%, #1e293b 100%) !important;
}

.main-header {
    text-align: center;
    padding: 2rem;
    background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
    border-radius: 16px;
    margin-bottom: 1.5rem;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
}

.main-header h1 {
    color: white;
    font-size: 2.5rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
}

.main-header p {
    color: #e2e8f0;
    font-size: 1.1rem;
}

.stat-card {
    background: var(--bg-card);
    border-radius: 12px;
    padding: 1.5rem;
    text-align: center;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.stat-card h3 {
    color: var(--accent-color);
    font-size: 2rem;
    font-weight: 700;
}

.stat-card p {
    color: var(--text-secondary);
    font-size: 0.9rem;
}

.result-section {
    background: var(--bg-card);
    border-radius: 12px;
    padding: 1.5rem;
    margin-top: 1rem;
    border-left: 4px solid var(--accent-color);
}

.chatbot-container {
    border-radius: 12px !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
}

footer {
    display: none !important;
}
"""


def format_result_for_display(result) -> str:
    """Format pipeline result for display in the chat."""
    output = []

    # Header
    output.append("\n\n")
    output.append("==========================================\n")
    output.append("## 📊 Hasil Pemrosesan Aspirasi\n")

    # Aspirasi info
    output.append(f"**Aspirasi Diterima:** {result.aspirasi.content}\n")
    output.append(f"**Kategori:** {result.aspirasi.category}")
    output.append(f"**Sumber:** {result.aspirasi.source}")
    output.append(f"**Prioritas:** {result.aspirasi.priority}\n")

    # Simulation Details
    sim = result.simulation_details
    output.append("---\n### 🏛️ Detail Simulasi\n")
    
    # Visual representation of member selection
    total = sim.total_anggota_dpr
    selected = sim.anggota_relevan_terpilih
    responded = sim.anggota_merespons
    
    output.append(f"**Total Anggota DPR dalam Simulasi:** {total} orang")
    output.append(f"**Sample Size yang Diminta:** {sim.sample_size_requested} orang")
    output.append(f"**Anggota Relevan Terpilih:** {selected} orang")
    output.append(f"**Anggota yang Merespons:** {responded} orang\n")
    
    # Relevance breakdown
    output.append("**Breakdown Relevansi Tanggapan:**")
    output.append(f"- 🟢 Relevansi Tinggi: {sim.anggota_relevansi_tinggi} anggota")
    output.append(f"- 🟡 Relevansi Sedang: {sim.anggota_relevansi_sedang} anggota")
    output.append(f"- 🔴 Relevansi Rendah: {sim.anggota_relevansi_rendah} anggota\n")
    
    # Factions represented
    if sim.fraksi_terwakili:
        output.append(f"**Fraksi Terwakili ({len(sim.fraksi_terwakili)}):** {', '.join(sim.fraksi_terwakili)}\n")
    
    # Provinces represented
    if sim.provinsi_terwakili:
        output.append(f"**Provinsi Terwakili ({len(sim.provinsi_terwakili)}):** {', '.join(sim.provinsi_terwakili)}\n")

    # Stats
    output.append("---\n### 📈 Statistik Pemrosesan\n")
    output.append(f"- **Status Kompilasi:** {result.kompilasi.status}")
    output.append(f"- **Total Biaya Pemrosesan:** ${result.total_cost_usd:.6f} (~Rp {result.total_cost_usd * 16800:.0f})\n")

    # Kompilasi
    if result.kompilasi.status == "terkumpul":
        output.append("---\n### 📋 Kompilasi Tanggapan\n")
        output.append(f"**Ringkasan:** {result.kompilasi.ringkasan}\n")

        if result.kompilasi.tema_utama:
            output.append("**Tema Utama:**")
            for tema in result.kompilasi.tema_utama:
                output.append(f"- {tema}")

        if result.kompilasi.fraksi_terlibat:
            output.append(f"\n**Fraksi Terlibat:** {', '.join(result.kompilasi.fraksi_terlibat)}")

        output.append(f"\n**Rekomendasi:** {result.kompilasi.rekomendasi_tindak_lanjut}\n")

    # Tindak Lanjut
    if result.tindak_lanjut.komisi_penanggung_jawab:
        output.append("---\n### 📝 Rencana Tindak Lanjut DPR\n")
        output.append(f"**Komisi Penanggung Jawab:** {result.tindak_lanjut.komisi_penanggung_jawab}")
        output.append(f"**Mekanisme:** {result.tindak_lanjut.mekanisme}")
        output.append(f"**Timeline:** {result.tindak_lanjut.timeline}\n")

        if result.tindak_lanjut.langkah_tindak_lanjut:
            output.append("**Langkah-langkah Tindak Lanjut:**")
            for i, langkah in enumerate(result.tindak_lanjut.langkah_tindak_lanjut, 1):
                output.append(f"{i}. {langkah}")

        if result.tindak_lanjut.indikator_keberhasilan:
            output.append("\n**Indikator Keberhasilan:**")
            for indikator in result.tindak_lanjut.indikator_keberhasilan:
                output.append(f"- {indikator}")

        # Estimasi Anggaran dari AI DPR
        if result.tindak_lanjut.estimasi_anggaran:
            output.append("\n---\n### 💰 Estimasi Anggaran (Dihitung oleh AI DPR)\n")
            output.append(f"**Total Estimasi:** {result.tindak_lanjut.estimasi_anggaran}\n")
            
            if result.tindak_lanjut.rincian_anggaran:
                output.append("**Rincian Alokasi Anggaran:**")
                for rincian in result.tindak_lanjut.rincian_anggaran:
                    output.append(f"- {rincian}")
            
            if result.tindak_lanjut.sumber_dana:
                output.append(f"\n**Sumber Dana:** {result.tindak_lanjut.sumber_dana}")

    return "\n".join(output)


def members_to_dataframe(members: List[DPRMember]) -> pd.DataFrame:
    """Convert list of DPRMember to a DataFrame for display."""
    if not members:
        return pd.DataFrame(columns=["ID", "Nama", "Fraksi", "Dapil", "Provinsi", "Keahlian"])
    
    data = []
    for m in members:
        data.append({
            "ID": m.id,
            "Nama": m.name,
            "Fraksi": m.faction,
            "Dapil": m.dapil,
            "Provinsi": m.province,
            "Keahlian": ", ".join(m.expertise) if m.expertise else "-",
        })
    return pd.DataFrame(data)


async def process_aspirasi_async(
    content: str,
    category: str,
    source: str,
    priority: str,
    member_count: int,
    sample_size: int,
    api_key: str,
) -> Generator:
    """Process aspiration asynchronously with streaming updates.
    
    Yields tuples of (messages, all_members_df, relevant_members_df, responding_members_df)
    """

    # Empty dataframes for initial state
    empty_df = pd.DataFrame(columns=["ID", "Nama", "Fraksi", "Dapil", "Provinsi", "Keahlian"])
    empty_response_df = pd.DataFrame(columns=["ID", "Nama", "Fraksi", "Provinsi", "Relevansi", "Alasan"])

    # Validate API key
    if not api_key:
        yield (
            [{"role": "assistant", "content": "❌ Error: Mohon masukkan OpenAI API Key terlebih dahulu."}],
            empty_df, empty_df, empty_response_df
        )
        return

    # Initialize simulator
    simulator = DPRSimulator(api_key=api_key)
    simulator.create_members(member_count)
    
    # Get all members for display
    all_members = simulator.members
    all_members_df = members_to_dataframe(all_members)

    # Create aspiration
    aspirasi = Aspirasi(
        id=1,
        source=source,
        category=category,
        content=content,
        priority=priority,
        timestamp=datetime.now(),
    )

    # Progress messages - Gradio 6.x uses OpenAI-style message format by default
    messages = []

    def progress_callback(msg: str):
        messages.append({"role": "assistant", "content": msg})

    # Initial message
    user_msg = f"**Aspirasi Baru**\n\n{content}\n\n*Kategori: {category} | Sumber: {source} | Prioritas: {priority}*"
    messages.append({"role": "user", "content": user_msg})
    messages.append({"role": "assistant", "content": f"=========================================="})
    messages.append({"role": "assistant", "content": f"🚀 Memulai simulasi dengan {member_count} anggota DPR"})
    
    # Yield initial state with all members populated
    yield (messages, all_members_df, empty_df, empty_response_df)

    # Process
    try:
        result = await simulator.process_aspirasi(
            aspirasi,
            sample_size=sample_size,
            progress_callback=progress_callback,
        )

        # Build relevant members dataframe
        relevant_members = []
        if result.simulation_details and result.simulation_details.relevant_member_ids:
            for m in all_members:
                if m.id in result.simulation_details.relevant_member_ids:
                    relevant_members.append(m)
        relevant_members_df = members_to_dataframe(relevant_members)
        
        # Build responding members dataframe with their responses
        responding_data = []
        for resp in result.tanggapan_anggota:
            # Find the member
            member = next((m for m in all_members if m.id == resp.member_id), None)
            if member:
                responding_data.append({
                    "ID": member.id,
                    "Nama": member.name,
                    "Fraksi": member.faction,
                    "Provinsi": member.province,
                    "Relevansi": resp.relevansi,
                    "Alasan": resp.alasan_relevansi,
                })
        responding_members_df = pd.DataFrame(responding_data) if responding_data else empty_response_df

        # Final result
        messages.append({"role": "assistant", "content": format_result_for_display(result)})
        yield (messages, all_members_df, relevant_members_df, responding_members_df)

    except Exception as e:
        messages.append({"role": "assistant", "content": f"❌ Error: {str(e)}"})
        yield (messages, all_members_df, empty_df, empty_response_df)


def process_aspirasi_sync(
    content: str,
    category: str,
    source: str,
    priority: str,
    member_count: int,
    sample_size: int,
    api_key: str,
    history: List,
):
    """Synchronous wrapper for async processing.
    
    Yields tuples of (messages, all_members_df, relevant_members_df, responding_members_df)
    """
    # Run async function
    async def run():
        async for result in process_aspirasi_async(
            content, category, source, priority, member_count, sample_size, api_key
        ):
            yield result

    # Use asyncio to run
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        gen = run()
        while True:
            try:
                result = loop.run_until_complete(gen.__anext__())
                yield result
            except StopAsyncIteration:
                break
    finally:
        loop.close()


def create_app() -> gr.Blocks:
    """Create the Gradio application."""

    # Create theme for Gradio 6.x
    theme = gr.themes.Base(
        primary_hue="blue",
        secondary_hue="orange",
        neutral_hue="slate",
        font=gr.themes.GoogleFont("IBM Plex Sans"),
    ).set(
        body_background_fill="linear-gradient(135deg, #0f172a 0%, #1e293b 100%)",
        block_background_fill="#1e293b",
        block_border_color="rgba(255, 255, 255, 0.1)",
        input_background_fill="#334155",
        button_primary_background_fill="#ed8936",
        button_primary_background_fill_hover="#dd6b20",
    )

    with gr.Blocks(title="DPR Simulator - AI Parliament") as app:

        # Header
        gr.HTML("""
        <div class="main-header">
            <h1>🏛️ DPR Simulator</h1>
            <p>Simulasi AI untuk Menyerap, Menghimpun, dan Menindaklanjuti Aspirasi Rakyat</p>
        </div>
        """)

        with gr.Row():
            # Left column - Input
            with gr.Column(scale=1):
                gr.Markdown("### ⚙️ Konfigurasi")

                api_key = gr.Textbox(
                    label="OpenAI API Key",
                    placeholder="sk-...",
                    type="password",
                    info="API key Anda tidak disimpan dan hanya digunakan untuk sesi ini",
                )

                with gr.Accordion("Pengaturan Simulasi", open=False):
                    member_count = gr.Slider(
                        minimum=10,
                        maximum=575,
                        value=50,
                        step=10,
                        label="Jumlah Anggota DPR",
                        info="580 adalah jumlah anggota DPR RI periode 2024-2029 ini.\nTapi itu kebanyakan gak sih?",
                    )
                    sample_size = gr.Slider(
                        minimum=5,
                        maximum=100,
                        value=20,
                        step=5,
                        label="Sample Size per Aspirasi",
                        info="Jumlah anggota yang akan memproses setiap aspirasi",
                    )
                    
                    gr.Markdown("""
                    <div style='background: #1e3a5f; padding: 12px; border-radius: 8px; margin-top: 12px; border-left: 4px solid #3b82f6;'>
                    <strong style='color: #60a5fa;'>💡 Catatan Biaya API:</strong>
                    <p style='color: #e2e8f0; margin: 8px 0 0 0; font-size: 0.9em;'>
                    Dengan <strong>default parameter</strong> (50 anggota DPR, sample size 20) dan menggunakan 
                    contoh aspirasi <em>Banjir Rob Jakarta Utara</em>, biaya total pemrosesan hanya 
                    <strong style='color: #34d399;'>$0.0025</strong> atau <strong style='color: #34d399;'>~Rp 41,6</strong>
                    </p>
                    </div>
                    """, elem_classes="cost-note")

                gr.Markdown("### 📝 Input Aspirasi")

                content = gr.Textbox(
                    label="Isi Aspirasi",
                    placeholder="Masukkan aspirasi rakyat yang ingin diproses...",
                    lines=4,
                    info="""• DPR memang kadang tidak jelas dalam menangani aspirasi, tapi mungkin kita juga ada salahnya dalam tidak memberikannya dalam bentuk yang detail dan benar.
                    • Direkomendasikan untuk menggunakan template yang telah disediakan di bagian bawah aplikasi.""",
                )

                with gr.Row():
                    category = gr.Dropdown(
                        choices=[
                            "Ekonomi", "Pendidikan", "Kesehatan", "Infrastruktur",
                            "Pertanian", "Kelautan", "Energi", "Hukum", "Teknologi",
                            "Sosial", "Lingkungan", "Pertahanan", "Keuangan",
                            "Industri", "Perdagangan", "Pariwisata"
                        ],
                        value="Pendidikan",
                        label="Kategori",
                    )
                    priority = gr.Dropdown(
                        choices=["Tinggi", "Sedang", "Rendah"],
                        value="Tinggi",
                        label="Prioritas",
                    )

                source = gr.Dropdown(
                    choices=[
                        "Jawa Barat", "Jawa Timur", "Jawa Tengah", "Sumatra Utara",
                        "DKI Jakarta", "Sulawesi Selatan", "Banten", "Lampung",
                        "Kalimantan Timur", "Aceh", "Sumatra Barat", "Riau",
                        "Papua", "Bali", "Yogyakarta"
                    ],
                    value="Jawa Barat",
                    label="Sumber/Daerah",
                )

                submit_btn = gr.Button(
                    "🚀 Proses Aspirasi",
                    variant="primary",
                    size="lg",
                )

            # Right column - Output
            with gr.Column(scale=2):
                gr.Markdown("### 💬 Hasil Simulasi")

                chatbot = gr.Chatbot(
                    label="Proses & Hasil",
                    height=400,
                    buttons=["copy"],
                )

                clear_btn = gr.Button("🗑️ Bersihkan", variant="secondary")
                
                # Simulation Details Panel
                gr.Markdown("### 🏛️ Detail Simulasi")
                
                with gr.Accordion("📋 Semua Anggota DPR (Generated)", open=False):
                    all_members_df = gr.Dataframe(
                        headers=["ID", "Nama", "Fraksi", "Dapil", "Provinsi", "Keahlian"],
                        label="Daftar Semua Anggota DPR dalam Simulasi",
                        interactive=False,
                        wrap=True,
                    )
                
                with gr.Accordion("🎯 Anggota Relevan Terpilih (Sample)", open=False):
                    relevant_members_df = gr.Dataframe(
                        headers=["ID", "Nama", "Fraksi", "Dapil", "Provinsi", "Keahlian"],
                        label="Anggota yang Terpilih Berdasarkan Relevansi",
                        interactive=False,
                        wrap=True,
                    )
                
                with gr.Accordion("✅ Anggota yang Merespons & Relevansinya", open=True):
                    responding_members_df = gr.Dataframe(
                        headers=["ID", "Nama", "Fraksi", "Provinsi", "Relevansi", "Alasan"],
                        label="Detail Respons dari Setiap Anggota",
                        interactive=False,
                        wrap=True,
                    )

        # Example aspirations - store full text separately
        aspiration_1 = """Pendidikan Digital Daerah Terpencil - Kabupaten Garut
                    
LATAR BELAKANG:
Di 47 sekolah dasar di Kabupaten Garut (Kecamatan Cikajang, Bungbulang, dan Bayongbong), sebanyak 12.450 siswa tidak memiliki akses internet untuk pembelajaran digital. Saat pandemi, tingkat putus sekolah mencapai 23% dan nilai rata-rata ujian turun 18 poin dari sebelumnya.

DATA & FAKTA PERMASALAHAN:
- 47 SD tidak memiliki koneksi internet sama sekali (0% coverage)
- 156 guru belum pernah terlatih menggunakan platform e-learning
- Hanya 15% siswa (1.867 anak) memiliki perangkat untuk belajar online
- Anggaran BOS saat ini Rp 2.1 juta/sekolah tidak mencukupi untuk infrastruktur digital
- Nilai rata-rata ujian turun dari 72 menjadi 54 (penurunan 25%)
- 2.863 siswa terancam putus sekolah karena kesulitan mengikuti pembelajaran

SOLUSI YANG DIUSULKAN MASYARAKAT:
1. Penambahan alokasi dana BOS khusus untuk infrastruktur digital di 47 sekolah
2. Instalasi internet (via Starlink atau tower BTS) di 3 kecamatan terpencil tersebut
3. Pengadaan tablet/laptop untuk 2.500 siswa dari keluarga kurang mampu
4. Program pelatihan guru intensif untuk 156 guru dalam menggunakan teknologi pembelajaran
5. Pengadaan konten pembelajaran digital yang sesuai dengan kurikulum lokal

TARGET YANG DIHARAPKAN:
- 100% sekolah di 3 kecamatan tersebut terhubung internet
- Semua guru terlatih menggunakan platform e-learning
- Nilai ujian kembali ke level sebelum pandemi (minimal 70)
- Tingkat putus sekolah turun drastis ke angka normal (<5%)
- Program dapat berjalan dalam waktu maksimal 2 tahun

PIHAK YANG PERLU DILIBATKAN:
- Dinas Pendidikan Kabupaten Garut
- Kementerian Pendidikan dan Kebudayaan
- Komisi X DPR RI
- Provider telekomunikasi (Telkom, Indosat, XL)"""
        
        aspiration_2 = """Krisis Produktivitas Pertanian - Kabupaten Ngawi & Madiun
                    
LATAR BELAKANG:
Gabungan kelompok tani di 8 kecamatan Kabupaten Ngawi dan Madiun (meliputi 15.200 hektar sawah dan 4.850 petani) mengalami penurunan produktivitas padi dari 6.2 ton/ha menjadi 4.8 ton/ha dalam 2 tahun terakhir. Hal ini disebabkan kenaikan harga pupuk subsidi 85% dan kelangkaan bibit unggul.

DATA & FAKTA PERMASALAHAN:
- Harga pupuk Urea naik drastis dari Rp 1.800/kg menjadi Rp 3.330/kg (kenaikan 85%)
- Kuota pupuk bersubsidi berkurang 40% dibanding 2 tahun lalu (hanya 450 ton tersedia)
- Bibit unggul (Inpari 32, IR64) hanya tersedia untuk 30% dari kebutuhan total
- Produktivitas turun 22.6% dalam 2 tahun (dari 6.2 ton/ha ke 4.8 ton/ha)
- 1.240 petani terancam gulung tikar dan terpaksa jual lahan
- Pendapatan petani anjlok rata-rata 45% per musim tanam

SOLUSI YANG DIUSULKAN MASYARAKAT:
1. Peningkatan kuota pupuk bersubsidi untuk wilayah Ngawi-Madiun (kebutuhan: 1.200 ton/musim)
2. Program distribusi bibit unggul yang lebih merata (kebutuhan: 608 ton bibit untuk 15.200 ha)
3. Bantuan alat dan mesin pertanian (alsintan) untuk 12 kelompok tani agar lebih efisien
4. Pelatihan sistem pertanian modern (pertanian presisi & System of Rice Intensification)
5. Program asuransi pertanian untuk melindungi 4.850 petani dari gagal panen

TARGET YANG DIHARAPKAN:
- Produktivitas kembali ke level normal (6.2 ton/ha) dalam 1-2 tahun
- Tidak ada lagi petani yang gulung tikar atau jual lahan
- Akses pupuk subsidi dan bibit unggul merata ke seluruh petani
- Pendapatan petani stabil dan meningkat kembali

PIHAK YANG PERLU DILIBATKAN:
- Dinas Pertanian Kabupaten Ngawi dan Madiun
- Kementerian Pertanian RI
- Komisi IV DPR RI
- PT Pupuk Indonesia dan distributor pupuk
- Balai Besar Penelitian Tanaman Padi (BB Padi)"""
        
        aspiration_3 = """Banjir Rob Permanen Jakarta Utara - Penjaringan, Pluit, Muara Baru

LATAR BELAKANG:
Kelurahan Penjaringan, Pluit, dan Muara Baru di Jakarta Utara mengalami banjir rob (air laut pasang) permanen setinggi 20-50 cm selama 6-8 jam setiap hari. Kondisi ini telah berlangsung selama 3 tahun terakhir dan semakin parah. Penurunan tanah (land subsidence) 7-15 cm per tahun memperburuk situasi.

DATA & FAKTA PERMASALAHAN:
- 3 kelurahan tergenang air laut 365 hari/tahun (tinggi 20-50 cm saat air pasang)
- 28.500 warga terdampak langsung, ribuan rumah terendam setiap hari
- 12 km jalan protokol rusak parah dan nyaris tidak bisa dilalui kendaraan
- 840 rumah warga terendam permanen dan tidak layak huni
- 4.200 UMKM terpaksa tutup atau pindah lokasi usaha
- Sistem drainase eksisting hanya mampu menangani 40% volume air rob
- 8 pompa air di titik kritis sering mati karena overload
- Puskesmas Kelurahan Penjaringan terendam, layanan kesehatan terganggu
- Anak-anak tidak bisa sekolah dengan normal karena akses jalan tergenang

SOLUSI YANG DIUSULKAN MASYARAKAT:
1. Pembangunan tanggul laut (sea wall) yang tinggi dan kokoh sepanjang 8 km pantai
2. Perbaikan dan peningkatan kapasitas sistem drainase yang sudah tidak memadai
3. Pengadaan pompa air berkapasitas besar untuk memompa air rob keluar
4. Pembangunan kolam-kolam penampungan air (retensi) di beberapa titik strategis
5. Program relokasi prioritas untuk 840 keluarga yang rumahnya terendam permanen
6. Rehabilitasi dan elevasi (peninggian) jalan-jalan utama yang selalu tergenang
7. Sistem peringatan dini (early warning) banjir rob + pompa mobile siaga 24 jam

TARGET YANG DIHARAPKAN:
- Banjir rob berkurang signifikan atau hilang sama sekali
- Warga bisa beraktivitas normal tanpa terganggu genangan
- UMKM bisa beroperasi kembali dan ekonomi lokal pulih
- Akses kesehatan dan pendidikan kembali lancar
- Tidak ada lagi korban jiwa akibat banjir rob

PIHAK YANG PERLU DILIBATKAN:
- Pemerintah Provinsi DKI Jakarta
- Kementerian PUPR (Pekerjaan Umum dan Perumahan Rakyat)
- Kementerian Kelautan dan Perikanan
- Komisi V DPR RI
- BPBD DKI Jakarta
- Ahli teknik sipil dan hidrologi"""
        
        aspiration_4 = """Tambang Ilegal & Pencemaran Sungai - Kutai Kartanegara, Kalimantan Timur

LATAR BELAKANG:
Di Kabupaten Kutai Kartanegara, aktivitas tambang batubara ilegal telah merusak 24.800 hektar hutan lindung dan mencemari 3 sungai utama (Mahakam, Kedang Pahu, Belayan) yang menjadi sumber air bersih bagi 185.000 warga di 42 desa. Pencemaran sudah berlangsung sejak 2020 dan semakin parah setiap tahunnya.

DATA & FAKTA PERMASALAHAN:
- 24.800 hektar hutan lindung gundul akibat 67 lokasi tambang ilegal sejak 2020
- 3 sungai utama tercemar berat dengan kadar merkuri 0.08 mg/L (8x lipat batas aman WHO)
- pH air sungai mencapai 4.2 (sangat asam) - tidak layak konsumsi
- 185.000 warga di 42 desa kehilangan akses air bersih yang aman
- 1.240 kasus ISPA (Infeksi Saluran Pernapasan Akut) per bulan akibat polusi udara
- 18 spesies satwa dilindungi (orangutan, bekantan, dll) habitat rusak dan terancam punah
- Banjir dan longsor meningkat drastis karena hilangnya tutupan hutan
- Anak-anak di 42 desa mengalami masalah kesehatan kronis

SOLUSI YANG DIUSULKAN MASYARAKAT:
1. Operasi gabungan Polda-TNI untuk menutup 67 lokasi tambang ilegal secara paksa
2. Penegakan hukum tegas terhadap pelaku tambang ilegal dan backing-nya
3. Rehabilitasi 24.800 hektar hutan dengan penanaman kembali (reforestasi masif)
4. Pembangunan instalasi pengolahan air minum (IPAM) di 8 titik strategis
5. Program alih profesi untuk 2.400 penambang ilegal ke usaha berkelanjutan (budidaya lebah madu, ekowisata, pertanian)
6. Penyediaan air bersih mobile darurat untuk 42 desa sampai sungai pulih
7. Sistem monitoring kualitas air real-time dengan sensor otomatis
8. Patroli drone dan satelit untuk mencegah tambang ilegal baru muncul

TARGET YANG DIHARAPKAN:
- Semua tambang ilegal ditutup permanen dalam 6-12 bulan
- Kualitas air sungai kembali memenuhi standar WHO dalam 2 tahun
- Hutan lindung pulih dengan jutaan pohon baru tertanam
- 185.000 warga mendapat akses air bersih yang aman
- Kasus ISPA dan masalah kesehatan turun drastis
- Habitat satwa liar pulih, populasi orangutan & bekantan stabil

PIHAK YANG PERLU DILIBATKAN:
- Kementerian Lingkungan Hidup dan Kehutanan (KLHK)
- Kementerian ESDM (Energi dan Sumber Daya Mineral)
- Polda Kalimantan Timur & TNI
- Pemerintah Provinsi Kaltim
- Komisi VII dan Komisi IV DPR RI
- BPBD dan Dinas Kesehatan Kutai Kartanegara"""
        
        aspiration_5 = """Kemacetan Ekstrem Ring Road Surabaya - Juanda ke Tanjung Perak

LATAR BELAKANG:
Jalan Raya Juanda - Ahmad Yani - Tanjung Perak (Ring Road Surabaya) sepanjang 28 km mengalami kemacetan parah hampir sepanjang hari (14-18 jam/hari). Kecepatan rata-rata hanya 12 km/jam padahal seharusnya bisa 60 km/jam. Kemacetan ini sudah berlangsung bertahun-tahun dan terus memburuk.

DATA & FAKTA PERMASALAHAN:
- 28 km ruas jalan macet total 14-18 jam per hari, hampir tidak bergerak
- Kecepatan rata-rata hanya 12 km/jam (seharusnya minimal 40-60 km/jam)
- 285.000 kendaraan per hari melewati ruas ini (jauh melampaui kapasitas maksimal 180 ribu)
- Waktu tempuh Bandara Juanda ke Pelabuhan Tanjung Perak: 3-3.5 jam (normalnya 30-40 menit)
- 2.400 truk kontainer parkir sembarangan di badan jalan, memperparah kemacetan
- Tidak ada alternatif transportasi umum massal yang efektif dan terpercaya
- Emisi kendaraan sangat tinggi, polusi udara parah
- Kerugian waktu, BBM terbuang, dan produktivitas menurun drastis

SOLUSI YANG DIUSULKAN MASYARAKAT:
1. Pembangunan jalan layang (elevated road) atau jalan bawah tanah sepanjang 28 km untuk enteng beban
2. Pengadaan sistem Bus Rapid Transit (BRT) massal dengan ratusan unit bus dan jadwal ketat 5 menit sekali
3. Pembangunan terminal khusus truk kontainer off-street agar tidak parkir sembarangan
4. Sistem Electronic Road Pricing (ERP) untuk membatasi kendaraan pribadi masuk di jam sibuk
5. Jalur khusus sepeda dan pejalan kaki untuk mengurangi ketergantungan kendaraan
6. Traffic Management Center (TMC) dengan teknologi AI untuk mengoptimalkan lampu merah
7. Program car-free day atau pembatasan kendaraan tertentu di hari/jam tertentu

TARGET YANG DIHARAPKAN:
- Kemacetan berkurang signifikan, kecepatan rata-rata naik minimal 3x lipat
- Waktu tempuh Juanda-Tanjung Perak turun drastis menjadi sekitar 45-50 menit
- Transportasi umum menjadi pilihan utama (target: 30-40% pengguna jalan beralih ke transportasi umum)
- Konsumsi BBM dan emisi CO2 turun drastis
- Produktivitas ekonomi Surabaya meningkat, tidak terbuang di jalan

PIHAK YANG PERLU DILIBATKAN:
- Pemerintah Kota Surabaya
- Pemerintah Provinsi Jawa Timur
- Kementerian PUPR (Pekerjaan Umum dan Perumahan Rakyat)
- Kementerian Perhubungan
- Komisi V DPR RI
- PT Angkasa Pura (Bandara Juanda)
- Pelindo (Pelabuhan Tanjung Perak)"""
        
        aspiration_6 = """Krisis Nelayan & Illegal Fishing - Kabupaten Bone, Sulawesi Selatan

LATAR BELAKANG:
Nelayan tradisional di 28 desa pesisir Kabupaten Bone mengalami penurunan tangkapan ikan yang sangat drastis, dari rata-rata 450 kg per trip menjadi hanya 144 kg per trip (turun 68%) dalam 4 tahun terakhir. Hal ini disebabkan oleh illegal fishing kapal asing dan kerusakan terumbu karang. 8.400 nelayan terancam kehilangan mata pencaharian.

DATA & FAKTA PERMASALAHAN:
- Tangkapan ikan turun drastis 68% dalam 4 tahun (dari 450 kg menjadi 144 kg per trip)
- Minimal 42 kapal asing melakukan illegal fishing di ZEE (Zona Ekonomi Eksklusif) Sulawesi tanpa izin
- 12.500 hektar terumbu karang rusak parah akibat pengeboman ikan (40% dari total area)
- 8.400 nelayan pendapatan anjlok dari Rp 4.5 juta menjadi Rp 1.4 juta per bulan
- Tidak ada fasilitas cold storage di 28 desa, ikan terbuang/busuk 30% sebelum dijual
- 2.100 anak nelayan terpaksa putus sekolah karena orang tua tidak mampu bayar biaya pendidikan
- Nelayan tidak memiliki alat tangkap modern dan GPS untuk keselamatan di laut

SOLUSI YANG DIUSULKAN MASYARAKAT:
1. Pengadaan kapal patroli cepat dan pesawat surveillance untuk monitoring illegal fishing 24/7
2. Penegakan hukum tegas terhadap kapal asing yang melanggar, ditenggelamkan sesuai UU
3. Rehabilitasi masif 12.500 hektar terumbu karang dengan transplantasi karang
4. Pembangunan cold storage (gudang pendingin) di 28 desa + pabrik es
5. Bantuan alat tangkap ikan modern dan GPS tracker untuk 8.400 nelayan
6. Program budidaya rumput laut dan kerapu sebagai sumber pendapatan alternatif
7. Beasiswa penuh untuk 2.100 anak nelayan dari SD sampai SMA

TARGET YANG DIHARAPKAN:
- Illegal fishing hilang total dari perairan Sulawesi
- Tangkapan ikan nelayan kembali normal atau bahkan meningkat
- Terumbu karang pulih sehingga ikan banyak kembali
- Pendapatan nelayan meningkat dan stabil
- Tidak ada lagi ikan terbuang karena ada cold storage
- Semua anak nelayan bisa sekolah sampai tamat

PIHAK YANG PERLU DILIBATKAN:
- Kementerian Kelautan dan Perikanan (KKP)
- TNI Angkatan Laut (patroli dan penegakan hukum)
- Pemerintah Provinsi Sulawesi Selatan
- Dinas Kelautan dan Perikanan Kabupaten Bone
- Komisi IV DPR RI
- Bakamla (Badan Keamanan Laut)"""
        
        aspiration_7 = """Kabut Asap & Kebakaran Hutan Berulang - Provinsi Riau

LATAR BELAKANG:
Provinsi Riau mengalami kebakaran hutan dan lahan (karhutla) masif seluas 94.500 hektar pada musim kemarau 2023, menghasilkan kabut asap tebal yang melumpuhkan seluruh aktivitas di 7 kabupaten/kota. Indeks Standar Pencemar Udara (ISPU) mencapai 650 (kategori berbahaya). Masalah ini berulang setiap tahun dan semakin parah.

DATA & FAKTA PERMASALAHAN:
- 94.500 hektar lahan terbakar pada musim kemarau 2023 (naik 120% dari tahun sebelumnya)
- ISPU mencapai 650 (sangat berbahaya) selama 45 hari berturut-turut
- 2.4 juta warga terdampak kabut asap, tidak bisa beraktivitas normal
- 48.000 kasus ISPA (Infeksi Saluran Pernapasan Akut), 124 orang meninggal dunia
- 840 sekolah terpaksa tutup selama 3 minggu, 320.000 siswa pembelajaran terganggu
- Bandara Sultan Syarif Kasim II Pekanbaru tutup 18 hari, ribuan penerbangan batal
- Ekonomi lumpuh total: pariwisata mati, industri berhenti, pertanian hancur
- Kebakaran diduga disengaja (pembakaran lahan untuk perkebunan sawit dan pertanian)

SOLUSI YANG DIUSULKAN MASYARAKAT:
1. Pembangunan menara pemantau kebakaran dengan sensor IoT dan satelit real-time di seluruh Riau
2. Pengadaan helikopter water bomber dan ratusan mobil pemadam kebakaran
3. Rekrutmen dan pelatihan ribuan relawan pemadam kebakaran komunitas di setiap desa
4. Restorasi masif 94.500 hektar lahan gambut dengan sistem kanal blocking dan rewetting
5. Program alih profesi untuk petani dari pembakaran lahan ke sistem pertanian tanpa bakar
6. Penegakan hukum tegas: Pengadilan khusus karhutla dan denda berat untuk pelaku
7. Edukasi masif ke masyarakat tentang bahaya membakar lahan
8. Sistem early warning dan aplikasi mobile untuk melaporkan titik api

TARGET YANG DIHARAPKAN:
- Luas karhutla turun drastis minimal 80-90% dalam 2 tahun
- ISPU tetap di bawah 100 (kategori baik) sepanjang tahun
- Tidak ada lagi kematian akibat kabut asap
- Bandara dan sekolah operasional normal 100% tanpa gangguan
- Lahan gambut pulih dan tidak mudah terbakar lagi
- Emisi CO2 berkurang drastis, kontribusi ke perubahan iklim turun

PIHAK YANG PERLU DILIBATKAN:
- Kementerian Lingkungan Hidup dan Kehutanan (KLHK)
- Pemerintah Provinsi Riau
- BNPB (Badan Nasional Penanggulangan Bencana)
- Polda Riau (penegakan hukum)
- Komisi IV dan VII DPR RI
- Perusahaan perkebunan sawit (edukasi dan pengawasan)"""
        
        gr.Markdown("### 📚 Contoh Aspirasi Terstruktur")
        gr.Examples(
            examples=[
                [aspiration_1, "Pendidikan", "Jawa Barat", "Tinggi"],
                [aspiration_2, "Pertanian", "Jawa Timur", "Tinggi"],
                [aspiration_3, "Infrastruktur", "DKI Jakarta", "Tinggi"],
                [aspiration_4, "Lingkungan", "Kalimantan Timur", "Tinggi"],
                [aspiration_5, "Infrastruktur", "Jawa Timur", "Tinggi"],
                [aspiration_6, "Kelautan", "Sulawesi Selatan", "Tinggi"],
                [aspiration_7, "Lingkungan", "Riau", "Tinggi"],
            ],
            example_labels=[
                "📚 Pendidikan Digital Daerah Terpencil (Jawa Barat)",
                "🌾 Subsidi Pupuk & Produktivitas Pertanian (Jawa Timur)",
                "🌊 Banjir Permanen Jakarta Utara",
                "🌳 Deforestasi & Pencemaran Sungai (Kalimantan)",
                "🚗 Kemacetan Ekstrem Surabaya Ring Road",
                "🐟 Krisis Nelayan & Illegal Fishing (Sulawesi)",
                "🔥 Kabut Asap & Kebakaran Hutan (Riau)",
            ],
            inputs=[content, category, source, priority],
        )

        # Footer info
        gr.Markdown("""
        ---
        <center>
        <small>
        💡 <b>Tentang DPR Simulator:</b> Aplikasi ini mensimulasikan bagaimana AI dapat menggantikan fungsi DPR
        dalam menyerap, menghimpun, dan menindaklanjuti aspirasi rakyat dengan biaya yang jauh lebih efisien.
        </small>
        </center>
        """)

        # Event handlers
        submit_btn.click(
            fn=process_aspirasi_sync,
            inputs=[content, category, source, priority, member_count, sample_size, api_key, chatbot],
            outputs=[chatbot, all_members_df, relevant_members_df, responding_members_df],
        )

        # Clear all outputs
        empty_df = pd.DataFrame(columns=["ID", "Nama", "Fraksi", "Dapil", "Provinsi", "Keahlian"])
        empty_response_df = pd.DataFrame(columns=["ID", "Nama", "Fraksi", "Provinsi", "Relevansi", "Alasan"])
        
        clear_btn.click(
            fn=lambda: ([], empty_df, empty_df, empty_response_df),
            outputs=[chatbot, all_members_df, relevant_members_df, responding_members_df],
        )

    return app


def launch_app():
    """Launch the Gradio application."""
    app = create_app()
    app.launch(
        server_name=settings.gradio_server_name,
        server_port=settings.gradio_server_port,
        share=settings.gradio_share,
        theme=gr.themes.Base(
            primary_hue="blue",
            secondary_hue="orange",
            neutral_hue="slate",
            font=gr.themes.GoogleFont("IBM Plex Sans"),
        ).set(
            body_background_fill="linear-gradient(135deg, #0f172a 0%, #1e293b 100%)",
            block_background_fill="#1e293b",
            block_border_color="rgba(255, 255, 255, 0.1)",
            input_background_fill="#334155",
            button_primary_background_fill="#ed8936",
            button_primary_background_fill_hover="#dd6b20",
        ),
        css=CUSTOM_CSS,
    )


if __name__ == "__main__":
    launch_app()
