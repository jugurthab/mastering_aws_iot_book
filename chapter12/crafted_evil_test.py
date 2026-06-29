# Mqtt publisher libraries and dependencies
import random
import paho.mqtt.client as mqtt  # Eclipse Paho MQTT client library
import ssl                       # SSL/TLS module for loading cryptographic certificates
import time                      # Time module for managing execution delays
import json                      # JSON formatting
import sys

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
        print(f"Connection failed with result code: {reason_code}")

def generate_telemetry_msg():
    """
    Generates a telemetry message in JSON format, deliberately inflated 
    to trigger Device Defender alerts (> 150 bytes).
    """
    try:
        temperature = random.uniform(20.0, 30.0)
        humidity = random.uniform(30.0, 70.0)
    except Exception as e:
        print(f"Error generating mock telemetry: {e}")
        return None

    # Create telemetry data with artificial padding to force payload > 150 bytes
    telemetry_data = {
        "temperature": temperature,
        "humidity": humidity,
        "malicious_padding": "X" * 150 
    }
    
    payload = json.dumps(telemetry_data)
    return payload

# --- Main script logic ---

# 1. Create an MQTT client instance
mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                    client_id=client_id)

# 2. Assign the on_connect callback function
mqttc.on_connect = on_connect

# 3. Configure TLS/SSL for a secure connection
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
    sys.exit(1)

# 5. Start the asynchronous network loop.
mqttc.loop_start()

# Topic to publish telemetry data
telemetry_topic = f"farm/{client_id}/telemetry"

time.sleep(2) # Allow connection to establish

# 6. Keep the primary execution thread alive to maintain the active session.
try:
    print("Initiating aggressive publishing loop to validate Device Defender posture...")
    while True:
        # Generate the inflated telemetry payload
        payload_json = generate_telemetry_msg()

        # Publish the message to the cloud broker
        mqttc.publish(
            topic=telemetry_topic,
            payload=payload_json,
            qos=1 
        )

        # Output the exact byte size to the console for local validation
        payload_size = len(payload_json.encode('utf-8'))
        print(f"[Payload Size: {payload_size} bytes] Published to '{telemetry_topic}'")

        # Suspend execution for 1 second to aggressively violate the >10 msgs/5min threshold
        time.sleep(1)
        
except KeyboardInterrupt:
    print("\nGracefully disconnecting from the AWS IoT broker...")
    mqttc.loop_stop()
    mqttc.disconnect()
    print("Successfully disconnected from AWS IoT Core.")
