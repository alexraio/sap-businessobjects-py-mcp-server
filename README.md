# Python MCP Server for SAP BusinessObjects BI

## Overview

This project provides a Python-based Model Context Protocol (MCP) server for SAP BusinessObjects BI. It allows Large Language Models (LLMs) and other MCP-compatible clients to interact with your SAP BO data using natural language.

Unlike the original Java implementation, this version uses the official SAP BusinessObjects REST API for data access and is built using the [Model Context Protocol Python SDK](https://github.com/modelcontextprotocol/python-sdk).

## Prerequisites

*   Python 3.8+
*   `pip` for package installation

## Setup and Configuration

Follow these steps to set up and configure the server.

### 1. Install Dependencies

Navigate to the `python_sap_server` directory and install the required packages from the `requirements.txt` file:

```bash
cd /home/aballarin/git/sap-businessobjects-bi-mcp-server-by-cdata/python_sap_server
pip install -r requirements.txt
```

### 2. Configure Connection

You must provide your SAP BusinessObjects REST API endpoint and credentials.

1.  Open the `.env` file in the `python_sap_server` directory.
2.  Replace the placeholder values with your actual connection details.

```dotenv
# SAP BusinessObjects REST API Configuration
SAP_BO_REST_API_URL="http://<your_sap_bo_server>:6405/biprws"
SAP_BO_USERNAME="your_username"
SAP_BO_PASSWORD="your_password"
```

## Running the Server

There are two primary ways to run the server.

### Method 1: Standalone

You can run the server directly from your terminal. This is useful for testing and development. The server will use STDIO for communication.

```bash
python /home/aballarin/git/sap-businessobjects-bi-mcp-server-by-cdata/python_sap_server/app.py
```

### Method 2: Integration with an MCP Client (e.g., Gemini)

To have your client automatically load the server, you need to add it to the client's configuration file (e.g., `settings.json`).

1.  Locate your client's MCP server configuration file.
2.  Add the following JSON object to the `mcpServers` section:

```json
{
  "mcpServers": {
    "sap-bo-python": {
      "command": "python3",
      "args": [
        "/home/aballarin/git/sap-businessobjects-bi-mcp-server-by-cdata/python_sap_server/app.py"
      ],
      "workingDirectory": "/home/aballarin/git/sap-businessobjects-bi-mcp-server-by-cdata/python_sap_server"
    }
  }
}
```

**Note**: For robustness, you may want to replace `"python3"` with the absolute path to your Python executable.

3.  Restart your MCP client. The server will be launched automatically.

## Available Tools

Once running, the server exposes the following tools to the LLM:

### `sapbusinessobjectsbi_get_tables`

Retrieves a list of available Universes (treated as tables).

*   **Usage Example**: "list all tables in sap business objects"

### `sapbusinessobjectsbi_get_columns`

Retrieves the columns (dimensions, measures, etc.) for a specific table (Universe).

*   **Parameters**:
    *   `table` (str): The name of the table.
*   **Usage Example**: "what are the columns in the 'eFashion' table?"

### `sapbusinessobjectsbi_run_query`

Executes a simple `SELECT` query against a table (Universe).

*   **Parameters**:
    *   `sql` (str): The SQL query to run. Must be in the format `SELECT [Column1], [Column2] FROM [TableName]`.
*   **Usage Example**: "show me the 'Year' and 'Sales revenue' from the 'eFashion' table"

## Development Notes

**IMPORTANT**: The `sap_client.py` file contains a client for the SAP BusinessObjects REST API that is based on common API patterns. The specific endpoints, request payloads, and response parsing logic are **highly likely to require modification** to fit your specific version and configuration of SAP BusinessObjects.

Before extensive use, you should review and adapt `sap_client.py` by inspecting the actual requests and responses from your SAP BO server's REST API.
