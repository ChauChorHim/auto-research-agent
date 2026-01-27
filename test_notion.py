import logging
import os
from pathlib import Path

import dotenv
from notion_client import Client

from schemas import WeeklyResearchDigest

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dotenv.load_dotenv()


def list_accessible_databases():
    """Lists all databases the integration has access to."""
    try:
        notion_token = os.environ.get("NOTION_API_KEY")
        if not notion_token:
            logger.error("NOTION_API_KEY not found.")
            return

        notion = Client(auth=notion_token)
        logger.info("Searching for accessible databases...")

        # Search for all accessible objects (removing filter to avoid API validation errors)
        response = notion.search()

        results = response.get("results", [])
        logger.info(f"Found {len(results)} accessible items (databases + pages).")

        print("\n" + "=" * 50)
        print(" ACCESSIBLE DATABASES LIST")
        print("=" * 50)

        count = 0
        for item in results:
            obj_type = item["object"]
            db_id = item["id"]

            # Extract title
            if obj_type == "database":
                title_list = item.get("title", [])
            else:  # page
                # Pages usually have "properties" -> "title" -> "title"
                # But search results for pages typically have a 'properties' map where one key is type 'title'
                # Simplify for debug:
                title_list = []
                props = item.get("properties", {})
                for key, val in props.items():
                    if val["type"] == "title":
                        title_list = val.get("title", [])
                        break

            title = "Untitled"
            if title_list:
                title = "".join([t.get("plain_text", "") for t in title_list])

            # Extract properties (only for DBs usually, pages have property values)
            props_keys = list(item.get("properties", {}).keys())

            print(f"Type:       {obj_type.upper()}")
            print(f"Name:       {title}")
            print(f"ID:         {db_id}")
            if obj_type == "database":
                print(f"Properties: {props_keys}")
                count += 1
            print(f"URL:        {item.get('url')}")
            print("-" * 50)

        if count == 0:
            print("\nWARNING: No DATABASES found!")
            print("The integration sees pages, but not the database itself.")
            print("1. Open the original Database in Notion (Open as Page).")
            print("2. Click '...' -> 'Connect to' -> Select your integration.")
            print("3. Run this script again to get the new ID.")

        print("=" * 50 + "\n")

    except Exception as e:
        logger.error(f"Error listing databases: {e}")


def save_to_notion(digest_data: WeeklyResearchDigest):
    """Saves the digest data as a sub-page in Notion."""
    try:
        notion_token = os.environ.get("NOTION_API_KEY")
        # Allow user to set a specific PAGE ID, or fallback to the existing DB ID env var
        # assuming the user might just use that ID for the parent page.
        parent_id = os.environ.get("NOTION_PAGE_ID") or os.environ.get(
            "NOTION_DATABASE_ID"
        )

        if not notion_token or not parent_id:
            logger.warning(
                "Notion credentials not found. Please set NOTION_API_KEY and NOTION_PAGE_ID (or NOTION_DATABASE_ID) in .env"
            )
            return

        notion = Client(auth=notion_token)

        logger.info(f"Connected to Notion. Target Parent ID: {parent_id}")

        # Create blocks for the page content
        children_blocks = []

        # Add Metadata as Blocks (since we are not in a DB, we can't use Properties)
        children_blocks.append(
            {
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": f"Topic: {digest_data.topic}\nDate: {digest_data.report_date}"
                            },
                        }
                    ],
                    "icon": {"emoji": "📅"},
                },
            }
        )

        children_blocks.append({"object": "block", "type": "divider", "divider": {}})

        # Add Items
        for i, item in enumerate(digest_data.items, 1):
            # Heading with Link
            children_blocks.append(
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": f"{i}. "},
                            },
                            {
                                "type": "text",
                                "text": {"content": item.title},
                                "text": {
                                    "content": item.title,
                                    "link": {"url": item.source_link},
                                },
                            },
                        ]
                    },
                }
            )

            # Domain Tag
            children_blocks.append(
                {
                    "object": "block",
                    "type": "callout",
                    "callout": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": f"Domain: {item.primary_domain.value}"
                                },
                            }
                        ],
                        "icon": {"emoji": "🏷️"},
                    },
                }
            )

            # Details: Relevance
            children_blocks.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": "Relevance: "},
                                "annotations": {"bold": True},
                            },
                            {
                                "type": "text",
                                "text": {"content": item.relevance_explanation},
                            },
                        ]
                    },
                }
            )

            # Details: Innovation
            children_blocks.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": "Key Innovation: "},
                                "annotations": {"bold": True},
                            },
                            {"type": "text", "text": {"content": item.key_innovation}},
                        ]
                    },
                }
            )

            # Summary
            children_blocks.append(
                {
                    "object": "block",
                    "type": "quote",
                    "quote": {
                        "rich_text": [
                            {"type": "text", "text": {"content": item.summary}}
                        ]
                    },
                }
            )

            # Spacer
            children_blocks.append(
                {"object": "block", "type": "divider", "divider": {}}
            )

        logger.info("Creating page in Notion...")

        # Create the page under the parent page
        notion.pages.create(
            parent={"page_id": parent_id},
            properties={
                "title": [  # For pages, the property is lowercase 'title', but the key in properties dict is 'title' (usually 'title' or 'Name'?)
                    # Wait, for pages inside pages, the title property is always named "title".
                    {
                        "text": {
                            "content": f"{digest_data.topic} - {digest_data.report_date}"
                        }
                    }
                ]
            },
            children=children_blocks,
        )

        logger.info("Successfully saved report to Notion!")

    except Exception as e:
        logger.error(f"Failed to save to Notion: {e}")


if __name__ == "__main__":
    # 1. List databases first to help debug ID issues
    list_accessible_databases()

    report_dir = Path("saved_reports")
    json_files = list(report_dir.glob("*.json"))

    if not json_files:
        print("No JSON reports found in saved_reports/")
        exit(1)

    # Pick the most recent one
    latest_file = max(json_files, key=os.path.getmtime)
    print(f"Testing with report: {latest_file}")

    with open(latest_file, "r", encoding="utf-8") as f:
        json_content = f.read()

    digest = WeeklyResearchDigest.model_validate_json(json_content)

    save_to_notion(digest)
