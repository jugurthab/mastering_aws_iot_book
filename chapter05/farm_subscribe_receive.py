

# Mqtt publisher libraries and dependencies
import paho.mqtt.client as mqtt  # Eclipse Paho MQTT client library
import ssl                       # SSL/TLS module for loading cryptographic certificates
import time                      # Time module for managing execution delays
import json                      # JSON formatting
# Adafruit DHT library for reading from DHT sensors
import board
import adafruit_dht
import RPi.GPIO as GPIO

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

subscription_topic = "config/security" # Topic to subscribe to for configuration messages

# Define the physical data pin interfaced with the buzzer
BUZZER_PIN = 17

# --- Connection Callback Function ---
def on_connect(client, userdata, flags, reason_code, properties):
    """
    This callback is triggered when the client connects to the broker.
    """
    if reason_code == 0:
        print(f"Successfully connected to AWS IoT Core with client ID: {client_id}")
        
        # Automatically establish the subscription upon a successful connection
        print(f"Subscribing to topic: '{subscription_topic}'")
        client.subscribe(subscription_topic, qos=1)  # Subscribe requesting Quality of Service 1
    else:
        # The v2 API uses 'reason_code', not 'rc', to report the status.
        print(f"Connection failed with result code: {reason_code}")

def trigger_buzzer():
    """
    Activates the buzzer for a specified duration in seconds.
    """
    try:
        # Initialize the Pulse Width Modulation (PWM) signal.
        # The second argument (3000) establishes a constant
        # frequency of 3000 Hz.
        pwm_buzzer = GPIO.PWM(BUZZER_PIN, 3000)

        print("Activating the passive buzzer at a constant 3000 Hz pitch...")
        # Engage the PWM output with a 50% duty cycle
        # to generate a clear, sustained tone
        pwm_buzzer.start(50) 
        # Sustain the constant pitch for exactly 3 seconds
        time.sleep(3)  

    except KeyboardInterrupt:
        # Handle manual terminal interruptions gracefully
        print("\nExecution manually interrupted by the operator.")

    finally:
        print("Silencing the buzzer and releasing GPIO resources...")
        # Terminate the PWM oscillation to stop the audio output
        pwm_buzzer.stop()
        # Deallocate the hardware pins to prevent background droning
        GPIO.cleanup()
        
def on_message(client, userdata, msg):
    """
    This function is called every time a message is received
    on a subscribed topic.
    """
    print(f"Received message on topic '{msg.topic}':")
    try:
        # Attempt to pretty-print if the payload is JSON
        payload_json = json.loads(msg.payload.decode('utf-8'))
        print(json.dumps(payload_json, indent=2))
        # Check for a specific alert in the payload
        # and trigger the buzzer if found
        if "alert" in payload_json and \
            payload_json["alert"] == "security_breach":
            trigger_buzzer()
        
    except json.JSONDecodeError:
        # Otherwise, print as plain text
        print(msg.payload.decode('utf-8'))

def init_dht_sensor():
    """
    Initializes the DHT sensor. Adjust the pin and sensor type as needed.
    """
    # Example for DHT11 sensor connected to GPIO4
    dht_sensor = adafruit_dht.DHT11(board.D4)
    return dht_sensor

def generate_telemetry_msg(dht_sensor):
    """
    Generates a telemetry message in JSON format.
    """

    # Read sensor data
    try:
        temperature = dht_sensor.temperature
        humidity = dht_sensor.humidity
    except Exception as e:
        print(f"Error reading DHT sensor: {e}")
        return None

    # Create telemetry data
    telemetry_data = {
        "temperature": temperature,
        "humidity": humidity
    }
    payload = json.dumps(telemetry_data)
    return payload
# --- Main script logic ---

# 1. Create an MQTT client instance
mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                    client_id=client_id)
dht_sensor = init_dht_sensor()
# Configure the hardware abstraction layer
# to utilize Broadcom (BCM) pin mapping
GPIO.setmode(GPIO.BCM)
# Provision the designated buzzer pin as an output channel
GPIO.setup(BUZZER_PIN, GPIO.OUT)

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

# Topic to publish telemetry data
telemetry_topic = f"farm/{client_id}/telemetry"

time.sleep(2) # Wait for connection to establish

# 6. Keep the primary execution thread alive to maintain
# the active session.
try:
    while True:
        # Generate telemetry message
        payload_json = generate_telemetry_msg(dht_sensor)

        # Publish the message to the cloud broker
        mqttc.publish(
            topic=telemetry_topic,
            payload=payload_json,
            qos=1 # Quality of Service 1 guarantees "at least once" delivery
        )

        print(f"Published message to topic '{telemetry_topic}': {payload_json}")

        # Suspend execution for 5 seconds before transmitting the next payload
        time.sleep(5)
        
except KeyboardInterrupt:
    print("\nGracefully disconnecting from the AWS IoT broker...")
    # Stop the background thread and cleanly close the TCP/IP socket
    mqttc.loop_stop()
    mqttc.disconnect()
    print("Successfully disconnected from AWS IoT Core.")