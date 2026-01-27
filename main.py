import logging
import logging.handlers
import os
from datetime import datetime, timedelta
from pathlib import Path

import dotenv
from google import genai
from google.genai import types
from notion_client import Client

from research_topic_prompts import DAYS_LOOKBACK, garment_simulation_query
from schemas import WeeklyResearchDigest
from system_instruction_prompts import weekly_digest_system_instruction

dotenv.load_dotenv()

logger = logging.getLogger(__name__)
# logger_file_handler removed in favor of in-memory capture


try:
    GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
except KeyError:
    GEMINI_API_KEY = "Token not available!"
    logger.info("GEMINI_API_KEY not available!")
    raise ValueError


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

        # Add Logs if present
        if logs:
            children_blocks.append(
                {
                    "object": "block",
                    "type": "toggle",
                    "toggle": {
                        "rich_text": [
                            {"type": "text", "text": {"content": "Execution Logs"}}
                        ],
                        "children": [
                            {
                                "object": "block",
                                "type": "code",
                                "code": {
                                    "rich_text": [
                                        {"type": "text", "text": {"content": logs}}
                                    ],
                                    "language": "plain_text",
                                },
                            }
                        ],
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


if __name__ == "__main__":
    # Setup Logger
    logger.setLevel(logging.INFO)

    # Capture logs to a string buffer
    import io

    log_stream = io.StringIO()
    capture_handler = logging.StreamHandler(log_stream)
    capture_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(capture_handler)

    # Console output
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(console_handler)

    logger.info(
        "Starting GenAI Research Agent"
        "\n=================================================="
        "\n=================================================="
        "\n=================================================="
    )
    client = genai.Client(api_key=GEMINI_API_KEY)

    # Use the specific garment simulation query
    query = garment_simulation_query
    system_instruction = weekly_digest_system_instruction

    logger.info(f"Running query: {query}")

    try:
        response = client.models.generate_content(
            model="gemini-3-pro-preview",
            contents=query,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=WeeklyResearchDigest,
                tools=[types.Tool(google_search=types.GoogleSearch())],
            ),
        )

        logger.info("Response received")

        # Parse response
        digest_data = WeeklyResearchDigest.model_validate_json(response.text)

        # Force the report date to be today, to avoid LLM hallucinations
        digest_data.report_date = datetime.now().strftime("%Y-%m-%d")

        # Filter items older than DAYS_LOOKBACK
        cutoff_date = datetime.now() - timedelta(days=DAYS_LOOKBACK)
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
                # If date format is wrong, keep it but warn (or skip? User said strict.)
                # Let's assume strict format YYYY-MM-DD as per schema.
                logger.warning(
                    f"Invalid date format for item: {item.title} ({item.publication_date}). Keeping it."
                )
                filtered_items.append(item)

        digest_data.items = filtered_items
        logger.info(f"Filtered {len(digest_data.items)} items for the report.")

        # Create filenames
        date_str = datetime.now().strftime("%Y-%m-%d")
        safe_topic = digest_data.topic.lower().replace(" ", "_").replace("&", "and")
        base_filename = f"{date_str}_{safe_topic}"
        report_dir = Path("saved_reports")
        report_dir.mkdir(exist_ok=True)

        json_path = report_dir / f"{base_filename}.json"
        md_path = report_dir / f"{base_filename}.md"

        # Save JSON
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(digest_data.model_dump_json(indent=2))
        logger.info(f"Saved JSON report to {json_path}")

        # Generate and Save Markdown
        md_content = f"# {digest_data.topic}\n"
        md_content += f"**Date:** {digest_data.report_date}\n\n"
        md_content += "---\n\n"

        for i, item in enumerate(digest_data.items, 1):
            md_content += f"## {i}. [{item.title}]({item.source_link})\n"
            md_content += f"**Domain:** {item.primary_domain.value}\n\n"
            md_content += f"**Relevance:** {item.relevance_explanation}\n\n"
            md_content += f"**Key Innovation:** {item.key_innovation}\n\n"
            md_content += f"{item.summary}\n\n"
            md_content += "---\n\n"

        # Append logs to Markdown
        log_contents = log_stream.getvalue()
        md_content += "\n\n# Execution Logs\n\n```text\n" + log_contents + "\n```"

        # Save to Notion with logs
        save_to_notion(digest_data, logs=log_contents)

        # Re-save Markdown with logs
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        logger.info(f"Updated Markdown report with logs at {md_path}")

        print(f"Report generated successfully!\nMarkdown: {md_path}\nJSON: {json_path}")

    except Exception as e:
        logger.error(f"Error generating content: {e}")
        print(f"Error: {e}")
