import streamlit as st
from bigquery_client import BigQueryClient
from web_scraper import get_website_text_content, extract_domain_from_url, get_article_title
from datetime import datetime

def main():
    st.title("📰 Smart Media Tracker")

    try:
        bq_client = BigQueryClient()
        st.success("✅ Connected to BigQuery")
    except Exception as e:
        st.error(f"❌ BigQuery connection failed: {e}")
        return

    st.subheader("Step 1: Extract Article Data")
    url = st.text_input("Enter article URL:")
    scrape_clicked = st.button("🔍 Scrape Article")

    if scrape_clicked:
        if not url:
            st.error("❌ Please enter a URL")
        else:
            with st.spinner("Extracting content..."):
                try:
                    content = get_website_text_content(url)
                    title = get_article_title(url)
                    domain = extract_domain_from_url(url)

                    st.session_state.scraped_data = {
                        'url': url,
                        'content': content if content else '',
                        'title': title if title else '',
                        'domain': domain,
                        'publish_date': datetime.now().strftime('%Y-%m-%d')
                    }

                    if content:
                        st.success("✅ Content extracted successfully!")
                    else:
                        st.warning("⚠️ Could not extract content automatically. Please add manually below.")

                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Error: {e}")
                    st.session_state.scraped_data = {
                        'url': url,
                        'content': '',
                        'title': '',
                        'domain': extract_domain_from_url(url),
                        'publish_date': datetime.now().strftime('%Y-%m-%d')
                    }
                    st.rerun()

    if 'scraped_data' in st.session_state:
        st.markdown("---")
        st.subheader("Step 2: Review & Submit")

        data = st.session_state.scraped_data

        st.write("**Extracted Data Preview:**")
        col1, col2 = st.columns(2)

        with col1:
            st.write(f"**URL:** {data['url']}")
            st.write(f"**Domain:** {data['domain']}")
            st.write(f"**Publish Date:** {data['publish_date']}")
            if data.get('title'):
                st.write(f"**Title:** {data['title']}")

        with col2:
            if data['content']:
                st.write(f"**Content Preview:** {data['content'][:150]}...")
            else:
                st.write("**Content Preview:** ❌ No content extracted")

        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            publish_date = st.date_input("Publish Date:", value=datetime.strptime(data['publish_date'], '%Y-%m-%d').date())
            title = st.text_input("Article Title:", value=data.get('title', ''), placeholder="Enter article title/headline")
            spokesperson = st.text_input("Spokesperson:", placeholder="Enter spokesperson name")

        with col2:
            portfolio_company = st.text_input("Portfolio Company:", placeholder="Enter portfolio company")
            managed_by_fund = st.checkbox("📊 Managed by Fund")

        st.subheader("Article Content")
        content = st.text_area(
            "Edit or add article content:",
            value=data['content'],
            height=200,
            placeholder="Paste or type the full article content here...",
            help="Edit the extracted content or add it manually if extraction failed"
        )

        if st.button("💾 Save to BigQuery", type="primary"):
            if not content.strip():
                st.error("❌ Content is required!")
                return

            record_data = {
                'url': data['url'],
                'content': content,
                'domain': data['domain'],
                'title': title,
                'publish_date': publish_date.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'matched_spokespeople': spokesperson or '',
                'matched_portcos': portfolio_company or '',
                'managed_by_fund': managed_by_fund,
            }

            with st.spinner("Saving to BigQuery..."):
                success = bq_client.insert_media_record(record_data)
                if success:
                    st.success("✅ Saved to BigQuery!")
                    del st.session_state.scraped_data
                    st.rerun()
                else:
                    st.error("❌ Failed to save")

if __name__ == "__main__":
    main()
