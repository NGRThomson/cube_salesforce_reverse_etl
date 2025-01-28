import os
import modal
import random
import requests
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from simple_salesforce import Salesforce
from tabulate import tabulate

# Load environment variables
load_dotenv()

# Create a Modal app
app = modal.App("salesforce-account-updater")

# Create an image with our dependencies
image = modal.Image.debian_slim().pip_install(
    "simple-salesforce",
    "python-dotenv",
    "requests",
    "tabulate"
)

# Create secrets from environment variables
salesforce_secret = modal.Secret.from_dict({
    "SF_USERNAME": os.getenv("SF_USERNAME"),
    "SF_PASSWORD": os.getenv("SF_PASSWORD"),
    "SF_SECURITY_TOKEN": os.getenv("SF_SECURITY_TOKEN")
})

cube_secret = modal.Secret.from_dict({
    "CUBE_API_URL": os.getenv("CUBE_API_URL"),
    "CUBE_API_TOKEN": os.getenv("CUBE_API_TOKEN")
})

def get_top_companies():
    """Query top companies by sessions from Cube"""
    try:
        current_time = datetime.now(timezone.utc)
        yesterday = (current_time - timedelta(days=1)).date().isoformat()
        
        print(f"\n📊 Querying top companies for date: {yesterday}")
        print("=" * 50)
        cube_api_token = os.getenv("CUBE_API_TOKEN")
        cube_api_url = os.getenv("CUBE_API_URL")

        headers = {
            "Authorization": cube_api_token.replace("Authorization: ", ""),
            "Content-Type": "application/json"
        }

        query = {
            "query": {
                "dimensions": [
                    "product_tour_company_metrics.company_name",
                    "product_tour_company_metrics.total_visitors",
                    "product_tour_company_metrics.first_product_tour_date",
                    "product_tour_company_metrics.last_product_tour_date",
                    "product_tour_company_metrics.total_session_time_minutes"
                ],
                "filters": [
                    {
                        "member": "product_tour_company_metrics.last_product_tour_date",
                        "operator": "afterOrOnDate",
                        "values": [yesterday]
                    },
                    {
                        "member": "product_tour_company_metrics.has_engaged_users",
                        "operator": "equals",
                        "values": [True]
                    }
                ],
                "order": {
                    "product_tour_company_metrics.total_sessions": "desc"
                }
            }
        }

        response = requests.post(
            cube_api_url,
            headers=headers,
            json=query
        )

        if response.status_code == 200:
            data = response.json()
            companies = []
            for row in data.get("data", []):
                company_data = {
                    'name': row.get('product_tour_company_metrics.company_name'),
                    'sessions': row.get('product_tour_company_metrics.total_sessions'),
                    'visitors': row.get('product_tour_company_metrics.total_visitors'),
                    'first_tour_date': row.get('product_tour_company_metrics.first_product_tour_date'),
                    'last_tour_date': row.get('product_tour_company_metrics.last_product_tour_date'),
                    'total_minutes': row.get('product_tour_company_metrics.total_session_time_minutes')
                }
                if company_data['name']:  # Only include companies with names
                    companies.append(company_data)
            
            if companies:
                # Prepare table data
                table_data = [[
                    company['name'],
                    company['visitors'],
                    company['first_tour_date'],
                    company['last_tour_date'],
                    f"{company['total_minutes']:.1f}"
                ] for company in companies]
                
                # Print table
                print("\n📈 Company Activity Report:")
                print(tabulate(
                    table_data,
                    headers=['Company', 'Visitors', 'First Tour', 'Last Tour', 'Total Minutes'],
                    tablefmt='grid'
                ))
                print(f"\nTotal companies found: {len(companies)}")
                print("=" * 50)
            else:
                print("\n⚠️  No companies found for yesterday")
                print("=" * 50)
            return companies
        else:
            print(f"Error querying Cube Cloud: {response.status_code}")
            print(response.text)
            return []

    except Exception as e:
        print(f"Error getting top companies: {str(e)}")
        return []

@app.function(
    image=image,
    secrets=[salesforce_secret, cube_secret]
)
def update_account_employees():
    """Update Test account's employee field with a random company's session count"""
    try:
        print(f"\n🔄 Starting update at: {datetime.now(timezone.utc).isoformat()}")
        print("=" * 60)

        # Get Salesforce credentials
        sf_username = os.getenv("SF_USERNAME")
        sf_password = os.getenv("SF_PASSWORD")
        sf_security_token = os.getenv("SF_SECURITY_TOKEN")

        if not all([sf_username, sf_password, sf_security_token]):
            print("❌ Error: Missing Salesforce credentials in environment variables")
            return

        # Initialize Salesforce connection
        sf = Salesforce(
            username=sf_username,
            password=sf_password,
            security_token=sf_security_token,
            domain='test'  # This specifies that we're connecting to a sandbox
        )

        # Get top companies from Cube
        top_companies = get_top_companies()
        if not top_companies:
            print("❌ No companies found in Cube data")
            return

        # Select a random company from the top companies
        selected_company = random.choice(top_companies)
        print("📊 Source Data:")
        print("-" * 60)
        print(f"Company:              {selected_company['name']}")
        print(f"Total Visitors:       {selected_company['visitors']}")
        print(f"First Product Tour:   {selected_company['first_tour_date']}")
        print(f"Last Product Tour:    {selected_company['last_tour_date']}")
        print(f"Total Minutes Spent:  {selected_company['total_minutes']}")
        print("-" * 60)

        # Query Salesforce for the Test account
        accounts = sf.query("""
            SELECT Id, Name, NumberOfEmployees
            FROM Account
            WHERE Name = 'Test'
        """)

        if accounts['records']:
            account = accounts['records'][0]
            current_employees = account.get('NumberOfEmployees', 0) or 0
            new_employees = selected_company['sessions']

            print("\n📝 Update Details:")
            print("-" * 60)
            print(f"Target Account:     Test")
            print(f"Current Employees:  {current_employees}")
            print(f"New Employees:      {new_employees}")
            print(f"Change:            {'⬆️ +' if new_employees > current_employees else '⬇️ '}{abs(new_employees - current_employees)}")
            print("-" * 60)
            
            # Update the account
            sf.Account.update(account['Id'], {
                'NumberOfEmployees': new_employees
            })
            
            print("\n✅ Update Summary:")
            print("-" * 60)
            print(f"Status:     Success")
            print(f"Timestamp:  {datetime.now(timezone.utc).isoformat()}")
            print("=" * 60)
        else:
            print("\n❌ Error: Test account not found in Salesforce")
            print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error updating account employees: {str(e)}")
        print("=" * 60)

@app.function(
    image=image,
    secrets=[salesforce_secret],
    schedule=modal.Period(hours=1)
)
def scheduled_update():
    """Scheduled function to perform hourly account updates"""
    try:
        update_account_employees.remote()
    except Exception as e:
        print(f"Error in scheduled update: {str(e)}")

if __name__ == "__main__":
    scheduled_update.remote()
