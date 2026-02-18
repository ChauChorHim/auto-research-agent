import logging
import os
from notion_client import Client
from auto_research_agent.src.schemas import WeeklyResearchDigest

logger = logging.getLogger(__name__)

def save_to_notion(digest_data: WeeklyResearchDigest, logs: str = ""):
    """Saves the digest data to a Notion Page (creating a sub-page)."""
    try:
        notion_token = os.environ.get("NOTION_API_KEY")
        # Use NOTION_PAGE_ID if set, otherwise fallback to NOTION_DATABASE_ID but treat it as a page parent
        parent_page_id = os.environ.get("NOTION_PAGE_ID") or os.environ.get(
            "NOTION_DATABASE_ID"
        )

        if not notion_token or not parent_page_id:
            logger.warning(
                "Notion credentials (NOTION_API_KEY or NOTION_PAGE_ID) not found. Skipping Notion save."
            )
            print("Skipping Notion save (credentials missing).")
            return

        notion = Client(auth=notion_token)

        # Create blocks for the page content
        children_blocks = []

        # Add Intro/Metadata
        children_blocks.append(
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": f"Generated on {digest_data.report_date}"
                            },
                            "annotations": {"italic": True},
                        }
                    ]
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

        # Add Logs if present (split into multiple blocks if needed)
        if logs:
            # Split logs into chunks of 2000 characters (Notion block limit)
            chunk_size = 2000
            log_chunks = [
                logs[i : i + chunk_size] for i in range(0, len(logs), chunk_size)
            ]

            log_children_blocks = []
            for chunk in log_chunks:
                log_children_blocks.append(
                    {
                        "object": "block",
                        "type": "code",
                        "code": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {"content": chunk},
                                }
                            ],
                            "language": "plain text",
                        },
                    }
                )

            children_blocks.append(
                {
                    "object": "block",
                    "type": "toggle",
                    "toggle": {
                        "rich_text": [
                            {"type": "text", "text": {"content": "Execution Logs"}}
                        ],
                        "children": log_children_blocks,
                    },
                }
            )

        # Create the page
        # Note: When creating a page under a parent PAGE, properties only contains 'title'.
        logger.info(f"Creating child page under parent ID: {parent_page_id}")
        notion.pages.create(
            parent={"page_id": parent_page_id},
            properties={
                "title": [
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
        print("Successfully saved report to Notion!")

    except Exception as e:
        logger.error(f"Failed to save to Notion: {e}")
        print(f"Failed to save to Notion: {e}")
