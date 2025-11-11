"""
Function Tools Demo
Using FindSGJobs API as Real-World Example

This script demonstrates function tools in ADK using a practical job search scenario:
- Custom Python functions for job search API

Based on: 1_basic_api_usage.py (FindSGJobs API)
Author: ADK Demo
Date: November 11, 2025
"""

import os
import requests
import json
from time import sleep
from dotenv import load_dotenv
from google.genai import types
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner

from function_tool import search_jobs_api, calculate_job_statistics


# ========================================
# Setup and Configuration
# ========================================

def setup_environment() -> None:
    """
    Load environment variables and configure API key.

    Loads GOOGLE_API_KEY from .env file and sets it as an environment variable.
    """
    try:
        load_dotenv()
        GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
        if GOOGLE_API_KEY and GOOGLE_API_KEY != "your_google_api_key_here":
            os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
            print("✅ Environment setup complete.")
        else:
            print(
                "🔑 Authentication Error: Please add your GOOGLE_API_KEY to the .env file."
            )
    except Exception as e:
        print(f"🔑 Authentication Error: Failed to load .env file. Details: {e}")


# Configure retry options for robust API calls
retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)


# ========================================
# FUNCTION TOOLS
# ========================================

def search_jobs(keywords: str, page: int = 1, per_page_count: int = 10) -> dict:
    """
    Search for jobs using the FindSGJobs API.

    This function tool demonstrates integration with real-world APIs.
    It connects to FindSGJobs.com API and returns structured job search results.

    Args:
        keywords: Search keywords (e.g., "cook", "engineer", "data analyst").
        page: Page number for pagination (default: 1).
        per_page_count: Number of results per page (default: 10, max: 20).

    Returns:
        Dictionary with status and job search results.
        Success: {"status": "success", "total_jobs": 150, "jobs": [...]}
        Error: {"status": "error", "error_message": "API request failed"}
    """
    result = search_jobs_api(keywords, page, per_page_count)
    
    if result.get("success"):
        return {
            "status": "success",
            "total_jobs": result.get("total_jobs", 0),
            "page": result.get("current_page", page),
            "results_on_page": result.get("results_on_page", 0),
            "jobs": result.get("jobs", [])
        }
    else:
        return {
            "status": "error",
            "error_message": result.get("error", "Unknown error")
        }


def get_job_statistics(keywords: str) -> dict:
    """
    Get statistical summary of job search results.

    This function tool demonstrates data aggregation and analysis.
    It fetches job listings and computes statistics like category distribution.

    Args:
        keywords: Search keywords for job search.

    Returns:
        Dictionary with status and statistics.
        Success: {"status": "success", "stats": {...}}
        Error: {"status": "error", "error_message": "..."}
    """
    result = calculate_job_statistics(keywords, sample_size=20)
    
    if result.get("success"):
        stats = result.get("statistics", {})
        return {
            "status": "success",
            "keyword": result.get("keyword", keywords),
            "stats": {
                "total_jobs_found": result.get("total_jobs_in_market", 0),
                "jobs_analyzed": result.get("jobs_analyzed", 0),
                "top_categories": stats.get("top_categories", {}),
                "employment_types": stats.get("employment_types", {}),
                "top_locations": stats.get("top_locations", {}),
            }
        }
    else:
        return {
            "status": "error",
            "error_message": result.get("error", "Unknown error")
        }


# ========================================
# DEMONSTRATION FUNCTION
# ========================================

async def demo_function_tools() -> None:
    """
    Demonstrate function tools with job search API calls.

    This shows how custom Python functions become agent tools that the LLM
    can call to retrieve real-world data from external APIs.
    """
    print("\n" + "=" * 60)
    print("DEMO: FUNCTION TOOLS")
    print("=" * 60)
    print("Testing custom function tools: job search API integration\n")

    # Test individual functions
    print("Testing functions directly:")
    print(f"Searching for 'software engineer' jobs...")
    result = search_jobs("software engineer", per_page_count=3)
    if result["status"] == "success":
        print(f"✓ Found {result['total_jobs']} total jobs")
        print(f"✓ Retrieved {result['results_on_page']} results on page {result['page']}\n")

    print(f"Getting statistics for 'data analyst' jobs...")
    stats = get_job_statistics("data analyst")
    if stats["status"] == "success":
        print(f"✓ Statistics computed successfully")
        print(f"✓ Total jobs: {stats['stats']['total_jobs_found']}\n")

    # Respect rate limit
    sleep(1)

    # Create agent with function tools only
    simple_agent = LlmAgent(
        name="SimpleJobSearchAgent",
        model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
        # instruction="""You are a job search assistant. Use search_jobs() to find job
        # listings and get_job_statistics() for market insights. Always check for errors.""",
        # tools=[search_jobs, get_job_statistics],
        instruction="""You are a job search assistant. Use get_job_statistics() to find job
        listings and market insights. Always check for errors.""",
        tools=[get_job_statistics],
    )

    runner = InMemoryRunner(agent=simple_agent)

    print("Agent Query: Find cook jobs, summarize the key details and show in point form.")
    response = await runner.run_debug(
        "Find cook jobs, summarize the key details and show in point form."
    )
    print(f"\n✅ Function tools demonstration complete!\n")

    # Respect rate limit
    sleep(2)


# ========================================
# MAIN EXECUTION
# ========================================

async def main() -> None:
    """
    Main function to run the function tools demonstration.
    """
    print("\n" + "=" * 60)
    print("ADK FUNCTION TOOLS DEMONSTRATION")
    print("=" * 60)
    print("This script demonstrates:")
    print("1. Function Tools - Job search API")
    print("2. Function Tools - Job search API + statistics")
    print("=" * 60)

    # Setup environment
    setup_environment()

    # Run demonstration
    await demo_function_tools()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())