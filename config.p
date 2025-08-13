from dataclasses import dataclass
import os
import streamlit as st


@dataclass(frozen=True)
class Settings:
    app_title: str = os.getenv("APP_TITLE", "Media Tracker")
    logo_url: str | None = os.getenv("LOGO_URL", None)
    default_fund_name: str | None = os.getenv("DEFAULT_FUND_NAME", None)

    # BigQuery
    bq_dataset: str = st.secrets.get("bigquery", {}).get("dataset", "")
    bq_table: str = st.secrets.get("bigquery", {}).get("table", "")
    bq_location: str | None = st.secrets.get("bigquery", {}).get("location", None)

    # Footer / contact
    contact_email: str | None = os.getenv("CONTACT_EMAIL", None)
    footer_text: str = os.getenv("FOOTER_TEXT", "Built with Streamlit")
