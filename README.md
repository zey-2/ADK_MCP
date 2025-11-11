# ADK MCP Demo Repository

## Overview

This repository demonstrates the integration of Google's Agent Development Kit (ADK) with the Model Context Protocol (MCP) using real-world job search scenarios. It showcases all three ADK tool types - Function Tools, Agent Tools, and MCP Tools - through examples.

### Types of Tools

- **Function Tools**: Custom Python functions that integrate with real APIs (FindSGJobs.com)
- **Agent Tools**: Specialist agents that delegate complex tasks to other agents
- **MCP Tools**: External service integration via standardized MCP protocol

## Table of Contents

- [Setup Instructions](#setup-instructions)
- [Tool Types](#tool-types)
  - [Function Tools](#function-tools)
  - [Agent Tools](#agent-tools)
  - [MCP Tools](#mcp-tools)

## Setup Instructions

### Prerequisites

- Python 3.13+
- Google API key (Gemini API access)

### 3-Step Setup

1. **Install dependencies:**

   ```bash
   conda env create -f environment.yml
   conda activate google-adk
   ```

2. **Configure API key:**

   ```bash
   # Create a .env file in the root directory
   echo "GOOGLE_API_KEY=your_google_api_key_here" > .env
   # Then edit .env and replace with your actual API key
   ```

3. **Run demos:**

   ```bash
   # Demo 1: Function Tools
   python 1_function_tools_demo.py

   # Demo 2: Agent Tools
   python 2_agent_tools_demo.py

   # Demo 3: MCP Integration
   python 3_demo_mcp_with_adk.py
   ```

### File Structure

```
ADK_MCP/
├── 1_function_tools_demo.py       # Function tools demo
├── 2_agent_tools_demo.py          # Agent tools demo
├── 3_demo_mcp_with_adk.py         # MCP + ADK integration demo
├── findsgjobs_mcp_server.py       # MCP server implementation
├── function_tool.py               # Shared API functions
├── environment.yml                # Conda dependencies
├── .env                           # API keys (create this)
└── README.md                      # This file
```

## Tool Types

### Function Tools

**Custom Python functions that become agent tools**

#### When to Use

- You have custom business logic
- Need to call external APIs
- Require deterministic, fast execution
- Want full control over implementation

#### Example Implementation

```python
def search_jobs(keywords: str, page: int = 1) -> dict:
    """
    Search FindSGJobs API for job listings.

    Args:
        keywords: Search terms (e.g., "software engineer")
        page: Page number for pagination

    Returns:
        Structured dict with status and job data
    """
    try:
        response = requests.get(
            "https://www.findsgjobs.com/apis/job/search",
            params={"keywords": keywords, "page": page},
            timeout=10
        )
        response.raise_for_status()

        data = response.json()
        jobs = parse_job_results(data)

        return {
            "status": "success",
            "total_jobs": data.get("total", 0),
            "jobs": jobs
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e)
        }
```

### Agent Tools

**Using specialized agents as tools for other agents**

#### When to Use

- Need specialized expertise
- Complex analysis or reasoning required
- Code generation and execution needed
- Multi-step problem solving

#### Example Implementation

```python
# Create specialist agent
data_analyst = LlmAgent(
    name="DataAnalystAgent",
    model=Gemini(model="gemini-2.5-flash-lite"),
    instruction="""You are a data analyst specializing in job market analysis.
    When given job data, generate Python code to analyze trends and provide insights.
    Always print your results to stdout.""",
    code_executor=BuiltInCodeExecutor(),
)

# Use as tool in main agent
job_assistant = LlmAgent(
    name="JobSearchAssistant",
    instruction="Use DataAnalystAgent for complex market analysis",
    tools=[AgentTool(agent=data_analyst)],
)
```

### MCP Tools

**Connecting to external Model Context Protocol servers**

#### When to Use

- Want to use community-built integrations
- Need standardized external service access
- Prefer not to write custom integration code
- Want ecosystem compatibility

#### Example Implementation

```python
# Connect to MCP server
mcp_toolset = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="python",
            args=["findsgjobs_mcp_server.py"],
        ),
        timeout=30,
    )
)

# Use in agent
agent = LlmAgent(
    tools=[mcp_toolset]
)
```

## License

Educational demonstration for learning purposes.

---
