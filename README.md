# 📰 Smart Media Tracker

A Streamlit-powered media tracking application for intelligent web content analysis and data collection with BigQuery integration.

## Features

- 🔍 **Smart Web Scraping** - Automatic article content and title extraction
- 📊 **BigQuery Integration** - Direct database storage with authentication
- 🎯 **Two-Step Workflow** - Extract → Review → Save
- ✏️ **Manual Editing** - Fallback content entry and title editing
- 📈 **Fund Management** - "Managed by Fund" tracking option

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up BigQuery credentials (environment variable: `GOOGLE_APPLICATION_CREDENTIALS_JSON`)
4. Run: `streamlit run app.py`

## Usage

1. Enter article URL
2. Click "🔍 Scrape Article"
3. Review extracted data and edit as needed
4. Add spokesperson/portfolio company details
5. Save to BigQuery

## Tech Stack

- **Streamlit** - Web interface
- **Trafilatura** - Web scraping
- **Google BigQuery** - Data storage
- **Python** - Backend logic
