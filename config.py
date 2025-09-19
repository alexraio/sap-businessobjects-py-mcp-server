
import os
from dotenv import load_dotenv

load_dotenv()

SAP_BO_REST_API_URL = os.getenv("SAP_BO_REST_API_URL")
SAP_BO_USERNAME = os.getenv("SAP_BO_USERNAME")
SAP_BO_PASSWORD = os.getenv("SAP_BO_PASSWORD")
