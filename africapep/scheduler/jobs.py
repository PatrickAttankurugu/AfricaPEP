"""APScheduler jobs for automated scraping and sync.

Run with: python -m africapep.scheduler.jobs
"""
import uuid
from datetime import datetime, timezone

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import text
import structlog

from africapep.database.postgres_client import get_db
from africapep.database.sync import sync_all

log = structlog.get_logger()
scheduler = BlockingScheduler()


def _log_job(job_name: str, started: datetime, records: int,
             status: str, error: str = None):
    """Write job run to scheduler_log table."""
    try:
        with get_db() as db:
            db.execute(text("""
                INSERT INTO scheduler_log (id, job_name, started_at, finished_at,
                                          records_processed, status, error_message)
                VALUES (:id, :name, :started, :finished, :records, :status, :error)
            """), {
                "id": str(uuid.uuid4()),
                "name": job_name,
                "started": started.isoformat(),
                "finished": datetime.now(timezone.utc).isoformat(),
                "records": records,
                "status": status,
                "error": error,
            })
    except Exception as e:
        log.error("scheduler_log_failed", job=job_name, error=str(e))


def run_wikidata_scraper():
    """Run Wikidata SPARQL scraper for all 54 African countries."""
    started = datetime.now(timezone.utc)
    log.info("job_started", job="run_wikidata_scraper")
    total_records = 0

    try:
        from africapep.scraper.spiders.wikidata_scraper import WikidataScraper, COUNTRY_QIDS
        from africapep.pipeline.normaliser import normalise_record
        from africapep.pipeline.classifier import classify_pep_tier
        from africapep.pipeline.resolver import EntityResolver
        from africapep.database.neo4j_client import neo4j_client

        resolver = EntityResolver()

        for country_code in COUNTRY_QIDS:
            try:
                scraper = WikidataScraper(country_code=country_code)
                records = scraper.scrape()
                for record in records:
                    normalised = normalise_record(record)
                    tier = classify_pep_tier(normalised.title, normalised.institution)
                    resolver.add(normalised, tier)
                total_records += len(records)
                log.info("scraper_country_done", country=country_code,
                         records=len(records))
            except Exception as e:
                log.error("scraper_country_failed", country=country_code,
                          error=str(e))

        written = resolver.flush_to_neo4j(neo4j_client)
        log.info("job_finished", job="run_wikidata_scraper",
                 total_records=total_records, written=written)

        # Immediately sync Neo4j -> PostgreSQL instead of waiting for
        # the separate scheduled job hours later.
        log.info("post_scrape_sync_start")
        try:
            synced = sync_all()
            log.info("post_scrape_sync_done", synced=synced)
        except Exception as sync_err:
            log.error("post_scrape_sync_failed", error=str(sync_err))

        _log_job("run_wikidata_scraper", started, total_records, "SUCCESS")

    except Exception as e:
        log.error("job_failed", job="run_wikidata_scraper", error=str(e))
        _log_job("run_wikidata_scraper", started, total_records, "FAILED", str(e))


def sync_neo4j_to_postgres():
    """Sync Neo4j graph data to PostgreSQL search index."""
    started = datetime.now(timezone.utc)
    log.info("job_started", job="sync_neo4j_to_postgres")

    try:
        synced = sync_all()
        _log_job("sync_neo4j_to_postgres", started, synced, "SUCCESS")
    except Exception as e:
        log.error("job_failed", job="sync_neo4j_to_postgres", error=str(e))
        _log_job("sync_neo4j_to_postgres", started, 0, "FAILED", str(e))


def log_database_stats():
    """Log daily database statistics."""
    started = datetime.now(timezone.utc)
    log.info("job_started", job="log_database_stats")

    try:
        with get_db() as db:
            total = db.execute(text("SELECT COUNT(*) FROM pep_profiles")).scalar() or 0
            active = db.execute(text(
                "SELECT COUNT(*) FROM pep_profiles WHERE is_active_pep = true"
            )).scalar() or 0
            sources = db.execute(text("SELECT COUNT(*) FROM source_records")).scalar() or 0
            screenings = db.execute(text("SELECT COUNT(*) FROM screening_log")).scalar() or 0

        log.info("daily_stats", total_peps=total, active_peps=active,
                 sources=sources, screenings=screenings)
        _log_job("log_database_stats", started, total, "SUCCESS")

    except Exception as e:
        log.error("job_failed", job="log_database_stats", error=str(e))
        _log_job("log_database_stats", started, 0, "FAILED", str(e))


def setup_scheduler():
    """Configure all scheduled jobs."""
    # Run Wikidata scraper every Sunday at 02:00 UTC
    scheduler.add_job(
        run_wikidata_scraper,
        CronTrigger(day_of_week="sun", hour=2, minute=0),
        id="run_wikidata_scraper",
        name="Run Wikidata scraper",
        replace_existing=True,
    )

    # Sync Neo4j to PostgreSQL every Sunday at 06:00 UTC
    scheduler.add_job(
        sync_neo4j_to_postgres,
        CronTrigger(day_of_week="sun", hour=6, minute=0),
        id="sync_neo4j_to_postgres",
        name="Sync Neo4j to PostgreSQL",
        replace_existing=True,
    )

    # Log stats daily at midnight UTC
    scheduler.add_job(
        log_database_stats,
        CronTrigger(hour=0, minute=0),
        id="log_database_stats",
        name="Log database stats",
        replace_existing=True,
    )

    log.info("scheduler_configured", jobs=len(scheduler.get_jobs()))


if __name__ == "__main__":
    print("AfricaPEP Scheduler starting...")
    print("Jobs:")
    print("  - run_wikidata_scraper: Sunday 02:00 UTC")
    print("  - sync_neo4j_to_postgres: Sunday 06:00 UTC")
    print("  - log_database_stats: Daily 00:00 UTC")
    print()

    setup_scheduler()

    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("\nScheduler stopped.")
        scheduler.shutdown()
