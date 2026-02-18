import logging
import os

from google import genai
from google.genai import types

from auto_research_agent.prompts.research_topic_prompts import (
    DAYS_LOOKBACK,
    garment_simulation_query,
)
from auto_research_agent.prompts.system_instruction_prompts import (
    weekly_digest_system_instruction,
)
from auto_research_agent.src.schemas import WeeklyResearchDigest
from auto_research_agent.src.utils import filter_digest_items

logger = logging.getLogger(__name__)


class GarmentResearchTask:
    def __init__(self):
        try:
            self.api_key = os.environ["GEMINI_API_KEY"]
            self.client = genai.Client(api_key=self.api_key)
        except KeyError:
            logger.error("GEMINI_API_KEY not available!")
            raise ValueError("GEMINI_API_KEY not available!")

    def run(self) -> WeeklyResearchDigest:
        """Executes the garment research task."""
        query = garment_simulation_query
        system_instruction = weekly_digest_system_instruction

        logger.info(f"Running query: {query}")

        try:
            response = self.client.models.generate_content(
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

            if not response.text:
                logger.error("Empty response from Gemini.")
                raise ValueError("Empty response from Gemini.")

            # Parse response
            digest_data = WeeklyResearchDigest.model_validate_json(response.text)

            # Filter items
            digest_data = filter_digest_items(digest_data, days_lookback=DAYS_LOOKBACK)

            return digest_data

        except Exception as e:
            logger.error(f"Error executing GarmentResearchTask: {e}")
            raise
