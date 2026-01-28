"""Absorb (Menyerap) agent for processing aspirations."""

import json
from typing import Dict, Any

from langchain_core.messages import HumanMessage, SystemMessage

from .base import BaseAgent
from ...models import DPRMember, Aspirasi, AbsorpsiResponse


class AbsorbAgent(BaseAgent):
    """
    Agent for Step 1: Menyerap (Absorb)
    
    AI agent absorbs and understands the aspiration from a DPR member's perspective.
    """

    def get_system_prompt(self) -> str:
        return """Anda adalah seorang anggota DPR RI yang bertugas menyerap dan menganalisis aspirasi rakyat.
Tugas Anda adalah:
1. Memahami dan menganalisis aspirasi dari perspektif daerah pemilihan Anda
2. Menentukan relevansi aspirasi dengan konstituensi Anda
3. Mengidentifikasi poin-poin kunci yang perlu ditindaklanjuti

Selalu berikan respons dalam format JSON yang valid."""

    def _build_user_prompt(self, member: DPRMember, aspirasi: Aspirasi) -> str:
        return f"""Anda adalah anggota DPR RI:
{member.to_prompt_context()}

Aspirasi rakyat yang masuk:
{aspirasi.to_prompt_context()}

Tugas Anda:
1. Pahami dan analisis aspirasi ini dari perspektif daerah pemilihan Anda
2. Tentukan apakah aspirasi ini relevan dengan konstituensi Anda
3. Identifikasi poin-poin kunci yang perlu ditindaklanjuti

Berikan respons dalam format JSON:
{{
    "relevansi": "Tinggi/Sedang/Rendah",
    "alasan_relevansi": "penjelasan singkat",
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
        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=self._build_user_prompt(member, aspirasi)),
        ]

        cost = 0.0
        try:
            response = await self.llm.ainvoke(messages)

            # Calculate cost from token usage
            if hasattr(response, "response_metadata"):
                usage = response.response_metadata.get("token_usage", {})
                cost = self._calculate_cost(
                    usage.get("prompt_tokens", 0),
                    usage.get("completion_tokens", 0),
                )

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

            return AbsorpsiResponse(
                member_id=member.id,
                aspirasi_id=aspirasi.id,
                relevansi=result.get("relevansi", "rendah"),
                alasan_relevansi=result.get("alasan_relevansi", ""),
                poin_kunci=result.get("poin_kunci", []),
                rekomendasi_awal=result.get("rekomendasi_awal", ""),
                cost_usd=cost,
            )

        except Exception as e:
            return AbsorpsiResponse(
                member_id=member.id,
                aspirasi_id=aspirasi.id,
                relevansi="rendah",
                alasan_relevansi="",
                poin_kunci=[],
                rekomendasi_awal="",
                error=str(e),
                cost_usd=cost,
            )
