# Trending Content Analyzer

This tool analyzes trending.csv content using LangGraph to identify topics, generate tags, and classify content for different communities (B2B, B2C, or Hybrid).

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure your API key in `config.yaml`:
   - For OpenAI: Add your OpenAI API key
   - For Anthropic: Uncomment the Anthropic section and add your API key

3. Run the analyzer:
```bash
python analyze_trending.py
```

## Features

- **Topic Identification**: Analyzes article titles and snippets to identify main topics
- **Tag Generation**: Creates 3-5 relevant tags for each article
- **Community Classification**: Categorizes content as B2B, B2C, or Hybrid
- **LangGraph Workflow**: Uses a structured workflow for consistent analysis
- **CSV Processing**: Reads from trending.csv and adds new columns

## Output

The script adds two new columns to trending.csv:
- `community`: B2B, B2C, or Hybrid classification
- `tags`: Comma-separated list of relevant tags

## Configuration

Edit `config.yaml` to:
- Change the model provider (OpenAI or Anthropic)
- Adjust model parameters (temperature, max_tokens)
- Set your API key