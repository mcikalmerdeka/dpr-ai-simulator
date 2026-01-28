"""Follow-up (Menindaklanjuti) agent for determining concrete actions."""

import json

from langchain_core.messages import HumanMessage, SystemMessage

from .base import BaseAgent
from ...models import Aspirasi, KompilasiResponse, TindakLanjutResponse


class FollowUpAgent(BaseAgent):
    """
    Agent for Step 3: Menindaklanjuti (Follow-up)
    
    Determines concrete follow-up actions based on compiled responses.
    """

    def __init__(self, **kwargs):
        super().__init__(temperature=0.2, **kwargs)

    def get_system_prompt(self) -> str:
        return """Anda adalah Ketua Komisi terkait di DPR RI yang bertugas menentukan tindak lanjut aspirasi rakyat.
Tugas Anda adalah:
1. Menentukan langkah konkret tindak lanjut
2. Menentukan komisi atau badan yang bertanggung jawab
3. Membuat timeline pelaksanaan
4. Menentukan indikator keberhasilan
5. MENGHITUNG dan menentukan estimasi anggaran yang dibutuhkan (dalam Rupiah)
6. Merinci alokasi anggaran per item/langkah
7. Menentukan sumber dana yang tepat (APBN, APBD, atau kombinasi)

PENTING: Anda harus memberikan estimasi anggaran yang realistis berdasarkan:
- Harga pasar saat ini untuk barang/jasa terkait
- Skala dan cakupan program yang diusulkan
- Pengalaman program serupa di masa lalu
- Standar biaya pemerintah Indonesia

Selalu berikan respons dalam format JSON yang valid."""

    def _build_user_prompt(
        self, aspirasi: Aspirasi, kompilasi: KompilasiResponse
    ) -> str:
        kompilasi_data = {
            "status": kompilasi.status,
            "jumlah_anggota": kompilasi.jumlah_anggota,
            "ringkasan": kompilasi.ringkasan,
            "tema_utama": kompilasi.tema_utama,
            "fraksi_terlibat": kompilasi.fraksi_terlibat,
            "rekomendasi_tindak_lanjut": kompilasi.rekomendasi_tindak_lanjut,
        }

        return f"""Anda adalah Ketua Komisi terkait di DPR RI.

Aspirasi rakyat: {aspirasi.content}
Kategori: {aspirasi.category}
Prioritas: {aspirasi.priority}

Hasil kompilasi dari {kompilasi.jumlah_anggota} anggota:
{json.dumps(kompilasi_data, indent=2, ensure_ascii=False)}

Tugas Anda:
1. Tentukan langkah konkret tindak lanjut
2. Tentukan komisi atau badan yang bertanggung jawab
3. Buat timeline pelaksanaan
4. Tentukan indikator keberhasilan
5. HITUNG estimasi anggaran yang realistis (dalam Rupiah)
6. Rinci alokasi anggaran per langkah/item
7. Tentukan sumber dana (APBN/APBD/kombinasi)

Berikan respons dalam format JSON:
{{
    "langkah_tindak_lanjut": ["langkah1", "langkah2", ...],
    "komisi_penanggung_jawab": "nama komisi",
    "timeline": "estimasi waktu",
    "indikator_keberhasilan": ["indikator1", "indikator2", ...],
    "mekanisme": "RDP/Hearing/Kunjungan Kerja/dll",
    "estimasi_anggaran": "Total estimasi anggaran (misal: Rp 15.5 miliar untuk 2 tahun)",
    "rincian_anggaran": [
        "Item 1: Rp X miliar - deskripsi",
        "Item 2: Rp Y miliar - deskripsi",
        ...
    ],
    "sumber_dana": "Sumber dana usulan (misal: APBN 70% (Kementerian X) + APBD Provinsi Y 30%)"
}}"""

    async def invoke(
        self, aspirasi: Aspirasi, kompilasi: KompilasiResponse
    ) -> TindakLanjutResponse:
        """
        Determine follow-up actions based on compiled responses.

        Args:
            aspirasi: The original aspiration
            kompilasi: Compiled response from the compile stage

        Returns:
            TindakLanjutResponse with concrete action plan
        """
        if kompilasi.status != "terkumpul":
            return TindakLanjutResponse(
                langkah_tindak_lanjut=[],
                komisi_penanggung_jawab="",
                timeline="",
                indikator_keberhasilan=[],
                mekanisme="",
                error="Tidak ada kompilasi yang valid untuk ditindaklanjuti",
                cost_usd=0.0,
            )

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=self._build_user_prompt(aspirasi, kompilasi)),
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

            return TindakLanjutResponse(
                langkah_tindak_lanjut=result.get("langkah_tindak_lanjut", []),
                komisi_penanggung_jawab=result.get("komisi_penanggung_jawab", ""),
                timeline=result.get("timeline", ""),
                indikator_keberhasilan=result.get("indikator_keberhasilan", []),
                mekanisme=result.get("mekanisme", ""),
                estimasi_anggaran=result.get("estimasi_anggaran", ""),
                rincian_anggaran=result.get("rincian_anggaran", []),
                sumber_dana=result.get("sumber_dana", ""),
                cost_usd=cost,
            )

        except Exception as e:
            return TindakLanjutResponse(
                langkah_tindak_lanjut=[],
                komisi_penanggung_jawab="",
                timeline="",
                indikator_keberhasilan=[],
                mekanisme="",
                error=str(e),
                cost_usd=cost,
            )
