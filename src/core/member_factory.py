"""Factory for creating DPR members."""

from typing import List, Optional
import logging
from ..models import DPRMember
from .komisi_data import KOMISI_LIST, get_relevant_komisi

logger = logging.getLogger("dpr_simulator.members")


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
        logger.info(f"Creating {count} DPR members...")
        
        members = []
        for i in range(count):
            member = DPRMember(
                id=i + 1,
                name=f"Anggota_DPR_{i + 1}",
                faction=cls.FACTIONS[i % len(cls.FACTIONS)],
                komisi=KOMISI_LIST[i % len(KOMISI_LIST)],
                dapil=f"Dapil_{(i % 10) + 1}",
                province=cls.PROVINCES[i % len(cls.PROVINCES)],
                expertise=[
                    cls.EXPERTISE_AREAS[j % len(cls.EXPERTISE_AREAS)]
                    for j in range(i, i + 2)
                ],
            )
            members.append(member)
        
        # Log distribution statistics
        factions = {f: 0 for f in cls.FACTIONS}
        komisi_counts = {k: 0 for k in KOMISI_LIST}
        for m in members:
            factions[m.faction] = factions.get(m.faction, 0) + 1
            komisi_counts[m.komisi] = komisi_counts.get(m.komisi, 0) + 1
        
        logger.info(f"Created {len(members)} members across {len([f for f in factions.values() if f > 0])} factions and {len([k for k in komisi_counts.values() if k > 0])} commissions")
        logger.debug(f"Faction distribution: {dict(factions)}")
        logger.debug(f"Commission distribution: {dict(komisi_counts)}")
        
        return members

    @classmethod
    def get_relevant_members(
        cls,
        members: List[DPRMember],
        category: str,
        source: str,
        komisi_filter: Optional[str] = None,
        limit: int = 50,
    ) -> List[DPRMember]:
        """
        Filter members relevant to a specific aspiration.
        
        Priority:
        1. Members in the relevant Commission (Komisi)
        2. Members from the same Province (Dapil)

        Args:
            members: List of all DPR members
            category: Category of the aspiration
            source: Source region of the aspiration
            komisi_filter: Optional explicit commission filter
            limit: Maximum number of members to return

        Returns:
            List of relevant DPRMember instances
        """
        logger.info(f"Finding relevant members for category='{category}', source='{source}', limit={limit}")
        
        # Determine target commissions
        if komisi_filter:
            target_komisi = [komisi_filter]
            logger.debug(f"Using explicit komisi filter: {komisi_filter}")
        else:
            target_komisi = get_relevant_komisi(category)
            logger.debug(f"Category '{category}' maps to komisi: {target_komisi}")

        # Filter by Komisi (Primary Filter)
        relevant = [m for m in members if m.komisi in target_komisi]
        logger.info(f"Found {len(relevant)} members in target komisi ({target_komisi})")
        
        # If explicit commission filter is used but yields no results (unlikely given distribution),
        # or if category mapping fails, fallback to something reasonable or keep empty
        if not relevant and not komisi_filter:
            # Fallback: Filter by expertise if no commission match found (shouldn't happen with full mapping)
            logger.warning(f"No members found in target komisi, falling back to expertise filter for '{category}'")
            relevant = [m for m in members if category in m.expertise]

        # Sorting: Prioritize members from the source province within the relevant commission
        # This reflects that a member in the right commission who is ALSO from the area 
        # would be most interested/relevant.
        relevant.sort(key=lambda m: 0 if m.province in source else 1)
        
        # Count members from source province
        from_source = sum(1 for m in relevant if m.province in source)
        logger.info(f"Selected top {min(limit, len(relevant))} members ({from_source} from source province '{source}')")

        return relevant[:limit]
