import asyncio
import io
import csv
from contextlib import asynccontextmanager
from typing import Any, List, Dict

from mcp.server.fastmcp import FastMCP, Context

from config import SAP_BO_REST_API_URL, SAP_BO_USERNAME, SAP_BO_PASSWORD
from sap_client import SapApiClient

# 2. Define a lifespan manager for the SAP API client
# This ensures we log in on server startup and log out on shutdown.
@asynccontextmanager
async def sap_client_lifespan(app: FastMCP):
    """Manage the SAP API client's connection lifecycle."""
    print("Initializing SAP API client...")
    client = SapApiClient(
        base_url=SAP_BO_REST_API_URL,
        username=SAP_BO_USERNAME,
        password=SAP_BO_PASSWORD
    )
    try:
        client.login()
        # Make the client available to the tool functions via the app state
        app.sap_client = client
        yield
    finally:
        print("Shutting down SAP API client...")
        client.logout()

# 1. Initialize the MCP Server
# The name is used to prefix the tools, e.g., "sapbusinessobjectsbi_get_tables"
mcp = FastMCP("sapbusinessobjectsbi", lifespan=sap_client_lifespan)

# 3. Helper function to convert dictionary output to CSV string
def to_csv_string(data: List[Dict[str, Any]]) -> str:
    """Converts a list of dictionaries to a CSV formatted string."""
    if not data:
        return ""
    
    output = io.StringIO()
    # Use the keys from the first dictionary as the header
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)
    
    return output.getvalue()

# 4. Define the MCP Tools
# The SDK uses decorators and type hints to automatically generate the
# tool's input schema.

@mcp.tool()
def get_tables(ctx: Context) -> str:
    """
    Retrieves a list of objects, entities, collections, etc. (as tables) 
    available in the data source. Use the `get_columns` tool to list 
    available columns on a table.
    """
    print("Executing get_tables tool...")
    client: SapApiClient = ctx.fastmcp.sap_client
    tables = client.get_tables()
    return to_csv_string(tables)

@mcp.tool()
def get_columns(ctx: Context, table: str) -> str:
    """
    Retrieves a list of fields, dimensions, or measures (as columns) for an 
    object, entity or collection (table). Use the `get_tables` tool to get a 
    list of available tables.

    Args:
        table: The name of the table to retrieve columns for.
    """
    print(f"Executing get_columns tool for table: {table}...")
    client: SapApiClient = ctx.fastmcp.sap_client
    try:
        columns = client.get_columns(table)
        return to_csv_string(columns)
    except ValueError as e:
        return f"Error: {e}"

@mcp.tool()
def run_query(ctx: Context, sql: str) -> str:
    """
    Executes a SQL SELECT statement.

    Args:
        sql: The SELECT statement to execute. The format should be 
             'SELECT col1, col2 FROM [TableName]'.
    """
    print(f"Executing run_query tool with SQL: {sql}...")
    client: SapApiClient = ctx.fastmcp.sap_client
    try:
        results = client.run_query(sql)
        return to_csv_string(results)
    except ValueError as e:
        return f"Error: {e}"

# 5. Entry point to run the server
if __name__ == "__main__":
    # This will start the server using stdio transport by default,
    # which is what the original project did.
    mcp.run()