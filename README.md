# Cube to Salesforce Integration

This project integrates Cube analytics data with Salesforce, automatically updating Salesforce accounts with engagement metrics from Cube. It runs as a scheduled job using Modal.

## Features

- Queries Cube for company engagement metrics
- Updates Salesforce account records with engagement data
- Runs on Modal with hourly scheduling
- Supports sandbox and production Salesforce environments

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
Copy `.env.example` to `.env` and fill in your credentials:
```bash
cp .env.example .env
```

Required environment variables:
- `SF_USERNAME`: Salesforce username
- `SF_PASSWORD`: Salesforce password
- `SF_SECURITY_TOKEN`: Salesforce security token
- `CUBE_API_URL`: Cube API URL
- `CUBE_API_TOKEN`: Cube API token

## Usage

### Testing Salesforce Connection

Run the test script to verify Salesforce connectivity:
```bash
modal run test_salesforce.py
```

### Running the Integration

Run the main script:
```bash
modal run modal_cube_salesforce.py
```

Deploy to Modal for scheduled execution:
```bash
modal deploy modal_cube_salesforce.py
```

## Project Structure

- `modal_cube_salesforce.py`: Main integration script
- `test_salesforce.py`: Salesforce connection test script
- `requirements.txt`: Python dependencies
- `.env.example`: Example environment variables file
