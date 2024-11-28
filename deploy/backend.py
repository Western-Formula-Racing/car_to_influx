from flask import Flask, request, jsonify, send_from_directory
import cantools
import os
from datetime import datetime
# Importing the functions from readCanoptimized.py
from readCANOptimized import parse_can_message, process_lines
import influxdb_client
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# Set up InfluxDB credentials
token = os.environ.get("INFLUXDB_TOKEN")
org = "WFR"
url = "http://localhost:8086"
bucket = "canBus"
write_client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)

token = os.environ.get("INFLUXDB_TOKEN")
print(f"InfluxDB Token: {token}")  # Debugging: Check the token value


# Initialize Flask app
app = Flask(__name__)

# Define paths for the error log and CAN database
error_log_file = 'error_log.txt'
dbc_file = 'test.dbc'

# Load the CAN database
db = cantools.database.load_file(dbc_file)

# Function to log errors to a separate file
def log_error(message, line, row_num):
    log_message = f"Row {row_num}: {message} | Raw Message: {line.strip()}"
    with open(error_log_file, 'a') as f:
        f.write(log_message + '\n')

# Root route ("/")
@app.route('/')
def home():
    return "Welcome to the CAN message processor API!"

# Health check route ("/health")
@app.route('/health')
def health_check():
    return jsonify({"status": "Healthy"}), 200

# Serve the index.html from the 'templates' folder (if it's there)
@app.route('/index.html')
def serve_index():
    try:
        return send_from_directory(os.path.join(app.root_path, 'templates'), 'index.html')
    except Exception as e:
        return jsonify({"error": f"Error serving index.html: {str(e)}"}), 404

# Function to write processed CAN data to InfluxDB
def write_to_influxdb(can_data, bucket):
    try:
        # Write the point to the database
        write_api = write_client.write_api(write_options=SYNCHRONOUS)
        write_api.write(bucket=bucket, org=org, record=can_data)
    except Exception as e:
        print(f"Error writing to InfluxDB: {e}")

# API endpoint to process CAN data
@app.route('/process', methods=['POST'])
def process():
    data = request.get_json()
    input_text = data.get('input', '')

    if input_text:
        # Process the lines using the imported functions
        lines = input_text.split('\n')
        output_strings = process_lines(lines, db)  # Call the process_lines function from readCanoptimized.py

        # Assuming the output_strings contain a list of CAN message data
        for line in output_strings:
            print(line)
            # Write each CAN message data to InfluxDB
            write_to_influxdb(line, bucket)

        return jsonify({"output": output_strings})
    else:
        return jsonify({"error": "No input provided"}), 400

if __name__ == "__main__":
    app.run(debug=True, host='127.0.0.1', port=5000)
