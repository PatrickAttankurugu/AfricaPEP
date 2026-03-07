"""APScheduler jobs for automated scraping and sync.

Run with: python -m africapep.scheduler.jobs
"""
import uuid
from datetime import datetime, timezone

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import text
import structlog

from africapep.config import settings
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


def run_all_scrapers():
    """Run all scrapers, process through pipeline, write to Neo4j."""
    started = datetime.now(timezone.utc)
    log.info("job_started", job="run_all_scrapers")
    total_records = 0

    try:
        from africapep.scraper.spiders.ghana_parliament import GhanaParliamentScraper
        from africapep.scraper.spiders.ghana_presidency import GhanaPresidencyScraper
        from africapep.scraper.spiders.ghana_ec import GhanaECScraper
        from africapep.scraper.spiders.ghana_gazette import GhanaGazetteScraper
        from africapep.scraper.spiders.nigeria_nass import NigeriaNASSScraper
        from africapep.scraper.spiders.nigeria_presidency import NigeriaPresidencyScraper
        from africapep.scraper.spiders.nigeria_inec import NigeriaINECScraper
        from africapep.scraper.spiders.kenya_parliament import KenyaParliamentScraper
        from africapep.scraper.spiders.kenya_gazette import KenyaGazetteScraper
        from africapep.scraper.spiders.southafrica_parliament import SouthAfricaParliamentScraper

        from africapep.pipeline.normaliser import normalise_record
        from africapep.pipeline.classifier import classify_pep_tier
        from africapep.pipeline.resolver import EntityResolver
        from africapep.database.neo4j_client import neo4j_client

        scrapers = [
            GhanaParliamentScraper(),
            GhanaPresidencyScraper(),
            GhanaECScraper(),
            GhanaGazetteScraper(),
            NigeriaNASSScraper(),
            NigeriaPresidencyScraper(),
            NigeriaINECScraper(),
            KenyaParliamentScraper(),
            KenyaGazetteScraper(),
            SouthAfricaParliamentScraper(),
        ]

        resolver = EntityResolver()
        for scraper in scrapers:
            try:
                records = scraper.run()
                for record in records:
                    normalised = normalise_record(record)
                    tier = classify_pep_tier(normalised.title, normalised.institution)
                    resolver.add(normalised, tier)
                total_records += len(records)
                log.info("scraper_batch_done", scraper=scraper.__class__.__name__,
                         records=len(records))
            except Exception as e:
                log.error("scraper_job_failed", scraper=scraper.__class__.__name__,
                          error=str(e))

        written = resolver.flush_to_neo4j(neo4j_client)
        log.info("job_finished", job="run_all_scrapers",
                 total_records=total_records, written=written)

        _log_job("run_all_scrapers", started, total_records, "SUCCESS")

    except Exception as e:
        log.error("job_failed", job="run_all_scrapers", error=str(e))
        _log_job("run_all_scrapers", started, total_records, "FAILED", str(e))


def run_gazette_scrapers():
    """Run gazette-specific scrapers (published mid-week)."""
    started = datetime.now(timezone.utc)
    log.info("job_started", job="run_gazette_scrapers")
    total_records = 0

    try:
        from africapep.scraper.spiders.ghana_gazette import GhanaGazetteScraper
        from africapep.scraper.spiders.kenya_gazette import KenyaGazetteScraper
        from africapep.pipeline.normaliser import normalise_record
        from africapep.pipeline.classifier import classify_pep_tier
        from africapep.pipeline.resolver import EntityResolver
        from africapep.database.neo4j_client import neo4j_client

        scrapers = [GhanaGazetteScraper(), KenyaGazetteScraper()]
        resolver = EntityResolver()

        for scraper in scrapers:
            try:
                records = scraper.run()
                for record in records:
                    normalised = normalise_record(record)
                    tier = classify_pep_tier(normalised.title, normalised.institution)
                    resolver.add(normalised, tier)
                total_records += len(records)
            except Exception as e:
                log.error("gazette_scraper_failed", scraper=scraper.__class__.__name__,
                          error=str(e))

        written = resolver.flush_to_neo4j(neo4j_client)
        _log_job("run_gazette_scrapers", started, total_records, "SUCCESS")

    except Exception as e:
        log.error("job_failed", job="run_gazette_scrapers", error=str(e))
        _log_job("run_gazette_scrapers", started, total_records, "FAILED", str(e))


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
    # Run all scrapers every Sunday at 02:00 UTC
    scheduler.add_job(
        run_all_scrapers,
        CronTrigger(day_of_week="sun", hour=2, minute=0),
        id="run_all_scrapers",
        name="Run all scrapers",
        replace_existing=True,
    )

    # Run gazette scrapers every Wednesday at 06:00 UTC
    scheduler.add_job(
        run_gazette_scrapers,
        CronTrigger(day_of_week="wed", hour=6, minute=0),
        id="run_gazette_scrapers",
        name="Run gazette scrapers",
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
    print("  - run_all_scrapers: Sunday 02:00 UTC")
    print("  - run_gazette_scrapers: Wednesday 06:00 UTC")
    print("  - sync_neo4j_to_postgres: Sunday 06:00 UTC")
    print("  - log_database_stats: Daily 00:00 UTC")
    print()

    setup_scheduler()

    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("\nScheduler stopped.")
        scheduler.shutdown()
