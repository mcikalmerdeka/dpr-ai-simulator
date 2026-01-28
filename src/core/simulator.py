"""Main DPR Simulator class orchestrating the pipeline."""

import asyncio
from typing import List, Optional, Callable
from datetime import datetime

from ..config import settings
from ..models import (
    DPRMember,
    Aspirasi,
    AbsorpsiResponse,
    KompilasiResponse,
    TindakLanjutResponse,
    SimulationDetails,
    PipelineResult,
)
from .member_factory import DPRMemberFactory
from .agents import AbsorbAgent, CompileAgent, FollowUpAgent


class DPRSimulator:
    """
    Main simulator class that orchestrates the DPR aspiration processing pipeline.
    
    Pipeline stages:
    1. Menyerap (Absorb) - AI agents absorb and understand aspirations
    2. Menghimpun (Compile) - Aggregate responses from multiple members
    3. Menindaklanjuti (Follow-up) - Determine concrete follow-up actions
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """
        Initialize the DPR Simulator.

        Args:
            api_key: OpenAI API key (defaults to settings)
            model: OpenAI model name (defaults to settings)
        """
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.openai_model

        # Initialize agents
        self.absorb_agent = AbsorbAgent(api_key=self.api_key, model=self.model)
        self.compile_agent = CompileAgent(api_key=self.api_key, model=self.model)
        self.followup_agent = FollowUpAgent(api_key=self.api_key, model=self.model)

        # Initialize members
        self.members: List[DPRMember] = []
        self.aspirations: List[Aspirasi] = []

    def create_members(self, count: int = None) -> List[DPRMember]:
        """
        Create simulated DPR members.

        Args:
            count: Number of members to create (defaults to settings)

        Returns:
            List of created DPRMember instances
        """
        count = count or settings.default_member_count
        self.members = DPRMemberFactory.create_members(count)
        return self.members

    def add_aspirasi(self, aspirasi: Aspirasi) -> None:
        """Add a public aspiration to the system."""
        self.aspirations.append(aspirasi)

    async def _process_absorb_batch(
        self,
        members: List[DPRMember],
        aspirasi: Aspirasi,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> List[AbsorpsiResponse]:
        """Process a batch of members for the absorb stage."""
        tasks = [self.absorb_agent.invoke(member, aspirasi) for member in members]
        results = await asyncio.gather(*tasks)
        return list(results)

    async def process_aspirasi(
        self,
        aspirasi: Aspirasi,
        sample_size: int = None,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> PipelineResult:
        """
        Process a single aspiration through the complete pipeline.

        Args:
            aspirasi: The aspiration to process
            sample_size: Number of members to sample (defaults to settings)
            progress_callback: Optional callback for progress updates

        Returns:
            PipelineResult with complete processing results
        """
        sample_size = sample_size or settings.default_member_count
        batch_size = settings.batch_size
        total_cost = 0.0

        def log(msg: str):
            if progress_callback:
                progress_callback(msg)

        log(f"🔄 Aspirasi telah diterima, memproses aspirasi sekarang")

        # Get relevant members
        relevant_members = DPRMemberFactory.get_relevant_members(
            self.members, aspirasi.category, aspirasi.source, sample_size
        )
        log(f"📋 Ditemukan {len(relevant_members)} anggota relevan")

        # Step 1: Menyerap (Absorb)
        log(f"📥 Step 1: Menyerap aspirasi oleh {len(relevant_members)} anggota")
        all_responses: List[AbsorpsiResponse] = []

        for i in range(0, len(relevant_members), batch_size):
            batch = relevant_members[i : i + batch_size]
            batch_responses = await self._process_absorb_batch(batch, aspirasi, progress_callback)
            all_responses.extend(batch_responses)
            total_cost += sum(r.cost_usd for r in batch_responses)

            # Rate limiting
            if i + batch_size < len(relevant_members):
                await asyncio.sleep(settings.rate_limit_delay)

        log(f"✅ Step 1 selesai: {len(all_responses)} tanggapan dikumpulkan")

        # Step 2: Menghimpun (Compile)
        log("📊 Step 2: Menghimpun tanggapan anggota")
        kompilasi = await self.compile_agent.invoke(aspirasi, all_responses)
        total_cost += kompilasi.cost_usd
        log(f"✅ Step 2 selesai: Status {kompilasi.status}")

        # Step 3: Menindaklanjuti (Follow-up)
        if kompilasi.status == "terkumpul":
            log("📝 Step 3: Menindaklanjuti dengan rencana aksi")
            tindak_lanjut = await self.followup_agent.invoke(aspirasi, kompilasi)
            total_cost += tindak_lanjut.cost_usd
            log("✅ Step 3 selesai")
        else:
            tindak_lanjut = TindakLanjutResponse(
                langkah_tindak_lanjut=[],
                komisi_penanggung_jawab="",
                timeline="",
                indikator_keberhasilan=[],
                mekanisme="",
                error="Tidak ada tindak lanjut karena aspirasi tidak relevan",
            )
            log("⚠️ Step 3 dilewati: Tidak ada tanggapan relevan")

        log(f"💰 Total biaya pemrosesan aspirasi: ${total_cost:.6f}")

        # Calculate simulation details
        relevansi_tinggi = sum(1 for r in all_responses if r.relevansi.lower() == "tinggi" and r.error is None)
        relevansi_sedang = sum(1 for r in all_responses if r.relevansi.lower() == "sedang" and r.error is None)
        relevansi_rendah = sum(1 for r in all_responses if r.relevansi.lower() == "rendah" and r.error is None)
        
        # Get unique factions and provinces from relevant members
        fraksi_set = set(m.faction for m in relevant_members)
        provinsi_set = set(m.province for m in relevant_members)

        simulation_details = SimulationDetails(
            total_anggota_dpr=len(self.members),
            sample_size_requested=sample_size,
            anggota_relevan_terpilih=len(relevant_members),
            anggota_merespons=len([r for r in all_responses if r.error is None]),
            anggota_relevansi_tinggi=relevansi_tinggi,
            anggota_relevansi_sedang=relevansi_sedang,
            anggota_relevansi_rendah=relevansi_rendah,
            fraksi_terwakili=sorted(list(fraksi_set)),
            provinsi_terwakili=sorted(list(provinsi_set)),
            relevant_member_ids=[m.id for m in relevant_members],
        )

        return PipelineResult(
            aspirasi=aspirasi,
            tanggapan_anggota=all_responses,
            kompilasi=kompilasi,
            tindak_lanjut=tindak_lanjut,
            simulation_details=simulation_details,
            timestamp=datetime.now(),
            total_cost_usd=total_cost,
        )

    async def process_multiple_aspirasi(
        self,
        aspirasi_list: List[Aspirasi],
        sample_size: int = None,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> List[PipelineResult]:
        """
        Process multiple aspirations sequentially.

        Args:
            aspirasi_list: List of aspirations to process
            sample_size: Number of members to sample per aspiration
            progress_callback: Optional callback for progress updates

        Returns:
            List of PipelineResult for each aspiration
        """
        results = []
        for i, aspirasi in enumerate(aspirasi_list, 1):
            if progress_callback:
                progress_callback(f"\n{'='*60}\nAspirasi {i}/{len(aspirasi_list)}\n{'='*60}")
            result = await self.process_aspirasi(aspirasi, sample_size, progress_callback)
            results.append(result)
        return results
