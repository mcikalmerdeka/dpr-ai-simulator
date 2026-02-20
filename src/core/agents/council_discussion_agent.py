"""Council Discussion agent for multi-member deliberation."""

import json
from typing import List, Dict, Any
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from .base import BaseAgent
from ...models import Aspirasi, AbsorpsiResponse, CouncilDiscussionResponse, DPRMember
from ..faction_data import get_faction_persona

logger = logging.getLogger("dpr_simulator.agents.council")


class CouncilDiscussionAgent(BaseAgent):
    """
    Agent for Council Discussion stage - simulating multi-member deliberation.
    
    This agent orchestrates a discussion between selected DPR members where they:
    1. Present their initial positions
    2. Respond to each other's arguments
    3. Build consensus or identify deadlock
    4. Produce collective recommendations
    
    Similar to the LLM Council concept, but adapted for DPR parliamentary context.
    """

    def __init__(self, **kwargs):
        super().__init__(temperature=0.8, **kwargs)

    def get_system_prompt(self) -> str:
        return """Anda adalah fasilitator rapat parlemen (Ketua Komisi) yang mengelola diskusi antar anggota DPR.

Tugas Anda adalah mensimulasikan diskusi konstruktif antar anggota dengan aturan:
1. Setiap anggota menyampaikan pandangan sesuai ideologi fraksi dan kepentingan dapilnya
2. Anggota dapat merespons argumen anggota lain (setuju, kontra, atau menambahkan perspektif)
3. Identifikasi titik kesepakatan dan perbedaan fundamental
4. Hasilkan rekomendasi kolektif yang merepresentasikan konsensus atau kompromi

Panduan Simulasi:
- Gunakan gaya bahasa politik yang natural
- Tunjukkan dinamika fraksi (koalisi vs oposisi)
- Refleksikan perbedaan kepentingan daerah vs nasional
- Hasilkan diskusi yang realistis dan konstruktif

Selalu berikan respons dalam format JSON yang valid."""

    def _build_user_prompt(
        self,
        aspirasi: Aspirasi,
        responses: List[AbsorpsiResponse],
        members: List[DPRMember],
        discussion_rounds: int = 2
    ) -> str:
        # Build member context with their responses
        member_contexts = []
        member_lookup = {m.id: m for m in members}
        
        for resp in responses:
            if resp.error is None and resp.relevansi.lower() in ["tinggi", "sedang"]:
                member = member_lookup.get(resp.member_id)
                if member:
                    ideologi = get_faction_persona(member.faction)
                    member_contexts.append({
                        "id": member.id,
                        "nama": member.name,
                        "fraksi": member.faction,
                        "komisi": member.komisi,
                        "dapil": member.dapil,
                        "provinsi": member.province,
                        "ideologi": ideologi,
                        "relevansi": resp.relevansi,
                        "sentiment": resp.sentiment,
                        "quote": resp.quote,
                        "poin_kunci": resp.poin_kunci,
                        "rekomendasi": resp.rekomendasi_awal
                    })

        return f"""Anda adalah Ketua Komisi yang memfasilitasi diskusi antar anggota DPR.

ASPIRASI RAKYAT:
{aspirasi.content}
Kategori: {aspirasi.category}
Prioritas: {aspirasi.priority}
Sumber: {aspirasi.source}

ANGGOTA YANG BERPARTISIPASI ({len(member_contexts)} anggota):
{json.dumps(member_contexts, indent=2, ensure_ascii=False)}

TUGAS ANDA:
Simulasikan diskusi parlemen dengan {discussion_rounds} putaran:

PUTARAN 1 - Pemaparan Awal:
Setiap anggota menyampaikan:
- Posisi mereka terhadap aspirasi ini
- Argumen utama berdasarkan ideologi fraksi dan kepentingan dapil
- Rekomendasi awal

PUTARAN 2 - Tanggapan dan Debat:
Anggota merespons satu sama lain:
- Anggota dari fraksi berbeda dapat menyanggah atau menambahkan perspektif
- Anggota dari fraksi sama dapat mendukung atau menyempurnakan argumen
- Identifikasi konflik kepentingan (daerah vs nasional, koalisi vs oposisi)

HASIL AKHIR:
1. Ringkasan perdebatan utama
2. Posisi masing-masing fraksi
3. Tingkat konsensus (sepenuhnya/setengah/terbagi/deadlock)
4. Rekomendasi kolektif yang disepakati

Berikan respons dalam format JSON:
{{
    "diskusi": [
        {{
            "putaran": 1,
            "intervensi": [
                {{
                    "anggota_id": 123,
                    "nama": "Nama Anggota",
                    "fraksi": "Nama Fraksi",
                    "tipe": "pemaparan",
                    "isi": "Pernyataan lengkap anggota..."
                }}
            ]
        }},
        {{
            "putaran": 2,
            "intervensi": [
                {{
                    "anggota_id": 456,
                    "nama": "Nama Anggota",
                    "fraksi": "Nama Fraksi",
                    "tipe": "tanggapan",
                    "menanggapi": 123,
                    "isi": "Tanggapan terhadap anggota lain..."
                }}
            ]
        }}
    ],
    "ringkasan_perdebatan": "Ringkasan komprehensif perdebatan...",
    "posisi_fraksi": {{
        "Fraksi A": "Posisi fraksi...",
        "Fraksi B": "Posisi fraksi..."
    }},
    "konsensus": "sepenuhnya/setengah/terbagi/deadlock",
    "rekomendasi_kolektif": "Rekomendasi yang disepakati bersama..."
}}"""

    async def invoke(
        self,
        aspirasi: Aspirasi,
        responses: List[AbsorpsiResponse],
        members: List[DPRMember],
        discussion_rounds: int = 2
    ) -> CouncilDiscussionResponse:
        """
        Simulate a council discussion between selected DPR members.

        Args:
            aspirasi: The original aspiration
            responses: Individual member responses from absorb stage
            members: List of DPRMember objects who participated
            discussion_rounds: Number of discussion rounds (default 2)

        Returns:
            CouncilDiscussionResponse with the deliberation results
        """
        logger.info(f"CouncilDiscussionAgent starting discussion with {len(members)} members, {discussion_rounds} rounds")
        
        # Filter to relevant responses only
        relevant_responses = [
            r for r in responses 
            if r.relevansi.lower() in ["tinggi", "sedang"] and r.error is None
        ]
        
        if len(relevant_responses) < 2:
            logger.warning(f"Not enough relevant responses for discussion: {len(relevant_responses)}")
            return CouncilDiscussionResponse(
                status="error",
                error="Tidak cukup tanggapan relevan untuk diskusi (minimum 2 anggota)",
                cost_usd=0.0
            )

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=self._build_user_prompt(aspirasi, responses, members, discussion_rounds)),
        ]

        cost = 0.0
        try:
            logger.debug(f"Making OpenAI API call for council discussion...")
            response = await self.llm.ainvoke(messages)

            # Calculate cost
            if hasattr(response, "response_metadata"):
                usage = response.response_metadata.get("token_usage", {})
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)
                cost = self._calculate_cost(prompt_tokens, completion_tokens)
                logger.debug(f"Council discussion - Tokens: {prompt_tokens} prompt, {completion_tokens} completion, Cost: ${cost:.6f}")

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
            
            diskusi = result.get("diskusi", [])
            konsensus = result.get("konsensus", "")
            
            logger.info(f"Council discussion completed - Rounds: {len(diskusi)}, Consensus: {konsensus}, Cost: ${cost:.6f}")

            return CouncilDiscussionResponse(
                status="success",
                diskusi=diskusi,
                ringkasan_perdebatan=result.get("ringkasan_perdebatan", ""),
                posisi_fraksi=result.get("posisi_fraksi", {}),
                konsensus=konsensus,
                rekomendasi_kolektif=result.get("rekomendasi_kolektif", ""),
                cost_usd=cost,
            )

        except Exception as e:
            logger.error(f"CouncilDiscussionAgent failed: {str(e)}")
            return CouncilDiscussionResponse(
                status="error",
                error=str(e),
                cost_usd=cost,
            )
