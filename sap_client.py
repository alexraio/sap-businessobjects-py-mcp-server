
import requests
import json
from typing import List, Dict, Any

class SapApiClient:
    """
    A client for interacting with the SAP BusinessObjects RESTful Web Service API.
    
    This client handles authentication and provides methods to query universes,
    their structure, and execute queries.
    
    Note: The API endpoints and payload structures used here are based on common
    SAP BO 4.x REST API patterns. You may need to adjust them for your specific
    version. The API typically communicates in XML by default, so headers
    requesting JSON are important.
    """
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.logon_token = None
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json"
        })

    def login(self):
        """
        Authenticates with the SAP BO server and retrieves a logon token.
        """
        login_url = f"{self.base_url}/logon/long"
        auth_payload = {
            "userName": self.username,
            "password": self.password,
            "auth": "secEnterprise" # This can vary, e.g., secLDAP, secWinAD
        }
        
        try:
            response = self.session.post(login_url, data=json.dumps(auth_payload))
            response.raise_for_status()
            
            # The token is often returned in the headers, but can also be in the body.
            # Adjust as needed.
            self.logon_token = response.headers.get("X-SAP-LogonToken")
            if not self.logon_token:
                # As a fallback, check the response body
                data = response.json()
                self.logon_token = data.get("logonToken")

            if not self.logon_token:
                raise ConnectionError("Failed to retrieve logon token from SAP BO server.")

            # Add the token to session headers for all subsequent requests
            self.session.headers.update({"X-SAP-LogonToken": self.logon_token})
            print("Successfully logged into SAP BusinessObjects.")

        except requests.exceptions.RequestException as e:
            print(f"Error during SAP BO login: {e}")
            raise ConnectionError(f"Could not connect to SAP BO server at {login_url}. Please check the URL and credentials.") from e

    def logout(self):
        """
        Logs out from the SAP BO server, invalidating the token.
        """
        if not self.logon_token:
            return
            
        logout_url = f"{self.base_url}/logon/long"
        try:
            self.session.post(logout_url, data="{}") # Body might not be needed
            print("Successfully logged out from SAP BusinessObjects.")
        except requests.exceptions.RequestException as e:
            print(f"Error during SAP BO logout: {e}")
        finally:
            self.logon_token = None
            self.session.headers.pop("X-SAP-LogonToken", None)


    def get_tables(self) -> List[Dict[str, str]]:
        """
        Retrieves a list of available Universes, which we treat as tables.
        
        Returns:
            A list of dictionaries, where each dictionary represents a table.
        """
        # This endpoint is a guess. You might need to find the correct one for your version.
        universes_url = f"{self.base_url}/raylight/v1/universes"
        
        try:
            response = self.session.get(universes_url)
            response.raise_for_status()
            data = response.json()
            
            # The response structure needs to be parsed. This is a hypothetical structure.
            # It might be under a key like 'universes' or 'universe'.
            universes = data.get("universes", {}).get("universe", [])
            
            # Ensure universes is a list
            if not isinstance(universes, list):
                universes = [universes]

            return [{"table_name": u.get("name"), "id": u.get("id")} for u in universes if u.get("name")]
        except requests.exceptions.RequestException as e:
            print(f"Error fetching universes: {e}")
            return []
        except (json.JSONDecodeError, AttributeError) as e:
            print(f"Error parsing universes response: {e}")
            return []

    def get_columns(self, table_name: str) -> List[Dict[str, str]]:
        """
        Retrieves the columns (dimensions and measures) for a given Universe.
        
        Args:
            table_name: The name of the universe to inspect.
            
        Returns:
            A list of dictionaries, where each dictionary represents a column.
        """
        # First, we need to find the ID of the universe by its name.
        # This might require an extra API call or can be cached from get_tables().
        universes = self.get_tables()
        universe_id = next((u["id"] for u in universes if u["table_name"] == table_name), None)

        if not universe_id:
            raise ValueError(f"Universe '{table_name}' not found.")

        # This endpoint is a guess. It might be /outline, /dictionary, etc.
        #columns_url = f"{self.base_url}/raylight/v1/universes/{universe_id}/outline"
        columns_url = f"{self.base_url}/raylight/v1/universes/{universe_id}?aggregated=true"
        
        try:
            response = self.session.get(columns_url)
            response.raise_for_status()
            data = response.json()

            # The response structure is highly hypothetical. You will need to inspect
            # the actual output from your server to parse it correctly.
            # We assume a structure with "nodes" or "items".
            columns = []
            items = data.get("nodes", {}).get("node", [])

            def extract_items(nodes):
                for item in nodes:
                    # Check if it's a leaf node (a column)
                    if item.get("techType") in ["Dimension", "Measure", "Attribute"]:
                        columns.append({
                            "column_name": item.get("name"),
                            "data_type": item.get("dataType", "string"),
                            "description": item.get("description", "")
                        })
                    # Recurse if there are children
                    if "nodes" in item and "node" in item["nodes"]:
                        extract_items(item["nodes"]["node"])
            
            extract_items(items)
            return columns

        except requests.exceptions.RequestException as e:
            print(f"Error fetching columns for {table_name}: {e}")
            return []
        except (json.JSONDecodeError, AttributeError) as e:
            print(f"Error parsing columns response: {e}")
            return []

    def run_query(self, sql: str) -> List[Dict[str, Any]]:
        """
        Executes a query against a Universe.
        
        Note: The BO REST API does not typically accept raw SQL. This method
        parses a simple "SELECT col1, col2 FROM table" query and translates it
        into the necessary API calls to create and run a query document.
        This is a highly simplified and may need significant enhancement.
        
        Args:
            sql: A simple SQL string in the format "SELECT ... FROM ...".
            
        Returns:
            A list of dictionaries representing the query result rows.
        """
        # 1. Basic SQL Parsing
        try:
            select_part, from_part = sql.upper().split(" FROM ")
            table_name = from_part.strip().strip('[]"')
            columns_str = select_part.replace("SELECT", "").strip()
            selected_columns = [c.strip().strip('[]"') for c in columns_str.split(',')]
        except ValueError:
            raise ValueError("Unsupported SQL format. Please use 'SELECT col1, col2 FROM table'.")

        # 2. Get Universe and Column details
        universe_id = next((u["id"] for u in self.get_tables() if u["table_name"] == table_name), None)
        if not universe_id:
            raise ValueError(f"Universe '{table_name}' not found.")
            
        available_columns = self.get_columns(table_name)
        
        # This is a placeholder. The API needs object IDs, not just names.
        # A real implementation would need to map names back to the IDs from the get_columns response.
        result_objects = []
        for col_name in selected_columns:
            # This is a simplification. The actual object ID is needed.
            # Example: find the object in `available_columns` and get its real ID.
            result_objects.append({"id": col_name, "name": col_name})


        # 3. Create a transient document/query
        # This is a complex, multi-step process in the BO API.
        # The following is a conceptual and simplified workflow.
        
        # a. Define the query
        query_spec = {
            "name": "MCP_Transient_Query",
            "query": {
                "dataSourceId": universe_id,
                "resultObjects": result_objects,
                # "queryFilter": [], # WHERE clauses would be defined here
            }
        }
        
        # b. Create the document
        create_doc_url = f"{self.base_url}/raylight/v1/documents"
        try:
            response = self.session.post(create_doc_url, data=json.dumps({"document": query_spec}))
            response.raise_for_status()
            doc_data = response.json()
            document_id = doc_data.get("document", {}).get("id")
            
            if not document_id:
                raise ValueError("Failed to create transient document for query.")

            # c. Get the data provider (flow) for the results
            # The endpoint and structure are hypothetical
            flows_url = f"{self.base_url}/raylight/v1/documents/{document_id}/dataproviders/1/flows/1"
            response = self.session.get(flows_url)
            response.raise_for_status()
            
            # The data is often returned in a non-standard format (e.g., csv-like lists)
            # and needs careful parsing. This is a major simplification.
            flow_data = response.json()
            
            # d. Clean up the transient document
            delete_doc_url = f"{self.base_url}/raylight/v1/documents/{document_id}"
            self.session.delete(delete_doc_url)

            # Assume flow_data is a list of rows
            # This part is highly dependent on the actual API response format
            # For example: {"flow": {"values": [["val1", "val2"], ["valA", "valB"]]}}
            rows = flow_data.get("flow", {}).get("values", [])
            header = selected_columns
            
            return [dict(zip(header, row)) for row in rows]

        except requests.exceptions.RequestException as e:
            print(f"Error running query: {e}")
            # Try to include response text for better debugging
            if e.response is not None:
                print(f"Response body: {e.response.text}")
            return []
        except (json.JSONDecodeError, AttributeError, ValueError) as e:
            print(f"Error processing query response: {e}")
            return []

