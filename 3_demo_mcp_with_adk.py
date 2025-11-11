"""
Demo: Using FindSGJobs MCP Server with Google ADK
==================================================

This script demonstrates how to use a custom MCP server (FindSGJobs)
with Google's Agent Development Kit (ADK).

It shows:
1. How to connect to a custom MCP server
2. How to integrate MCP tools with ADK agents
3. Real-world use case: Job search assistant with market analysis
4. Combining MCP tools with other ADK capabilities

Prerequisites:
- findsgjobs_mcp_server.py (the MCP server)
- Python MCP SDK installed
- Google ADK installed
- GOOGLE_API_KEY in .env file

Usage:
    python demo_mcp_with_adk.py
"""

import os
import asyncio
from dotenv import load_dotenv
from google.genai import types
from google.adk.agents import LlmAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.tools import AgentTool
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from google.adk.code_executors import BuiltInCodeExecutor
from mcp import StdioServerParameters


# ========================================
# Setup and Configuration
# ========================================

def setup_environment() -> None:
    """Load environment variables and configure API key."""
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
# Create MCP Toolset for FindSGJobs
# ========================================

def create_findsgjobs_mcp_toolset() -> McpToolset:
    """
    Create an MCP toolset that connects to our custom FindSGJobs MCP server.
    
    This demonstrates how to integrate a custom MCP server with ADK.
    The server runs as a separate Python process and communicates via stdio.
    
    Returns:
        McpToolset configured to connect to FindSGJobs MCP server
    """
    # Get the absolute path to the MCP server script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    server_path = os.path.join(current_dir, "findsgjobs_mcp_server.py")
    
    mcp_toolset = McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command="python",
                args=[server_path],
            ),
            timeout=30,
        )
    )
    
    print("✅ FindSGJobs MCP toolset created")
    print(f"   Server: {server_path}")
    print("   Available tools:")
    print("   • search_jobs - Search for job listings")
    print("   • get_job_statistics - Get market statistics")
    print("   • get_job_details - Get detailed job info")
    
    return mcp_toolset


# ========================================
# Create Data Analyst Agent
# ========================================

def create_analyst_agent() -> LlmAgent:
    """
    Create a data analyst agent that can analyze job market data.
    
    This agent uses code execution to perform complex analysis on the
    data retrieved from the MCP server.
    
    Returns:
        LlmAgent configured for data analysis
    """
    analyst = LlmAgent(
        name="JobMarketAnalyst",
        model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
        instruction="""You are a specialized job market analyst.
        
        Your expertise:
        1. Analyze job market data and statistics
        2. Generate Python code to compute insights
        3. Identify trends and patterns in job listings
        4. Provide actionable career recommendations
        5. Compare different job categories and locations
        
        Your code MUST:
        - Print clear, actionable insights
        - Calculate percentages and ratios
        - Identify top opportunities
        - Provide data-driven recommendations
        
        Keep your analysis focused and practical for job seekers.
        """,
        code_executor=BuiltInCodeExecutor(),
    )
    return analyst


# ========================================
# Create Main Job Search Assistant
# ========================================

def create_job_search_assistant(mcp_toolset: McpToolset, analyst: LlmAgent) -> LlmAgent:
    """
    Create the main job search assistant that coordinates all capabilities.
    
    This agent combines:
    - MCP tools (FindSGJobs server) for job search
    - Agent tool (analyst) for data analysis
    
    Args:
        mcp_toolset: The FindSGJobs MCP toolset
        analyst: The data analyst agent
        
    Returns:
        LlmAgent configured as job search assistant
    """
    assistant = LlmAgent(
        name="JobSearchAssistant",
        model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
        instruction="""You are an expert job search assistant for Singapore.
        
        Your capabilities:
        1. search_jobs - Find job listings using keywords
        2. get_job_statistics - Get market insights and trends
        3. JobMarketAnalyst - Analyze data and provide recommendations
        
        Workflow:
        - For job searches: Use search_jobs with relevant keywords
        - For market insights: Use get_job_statistics 
        - For analysis: Delegate to JobMarketAnalyst with the data
        - Always provide clear, actionable advice for job seekers
        - Highlight key details: title, company, salary, location
        
        When presenting results:
        1. Summarize the total number of jobs found
        2. Show the most relevant job listings
        3. Provide market insights if requested
        4. Give actionable recommendations
        
        Be helpful, clear, and focused on the user's career goals.
        """,
        tools=[
            mcp_toolset,  # MCP tools from FindSGJobs server
            AgentTool(agent=analyst),  # Data analyst agent
        ],
    )
    
    print("✅ Job Search Assistant created")
    print("   Capabilities: MCP tools + Data analyst agent")
    
    return assistant


# ========================================
# Demonstration Functions
# ========================================

async def demo_basic_job_search():
    """
    Demo 1: Basic job search using MCP server.
    
    Shows how the agent uses the MCP server to search for jobs.
    """
    print("\n" + "=" * 70)
    print("DEMO 1: Basic Job Search with MCP Server")
    print("=" * 70)
    print("Testing MCP tool: search_jobs\n")
    
    # Create MCP toolset for this demo
    mcp_toolset = create_findsgjobs_mcp_toolset()
    
    try:
        # Create simple agent with just MCP tools
        agent = LlmAgent(
            name="SimpleSearchAgent",
            model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
            instruction="""You are a job search assistant. Use search_jobs to find jobs.
        Present the results clearly with job titles, companies, and key details.""",
            tools=[mcp_toolset],
        )
        
        runner = InMemoryRunner(agent=agent)
        
        print("Query: Find me 5 cook jobs in Singapore\n")
        response = await runner.run_debug(
            "Find me 5 cook jobs in Singapore"
        )
        
        print("\n✅ Basic job search demo complete!\n")
    
    finally:
        # Properly close the MCP toolset
        try:
            if hasattr(mcp_toolset, 'close'):
                await mcp_toolset.close()
        except Exception as e:
            print(f"Warning: Error closing MCP toolset: {e}")


async def demo_job_market_statistics():
    """
    Demo 2: Get job market statistics using MCP server.
    
    Shows how the agent uses the MCP server to get market insights.
    """
    print("\n" + "=" * 70)
    print("DEMO 2: Job Market Statistics with MCP Server")
    print("=" * 70)
    print("Testing MCP tool: get_job_statistics\n")
    
    # Create MCP toolset for this demo
    mcp_toolset = create_findsgjobs_mcp_toolset()
    
    try:
        # Create agent with MCP tools
        agent = LlmAgent(
            name="StatsAgent",
            model=Gemini(model="gemini-2.5-flash-lite", retry_options=retry_config),
            instruction="""You are a job market analyst. Use get_job_statistics to get 
        market data. Present the statistics clearly with insights.""",
            tools=[mcp_toolset],
        )
        
        runner = InMemoryRunner(agent=agent)

        print("Query: What's the job market like for cooks?\n")
        response = await runner.run_debug(
            "What's the job market like for cooks? Give me statistics."
        )
        
        print("\n✅ Job market statistics demo complete!\n")
    
    finally:
        # Properly close the MCP toolset
        try:
            if hasattr(mcp_toolset, 'close'):
                await mcp_toolset.close()
        except Exception as e:
            print(f"Warning: Error closing MCP toolset: {e}")


async def demo_full_assistant():
    """
    Demo 3: Complete job search assistant with analysis.
    
    Shows the full power of combining MCP tools with agent tools.
    """
    print("\n" + "=" * 70)
    print("DEMO 3: Complete Job Search Assistant (MCP + Agent Tools)")
    print("=" * 70)
    print("Combining: FindSGJobs MCP Server + Data Analyst Agent\n")
    
    # Create MCP toolset for this demo
    mcp_toolset = create_findsgjobs_mcp_toolset()
    
    try:
        # Create all components
        analyst = create_analyst_agent()
        assistant = create_job_search_assistant(mcp_toolset, analyst)
        
        runner = InMemoryRunner(agent=assistant)
        
        print("Query: Find cook jobs and analyze the market opportunities\n")
        response = await runner.run_debug(
            "Find cook jobs in Singapore, get market statistics, and analyze what this means for someone looking for cook positions. What are the key insights and recommendations?"
        )
        
        print("\n✅ Complete assistant demo complete!\n")
    
    finally:
        # Properly close the MCP toolset
        try:
            if hasattr(mcp_toolset, 'close'):
                await mcp_toolset.close()
        except Exception as e:
            print(f"Warning: Error closing MCP toolset: {e}")


# ========================================
# Main Execution
# ========================================

async def main():
    """
    Main function to run all demonstrations.
    
    Executes all demos to showcase MCP server integration with ADK.
    """
    print("\n" + "=" * 70)
    print("FINDSGJOBS MCP SERVER WITH GOOGLE ADK DEMONSTRATION")
    print("=" * 70)
    print("This script demonstrates:")
    print("1. Basic MCP server integration")
    print("2. Job market statistics via MCP")
    print("3. Combining MCP tools with Agent tools")
    print("=" * 70)
    
    # Setup environment
    setup_environment()
    
    # Check if MCP server file exists
    current_dir = os.path.dirname(os.path.abspath(__file__))
    server_path = os.path.join(current_dir, "findsgjobs_mcp_server.py")
    
    if not os.path.exists(server_path):
        print(f"\n❌ Error: MCP server not found at {server_path}")
        print("Please ensure findsgjobs_mcp_server.py is in the same directory.")
        return
    
    print(f"\n✅ MCP server found: {server_path}")
    
    # Run demonstrations
    try:
        await demo_basic_job_search()
        await demo_job_market_statistics()
        await demo_full_assistant()
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {str(e)}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        raise
