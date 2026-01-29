"""Compile (Menghimpun) agent for aggregating member responses."""

import json
from typing import List

from langchain_core.messages import HumanMessage, SystemMessage

from .base import BaseAgent
from ...models import Aspirasi, AbsorpsiResponse, KompilasiResponse


class CompileAgent(BaseAgent):
    """
    Agent for Step 2: Menghimpun (Compile)
    
    Compiles and aggregates responses from multiple DPR members.
    """

    def __init__(self, **kwargs):
        super().__init__(temperature=0.7, **kwargs)

    def get_system_prompt(self) -> str:
        return """Anda adalah staff ahli DPR yang bertugas mengompilasi masukan dari para anggota DPR.
Tugas Anda adalah:
1. Merangkum konsensus dari para anggota
2. Mengidentifikasi pola dan tema umum
3. Menyusun rekomendasi tindak lanjut yang komprehensif

Selalu berikan respons dalam format JSON yang valid."""

    def _build_user_prompt(
        self, aspirasi: Aspirasi, responses: List[AbsorpsiResponse]
    ) -> str:
        # Convert responses to dict format for JSON serialization
        responses_data = [
            {
                "member_id": r.member_id,
                "relevansi": r.relevansi,
                "alasan_relevansi": r.alasan_relevansi,
                "poin_kunci": r.poin_kunci,
                "rekomendasi_awal": r.rekomendasi_awal,
            }
            for r in responses
            if r.error is None
        ]

        return f"""Anda adalah staff ahli DPR yang mengompilasi masukan dari {len(responses_data)} anggota DPR.

Aspirasi: {aspirasi.content}
Kategori: {aspirasi.category}

Tanggapan anggota:
{json.dumps(responses_data, indent=2, ensure_ascii=False)}

Tugas Anda:
1. Rangkum konsensus dari para anggota
2. Identifikasi pola dan tema umum
3. Susun rekomendasi tindak lanjut yang komprehensif

Berikan respons dalam format JSON:
{{
    "ringkasan": "ringkasan konsensus",
    "tema_utama": ["tema1", "tema2", ...],
    "fraksi_terlibat": ["fraksi1", "fraksi2", ...],
    "rekomendasi_tindak_lanjut": "rekomendasi detail"
}}"""

    async def invoke(
        self, aspirasi: Aspirasi, responses: List[AbsorpsiResponse]
    ) -> KompilasiResponse:
        """
        Compile responses from multiple DPR members.

        Args:
            aspirasi: The original aspiration
            responses: List of individual member responses

        Returns:
            KompilasiResponse with compiled analysis
        """
        # Filter relevant responses
        relevant_responses = [
            r for r in responses if r.relevansi in ["Tinggi", "Sedang"] and r.error is None
        ]

        if not relevant_responses:
            return KompilasiResponse(
                status="tidak_relevan",
                jumlah_anggota=0,
                cost_usd=0.0,
            )

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=self._build_user_prompt(aspirasi, relevant_responses)),
        ]

        cost = 0.0
        try:
            response = await self.llm.ainvoke(messages)

            # Calculate cost
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

            return KompilasiResponse(
                status="terkumpul",
                jumlah_anggota=len(relevant_responses),
                ringkasan=result.get("ringkasan", ""),
                tema_utama=result.get("tema_utama", []),
                fraksi_terlibat=result.get("fraksi_terlibat", []),
                rekomendasi_tindak_lanjut=result.get("rekomendasi_tindak_lanjut", ""),
                cost_usd=cost,
            )

        except Exception as e:
            return KompilasiResponse(
                status="error",
                jumlah_anggota=len(relevant_responses),
                error=str(e),
                cost_usd=cost,
            )
