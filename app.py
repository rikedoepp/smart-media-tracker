import streamlit as st
from datetime import datetime, date
from bigquery_client import BigQueryClient
from web_scraper import (
    get_website_text_content,
    extract_domain_from_url,
    get_article_title,
)
from config import Settings

settings = Settings()

st.set_page_config(page_title="Media Tracker", page_icon="📰", layout="wide")


def header():
    col1, col2 = st.columns([1, 4])
    with col1:
        if settings.logo_url:
            st.image(settings.logo_url, width=80)
    with col2:
        st.title(settings.app_title)
        st.write("Extracts metadata from a website and inserts it into BigQuery.")


def init_bq():
    try:
        client = BigQueryClient(
            dataset=settings.bq_dataset,
            table=settings.bq_table,
            location=settings.bq_location,
        )
        st.success("✅ Connected to BigQuery")
        return client
    except Exception:
        st.error("❌ BigQuery connection failed. Check credentials & secrets.")
        st.stop()


def step_extract():
    st.subheader("Step 1: Extract Article Data")
    if "clear_url_field" not in st.session_state:
        st.session_state.clear_url_field = False

    url_key = "url_field_cleared" if st.session_state.clear_url_field else "url_field"
    url = st.text_input("Enter article URL:", key=url_key, placeholder="https://...")
    if st.session_state.clear_url_field:
        st.session_state.clear_url_field = False

    scrape_clicked = st.button("🔍 Scrape Article", type="primary")

    if scrape_clicked:
        if not url:
            st.error("❌ Please enter a URL first!")
            return

        with st.spinner("Extracting content..."):
            try:
                content = get_website_text_content(url)
                title = get_article_title(url)
                domain = extract_domain_from_url(url)

                st.session_state.scraped_data = {
                    "url": url,
                    "content": content or "",
                    "title": title or "",
                    "domain": domain,
                    "publish_date": datetime.now().strftime("%Y-%m-%d"),
                }

                if content:
                    st.success("✅ Content extracted.")
                else:
                    st.warning(
                        "⚠️ Could not extract content automatically. Add content manually below."
                    )

                st.session_state.clear_url_field = True
                st.rerun()

            except Exception as e:
                st.error("❌ Error extracting content. Manually complete the fields.")
                st.session_state.scraped_data = {
                    "url": url,
                    "content": "",
                    "title": "",
                    "domain": extract_domain_from_url(url),
                    "publish_date": datetime.now().strftime("%Y-%m-%d"),
                }
                st.session_state.clear_url_field = True
                st.rerun()


def step_review_and_save(bq_client: BigQueryClient):
    if "scraped_data" not in st.session_state:
        return

    st.markdown("---")
    st.subheader("Step 2: Review and Edit")

    data = st.session_state.scraped_data

    with st.expander("Extracted Data Preview", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            st.write(f"**Domain:** {data['domain']}")
            if data.get("title"):
                st.write(f"**Title:** {data['title']}")
        with c2:
            if data["content"]:
                # Render as plain text to avoid rendering/JS shenanigans
                st.text(f"{data['content'][:800]}")
            else:
                st.write("**Content Preview:** ❌ No content extracted")

    st.markdown("---")

    url = st.text_input("URL:", value=data["url"], help="Edit the article URL if needed")

    c1, c2 = st.columns(2)
    with c1:
        try:
            default_date = datetime.strptime(data["publish_date"], "%Y-%m-%d").date()
        except Exception:
            default_date = date.today()
        publish_date = st.date_input("Publish Date:", value=default_date)
        spokesperson = st.text_input("Spokesperson:", placeholder="Enter spokesperson")
        portfolio_company = st.text_input(
            "Portfolio Company:", placeholder="Enter portfolio company"
        )
        reporter = st.text_input("Reporter:", placeholder="Enter reporter name")
    with c2:
        gst_checkbox = st.checkbox("📊 GST Y/N")
        managed_by_fund_text = settings.default_fund_name if gst_checkbox else ""
        if gst_checkbox and settings.default_fund_name:
            st.caption(f"Will save '{settings.default_fund_name}' to managed_by_fund.")
        unbranded_win_checkbox = st.checkbox("🏆 Portfolio feature (no fund mention)")

    st.subheader("Article Headline")
    headline = st.text_input(
        "Headline/Title:",
        value=data.get("title", ""),
        placeholder="Enter article headline",
        help="Saved as the title in BigQuery",
    )

    st.subheader("Article Content")
    content = st.text_area(
        "Edit or add article content:",
        value=data["content"] or "",
        height=240,
        placeholder="Paste or type the full article content here…",
        help="Edit the extracted content or add it manually if extraction failed",
    )

    if st.button("💾 Save to BigQuery", type="primary"):
        if not content or not content.strip():
            st.error("❌ Content is required!")
            st.stop()

        with st.spinner("Checking for duplicates and saving to BigQuery…"):
            record_data = {
                "url": url,
                "content": content,
                "domain": extract_domain_from_url(url) or data["domain"],
                "title": headline,
                "publish_date": datetime.combine(publish_date, datetime.min.time()).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "matched_spokespeople": spokesperson or "",
                "matched_reporter": reporter or "",
                "backlinks": 0.0,
                "tagged_antler": bool(gst_checkbox),
                "language": "en",
                "matched_portcos": portfolio_company or "",
                "matched_portco_location": "",
                "matched_portco_deal_lead": "",
                "managed_by_fund": managed_by_fund_text,
                "unbranded_win": bool(unbranded_win_checkbox),
            }

            try:
                success, msg = bq_client.insert_media_record(record_data)
                if success:
                    st.success("✅ Saved to BigQuery!")
                    st.success("🔄 Ready to add another article!")

                    if "scraped_data" in st.session_state:
                        del st.session_state.scraped_data
                    st.session_state.clear_url_field = True

                    if st.button("➕ Add Another Article", type="primary"):
                        st.rerun()
                    st.rerun()
                else:
                    st.error(f"❌ Failed to save: {msg}")
            except Exception:
                st.error("❌ Save failed. Check logs and BigQuery permissions.")


def footer():
    st.markdown("---")
    f1, f2 = st.columns([1, 1])
    with f1:
        st.write(settings.footer_text)
    with f2:
        if settings.contact_email:
            st.write(f"Report bugs: {settings.contact_email}")


def main():
    header()
    bq_client = init_bq()
    step_extract()
    step_review_and_save(bq_client)
    footer()


if __name__ == "__main__":
    main()
