# Mqtt publisher libraries and dependencies
import paho.mqtt.client as mqtt  # Eclipse Paho MQTT client library
import ssl                       # SSL/TLS module for loading cryptographic certificates
import time                      # Time module for managing execution delays
import json                      # JSON formatting
from gpiozero import Servo, LED  # GPIO control for Raspberry Pi (servomotor and LED)

# --- AWS IoT Core Connection Details ---
# Reminder: To retrieve your specific AWS MQTT broker endpoint, use the CLI:
# aws iot describe-endpoint --endpoint-type iot:Data-ATS
aws_endpoint = "XXXXXXXXXXXXX-ats.iot.eu-west-1.amazonaws.com"
aws_port = 8883
CLIENT_ID = "gate_keeper_002" # Thing name as defined in AWS IoT

# --- Certificate File Paths ---
# Paths to your root CA, device certificate, and private key files
ca_path = "certs/AmazonRootCA1.pem"
cert_path = "certs/AZZZZZZZZZYYYYYYYY-certificate.pem.crt"
key_path = "certs/AZZZZZZZZZYYYYYYYY-private.pem.key"

# --- Shadow Reserved Topics ---
# The topic where the device publishes its reported state
SHADOW_UPDATE_TOPIC = f"$aws/things/{CLIENT_ID}/shadow/update"
# The topic where the device receives state mismatches (commands)
SHADOW_DELTA_TOPIC = f"$aws/things/{CLIENT_ID}/shadow/update/delta"

# --- Hardware Setup ---
# GPIO pin for the servo and status LED
SERVO_PIN = 4 # GPIO pin connected to the servo's signal wire
PWM_FREQUENCY = 50 # Standard servo frequency is 50Hz (20ms period)
status_led = LED(27)
# Define the GPIO pin connected to the servo's signal wire (GPIO 04)
# We use a custom min_pulse_width and max_pulse_width
# to prevent the servo from jittering Standard SG90 servos
# usually operate well between 1ms (1.0/1000) and 2ms (2.0/1000)
servo_pwm = Servo(SERVO_PIN, min_pulse_width=1.0/1000, max_pulse_width=2.0/1000)

# --- Connection Callback Function ---
def on_connect(client, userdata, flags, reason_code, properties):
    """
    Triggered when the client connects to the broker.
    We exclusively subscribe to the Delta topic to listen for state mismatches.
    """
    if reason_code == 0:
        print(f"Successfully connected to AWS IoT Core with client ID: {CLIENT_ID}")
        
        # Automatically establish the subscription upon a successful connection
        print(f"Subscribing to topic: '{SHADOW_DELTA_TOPIC}'")
        client.subscribe(SHADOW_DELTA_TOPIC, qos=1)
    else:
        # The v2 API uses 'reason_code', not 'rc', to report the status.
        print(f"[ERROR] Connection failed with result code: {reason_code}")

def on_message(client, userdata, msg):
    """
    Triggered when a message arrives from the cloud. Handles JSON parsing 
    and delegates the business logic to the process_shadow_delta actuator function.
    """
    print(f"\n[NETWORK] Received message on '{msg.topic}'")
    
    try:
        incoming_payload = json.loads(msg.payload.decode('utf-8'))
        # Delegate the payload extraction and actuation logic
        process_shadow_delta(incoming_payload)
            
    except json.JSONDecodeError:
        print("[ERROR] Failed to parse incoming Shadow JSON payload.")

def update_gate_state(is_open):
    """
    Helper function to update the physical state
    of the gate based on the desired state.
    """
    if is_open:
        servo_pwm.min()  # Open position
        applied_state = True
        status_led.on()
    else:
        servo_pwm.max()  # Closed position
        applied_state = False
        status_led.off()
    # Allow time for the servo to reach the desired position
    time.sleep(2)
    return applied_state

def process_shadow_delta(incoming_payload):
    """
    Extracts the changed state from the Delta payload, actuates the hardware, 
    and publishes the newly reported state back to the Update topic.
    """
    # Shadow Deltas wrap changes in a "state" object
    if "state" in incoming_payload and "gate_is_open" in incoming_payload["state"]:
        desired_gate_state = incoming_payload["state"]["gate_is_open"]
        
        print(f"[SYNC] Cloud requests gate to be: {'OPEN' if desired_gate_state else 'CLOSED'}")

        # Actuate the hardware to match the desired state
        applied_state = update_gate_state(desired_gate_state)
        
        # Construct the Shadow Update payload
        # Notice we only send the 'reported' state to clear the delta
        update_payload = {
            "state": {
                "reported": {
                    "gate_is_open": applied_state
                }
            }
        }

        # Publish the updated state back to the cloud
        # Shadows do not use the retain flag (persistence is managed by the service)
        mqttc.publish(
            topic=SHADOW_UPDATE_TOPIC,
            payload=json.dumps(update_payload),
            qos=1
        )
        print("[SYNC] Successfully reported synchronized state back to Shadow. Delta cleared.")
        
    else:
        print("[WARNING] Incoming Delta does not contain a valid 'state.gate_is_open' key.")

# --- Main script logic ---

# 1. Create an MQTT client instance
mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                    client_id=CLIENT_ID)


# 2. Assign the on_connect callback function
mqttc.on_connect = on_connect
# Register the message callback to handle incoming
# messages on subscribed topics
mqttc.on_message = on_message
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
# This non-blocking call runs on a background thread
# # to manage network traffic.
mqttc.loop_start()

time.sleep(2) # Wait for connection to establish

# 6. Keep the primary execution thread alive to maintain
# the active session.
try:
    # Keep the script alive.
    while True:
        time.sleep(2)
        
except KeyboardInterrupt:
    print("\nGracefully disconnecting...")
    status_led.off()
    status_led.close()
    servo_pwm.stop()
    mqttc.loop_stop()
    mqttc.disconnect()
    print("Disconnected.")