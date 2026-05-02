
# Before running, you need to install the library:
# ================ $ pip install paho-mqtt =================
import paho.mqtt.client as mqtt  # Eclipse Paho MQTT client library
import ssl                       # SSL/TLS module for loading cryptographic certificates
import time                      # Time module for managing execution delays

# --- AWS IoT Core Connection Details ---
# Reminder: To retrieve your specific AWS MQTT broker endpoint, use the CLI:
# aws iot describe-endpoint --endpoint-type iot:Data-ATS
aws_endpoint = "XXXXXXXXXXXXX-ats.iot.eu-west-1.amazonaws.com"
aws_port = 8883
client_id = "sensorTelemetry001" # Thing name as defined in AWS IoT

# --- Certificate File Paths ---
# Paths to your root CA, device certificate, and private key files
ca_path = "certs/AmazonRootCA1.pem"
cert_path = "certs/AZZZZZZZZZYYYYYYYY-certificate.pem.crt"
key_path = "certs/AZZZZZZZZZYYYYYYYY-private.pem.key"

# --- Connection Callback Function ---
def on_connect(client, userdata, flags, reason_code, properties):
    """
    This callback is triggered when the client connects to the broker.
    """
    if reason_code == 0:
        print(f"Successfully connected to AWS IoT Core with client ID: {client_id}")
    else:
        # The v2 API uses 'reason_code', not 'rc', to report the status.
        print(f"Connection failed with result code: {reason_code}")

# --- Main script logic ---

# 1. Create an MQTT client instance
mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
# 2. Assign the on_connect callback function
mqttc.on_connect = on_connect

# 3. Configure TLS/SSL for a secure connection
# This is mandatory for connecting to AWS IoT Core.
mqttc.tls_set(
    ca_certs=ca_path,
    certfile=cert_path,
    keyfile=key_path,
    cert_reqs=ssl.CERT_REQUIRED,
    tls_version=ssl.PROTOCOL_TLSv1_2,
    ciphers=None
)

# 4. Initiate the connection to the AWS IoT broker
try:
    print(f"Attempting to connect to AWS IoT Core at {aws_endpoint}...")
    mqttc.connect(aws_endpoint, aws_port, 60)
except Exception as e:
    print(f"An error occurred while trying to connect: {e}")
    exit()

# 5. Start the asynchronous network loop.
# This non-blocking call runs on a background thread to manage network traffic.
mqttc.loop_start()

# 6. Keep the primary execution thread alive to maintain the active session.
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nDisconnecting from AWS IoT broker...")
    mqttc.loop_stop()
    mqttc.disconnect()
    print("Disconnected from AWS IoT broker.")