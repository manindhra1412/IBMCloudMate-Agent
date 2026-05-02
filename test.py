from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_scc.security_and_compliance_center_api_v3 import SecurityAndComplianceCenterApiV3
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_scc_sdk():
    print("\n🔍 Testing IBM Security and Compliance Center SDK...")
    print("=" * 50)
    
    # Initialize the SDK
    api_key = os.getenv('IAM_API_KEY')
    instance_id = os.getenv('SCC_INSTANCE_ID')
    region = os.getenv('SCC_REGION', 'us-south')
    
    print(f"\n📌 Configuration:")
    print(f"- Region: {region}")
    print(f"- Instance ID: {instance_id}")
    print(f"- API Key: {'*' * len(api_key) if api_key else 'Not set'}")
    
    if not all([api_key, instance_id]):
        print("\n❌ Missing required environment variables")
        return
    
    # Create authenticator and service instance
    authenticator = IAMAuthenticator(apikey=api_key, url="https://iam.test.cloud.ibm.com")
    scc = SecurityAndComplianceCenterApiV3(
        authenticator=authenticator
    )
    scc.set_service_url(f'https://{region}.compliance.test.cloud.ibm.com/instances/{instance_id}/api/v3')
    
    print("\n1. Testing get_scan_summaries:")
    print("-" * 30)
    try:
        response = scc.get_scan_summaries()
        result = response.get_result()
        print(f"Response Status: {response.get_status_code()}")
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {str(e)}")
    
    print("\n2. Testing get_profiles:")
    print("-" * 30)
    try:
        response = scc.get_profiles()
        result = response.get_result()
        print(f"Response Status: {response.get_status_code()}")
        print(f"Result: {result}")
        
        # If we have profiles, test get_attachments with the first profile
        if result and 'profiles' in result and len(result['profiles']) > 0:
            profile_id = result['profiles'][0]['id']
            print(f"\n3. Testing get_attachments for profile {profile_id}:")
            print("-" * 30)
            try:
                response = scc.get_attachments(profile_id=profile_id)
                result = response.get_result()
                print(f"Response Status: {response.get_status_code()}")
                print(f"Result: {result}")
            except Exception as e:
                print(f"Error: {str(e)}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_scc_sdk() 