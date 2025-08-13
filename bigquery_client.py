from typing import Tuple, Dict, Any
from google.cloud import bigquery
from google.api_core.exceptions import NotFound, GoogleAPICallError, BadRequest


class BigQueryClient:
    """
    Thin wrapper for BigQuery inserts using table.insert_rows_json.
    Auth:
      - Application Default Credentials (e.g., set GOOGLE_APPLICATION_CREDENTIALS)
      - Or Streamlit Cloud secrets with gcloud auth handled by the environment
    """

    def __init__(self, dataset: str, table: str, location: str | None = None):
        self.client = bigquery.Client(location=location) if location else bigquery.Client()
        self.dataset = dataset
        self.table = table

        # Ensure table exists; raise a clear error otherwise
        try:
            self.table_ref = self.client.dataset(self.dataset).table(self.table)
            self.client.get_table(self.table_ref)
        except NotFound as e:
            raise RuntimeError(
                f"BigQuery table {self.dataset}.{self.table} not found."
            ) from e

    def insert_media_record(self, row: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Inserts a single record. Returns (success, message).
        Uses JSON inserts to avoid string-building SQL and to rely on schema.
        """
        try:
            errors = self.client.insert_rows_json(self.table_ref, [row])
            if errors:
                # Collect error messages
                messages = []
                for err in errors:
                    if "errors" in err:
                        messages.extend(
                            f"{e.get('message','unknown')}" for e in err["errors"]
                        )
                    else:
                        messages.append(str(err))
                return False, "; ".join(messages)
            return True, "ok"
        except (GoogleAPICallError, BadRequest) as e:
            return False, str(e)
        except Exception as e:
            return False, f"Unexpected error: {e}"
