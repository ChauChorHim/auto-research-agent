import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path

import dotenv
from google import genai
from google.genai import types
from notion_client import Client

from research_topic_prompts import garment_simulation_query
from schemas import WeeklyResearchDigest
from system_instruction_prompts import weekly_digest_system_instruction

dotenv.load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger_file_handler = logging.handlers.RotatingFileHandler(
    "status.log",
    maxBytes=1024 * 1024,
    backupCount=1,
    encoding="utf8",
)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger_file_handler.setFormatter(formatter)
logger.addHandler(logger_file_handler)

try:
    GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
except KeyError:
    GEMINI_API_KEY = "Token not available!"
    logger.info("GEMINI_API_KEY not available!")
    raise ValueError


def save_to_notion(digest_data: WeeklyResearchDigest):
    """Saves the digest data to a Notion Database."""
    try:
        notion_token = os.environ.get("NOTION_API_KEY")
        database_id = os.environ.get("NOTION_DATABASE_ID")

        if not notion_token or not database_id:
            logger.warning("Notion credentials not found. Skipping Notion save.")
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
                                "text": {
                                    "content": "Relevance: ",
                                    "annotations": {"bold": True},
                                },
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
                                "text": {
                                    "content": "Key Innovation: ",
                                    "annotations": {"bold": True},
                                },
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

        # Create the page in the database
        notion.pages.create(
            parent={"database_id": database_id},
            properties={
                "Name": {
                    "title": [
                        {
                            "text": {
                                "content": f"{digest_data.topic} - {digest_data.report_date}"
                            }
                        }
                    ]
                },
                "Date": {"date": {"start": datetime.now().isoformat()}},
                # You can add more properties here if your DB has columns like "Status", "Topic", etc.
                "Topic": {"rich_text": [{"text": {"content": digest_data.topic}}]},
            },
            children=children_blocks,
        )

        logger.info("Successfully saved report to Notion!")
        print("Successfully saved report to Notion!")

    except Exception as e:
        logger.error(f"Failed to save to Notion: {e}")
        print(f"Failed to save to Notion: {e}")


if __name__ == "__main__":
    logger.info("==================================================")
    logger.info("Starting GenAI Research Agent")

    client = genai.Client(api_key=GEMINI_API_KEY)

    # Use the specific garment simulation query
    query = garment_simulation_query
    system_instruction = weekly_digest_system_instruction

    logger.info(f"Running query: {query}")

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=query,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=WeeklyResearchDigest,
            ),
        )

        logger.info("Response received")

        # Parse response
        digest_data = WeeklyResearchDigest.model_validate_json(response.text)

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

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        logger.info(f"Saved Markdown report to {md_path}")

        print(f"Report generated successfully!\nMarkdown: {md_path}\nJSON: {json_path}")

        # Save to Notion
        save_to_notion(digest_data)

    except Exception as e:
        logger.error(f"Error generating content: {e}")
        print(f"Error: {e}")
