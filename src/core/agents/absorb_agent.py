"""Absorb (Menyerap) agent for processing aspirations."""

import json
from typing import Dict, Any
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from .base import BaseAgent
from ...models import DPRMember, Aspirasi, AbsorpsiResponse
from ..faction_data import get_faction_persona

logger = logging.getLogger("dpr_simulator.agents.absorb")

class AbsorbAgent(BaseAgent):
    """
    Agent for Step 1: Menyerap (Absorb)
    
    AI agent absorbs and understands the aspiration from a DPR member's perspective.
    """

    def get_system_prompt(self) -> str:
        return """Anda adalah seorang anggota DPR RI yang bertugas menyerap dan menganalisis aspirasi rakyat.

Panduan Penilaian Relevansi:
1. **PRIORITAS UTAMA (Fungsional)**: Jika aspirasi berkaitan dengan ruang lingkup KOMISI Anda, anggaplah RELEVANSI TINGGI meskipun bukan dari Dapil Anda. Anda bertanggung jawab secara nasional untuk bidang tersebut.
2. **PRIORITAS KEDUA (Representasi)**: Jika aspirasi berasal dari DAPIL Anda, itu juga RELEVAN.

Tugas Anda adalah:
1. Memahami aspirasi dari kacamata Ideologi Fraksi dan Kepentingan Dapil/Komisi Anda.
2. Menentukan relevansi (Tinggi/Sedang/Rendah) sesuai panduan.
3. Memberikan **TANGGAPAN LISAN (Quote)** yang mencerminkan persona politik Anda.

Selalu berikan respons dalam format JSON yang valid."""

    def _build_user_prompt(self, member: DPRMember, aspirasi: Aspirasi) -> str:
        ideologi = get_faction_persona(member.faction)
        
        return f"""Anda adalah anggota DPR RI dengan profil:
{member.to_prompt_context()}
Ideologi/Gaya Politik Fraksi ({member.faction}): {ideologi}

Aspirasi rakyat yang masuk:
{aspirasi.to_prompt_context()}

Panduan Penilaian Relevansi:
1. **CEK KOMISI**: Apakah topik aspirasi ini masuk lingkup Komisi Anda? Jika YA -> Relevansi TINGGI (Anda membahas kebijakan nasionalnya).
2. **CEK DAPIL**: Apakah lokasi aspirasi ini di Dapil Anda? Jika YA -> Relevansi TINGGI (Anda mewakili konstituen tersebut).
3. Jika TIDAK keduanya -> Relevansi RENDAH.
4. **PENTING**: JANGAN menolak atau memberi relevansi Rendah hanya karena aspirasi bukan dari Dapil Anda, JIKA aspirasi tersebut masuk dalam wewenang Komisi Anda.

Tugas Anda:
1. Analisis aspirasi ini.
2. Tentukan relevansi (Tinggi/Sedang/Rendah).
3. Buat **QUOTE (Tanggapan Lisan)**:
   - Gunakan gaya bicara politisi sesuai fraksi Anda ({member.faction}).
   - Jika PKS/PPP/PKB: Boleh gunakan istilah agamis/kerakyatan/pesantren jika relevan.
   - Jika PDIP/Gerindra: Gunakan nada nasionalis/tegas/wong cilik.
   - Jika Golkar/PAN/Demokrat: Gunakan nada teknokratis/pembangunan/solutif.
   - **PENTING**: Quote harus terdengar natural, seperti diwawancara wartawan atau berbicara di sidang paripurna. JANGAN KAKU.
4. Tentukan **SENTIMENT** (Positif/Negatif/Netral/Kritis) terhadap isu ini.

Berikan respons dalam format JSON:
{{
    "relevansi": "Tinggi/Sedang/Rendah",
    "alasan_relevansi": "penjelasan singkat teknis (untuk internal)",
    "sentiment": "Positif/Negatif/Netral/Kritis",
    "quote": "Tanggapan lisan Anda di sini...",
    "poin_kunci": ["poin1", "poin2", ...],
    "rekomendasi_awal": "saran tindak lanjut"
}}"""

    async def invoke(
        self, member: DPRMember, aspirasi: Aspirasi
    ) -> AbsorpsiResponse:
        """
        Process an aspiration from a specific DPR member's perspective.

        Args:
            member: The DPR member processing the aspiration
            aspirasi: The public aspiration to process

        Returns:
            AbsorpsiResponse with the member's analysis
        """
        logger.debug(f"AbsorbAgent processing - Member {member.id} ({member.faction}, {member.komisi}) analyzing aspirasi {aspirasi.id}")
        
        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=self._build_user_prompt(member, aspirasi)),
        ]

        cost = 0.0
        try:
            logger.debug(f"Making OpenAI API call for Member {member.id}...")
            response = await self.llm.ainvoke(messages)

            # Calculate cost from token usage
            if hasattr(response, "response_metadata"):
                usage = response.response_metadata.get("token_usage", {})
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)
                cost = self._calculate_cost(prompt_tokens, completion_tokens)
                logger.debug(f"Member {member.id} - Tokens: {prompt_tokens} prompt, {completion_tokens} completion")

            # Parse JSON response
            content = response.content
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            result = json.loads(content)
            
            relevansi = result.get("relevansi", "rendah")
            sentiment = result.get("sentiment", "Netral")
            
            logger.debug(f"Member {member.id} response - Relevance: {relevansi}, Sentiment: {sentiment}, Cost: ${cost:.6f}")

            return AbsorpsiResponse(
                member_id=member.id,
                aspirasi_id=aspirasi.id,
                relevansi=relevansi,
                alasan_relevansi=result.get("alasan_relevansi", ""),
                sentiment=sentiment,
                quote=result.get("quote", ""),
                poin_kunci=result.get("poin_kunci", []),
                rekomendasi_awal=result.get("rekomendasi_awal", ""),
                cost_usd=cost,
            )

        except Exception as e:
            logger.error(f"AbsorbAgent failed for Member {member.id}: {str(e)}")
            return AbsorpsiResponse(
                member_id=member.id,
                aspirasi_id=aspirasi.id,
                relevansi="rendah",
                alasan_relevansi="",
                sentiment="Netral",
                quote="",
                poin_kunci=[],
                rekomendasi_awal="",
                error=str(e),
                cost_usd=cost,
            )
