"""Main DPR AI Simulator class orchestrating the pipeline."""

import asyncio
from typing import List, Optional, Callable
from datetime import datetime
import logging

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

logger = logging.getLogger("dpr_simulator.simulator")


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
        Initialize the DPR AI Simulator.

        Args:
            api_key: OpenAI API key (defaults to settings)
            model: OpenAI model name (defaults to settings)
        """
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.openai_model

        logger.info(f"Initializing DPR Simulator with model: {self.model}")

        # Initialize agents
        logger.debug("Initializing agents (Absorb, Compile, FollowUp)")
        self.absorb_agent = AbsorbAgent(api_key=self.api_key, model=self.model)
        self.compile_agent = CompileAgent(api_key=self.api_key, model=self.model)
        self.followup_agent = FollowUpAgent(api_key=self.api_key, model=self.model)

        # Initialize members
        self.members: List[DPRMember] = []
        self.aspirations: List[Aspirasi] = []
        
        logger.info("DPR Simulator initialized successfully")

    def create_members(self, count: int = None) -> List[DPRMember]:
        """
        Create simulated DPR members.

        Args:
            count: Number of members to create (defaults to settings)

        Returns:
            List of created DPRMember instances
        """
        count = count or settings.default_member_count
        logger.info(f"Creating {count} DPR members")
        
        self.members = DPRMemberFactory.create_members(count)
        
        # Log member distribution
        factions = {}
        komisi = {}
        for m in self.members:
            factions[m.faction] = factions.get(m.faction, 0) + 1
            komisi[m.komisi] = komisi.get(m.komisi, 0) + 1
        
        logger.info(f"Member distribution - Factions: {len(factions)}, Commissions: {len(komisi)}")
        logger.debug(f"Factions breakdown: {dict(factions)}")
        logger.debug(f"Commissions breakdown: {dict(komisi)}")
        
        return self.members

    def add_aspirasi(self, aspirasi: Aspirasi) -> None:
        """Add a public aspiration to the system."""
        self.aspirations.append(aspirasi)

    async def _process_absorb_batch(
        self,
        members: List[DPRMember],
        aspirasi: Aspirasi,
        progress_callback: Optional[Callable[[str], None]] = None,
        batch_num: int = 0,
        total_batches: int = 0,
    ) -> List[AbsorpsiResponse]:
        """Process a batch of members for the absorb stage."""
        logger.info(f"Processing absorb batch {batch_num}/{total_batches} with {len(members)} members")
        
        tasks = [self.absorb_agent.invoke(member, aspirasi) for member in members]
        results = await asyncio.gather(*tasks)
        
        # Log batch results
        success_count = sum(1 for r in results if r.error is None)
        error_count = len(results) - success_count
        batch_cost = sum(r.cost_usd for r in results)
        
        logger.info(f"Batch {batch_num} completed - Success: {success_count}, Errors: {error_count}, Cost: ${batch_cost:.6f}")
        
        if error_count > 0:
            errors = [r.error for r in results if r.error]
            logger.warning(f"Batch {batch_num} errors: {errors}")
        
        return list(results)

    async def process_aspirasi(
        self,
        aspirasi: Aspirasi,
        sample_size: int = None,
        komisi_filter: Optional[str] = None,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> PipelineResult:
        """
        Process a single aspiration through the complete pipeline.

        Args:
            aspirasi: The aspiration to process
            sample_size: Number of members to sample (defaults to settings)
            komisi_filter: Optional specific commission to filter by
            progress_callback: Optional callback for progress updates

        Returns:
            PipelineResult with complete processing results
        """
        sample_size = sample_size or settings.default_member_count
        batch_size = settings.batch_size
        total_cost = 0.0
        
        logger.info("=" * 60)
        logger.info(f"STARTING PIPELINE - Aspirasi ID: {aspirasi.id}")
        logger.info(f"  Category: {aspirasi.category}")
        logger.info(f"  Source: {aspirasi.source}")
        logger.info(f"  Priority: {aspirasi.priority}")
        logger.info(f"  Sample Size: {sample_size}")
        logger.info(f"  Komisi Filter: {komisi_filter or 'Auto'}")
        logger.info("=" * 60)

        def log(msg: str):
            if progress_callback:
                progress_callback(msg)

        log(f"🔄 Aspirasi telah diterima, memproses aspirasi sekarang")

        # Get relevant members
        logger.info("Finding relevant members...")
        relevant_members = DPRMemberFactory.get_relevant_members(
            self.members, aspirasi.category, aspirasi.source, komisi_filter, sample_size
        )
        logger.info(f"Found {len(relevant_members)} relevant members from {len(self.members)} total")
        log(f"📋 Ditemukan {len(relevant_members)} anggota relevan")

        # Step 1: Menyerap (Absorb)
        logger.info(f"[STEP 1: ABSORB] Processing {len(relevant_members)} members in batches of {batch_size}")
        log(f"📥 Step 1: Menyerap aspirasi oleh {len(relevant_members)} anggota")
        all_responses: List[AbsorpsiResponse] = []
        total_batches = (len(relevant_members) + batch_size - 1) // batch_size

        for i in range(0, len(relevant_members), batch_size):
            batch_num = (i // batch_size) + 1
            batch = relevant_members[i : i + batch_size]
            batch_responses = await self._process_absorb_batch(
                batch, aspirasi, progress_callback, batch_num, total_batches
            )
            all_responses.extend(batch_responses)
            total_cost += sum(r.cost_usd for r in batch_responses)

            # Rate limiting
            if i + batch_size < len(relevant_members):
                logger.debug(f"Rate limiting: sleeping for {settings.rate_limit_delay}s")
                await asyncio.sleep(settings.rate_limit_delay)

        # Calculate absorb statistics
        absorb_cost = sum(r.cost_usd for r in all_responses)
        success_responses = [r for r in all_responses if r.error is None]
        error_responses = [r for r in all_responses if r.error]
        
        logger.info(f"[STEP 1: ABSORB] Completed - {len(success_responses)} success, {len(error_responses)} errors, Cost: ${absorb_cost:.6f}")
        log(f"✅ Step 1 selesai: {len(all_responses)} tanggapan dikumpulkan")

        # Step 2: Menghimpun (Compile)
        logger.info("[STEP 2: COMPILE] Compiling responses...")
        log("📊 Step 2: Menghimpun tanggapan anggota")
        kompilasi = await self.compile_agent.invoke(aspirasi, all_responses)
        total_cost += kompilasi.cost_usd
        
        logger.info(f"[STEP 2: COMPILE] Completed - Status: {kompilasi.status}, Cost: ${kompilasi.cost_usd:.6f}")
        if kompilasi.status == "terkumpul":
            logger.info(f"  - Members involved: {kompilasi.jumlah_anggota}")
            logger.info(f"  - Themes: {kompilasi.tema_utama}")
        elif kompilasi.error:
            logger.error(f"  - Error: {kompilasi.error}")
        log(f"✅ Step 2 selesai: Status {kompilasi.status}")

        # Step 3: Menindaklanjuti (Follow-up)
        tindak_lanjut = None
        if kompilasi.status == "terkumpul":
            logger.info("[STEP 3: FOLLOW-UP] Creating action plan...")
            log("📝 Step 3: Menindaklanjuti dengan rencana aksi")
            tindak_lanjut = await self.followup_agent.invoke(aspirasi, kompilasi)
            total_cost += tindak_lanjut.cost_usd
            
            logger.info(f"[STEP 3: FOLLOW-UP] Completed - Cost: ${tindak_lanjut.cost_usd:.6f}")
            if tindak_lanjut.komisi_penanggung_jawab:
                logger.info(f"  - Responsible commission: {tindak_lanjut.komisi_penanggung_jawab}")
                logger.info(f"  - Timeline: {tindak_lanjut.timeline}")
            if tindak_lanjut.error:
                logger.error(f"  - Error: {tindak_lanjut.error}")
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
            logger.warning("[STEP 3: FOLLOW-UP] Skipped - No relevant responses to compile")
            log("⚠️ Step 3 dilewati: Tidak ada tanggapan relevan")

        # Final summary
        logger.info("=" * 60)
        logger.info(f"PIPELINE COMPLETED - Total Cost: ${total_cost:.6f}")
        logger.info("=" * 60)
        log(f"💰 Total biaya pemrosesan aspirasi: ${total_cost:.6f}")

        # Calculate simulation details
        relevansi_tinggi = sum(1 for r in all_responses if r.relevansi.lower() == "tinggi" and r.error is None)
        relevansi_sedang = sum(1 for r in all_responses if r.relevansi.lower() == "sedang" and r.error is None)
        relevansi_rendah = sum(1 for r in all_responses if r.relevansi.lower() == "rendah" and r.error is None)
        
        # Get unique factions and provinces from relevant members
        fraksi_set = set(m.faction for m in relevant_members)
        provinsi_set = set(m.province for m in relevant_members)
        komisi_set = set(m.komisi for m in relevant_members)

        # Get primary commission
        from .komisi_data import get_primary_komisi
        komisi_utama = komisi_filter if komisi_filter else get_primary_komisi(aspirasi.category)

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
            komisi_terwakili=sorted(list(komisi_set)),
            komisi_utama=komisi_utama,
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
