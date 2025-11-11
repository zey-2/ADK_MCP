"""
Agent Tools Demo
Using FindSGJobs API as Real-World Example

This script demonstrates agent tools in ADK using a practical job search scenario:
- Using other agents as tools for analysis

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

from function_tool import search_jobs_api
from google.adk.tools import AgentTool
from google.adk.code_executors import BuiltInCodeExecutor


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
# FUNCTION TOOLS (Required for Agent Tools Demo)
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


# ========================================
# AGENT TOOLS
# ========================================

def create_data_analyst_agent() -> LlmAgent:
    """
    Create a specialized data analyst agent that analyzes job market data.

    This agent is designed to be used as a tool by other agents, demonstrating
    the Agent Tool pattern where one agent delegates data analysis tasks to another.

    Returns:
        LlmAgent configured with code execution capabilities for data analysis.
    """
    analyst_agent = LlmAgent(
        name="DataAnalystAgent",
        model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
        instruction="""You are a specialized data analyst that analyzes job market data.

        Your task:
        1. Receive job market data or statistics
        2. Generate Python code to analyze and visualize insights
        3. The code MUST print analysis results to stdout
        4. Focus on actionable insights (trends, patterns, recommendations)
        5. Do NOT provide lengthy explanations, let the code speak

        Example: Given job statistics, generate code to:
        - Calculate percentages and ratios
        - Identify top opportunities
        - Compare different categories
        - Provide data-driven recommendations
        """,
        code_executor=BuiltInCodeExecutor(),
    )
    return analyst_agent


def create_job_search_assistant() -> LlmAgent:
    """
    Create a job search assistant that uses function tools and an agent tool.

    This demonstrates how to combine multiple tool types:
    - Function tools for API calls (search_jobs, get_job_statistics)
    - Agent tool for data analysis (data_analyst_agent)

    Returns:
        LlmAgent configured with multiple tool types.
    """
    analyst_agent = create_data_analyst_agent()

    job_assistant = LlmAgent(
        name="JobSearchAssistant",
        model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
        instruction="""You are a helpful job search assistant for Singapore jobs.

        For job search queries:
        1. Use search_jobs() to find job listings based on keywords
        2. Use DataAnalystAgent for complex data analysis and recommendations
        3. Check the "status" field in each tool's response for errors
        4. Provide clear, structured responses with actionable information
        5. When showing job results, highlight key details: title, company, location, salary

        If any tool returns status "error", explain the issue to the user clearly.
        Always provide helpful guidance for job seekers.
        """,
        tools=[
            search_jobs,
            AgentTool(agent=analyst_agent),  # Using agent as a tool!
        ],
    )
    return job_assistant


# ========================================
# DEMONSTRATION FUNCTION
# ========================================

async def demo_agent_tools() -> None:
    """
    Demonstrate agent tools where one agent uses another as a tool.

    This shows the delegation pattern where a job search assistant delegates
    data analysis to a specialized analyst agent.
    """
    print("\n" + "=" * 60)
    print("DEMO: AGENT TOOLS")
    print("=" * 60)
    print("Testing agent delegation: Job assistant uses data analyst agent\n")

    job_assistant = create_job_search_assistant()
    runner = InMemoryRunner(agent=job_assistant)

    print("Agent Query: Search for 'engineering' jobs and analyze the market trends.")
    print("What are the top categories and employment types?")
    response = await runner.run_debug(
        "Search for 'engineering' jobs and analyze the market trends. What are the top categories and what insights can you provide?"
    )
    print(f"\n✅ Agent tools demonstration complete!\n")

    # Respect rate limit
    sleep(2)


# ========================================
# MAIN EXECUTION
# ========================================

async def main() -> None:
    """
    Main function to run the agent tools demonstration.
    """
    print("\n" + "=" * 60)
    print("ADK AGENT TOOLS DEMONSTRATION")
    print("Using FindSGJobs API as Real-World Example")
    print("=" * 60)
    print("This script demonstrates:")
    print("1. Agent Tools - Data analyst agent delegation")
    print("=" * 60)

    # Setup environment
    setup_environment()

    # Run demonstration
    await demo_agent_tools()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())