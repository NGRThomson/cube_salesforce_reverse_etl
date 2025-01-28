import os
import modal
from dotenv import load_dotenv
from simple_salesforce import Salesforce

# Create a Modal app
app = modal.App("salesforce-test")

# Create an image with our dependencies
image = modal.Image.debian_slim().pip_install(
    "simple-salesforce",
    "python-dotenv"
)

# Create secrets from environment variables
load_dotenv()
salesforce_secret = modal.Secret.from_dict({
    "SF_USERNAME": os.getenv("SF_USERNAME"),
    "SF_PASSWORD": os.getenv("SF_PASSWORD"),
    "SF_SECURITY_TOKEN": os.getenv("SF_SECURITY_TOKEN")
})

@app.function(
    image=image,
    secrets=[salesforce_secret]
)
def test_salesforce_connection():
    """Test Salesforce connection and basic query"""
    print("\n🔑 Testing Salesforce Connection")
    print("=" * 50)
    
    try:
        # Get credentials from environment
        username = os.getenv("SF_USERNAME")
        password = os.getenv("SF_PASSWORD")
        security_token = os.getenv("SF_SECURITY_TOKEN")
        
        print(f"Username: {username}")
        print(f"Security Token Length: {len(security_token) if security_token else 0}")
        
        # Initialize Salesforce connection
        sf = Salesforce(
            username=username,
            password=password,
            security_token=security_token,
            domain='test'  # This specifies that we're connecting to a sandbox
        )
        
        print("\n✅ Successfully connected to Salesforce!")
        
        # Try to query an account
        print("\n🔍 Attempting to query accounts...")
        result = sf.query("SELECT Id, Name FROM Account LIMIT 1")
        
        if result['records']:
            account = result['records'][0]
            print(f"\nFound account:")
            print(f"ID: {account['Id']}")
            print(f"Name: {account['Name']}")
        else:
            print("\nNo accounts found")
            
        print("\n✅ Query successful!")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
    
    print("=" * 50)

if __name__ == "__main__":
    test_salesforce_connection.remote()
