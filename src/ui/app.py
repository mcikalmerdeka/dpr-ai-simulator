"""Gradio UI for DPR AI Simulator."""

import asyncio
import json
import logging
from datetime import datetime
from typing import List, Generator, Tuple, Any

import gradio as gr
import pandas as pd

from ..config import settings
from ..core import DPRSimulator, DPRMemberFactory
from ..models import Aspirasi, DPRMember
from ..core.komisi_data import KOMISI_LIST
from ..config.examples import (
    ASPIRATION_1, ASPIRATION_2, ASPIRATION_3, ASPIRATION_4,
    ASPIRATION_5, ASPIRATION_6, ASPIRATION_7
)

logger = logging.getLogger("dpr_simulator.ui")


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

    # Commissions represented
    if sim.komisi_terwakili:
        output.append(f"**Komisi Terwakili ({len(sim.komisi_terwakili)}):** {', '.join(sim.komisi_terwakili)}\n")

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
        return pd.DataFrame(columns=["ID", "Nama", "Fraksi", "Komisi", "Dapil", "Provinsi", "Keahlian"])
    
    data = []
    for m in members:
        data.append({
            "ID": m.id,
            "Nama": m.name,
            "Fraksi": m.faction,
            "Komisi": m.komisi,
            "Dapil": m.dapil,
            "Provinsi": m.province,
            "Keahlian": ", ".join(m.expertise) if m.expertise else "-",
        })
    return pd.DataFrame(data)


async def process_aspirasi_async(
    content: str,
    category: str,
    komisi: str,
    source: str,
    priority: str,
    member_count: int,
    sample_size: int,
    api_key: str,
) -> Generator:
    """Process aspiration asynchronously with streaming updates.
    
    Yields tuples of (messages, all_members_df, relevant_members_df, responding_members_df)
    """
    logger.info("=" * 70)
    logger.info("NEW ASPIRATION REQUEST RECEIVED")
    logger.info(f"  Category: {category}")
    logger.info(f"  Source: {source}")
    logger.info(f"  Priority: {priority}")
    logger.info(f"  Member Count: {member_count}")
    logger.info(f"  Sample Size: {sample_size}")
    logger.info(f"  Komisi Filter: {komisi}")
    logger.info("=" * 70)

    # Empty dataframes for initial state
    empty_df = pd.DataFrame(columns=["ID", "Nama", "Fraksi", "Komisi", "Dapil", "Provinsi", "Keahlian"])
    empty_response_df = pd.DataFrame(columns=["ID", "Nama", "Fraksi", "Komisi", "Provinsi", "Relevansi", "Sikap", "Tanggapan"])

    # Validate API key
    if not api_key:
        logger.error("Processing failed: No API key provided")
        yield (
            [{"role": "assistant", "content": "❌ Error: Mohon masukkan OpenAI API Key terlebih dahulu."}],
            empty_df, empty_df, empty_response_df
        )
        return
    
    logger.info("API key validated, initializing simulator...")

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
    
    logger.info(f"Aspirasi created (ID: {aspirasi.id}), starting pipeline...")

    # Progress messages - Gradio 6.x uses OpenAI-style message format by default
    messages = []

    def progress_callback(msg: str):
        messages.append({"role": "assistant", "content": msg})

    # Initial message
    user_msg = f"**Aspirasi Baru**\n\n{content}\n\n*Kategori: {category} | Komisi: {komisi} | Sumber: {source} | Prioritas: {priority}*"
    messages.append({"role": "user", "content": user_msg})
    messages.append({"role": "assistant", "content": f"=========================================="})
    messages.append({"role": "assistant", "content": f"🚀 Memulai simulasi dengan {member_count} anggota DPR"})
    
    # Yield initial state with all members populated
    yield (messages, all_members_df, empty_df, empty_response_df)

    # Process
    try:
        # Resolve komisi filter
        komisi_filter = komisi if komisi != "Auto (Sesuai Kategori)" else None
        logger.info(f"Starting pipeline with komisi_filter: {komisi_filter or 'Auto'}")

        result = await simulator.process_aspirasi(
            aspirasi,
            sample_size=sample_size,
            komisi_filter=komisi_filter,
            progress_callback=progress_callback,
        )
        
        logger.info(f"Pipeline completed successfully - Total cost: ${result.total_cost_usd:.6f}")

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
                    "Komisi": member.komisi,
                    "Provinsi": member.province,
                    "Relevansi": resp.relevansi,
                    "Sikap": resp.sentiment,
                    "Tanggapan": f'"{resp.quote}"' if resp.quote else resp.alasan_relevansi,
                })
        responding_members_df = pd.DataFrame(responding_data) if responding_data else empty_response_df

        # Final result
        messages.append({"role": "assistant", "content": format_result_for_display(result)})
        yield (messages, all_members_df, relevant_members_df, responding_members_df)

    except Exception as e:
        logger.exception(f"Pipeline failed with error: {str(e)}")
        messages.append({"role": "assistant", "content": f"❌ Error: {str(e)}"})
        yield (messages, all_members_df, empty_df, empty_response_df)


def process_aspirasi_sync(
    content: str,
    category: str,
    komisi: str,
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
            content, category, komisi, source, priority, member_count, sample_size, api_key
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

    with gr.Blocks(title="DPR AI Simulator - AI Parliament") as app:

        # Header
        gr.HTML("""
        <div class="main-header">
            <h1>🏛️ DPR AI Simulator</h1>
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
                    info="API key Anda tidak disimpan dan hanya digunakan untuk sesi ini. Silahkan buat di https://platform.openai.com/api-keys.",
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
                    komisi = gr.Dropdown(
                        choices=["Auto (Sesuai Kategori)"] + KOMISI_LIST,
                        value="Auto (Sesuai Kategori)",
                        label="Filter Komisi (Opsional)",
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
                        headers=["ID", "Nama", "Fraksi", "Komisi", "Dapil", "Provinsi", "Keahlian"],
                        label="Daftar Semua Anggota DPR dalam Simulasi",
                        interactive=False,
                        wrap=True,
                    )
                
                with gr.Accordion("🎯 Anggota Relevan Terpilih (Sample)", open=False):
                    relevant_members_df = gr.Dataframe(
                        headers=["ID", "Nama", "Fraksi", "Komisi", "Dapil", "Provinsi", "Keahlian"],
                        label="Anggota yang Terpilih Berdasarkan Relevansi",
                        interactive=False,
                        wrap=True,
                    )
                
                with gr.Accordion("✅ Anggota yang Merespons & Relevansinya", open=True):
                    responding_members_df = gr.Dataframe(
                        headers=["ID", "Nama", "Fraksi", "Komisi", "Provinsi", "Relevansi", "Sikap", "Tanggapan"],
                        label="Detail Respons dari Setiap Anggota",
                        interactive=False,
                        wrap=True,
                    )

        # Example aspirations - store full text separately
        aspiration_1 = ASPIRATION_1
        aspiration_2 = ASPIRATION_2
        aspiration_3 = ASPIRATION_3
        aspiration_4 = ASPIRATION_4
        aspiration_5 = ASPIRATION_5
        aspiration_6 = ASPIRATION_6
        aspiration_7 = ASPIRATION_7
        
        gr.Markdown("### 📚 Contoh Aspirasi Terstruktur")
        gr.Examples(
            examples=[
                [aspiration_1, "Pendidikan", "Komisi X", "Jawa Barat", "Tinggi"],
                [aspiration_2, "Pertanian", "Komisi IV", "Jawa Timur", "Tinggi"],
                [aspiration_3, "Infrastruktur", "Komisi V", "DKI Jakarta", "Tinggi"],
                [aspiration_4, "Lingkungan", "Komisi XII", "Kalimantan Timur", "Tinggi"],
                [aspiration_5, "Infrastruktur", "Komisi V", "Jawa Timur", "Tinggi"],
                [aspiration_6, "Kelautan", "Komisi IV", "Sulawesi Selatan", "Tinggi"],
                [aspiration_7, "Lingkungan", "Komisi IV", "Riau", "Tinggi"],
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
            inputs=[content, category, komisi, source, priority],
        )

        # API Call Breakdown Section
        with gr.Accordion("🔧 LLM API Call Breakdown (For Developers Only)", open=False):
            gr.Markdown("""
### How Many API Calls Happen?

**Formula: Total API Calls = N + 2**

Where **N** = sample size (number of DPR members processing the aspiration)

**The 3 Stages:**
1. **Menyerap (Absorb):** N API calls - each DPR member independently analyzes the aspiration (Output: Relevance, Sentiment, Quote)
2. **Menghimpun (Compile):** 1 API call - aggregates all responses into consensus
3. **Menindaklanjuti (Follow-up):** 1 API call - creates concrete action plan

**Examples Breakdown:**

| Sample Size | Stage 1 Calls | Stage 2 Calls | Stage 3 Calls | **Total API Calls** |
| ----------- | ------------- | ------------- | ------------- | ------------------- |
| 20 members  | 20            | 1             | 1             | **22**              |
| 50 members  | 50            | 1             | 1             | **52**              |
| 100 members | 100           | 1             | 1             | **102**             |
| 575 members | 575           | 1             | 1             | **577**             |

**Key Points:**
- Each DPR member is a truly independent AI agent with unique context (name, faction, province, expertise)
- Stage 1 processes members in parallel batches of 10 for efficiency
- All API costs are tracked and displayed in the results
            """)

        # Footer info
        gr.Markdown("""
        ---
        <center>
        <small>
        💡 <b>Tentang DPR AI Simulator:</b> Aplikasi ini mensimulasikan bagaimana AI dapat menggantikan fungsi DPR
        dalam menyerap, menghimpun, dan menindaklanjuti aspirasi rakyat dengan biaya yang jauh lebih efisien.
        </small>
        </center>
        """)

        # Event handlers
        submit_btn.click(
            fn=process_aspirasi_sync,
            inputs=[content, category, komisi, source, priority, member_count, sample_size, api_key, chatbot],
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
    logger.info("Creating Gradio application...")
    app = create_app()
    
    logger.info(f"Launching Gradio app on {settings.gradio_server_name}:{settings.gradio_server_port}")
    logger.info(f"Share mode: {settings.gradio_share}")
    
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
