# Before running, you need to install the library:
# ================ $ pip install paho-mqtt =================
import paho.mqtt.client as mqtt # Paho MQTT library
import ssl # SSL module for secure connections and loading certificates
import time # Time module for sleep functionality
import random # For generating random telemetry data
import json # For JSON formatting

# --- AWS IoT Core Connection Details ---
# To get your AWS MQTT broker endpoint:
# ======== $ aws iot describe-endpoint --endpoint-type iot:Data-ATS ===========
AWS_ENDPOINT = "XXXXXXXXXXXXX-ats.iot.eu-west-1.amazonaws.com"
AWS_PORT = 8883
CLIENT_ID = "device-fleet_provisioning-001"
# --- Certificate File Paths ---
# Paths to your root CA, device certificate, and private key files
INITIAL_CA_PATH = "certs/AmazonRootCA1.pem"
# For the initial connection, we use a temporary certificate that has permissions to perform fleet provisioning. This certificate is typically created in AWS IoT Core and downloaded to your local machine for testing purposes. In a production environment, this would be securely injected into the device during manufacturing or via a secure provisioning process.
INITIAL_CERT_PATH = "certs/AZZZZZZZZZYYYYYYYY-certificate.pem.crt"
INITIAL_KEY_PATH = "certs/AZZZZZZZZZYYYYYYYY-private.pem.key"

# --- MQTT Topics for Fleet Provisioning ---
# These topics are defined by AWS IoT Core for the fleet provisioning workflow.
CREATE_KEYS_AND_CERTIFICATE_REQUEST_TOPIC = f"$aws/certificates/create/json"
CREATE_KEYS_AND_CERTIFICATE_RESPONSE_ACCEPTED_TOPIC = f"{CREATE_KEYS_AND_CERTIFICATE_REQUEST_TOPIC}/accepted"
CREATE_KEYS_AND_CERTIFICATE_RESPONSE_REJECTED_TOPIC = f"{CREATE_KEYS_AND_CERTIFICATE_REQUEST_TOPIC}/rejected"
# The topic for registering the thing with the provisioning template. The template name must match the one defined in AWS IoT Core.
PROVISIONING_TEMPLATE_NAME = "fleet_provisioning"
REGISTER_THING_REQUEST_TOPIC = f"$aws/provisioning-templates/{PROVISIONING_TEMPLATE_NAME}/provision/json"
REGISTER_THING_RESPONSE_ACCEPTED_TOPIC = f"{REGISTER_THING_REQUEST_TOPIC}/accepted"
REGISTER_THING_RESPONSE_REJECTED_TOPIC = f"{REGISTER_THING_REQUEST_TOPIC}/rejected"

FLEET_PROVISIONING_CERT = None
FLEET_PROVISIONING_KEY = None
FLEET_PROVISIONING_OWNERSHIP_TOKEN = None
FLEET_PROVISIONING_CERT_LOCAL_PATH = "./certs/device-certificate.pem.crt"
FLEET_PROVISIONING_KEY_LOCAL_PATH = "./certs/device-private.pem.key"
FLEET_PROVISIONING_DEVICE_ID = f"SN-Fleet-Provisi{random.randint(100000, 999999)}"

mqtt_client = None

# --- Callback function for when the client connects to the broker ---
def on_connect(client, userdata, flags, reason_code, properties):
    """
    This callback is triggered when the client connects to the broker.
    """
    if reason_code == 0:
        print(f"Successfully connected to AWS IoT Core with client ID: {CLIENT_ID}")
    else:
        # *** FIX WAS HERE ***
        # The v2 API uses 'reason_code', not 'rc', to report the status.
        print(f"Connection failed with result code: {reason_code}")

def on_message(client, userdata, msg):
    """
    This function is called every time a message is received on a subscribed topic.
    """
    global FLEET_PROVISIONING_KEY, FLEET_PROVISIONING_CERT, FLEET_PROVISIONING_OWNERSHIP_TOKEN
    print(f"Intercepted payload on topic '{msg.topic}'")

    try:
        payload_json = json.loads(msg.payload.decode('utf-8'))
        print(json.dumps(payload_json, indent=2))
        # Final and permanent certificate and key handling for fleet provisioning response
        if msg.topic == CREATE_KEYS_AND_CERTIFICATE_RESPONSE_ACCEPTED_TOPIC:
            FLEET_PROVISIONING_CERT = payload_json.get("certificatePem")
            FLEET_PROVISIONING_KEY = payload_json.get("privateKey")
            FLEET_PROVISIONING_OWNERSHIP_TOKEN = payload_json.get("certificateOwnershipToken")
            print("Certificate and key received for fleet provisioning.")
            if FLEET_PROVISIONING_CERT and FLEET_PROVISIONING_KEY:
                save_file(FLEET_PROVISIONING_CERT_LOCAL_PATH, FLEET_PROVISIONING_CERT)
                save_file(FLEET_PROVISIONING_KEY_LOCAL_PATH, FLEET_PROVISIONING_KEY)
                print("Permanent cryptographic credentials securely persisted to local filesystem.")
        elif msg.topic == CREATE_KEYS_AND_CERTIFICATE_RESPONSE_REJECTED_TOPIC:
            error_message = payload_json.get("message", "No error message provided.")
            print(f"Error message: {error_message}")
        
        # Thing Registration response handling
        elif msg.topic == REGISTER_THING_RESPONSE_ACCEPTED_TOPIC:
            print("Thing registration successful.")
            thing_arn = payload_json.get("thingArn")
            if thing_arn:
                print(f"Thing ARN: {thing_arn}")
        elif msg.topic == REGISTER_THING_RESPONSE_REJECTED_TOPIC:
            error_message = payload_json.get("message", "No error message provided.")
            print(f"Error message: {error_message}")
        else:
            print("Unknown response topic.")

    except Exception as e:
        print(f"Error processing message: {e}")

def save_file(filename, content):
    """
    Saves content to a file.
    """
    with open(filename, 'w') as file:
        file.write(content)
    print(f"Saved file: {filename}")

def generate_certificate_request():
    """
    Synthesizes a strictly empty JSON payload to
    initiate the cryptographic request.
    """
    payload = {}
    return json.dumps(payload)

def generate_thing_registration_request(certificate_ownership_token):
    """
    Generates a thing registration request in JSON format.
    """
    payload = {
        "certificateOwnershipToken": certificate_ownership_token,
        "parameters": {
            "SerialNumber": FLEET_PROVISIONING_DEVICE_ID
        }
    }
    return json.dumps(payload)

def init_mqtt_client(cert_path, key_path, ca_path, client_id):
    global mqtt_client
    if mqtt_client != None:
        print("Disconnecting to swap certificates...")
        # Wait for the disconnect to complete nicely
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        del mqtt_client
    # 1. Create an MQTT client instance
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
    # 2. Assign the on_connect callback function
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    # === Configure TLS ===
    mqtt_client.tls_set(
        ca_certs=ca_path,
        certfile=cert_path,
        keyfile=key_path,
        cert_reqs=ssl.CERT_REQUIRED,
        tls_version=ssl.PROTOCOL_TLSv1_2,
        ciphers=None
    )
    try:
        print(f"Attempting to connect to AWS IoT Core at {AWS_ENDPOINT}...")
        mqtt_client.connect(AWS_ENDPOINT, AWS_PORT, 60)
    except Exception as e:
        print(f"An error occurred while trying to connect: {e}")
        exit()
    mqtt_client.loop_start()

init_mqtt_client(INITIAL_CERT_PATH, INITIAL_KEY_PATH, INITIAL_CA_PATH, CLIENT_ID)

time.sleep(2) # Wait for connection to establish

certificate_request_json = generate_certificate_request()

# Certificate Creation Request
mqtt_client.publish(
    topic=CREATE_KEYS_AND_CERTIFICATE_REQUEST_TOPIC,
    payload=certificate_request_json,
    qos=1 # Quality of Service 1: At least once delivery
)

print(f"Published message to topic '{CREATE_KEYS_AND_CERTIFICATE_REQUEST_TOPIC}': {certificate_request_json}")
# Wait for 5 seconds before sending the next message
time.sleep(5)

thing_registration_request_json = generate_thing_registration_request(FLEET_PROVISIONING_OWNERSHIP_TOKEN)
# Thing Registration Request
mqtt_client.publish(
    topic=REGISTER_THING_REQUEST_TOPIC,
    payload=thing_registration_request_json,
    qos=1 # Quality of Service 1: At least once delivery
)

print(f"Published message to topic '{REGISTER_THING_REQUEST_TOPIC}': {thing_registration_request_json}")

time.sleep(3) # Wait for connection to establish


# Keep the main thread alive to maintain the connection.
try:
    init_mqtt_client(FLEET_PROVISIONING_CERT_LOCAL_PATH, FLEET_PROVISIONING_KEY_LOCAL_PATH, INITIAL_CA_PATH, FLEET_PROVISIONING_DEVICE_ID)
    while True:
        # Generate telemetry message
        print("Publishing telemetry message...")
        mqtt_client.publish(
            topic=f"farm/{FLEET_PROVISIONING_DEVICE_ID}/telemetry",
            payload=json.dumps({"message": "Device successfully provisioned!"}),
            qos=1 # Quality of Service 1: At least once delivery
        )
        print(f"Published telemetry message for device ID '{FLEET_PROVISIONING_DEVICE_ID}'")
        time.sleep(5)
except KeyboardInterrupt:
    print("Disconnecting from AWS IoT broker...")
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
    print("Disconnected from AWS IoT broker.")


