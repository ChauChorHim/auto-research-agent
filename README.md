# Auto Research Agent

This repository contains a Python-based autonomous agent designed to conduct weekly research on specific technical topics and publish a digest to Notion. 

Currently configured to track advancements in **Garment Simulation & Computational Fashion**.

## How It Works

1.  **Trigger:** The agent runs automatically every **Saturday at 06:00 UTC** via GitHub Actions.
2.  **Research:** It uses **Google Gemini 3.0 Pro** (with Google Search tools) to find and analyze recent papers, articles, and codebases.
3.  **Filtering:** It strictly filters results to ensure they were published within the last 30 days.
4.  **Reporting:** It generates a structured report and saves it as a new child page in a specified **Notion** workspace. Execution logs are also attached to the Notion page for debugging.

## Features

-   **AI-Powered Research:** Leverages Gemini's multimodal and search capabilities to understand complex technical queries.
-   **Structured Output:** Uses Pydantic models to ensure consistent data formatting (Title, Relevance, Innovation, Summary).
-   **Notion Integration:** Automatically formats the report with headers, links, and tags in Notion blocks.
-   **Log Capture:** Captures runtime logs and embeds them directly into the Notion report for easy monitoring.

## Configuration

### Environment Variables

The agent requires the following secrets to be set in your GitHub Repository Secrets (or `.env` for local development):

| Variable | Description |
| :--- | :--- |
| `GEMINI_API_KEY` | API Key for Google GenAI (Gemini). |
| `NOTION_API_KEY` | Notion Integration Token (Internal Integration). |
| `NOTION_PAGE_ID` | The ID of the parent Notion page where weekly reports will be created. |

### modifying the Research Topic

To change the research focus, edit `research_topic_prompts.py`:

```python
# research_topic_prompts.py

# Update the query string to change the research directive
garment_simulation_query = """..."""

# Adjust the lookback period
DAYS_LOOKBACK = 30
```

## Local Development

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/ChauChorHim/auto-research-agent
    cd auto-research-agent
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up environment variables:**
    Create a `.env` file in the root directory:
    ```env
    GEMINI_API_KEY=your_gemini_key
    NOTION_API_KEY=your_notion_key
    NOTION_PAGE_ID=your_parent_page_id
    ```

4.  **Run the agent:**
    ```bash
    python main.py
    ```

## File Structure

-   `main.py`: The core entry point. Handles logging, API initialization, and orchestration.
-   `research_topic_prompts.py`: Contains the specific prompts and constraints for the research topic.
-   `system_instruction_prompts.py`: System-level instructions for the LLM to define its persona and output format.
-   `schemas.py`: Pydantic definitions for the expected JSON response from Gemini.
-   `.github/workflows/actions.yml`: GitHub Actions configuration for the weekly schedule.
