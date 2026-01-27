import logging
import logging.handlers
import os
import dotenv
from datetime import datetime
from pathlib import Path

from google import genai
from google.genai import types
from system_instruction_prompts import weekly_digest_system_instruction
from research_topic_prompts import garment_simulation_query
from schemas import WeeklyResearchDigest

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


if __name__ == "__main__":
    logger.info("Starting GenAI Research Agent")

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
                response_schema=WeeklyResearchDigest
            )
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
        
    except Exception as e:
        logger.error(f"Error generating content: {e}")
        print(f"Error: {e}")
