"""Factory for creating DPR members."""

from typing import List
from ..models import DPRMember


class DPRMemberFactory:
    """Factory class for creating simulated DPR members."""

    FACTIONS = [
        "PDI-P", "Golkar", "Gerindra", "PKB", "Nasdem", "PKS",
        "Demokrat", "PAN", "PPP", "PSI", "Perindo", "Hanura",
        "Garuda", "PBB", "PKPI", "Gelora", "Ummat"
    ]

    PROVINCES = [
        "Jawa Barat", "Jawa Timur", "Jawa Tengah", "Sumatra Utara",
        "DKI Jakarta", "Sulawesi Selatan", "Banten", "Lampung",
        "Kalimantan Timur", "Aceh", "Sumatra Barat", "Riau",
        "Jambi", "Sumatra Selatan", "Bengkulu", "Kepulauan Riau",
        "Bangka Belitung", "Kalimantan Barat", "Kalimantan Tengah",
        "Kalimantan Selatan", "Kalimantan Utara", "Sulawesi Utara",
        "Sulawesi Tengah", "Sulawesi Tenggara", "Gorontalo",
        "Maluku", "Maluku Utara", "Papua", "Papua Barat",
        "Nusa Tenggara Barat", "Nusa Tenggara Timur", "Bali",
        "Daerah Istimewa Yogyakarta"
    ]

    EXPERTISE_AREAS = [
        "Ekonomi", "Pendidikan", "Kesehatan", "Infrastruktur",
        "Pertanian", "Kelautan", "Energi", "Hukum", "Teknologi",
        "Sosial", "Lingkungan", "Pertahanan", "Keuangan",
        "Industri", "Perdagangan", "Pariwisata"
    ]

    @classmethod
    def create_members(cls, count: int = 50) -> List[DPRMember]:
        """
        Create simulated DPR members with diverse backgrounds.

        Args:
            count: Number of members to create (default: 50)

        Returns:
            List of DPRMember instances
        """
        members = []
        for i in range(count):
            member = DPRMember(
                id=i + 1,
                name=f"Anggota_DPR_{i + 1}",
                faction=cls.FACTIONS[i % len(cls.FACTIONS)],
                dapil=f"Dapil_{(i % 10) + 1}",
                province=cls.PROVINCES[i % len(cls.PROVINCES)],
                expertise=[
                    cls.EXPERTISE_AREAS[j % len(cls.EXPERTISE_AREAS)]
                    for j in range(i, i + 2)
                ],
            )
            members.append(member)
        return members

    @classmethod
    def get_relevant_members(
        cls,
        members: List[DPRMember],
        category: str,
        source: str,
        limit: int = 50,
    ) -> List[DPRMember]:
        """
        Filter members relevant to a specific aspiration.

        Args:
            members: List of all DPR members
            category: Category of the aspiration
            source: Source region of the aspiration
            limit: Maximum number of members to return

        Returns:
            List of relevant DPRMember instances
        """
        relevant = [
            m for m in members
            if category in m.expertise or m.province in source
        ]
        return relevant[:limit]
