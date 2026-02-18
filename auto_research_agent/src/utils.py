import logging
from datetime import datetime, timedelta
from auto_research_agent.src.schemas import WeeklyResearchDigest

logger = logging.getLogger(__name__)

def filter_digest_items(digest_data: WeeklyResearchDigest, days_lookback: int = 30) -> WeeklyResearchDigest:
    """Filters digest items based on publication date."""
    
    # Force the report date to be today
    digest_data.report_date = datetime.now().strftime("%Y-%m-%d")

    cutoff_date = datetime.now() - timedelta(days=days_lookback)
    filtered_items = []
    
    for item in digest_data.items:
        try:
            # Try to parse YYYY-MM-DD
            pub_date = datetime.strptime(item.publication_date, "%Y-%m-%d")
            if pub_date >= cutoff_date:
                filtered_items.append(item)
            else:
                logger.info(
                    f"Skipping old item: {item.title} ({item.publication_date})"
                )
        except ValueError:
            # If date format is wrong, keep it but warn
            logger.warning(
                f"Invalid date format for item: {item.title} ({item.publication_date}). Keeping it."
            )
            filtered_items.append(item)

    digest_data.items = filtered_items
    logger.info(f"Filtered {len(digest_data.items)} items for the report.")
    return digest_data
