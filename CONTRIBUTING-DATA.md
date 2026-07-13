# Contributing Without Writing Code

AfricaPEP's hardest problems are not software problems. They are data problems: is the Nigeria data complete, are Ghana's judges in the right FATF tier, does a common Hausa spelling of a governor's name actually match? Answering those questions requires knowledge of a country's political landscape, not Python.

If you are a compliance officer, AML analyst, journalist, researcher, or simply someone who knows a country's politics well, this guide is for you.

## Ways to contribute

### 1. Validate a country's data (highest impact)

Pick a country you know. Open a [Country Data Validation issue](https://github.com/PatrickAttankurugu/AfricaPEP/issues/new?template=country_validation.md) and work through the checklist: coverage gaps, stale records, wrong tiers, missing name variants, duplicates.

You can do the whole review from the live demo at [pep.patrickaiafrica.com](https://pep.patrickaiafrica.com), no setup required. Search for officials you know should be there, screen names with common local spellings, and record what is wrong or missing.

Every finding should link to public evidence: a government website, gazette, reputable news source, or official register.

### 2. Improve FATF tier classification

Tier assignment is keyword-based and misses country-specific titles (see issue [#3](https://github.com/PatrickAttankurugu/AfricaPEP/issues/3)). If you know that, for example, a "Regional Chief Executive" in one country carries Tier 1 influence while the same title elsewhere is Tier 3, that knowledge is a contribution. Comment on the issue or open a new one.

### 3. Propose national data sources

Wikidata is the current sole source. If you know an official register that lists office-holders for your country (electoral commission, government gazette, judiciary site, parliament register), propose it with a [New Data Source issue](https://github.com/PatrickAttankurugu/AfricaPEP/issues/new?template=new_scraper.md). You do not need to build the scraper; documenting the source, its URL structure, and its update cadence is the hard part.

### 4. Review screening quality

Run real-world style screenings (with public figures' names, never real customer data) and report false positives and false negatives. Name matching across African languages and transliteration systems is an open problem here (issues [#2](https://github.com/PatrickAttankurugu/AfricaPEP/issues/2), [#8](https://github.com/PatrickAttankurugu/AfricaPEP/issues/8), [#12](https://github.com/PatrickAttankurugu/AfricaPEP/issues/12)).

## Ground rules

- Every claim needs a public, citable source. "I know this person" is a lead; a gazette entry is evidence.
- Never submit non-public personal data. This project only records what is already public about public officials.
- One country per validation issue, so findings stay reviewable.
- Be factual and neutral in describing officials. This is a compliance dataset, not a commentary platform.

## Recognition

Data validators are credited in release notes alongside code contributors. Sustained validation work for a country effectively makes you that country's data steward, and we will say so publicly.

Questions? Open a [Discussion](https://github.com/PatrickAttankurugu/AfricaPEP/discussions).
