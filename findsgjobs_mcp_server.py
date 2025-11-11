#!/usr/bin/env python3
"""
FindSGJobs MCP Server
=====================
This script implements a Model Context Protocol (MCP) server that provides
job search capabilities using the FindSGJobs API.

The server exposes three tools:
1. search_jobs - Search for jobs by keywords
2. get_job_details - Get detailed information about a specific job
3. get_job_statistics - Get aggregated statistics about job market

Usage:
    python findsgjobs_mcp_server.py

Based on: 1_basic_api_usage.py
"""

import asyncio
import requests
from typing import Any
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from bs4 import BeautifulSoup
import re

from function_tool import search_jobs_api, calculate_job_statistics


# Initialize MCP Server
app = Server("findsgjobs-server")


# ============================================================
# MCP Server Tool Definitions
# ============================================================

@app.list_tools()
async def list_tools() -> list[Tool]:
    """
    List all available tools provided by this MCP server.
    
    Returns:
        List of Tool objects describing available capabilities
    """
    return [
        Tool(
            name="search_jobs",
            description="""Search for jobs in Singapore using keywords. 
            Returns a list of job listings with details like title, company, location, 
            salary, requirements, and more. Rate limit: 60 requests per minute.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "keywords": {
                        "type": "string",
                        "description": "Search keywords (e.g., 'software engineer', 'cook', 'manager')"
                    },
                    "page": {
                        "type": "integer",
                        "description": "Page number for pagination (default: 1)",
                        "default": 1
                    },
                    "per_page_count": {
                        "type": "integer",
                        "description": "Number of results per page (max: 20, default: 10)",
                        "default": 10
                    }
                },
                "required": ["keywords"]
            }
        ),
        Tool(
            name="get_job_statistics",
            description="""Get aggregated statistics about the job market for specific keywords.
            Returns statistics like top categories, employment types, locations, and requirements.
            Based on analysis of up to 20 job listings.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "keywords": {
                        "type": "string",
                        "description": "Search keywords to analyze (e.g., 'data scientist', 'accountant')"
                    },
                    "sample_size": {
                        "type": "integer",
                        "description": "Number of jobs to analyze (max: 20, default: 20)",
                        "default": 20
                    }
                },
                "required": ["keywords"]
            }
        ),
        Tool(
            name="get_job_details",
            description="""Get detailed information about a specific job by ID.
            Use this after searching for jobs to get the full description and requirements.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "job_id": {
                        "type": "string",
                        "description": "The job ID from search results"
                    }
                },
                "required": ["job_id"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """
    Handle tool execution requests from MCP clients.
    
    Args:
        name: Tool name to execute
        arguments: Tool-specific arguments
        
    Returns:
        List of TextContent with execution results
    """
    if name == "search_jobs":
        keywords = arguments.get("keywords", "")
        page = arguments.get("page", 1)
        per_page_count = arguments.get("per_page_count", 10)
        
        if not keywords:
            return [TextContent(
                type="text",
                text="Error: 'keywords' parameter is required"
            )]
        
        result = search_jobs_api(keywords, page, per_page_count)
        
        if result.get("success"):
            # Format response nicely
            response_text = f"Found {result['total_jobs']} jobs for '{keywords}'\n"
            response_text += f"Showing page {result['current_page']} of {result['total_pages']}\n"
            response_text += f"Results on this page: {result['results_on_page']}\n\n"
            
            for i, job in enumerate(result['jobs'], 1):
                response_text += f"{i}. {job['title']}\n"
                response_text += f"   Company: {job['company']}\n"
                response_text += f"   Job ID: {job['job_id']}\n"
                if job['salary']:
                    response_text += f"   Salary: {job['salary']}\n"
                if job['location']:
                    response_text += f"   Location: {', '.join(job['location'][:3])}\n"
                if job['categories']:
                    response_text += f"   Categories: {', '.join(job['categories'])}\n"
                response_text += f"   URL: {job['url']}\n\n"
            
            return [TextContent(type="text", text=response_text)]
        else:
            return [TextContent(
                type="text",
                text=f"Error: {result.get('error', 'Unknown error')}"
            )]
    
    elif name == "get_job_statistics":
        keywords = arguments.get("keywords", "")
        sample_size = arguments.get("sample_size", 20)
        
        if not keywords:
            return [TextContent(
                type="text",
                text="Error: 'keywords' parameter is required"
            )]
        
        result = calculate_job_statistics(keywords, sample_size)
        
        if result.get("success"):
            stats = result['statistics']
            response_text = f"Job Market Statistics for '{keywords}'\n"
            response_text += f"Total jobs in market: {result['total_jobs_in_market']}\n"
            response_text += f"Jobs analyzed: {result['jobs_analyzed']}\n\n"
            
            response_text += "Top Categories:\n"
            for category, count in stats['top_categories'].items():
                percentage = (count / result['jobs_analyzed'] * 100)
                response_text += f"  • {category}: {count} ({percentage:.1f}%)\n"
            
            response_text += "\nEmployment Types:\n"
            for emp_type, count in stats['employment_types'].items():
                percentage = (count / result['jobs_analyzed'] * 100)
                response_text += f"  • {emp_type}: {count} ({percentage:.1f}%)\n"
            
            response_text += "\nTop Locations:\n"
            for location, count in stats['top_locations'].items():
                response_text += f"  • {location}: {count} jobs\n"
            
            if stats['education_requirements']:
                response_text += "\nEducation Requirements:\n"
                for edu, count in stats['education_requirements'].items():
                    response_text += f"  • {edu}: {count} jobs\n"
            
            if stats['experience_requirements']:
                response_text += "\nExperience Requirements:\n"
                for exp, count in stats['experience_requirements'].items():
                    response_text += f"  • {exp}: {count} jobs\n"
            
            return [TextContent(type="text", text=response_text)]
        else:
            return [TextContent(
                type="text",
                text=f"Error: {result.get('error', 'Unknown error')}"
            )]
    
    elif name == "get_job_details":
        job_id = arguments.get("job_id", "")
        
        if not job_id:
            return [TextContent(
                type="text",
                text="Error: 'job_id' parameter is required"
            )]
        
        # Search for the specific job ID
        # Note: The API doesn't have a direct job detail endpoint, 
        # so we would need to search and filter
        return [TextContent(
            type="text",
            text=f"Job details for ID {job_id}: This would require additional API implementation. "
                 f"Currently, use search_jobs and find the job in results."
        )]
    
    else:
        return [TextContent(
            type="text",
            text=f"Error: Unknown tool '{name}'"
        )]


async def main():
    """
    Main entry point for the MCP server.
    Runs the server using stdio transport.
    """
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    # print("Starting FindSGJobs MCP Server...", flush=True)  # Removed print to avoid JSON-RPC protocol issues
    asyncio.run(main())
