"""Scraper for the Tanzania Parliament (Bunge) members list.

Source: https://www.parliament.go.tz/parliament_member
API:    https://polis.bunge.go.tz/api/members (DataTable server-side API)
Method: JSON API via HTTP GET (params: start, length)
Extracts: MP name, constituency, party, member_type
Schedule: Weekly
"""
from datetime import datetime

import structlog

from africapep.scraper.base_scraper import BaseScraper, RawPersonRecord

log = structlog.get_logger()

SOURCE_URL = "https://www.parliament.go.tz/parliament_member"
API_URL = "https://polis.bunge.go.tz/api/members"
PAGE_SIZE = 100


class TanzaniaParliamentScraper(BaseScraper):
    """Scraper for Tanzania Parliament (Bunge) MPs."""

    country_code = "TZ"
    source_type = "PARLIAMENT"

    def scrape(self) -> list[RawPersonRecord]:
        records = []
        start = 0

        while True:
            try:
                resp = self._get(f"{API_URL}?start={start}&length={PAGE_SIZE}")
                data = resp.json()
            except Exception as e:
                log.error("tanzania_parliament_request_failed", url=API_URL, start=start, error=str(e))
                break

            members = data.get("data", [])
            if not members:
                break

            batch = self._parse_members(members)
            records.extend(batch)
            log.info("tanzania_parliament_page", start=start, found=len(batch))

            # Check if we have fetched all records
            total = data.get("recordsTotal", 0)
            start += PAGE_SIZE
            if start >= total:
                break

        return records

    def _parse_members(self, members: list[dict]) -> list[RawPersonRecord]:
        records = []
        now = datetime.utcnow()

        for member in members:
            try:
                first_name = (member.get("first_name") or "").strip()
                middle_name = (member.get("middle_name") or "").strip()
                surname = (member.get("surname") or "").strip()

                name_parts = [p for p in [first_name, middle_name, surname] if p]
                full_name = " ".join(name_parts)

                if not full_name or len(full_name) < 3:
                    continue

                constituency = (member.get("constituent") or "").strip()
                party = (member.get("political_party") or "").strip()
                member_type = (member.get("member_type") or "").strip()
                photo = (member.get("photo") or "").strip()

                records.append(RawPersonRecord(
                    full_name=full_name,
                    title="Member of Parliament",
                    institution="Bunge la Tanzania",
                    country_code="TZ",
                    source_url=SOURCE_URL,
                    source_type="PARLIAMENT",
                    raw_text=f"{full_name} - MP, {constituency} ({party})",
                    scraped_at=now,
                    extra_fields={
                        "party": party,
                        "constituency": constituency,
                        "member_type": member_type,
                        "photo": photo,
                        "first_name": first_name,
                        "middle_name": middle_name,
                        "surname": surname,
                    },
                ))
            except Exception as e:
                log.warning("tanzania_parliament_parse_error", error=str(e))

        return records

    def _load_fixture(self) -> list[RawPersonRecord]:
        return self._synthetic_fixture()

    def _synthetic_fixture(self) -> list[RawPersonRecord]:
        now = datetime.utcnow()
        mps = [
            # ---- Speaker & Deputy Speaker ----
            {"name": "Tulia Ackson", "constituency": "Speaker", "party": "CCM", "member_type": "Speaker"},
            {"name": "Mussa Azzan Zungu", "constituency": "Ilala", "party": "CCM", "member_type": "Deputy Speaker"},
            # ---- Clerk of the National Assembly ----
            {"name": "Nenelwa Joyce Mwihambi", "constituency": "Clerk", "party": "N/A", "member_type": "Clerk of the National Assembly"},
            {"name": "Stephen Kagaigai", "constituency": "Clerk", "party": "N/A", "member_type": "Former Clerk of the National Assembly"},
            # ---- Former Speakers ----
            {"name": "Job Yustino Ndugai", "constituency": "Kongwa", "party": "CCM", "member_type": "Former Speaker"},
            {"name": "Anne Semamba Makinda", "constituency": "Njombe Mjini", "party": "CCM", "member_type": "Former Speaker"},
            # ---- Party Whips ----
            {"name": "David Ernest Silinde", "constituency": "Momba", "party": "CHADEMA", "member_type": "Opposition Chief Whip"},
            {"name": "Rashid Ali Abdallah", "constituency": "Tumbe", "party": "ACT-Wazalendo", "member_type": "ACT-Wazalendo Whip"},
            # ---- Committee Chairs ----
            {"name": "Atashasta Justus Nditiye", "constituency": "Muheza", "party": "CCM", "member_type": "Chair, Budget Committee"},
            {"name": "Godwin Emmanuel Kunambi", "constituency": "Mlimba", "party": "CCM", "member_type": "Chair, Public Accounts Committee"},
            {"name": "Suleiman Jafo", "constituency": "Kisarawe", "party": "CCM", "member_type": "Chair, Local Authorities Accounts Committee"},
            {"name": "Andrew John Chenge", "constituency": "Bariadi Mjini", "party": "CCM", "member_type": "Chair, Constitutional and Legal Affairs Committee"},
            {"name": "Shaaban Shekilindi", "constituency": "Lushoto", "party": "CCM", "member_type": "Chair, Defence and Security Committee"},
            {"name": "Katani Ahmad Katani", "constituency": "Tandahimba", "party": "CCM", "member_type": "Chair, Foreign Affairs Committee"},
            {"name": "Peter Joseph Serukamba", "constituency": "Kigoma Kaskazini", "party": "CCM", "member_type": "Chair, Infrastructure Committee"},
            {"name": "Conchesta Leonce Rwamlaza", "constituency": "Special Seats", "party": "CHADEMA", "member_type": "Chair, Social Services Committee"},
            {"name": "Silafu Jumbe Maufi", "constituency": "Special Seats", "party": "CCM", "member_type": "Chair, Land, Natural Resources and Environment Committee"},
            {"name": "Jerome Dismas Bwanausi", "constituency": "Lulindi", "party": "CCM", "member_type": "Chair, Agriculture, Livestock and Water Committee"},
            {"name": "Oscar Rwegasira Mukasa", "constituency": "Biharamulo", "party": "CCM", "member_type": "Chair, Industries, Trade and Environment Committee"},
            # ---- Prominent CCM MPs ----
            {"name": "January Yusuf Makamba", "constituency": "Bumbuli", "party": "CCM", "member_type": "Constituency"},
            {"name": "Nape Moses Nnauye", "constituency": "Mtama", "party": "CCM", "member_type": "Constituency"},
            {"name": "Abdallah Jafari Bulembo", "constituency": "Buchosa", "party": "CCM", "member_type": "Constituency"},
            {"name": "Josephat Sinkamba Gwajima", "constituency": "Kawe", "party": "CCM", "member_type": "Constituency"},
            {"name": "Mwita Mwikabe Waitara", "constituency": "Ukonga", "party": "CCM", "member_type": "Constituency"},
            {"name": "Hussein Bashe", "constituency": "Nzega Mjini", "party": "CCM", "member_type": "Constituency"},
            {"name": "Doto Mashaka Biteko", "constituency": "Bukombe", "party": "CCM", "member_type": "Constituency"},
            {"name": "Mwigulu Lameck Nchemba", "constituency": "Iramba Mashariki", "party": "CCM", "member_type": "Constituency"},
            {"name": "Innocent Bashungwa", "constituency": "Karagwe", "party": "CCM", "member_type": "Constituency"},
            {"name": "Damas Daniel Ndumbaro", "constituency": "Songea Mjini", "party": "CCM", "member_type": "Constituency"},
            {"name": "George Simbachawene", "constituency": "Kibakwe", "party": "CCM", "member_type": "Constituency"},
            {"name": "Richard Mbogo Sapi", "constituency": "Tunduru Kaskazini", "party": "CCM", "member_type": "Constituency"},
            {"name": "Boniphace Mwita Getere", "constituency": "Bunda", "party": "CCM", "member_type": "Constituency"},
            {"name": "Joseph Kasheku Musukuma", "constituency": "Geita Mjini", "party": "CCM", "member_type": "Constituency"},
            {"name": "Anthony Peter Mavunde", "constituency": "Dodoma Mjini", "party": "CCM", "member_type": "Constituency"},
            {"name": "Eliezer Feleshi", "constituency": "Mbeya Mjini", "party": "CCM", "member_type": "Constituency"},
            {"name": "Omary Tebere Mgumba", "constituency": "Morogoro Kusini", "party": "CCM", "member_type": "Constituency"},
            {"name": "Juma Hamisi Kombo", "constituency": "Kibiti", "party": "CCM", "member_type": "Constituency"},
            {"name": "Seif Ungando", "constituency": "Kishapu", "party": "CCM", "member_type": "Constituency"},
            {"name": "Hassan Elias Masala", "constituency": "Nachingwea", "party": "CCM", "member_type": "Constituency"},
            {"name": "Mohamed Mchengerwa", "constituency": "Rufiji", "party": "CCM", "member_type": "Constituency"},
            {"name": "Joseph George Kakunda", "constituency": "Sikonge", "party": "CCM", "member_type": "Constituency"},
            {"name": "William Vangimembe Lukuvi", "constituency": "Ismani", "party": "CCM", "member_type": "Constituency"},
            # ---- CHADEMA MPs ----
            {"name": "Tundu Antiphas Lissu", "constituency": "Singida Mashariki", "party": "CHADEMA", "member_type": "Constituency"},
            {"name": "Freeman Aikaeli Mbowe", "constituency": "Hai", "party": "CHADEMA", "member_type": "Constituency"},
            {"name": "Halima James Mdee", "constituency": "Kawe", "party": "CHADEMA", "member_type": "Constituency"},
            {"name": "Ester Amos Bulaya", "constituency": "Bunda Mjini", "party": "CHADEMA", "member_type": "Constituency"},
            {"name": "Godbless Jonathan Lema", "constituency": "Arusha Mjini", "party": "CHADEMA", "member_type": "Constituency"},
            {"name": "John Heche", "constituency": "Tarime Mjini", "party": "CHADEMA", "member_type": "Constituency"},
            {"name": "Salome Makamba", "constituency": "Special Seats", "party": "CHADEMA", "member_type": "Special Seats"},
            {"name": "Cecilia Daniel Paresso", "constituency": "Special Seats", "party": "CHADEMA", "member_type": "Special Seats"},
            {"name": "Wilfred Muganyizi Lwakatare", "constituency": "Bukoba Mjini", "party": "CHADEMA", "member_type": "Constituency"},
            {"name": "Devotha Methew Minja", "constituency": "Special Seats", "party": "CHADEMA", "member_type": "Special Seats"},
            {"name": "Peter Msigwa", "constituency": "Iringa Mjini", "party": "CHADEMA", "member_type": "Constituency"},
            # ---- ACT-Wazalendo / CUF / Other MPs ----
            {"name": "Zitto Zuberi Kabwe", "constituency": "Kigoma Mjini", "party": "ACT-Wazalendo", "member_type": "Constituency"},
            {"name": "Aysah Abdallah Omar", "constituency": "Special Seats", "party": "CUF", "member_type": "Special Seats"},
            {"name": "Ally Saleh Ally", "constituency": "Malindi", "party": "CUF", "member_type": "Constituency"},
            # ---- Special Seats (Women) CCM ----
            {"name": "Anatropia Lwehikila Theonest", "constituency": "Special Seats", "party": "CCM", "member_type": "Special Seats"},
            {"name": "Angelina Adam Malembeka", "constituency": "Special Seats", "party": "CCM", "member_type": "Special Seats"},
        ]
        return [
            RawPersonRecord(
                full_name=mp["name"],
                title="Member of Parliament",
                institution="Bunge la Tanzania",
                country_code="TZ",
                source_url=SOURCE_URL,
                source_type="PARLIAMENT",
                raw_text=f"{mp['name']} - MP, {mp['constituency']} ({mp['party']})",
                scraped_at=now,
                extra_fields=mp,
            )
            for mp in mps
        ]
