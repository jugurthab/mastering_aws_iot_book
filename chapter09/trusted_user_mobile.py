import boto3
from botocore import UNSIGNED
from botocore.config import Config

# --- CONFIGURATION ---
# Target Deployment Region for the AWS control plane
REGION = 'eu-west-1'
# Authoritative Cognito User Pool Identifier (extracted from the User Pool operational dashboard)
USER_POOL_ID = 'eu-west-1_xxxxxxxxx'
# Dedicated App Client Identifier orchestrating the authentication lifecycle
APP_CLIENT_ID = 'xxxxxxxxxxxxxxxxxxxxxxxxxx'
# Federated Identity Pool Identifier explicitly mapped to the execution IAM roles
IDENTITY_POOL_ID = 'eu-west-1:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
# Ephemeral test credentials provisioned during the initialization phase.
# Architectural Constraint: In a strict production environment, the companion mobile 
# application dynamically resolves and securely injects these attributes via native SDKs.
USERNAME = 'username'
PASSWORD = 'YourSecurePassword123!' 

# Authoritative Provisioning Template orchestrating the zero-touch enrollment lifecycle
PROVISIONING_TEMPLATE_NAME = 'fleet_provisioning'

def main():
    print(f"--- Mobile App Simulator ---")
    
    try:
        # Authenticate with User Pool (Simulating App Login)
        # We use UNSIGNED to prove we don't need AWS Admin keys/credentials locally
        print(f"Logging in as {USERNAME}...")
        idp_client = boto3.client('cognito-idp', region_name=REGION, config=Config(signature_version=UNSIGNED))
        
        try:
            auth_resp = idp_client.initiate_auth(
                ClientId=APP_CLIENT_ID,
                AuthFlow='USER_PASSWORD_AUTH',
                AuthParameters={'USERNAME': USERNAME, 'PASSWORD': PASSWORD}
            )
        except idp_client.exceptions.NotAuthorizedException:
            print("[!] Login Failed: Incorrect username or password.")
            return
        except idp_client.exceptions.UserNotConfirmedException:
            print("[!] Login Failed: User is not confirmed.")
            return

        id_token = auth_resp['AuthenticationResult']['IdToken']
        print("Login successful! JWT ID Token acquired.")

        # Exchange Token for AWS Credentials
        print("Exchanging JWT for AWS Temporary Credentials...")
        ci_client = boto3.client('cognito-identity', region_name=REGION, config=Config(signature_version=UNSIGNED))
        
        id_resp = ci_client.get_id(
            IdentityPoolId=IDENTITY_POOL_ID,
            Logins={f'cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}': id_token}
        )
        creds = ci_client.get_credentials_for_identity(
            IdentityId=id_resp['IdentityId'],
            Logins={f'cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}': id_token}
        )['Credentials']
        
        print("AWS Identity acquired.")

        # Call CreateProvisioningClaim
        print("Requesting Provisioning Claim (Bootstrap Certificate)...")
        iot_client = boto3.client(
            'iot', region_name=REGION,
            aws_access_key_id=creds['AccessKeyId'],
            aws_secret_access_key=creds['SecretKey'],
            aws_session_token=creds['SessionToken']
        )
        
        claim = iot_client.create_provisioning_claim(templateName=PROVISIONING_TEMPLATE_NAME)
        
        print(f"\n--- CLAIM SUCCESSFUL ---")
        print(f"Cert ID: {claim['certificateId']}")
        
        # Save files
        with open("claim-cert.pem", "w") as f: f.write(claim['certificatePem'])
        with open("claim-private.key", "w") as f: f.write(claim['keyPair']['PrivateKey'])

    except Exception as e:
        print(f"\n[ERROR] Simulation Failed: {e}")

if __name__ == '__main__':
    main()