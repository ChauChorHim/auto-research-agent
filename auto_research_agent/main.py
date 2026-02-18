import argparse
import io
import logging
import sys

import dotenv

from auto_research_agent.src.chat_utils import send_to_google_chat
from auto_research_agent.src.notion_utils import save_to_notion
from auto_research_agent.tasks.garment_code_related import GarmentResearchTask

dotenv.load_dotenv()

# Define available tasks
TASKS = {
    "garment_research": GarmentResearchTask,
}


def main():
    parser = argparse.ArgumentParser(description="Run research tasks.")
    parser.add_argument(
        "task",
        nargs="?",
        default="garment_research",
        choices=TASKS.keys(),
        help="Name of the task to run (default: garment_research)",
    )
    args = parser.parse_args()

    # Setup Logging
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Clear existing handlers if any to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()

    log_stream = io.StringIO()
    capture_handler = logging.StreamHandler(log_stream)
    capture_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(capture_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(console_handler)

    logger.info(
        "Starting GenAI Research Agent"
        "\n=================================================="
    )

    task_class = TASKS.get(args.task)
    if not task_class:
        logger.error(
            f"Task '{args.task}' not found. Available tasks: {list(TASKS.keys())}"
        )
        return

    try:
        logger.info(f"Initializing task: {args.task}")
        task = task_class()

        logger.info("Executing task...")
        digest_data = task.run()

        if digest_data:
            logger.info("Task execution successful. Saving results...")

            # Save to Notion with logs
            log_contents = log_stream.getvalue()
            save_to_notion(digest_data, logs=log_contents)

            # Send to Google Chat
            send_to_google_chat(digest_data)

            logger.info("All operations completed successfully.")
        else:
            logger.warning("Task executed but returned no data.")

    except Exception as e:
        logger.error(f"Task failed with error: {e}")
        # Could implement error notification here


if __name__ == "__main__":
    main()
