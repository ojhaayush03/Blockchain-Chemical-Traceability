from app import create_app
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

app = create_app()

if __name__ == "__main__":
    # Print blockchain configuration status
    if os.environ.get('ETH_CONTRACT_ADDRESS') and os.environ.get('ETH_ACCOUNT_ADDRESS'):
        print(f"Blockchain configuration detected:")
        print(f"  - Contract Address: {os.environ.get('ETH_CONTRACT_ADDRESS')}")
        print(f"  - Account Address: {os.environ.get('ETH_ACCOUNT_ADDRESS')}")
        print(f"  - Infura URL: {os.environ.get('INFURA_URL', 'Not set')}")
    else:
        print("Blockchain configuration not detected. Check your .env file.")
    
    app.run(debug=True)
