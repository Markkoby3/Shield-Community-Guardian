import re
import logging
import feedparser
from backend.models import Report
from backend.services.pipeline import process_reports
from backend.db.database import save_alert


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()

logger = logging.getLogger(__name__)

# Public safety RSS feeds — add more as needed
RSS_FEEDS = [
    {
        "url": "https://www.cisa.gov/cybersecurity-advisories/all.xml",
        "location": "national",
        "source": "CISA",
    },
    {
        "url": "https://feeds.feedburner.com/TheHackersNews",
        "location": "national",
        "source": "TheHackerNews",
    },
]


def ingest_rss_feeds() -> dict:
    """
    Fetch all configured RSS feeds, run reports through the pipeline,
    and persist results to the database.
    Returns a summary of what was ingested.
    """
    total_fetched = 0
    total_saved = 0

    for feed_config in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_config["url"])
            reports = []

            for entry in feed.entries[:20]:  # cap at 20 per feed
                title = _strip_html(entry.get("title", ""))
                summary = _strip_html(entry.get("summary", ""))
                text = f"{title}. {summary}" if summary else title
                if text:
                    reports.append(Report(
                        text=text[:2000],
                        location=feed_config["location"],
                    ))

            total_fetched += len(reports)
            alerts_saved = 0

            if reports:
                response = process_reports(reports, user_location=feed_config["location"])
                for alert in response.alerts:
                    save_alert(alert.model_dump(), source=feed_config["source"])
                    total_saved += 1
                    alerts_saved += 1

            logger.info("Ingested %d alerts from %s", alerts_saved, feed_config["source"])

        except Exception as e:
            logger.error("Failed to ingest feed %s: %s", feed_config["url"], e, exc_info=True)

    return {"feeds_processed": len(RSS_FEEDS), "fetched": total_fetched, "saved": total_saved}
