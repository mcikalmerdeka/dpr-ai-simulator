"""Response models for DPR AI Simulator pipeline stages."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from .dpr_member import DPRMember
from .aspirasi import Aspirasi


class AbsorpsiResponse(BaseModel):
    """Response from the Menyerap (Absorb) stage."""

    member_id: int = Field(..., description="ID of the responding member")
    aspirasi_id: int = Field(..., description="ID of the aspiration being processed")
    relevansi: str = Field(..., description="Relevance level: Tinggi/Sedang/Rendah")
    alasan_relevansi: str = Field(..., description="Explanation of relevance")
    poin_kunci: List[str] = Field(default_factory=list, description="Key points identified")
    rekomendasi_awal: str = Field(default="", description="Initial recommendation")
    sentiment: str = Field(default="Netral", description="Member's stance: Positif/Negatif/Kritis/Netral")
    quote: str = Field(default="", description="Direct verbal statement/opinion from the member")
    error: Optional[str] = Field(default=None, description="Error message if any")
    cost_usd: float = Field(default=0.0, description="Cost of this API call in USD")


class KompilasiResponse(BaseModel):
    """Response from the Menghimpun (Compile) stage."""

    status: str = Field(..., description="Status: terkumpul/tidak_relevan")
    jumlah_anggota: int = Field(default=0, description="Number of members who responded")
    ringkasan: str = Field(default="", description="Summary of consensus")
    tema_utama: List[str] = Field(default_factory=list, description="Main themes identified")
    fraksi_terlibat: List[str] = Field(default_factory=list, description="Factions involved")
    rekomendasi_tindak_lanjut: str = Field(default="", description="Follow-up recommendation")
    error: Optional[str] = Field(default=None, description="Error message if any")
    cost_usd: float = Field(default=0.0, description="Cost of this API call in USD")


class TindakLanjutResponse(BaseModel):
    """Response from the Menindaklanjuti (Follow-up) stage."""

    langkah_tindak_lanjut: List[str] = Field(
        default_factory=list, description="Concrete follow-up steps"
    )
    komisi_penanggung_jawab: str = Field(
        default="", description="Responsible commission"
    )
    timeline: str = Field(default="", description="Estimated timeline")
    indikator_keberhasilan: List[str] = Field(
        default_factory=list, description="Success indicators"
    )
    mekanisme: str = Field(
        default="", description="Mechanism: RDP/Hearing/Kunjungan Kerja/etc."
    )
    estimasi_anggaran: str = Field(
        default="", description="Budget estimation for the proposed solution"
    )
    rincian_anggaran: List[str] = Field(
        default_factory=list, description="Detailed budget breakdown per item"
    )
    sumber_dana: str = Field(
        default="", description="Proposed funding sources (APBN/APBD/etc)"
    )
    pihak_terlibat: List[str] = Field(
        default_factory=list, description="Parties/stakeholders that need to be involved"
    )
    error: Optional[str] = Field(default=None, description="Error message if any")
    cost_usd: float = Field(default=0.0, description="Cost of this API call in USD")


class CouncilDiscussionResponse(BaseModel):
    """Response from the Council Discussion stage - multi-member deliberation."""
    
    status: str = Field(default="success", description="Status: success/error")
    diskusi: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="Discussion rounds with member statements"
    )
    ringkasan_perdebatan: str = Field(
        default="", 
        description="Summary of the debate and key arguments"
    )
    posisi_fraksi: Dict[str, str] = Field(
        default_factory=dict,
        description="Position of each faction on the issue"
    )
    konsensus: str = Field(
        default="",
        description="Final consensus reached or deadlock status"
    )
    rekomendasi_kolektif: str = Field(
        default="",
        description="Collective recommendation after discussion"
    )
    error: Optional[str] = Field(default=None, description="Error message if any")
    cost_usd: float = Field(default=0.0, description="Cost of this API call in USD")


class SimulationDetails(BaseModel):
    """Details about the simulation setup and member selection."""
    
    total_anggota_dpr: int = Field(default=0, description="Total DPR members in simulation")
    sample_size_requested: int = Field(default=0, description="Requested sample size")
    anggota_relevan_terpilih: int = Field(default=0, description="Number of relevant members selected")
    anggota_merespons: int = Field(default=0, description="Number of members who responded")
    anggota_relevansi_tinggi: int = Field(default=0, description="Members with high relevance")
    anggota_relevansi_sedang: int = Field(default=0, description="Members with medium relevance")
    anggota_relevansi_rendah: int = Field(default=0, description="Members with low relevance")
    fraksi_terwakili: List[str] = Field(default_factory=list, description="Factions represented")
    provinsi_terwakili: List[str] = Field(default_factory=list, description="Provinces represented")
    komisi_terwakili: List[str] = Field(default_factory=list, description="Commissions represented")
    komisi_utama: str = Field(default="", description="Primary responsible commission")
    # IDs for building dataframes in UI
    relevant_member_ids: List[int] = Field(default_factory=list, description="IDs of relevant members")


class PipelineResult(BaseModel):
    """Complete result from the DPR AI Simulator pipeline."""

    aspirasi: Aspirasi = Field(..., description="The processed aspiration")
    tanggapan_anggota: List[AbsorpsiResponse] = Field(
        default_factory=list, description="Individual member responses"
    )
    kompilasi: KompilasiResponse = Field(..., description="Compiled response")
    council_discussion: Optional[CouncilDiscussionResponse] = Field(
        default=None, description="Council discussion between selected members"
    )
    tindak_lanjut: TindakLanjutResponse = Field(..., description="Follow-up actions")
    simulation_details: SimulationDetails = Field(
        default_factory=SimulationDetails, description="Simulation setup details"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now, description="When processing completed"
    )
    total_cost_usd: float = Field(default=0.0, description="Total cost in USD")


