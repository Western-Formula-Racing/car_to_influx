from flask import Flask, request, jsonify, send_from_directory
import cantools
import os
import re
from datetime import datetime

app = Flask(__name__)

# Define paths for the error log and CAN database
error_log_file = 'error_log.txt'
dbc_file = 'test.dbc'
pattern = r'\s*(\d+)\s+(\w+)(?:\s+X)?\s+(\d+)\s+([0-9\s]+)\s+(\d+\.\d+)\s+([RX])'


# Load the CAN database
db = cantools.database.load_file(dbc_file)

# Function to log errors to a separate file
def log_error(message, line, row_num):
    log_message = f"Row {row_num}: {message} | Raw Message: {line.strip()}"
    with open(error_log_file, 'a') as f:
        f.write(log_message + '\n')

# Function to parse CAN message line
def parse_can_message(line, db, row_num):
    match = re.match(pattern, line)
    if not match:
        log_error("Invalid format", line, row_num)
        return []

    index, can_id, dlc, data_bytes, timestamp, direction = match.groups()
    can_id_int = int(can_id)

    try:
        message = db.get_message_by_frame_id(can_id_int)
    except KeyError:
        log_error(f"No message found for CAN ID {can_id_int}", line, row_num)
        return []

    try:
        data_list = bytes(int(byte) for byte in data_bytes.split() if byte)
        decoded_data = message.decode(data_list)
    except Exception as e:
        log_error(f"Decoding error for CAN ID {can_id_int}: {str(e)}", line, row_num)
        return []

    output = []
    for signal_name, value in decoded_data.items():
        try:
            signal = message.get_signal_by_name(signal_name)
            description = signal.comment if signal.comment else "No description available"
            unit = signal.unit if signal.unit else "N/A"
        except AttributeError:
            description = "No description available"
            unit = "N/A"

        now = datetime.now()
        unix_time_ns = int(now.timestamp() * 1e9)
        formatted_string = (
            f"canBus,"
            f"signalName={signal_name},"
            f"description={description},"
            f"messageName={message.name},"
            f"RawCAN={can_id},"
            f"sensorReading={value},"
            f"unit={unit},"
            f"relativeTime={timestamp},"
            f"time={unix_time_ns}"
        )
        output.append(formatted_string)
    return output

# Function to process multiple CAN message lines
def process_lines(lines, db):
    output_strings = []
    for idx, line in enumerate(lines):
        try:
            parsed_strings = parse_can_message(line, db, idx + 1)
            output_strings.extend(parsed_strings)
        except Exception as e:
            log_error(f"Unexpected error: {str(e)}", line, idx + 1)
    return output_strings

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

# API endpoint to process CAN data
@app.route('/process', methods=['POST'])
def process():
    data = request.get_json()
    input_text = data.get('input', '')
    if input_text:
        output_strings = process_lines([input_text], db)
        return jsonify({"output": output_strings})
    else:
        return jsonify({"error": "No input provided"}), 400

if __name__ == "__main__":
    app.run(debug=True, host='127.0.0.1', port=5000)