import cantools
import re
import socket
from datetime import datetime

# Function to log errors to a separate file
def log_error(message, line, row_num):
    log_message = f"Row {row_num}: {message} | Raw Message: {line.strip()}"
    with open(error_log_file, 'a') as f:
        f.write(log_message + '\n')

def parse_can_message(line, db, row_num):
    # (Same as in your code above)
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

def process_lines(lines, db):
    output_strings = []
    for idx, line in enumerate(lines):
        try:
            parsed_strings = parse_can_message(line, db, idx + 1)  # Row number is 1-based
            output_strings.extend(parsed_strings)
        except Exception as e:
            log_error(f"Unexpected error: {str(e)}", line, idx + 1)
    return output_strings

def server_listen():
    host = '127.0.0.1'
    port = 65432  # Choose a port you want to listen on

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        # Allow reuse of the address/port
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Bind the server socket to the address and port
        try:
            server_socket.bind((host, port))
        except OSError as e:
            print(f"Error binding to port {port}: {e}")
            return

        server_socket.listen()
        print(f"Server listening on {host}:{port}")

        # Accept a client connection
        conn, addr = server_socket.accept()
        with conn:
            print(f"Connected by {addr}")

            # Load CAN database
            db = cantools.database.load_file(dbc_file)

            while True:
                data = conn.recv(1024)  # Buffer size
                if not data:
                    break
                line = data.decode('utf-8').strip()
                # Process the received line and send a response
                output_strings = process_lines([line], db)
                for output in output_strings:
                    conn.sendall(output.encode('utf-8') + b'\n')  # Send back the result

if __name__ == "__main__":
    error_log_file = 'testing_data/CanTraceJuly11_errors.txt'
    dbc_file = 'testing_data/20240129 Gen5 CAN DB.dbc'
    pattern = r'\s*(\d+)\s+(\w+)(?:\s+X)?\s+(\d+)\s+([0-9\s]+)\s+(\d+\.\d+)\s+([RX])'
    server_listen()