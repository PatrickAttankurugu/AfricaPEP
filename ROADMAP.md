# AfricaPEP Roadmap

This is the project's direction, kept honest and issue-linked. Items move as contributors pick them up; nothing here is a promise with a date. If you want to influence priorities, open a [Discussion](https://github.com/PatrickAttankurugu/AfricaPEP/discussions).

## Now (v1.x)

**Data quality and coverage**
- Per-country data quality reports, validated by people who know each country ([#15](https://github.com/PatrickAttankurugu/AfricaPEP/issues/15), see [CONTRIBUTING-DATA.md](CONTRIBUTING-DATA.md))
- Regional bodies: AU, ECOWAS, SADC, EAC officials ([#7](https://github.com/PatrickAttankurugu/AfricaPEP/issues/7))
- Party affiliation extraction from Wikidata ([#5](https://github.com/PatrickAttankurugu/AfricaPEP/issues/5))
- Better FATF tier classification for judiciary roles ([#3](https://github.com/PatrickAttankurugu/AfricaPEP/issues/3))

**Name matching**
- French name transliteration ([#2](https://github.com/PatrickAttankurugu/AfricaPEP/issues/2))
- Arabic name transliteration for North Africa ([#8](https://github.com/PatrickAttankurugu/AfricaPEP/issues/8))
- More African language support in matching ([#12](https://github.com/PatrickAttankurugu/AfricaPEP/issues/12))

**Developer experience**
- One-command Docker setup with bundled sample data ([#14](https://github.com/PatrickAttankurugu/AfricaPEP/issues/14))

## Next

**Beyond Wikidata**
- First national data source scrapers (electoral commissions, gazettes, judiciary sites), built on the existing scraper framework. Each source gets its own issue with the `new-scraper` label.
- Cross-source corroboration: records confirmed by two independent sources get a confidence marker.

**Matching depth**
- Phonetic candidate retrieval index, so purely phonetic matches are not gated by trigram overlap
- Published evaluation metrics for name matching (precision/recall on the QID-grounded harness)

**Operations**
- Shared-store (Redis) rate limiting so limits hold exactly across workers and restarts
- Public per-country coverage dashboard

## Later

- Dataset distribution: versioned exports published to Kaggle and Hugging Face Datasets
- Interoperability with the OpenSanctions ecosystem (FollowTheMoney entity format export)
- Sanctions and adverse-media adjacency: not in scope until PEP data quality is proven

## Non-goals

- Selling data or gating the API behind payment. AfricaPEP stays free and open source.
- Storing any non-public personal data. Only public information about public officials.
