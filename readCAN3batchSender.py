from influxdb_client import Point, InfluxDBClient
from influxdb_client.client.write_api import WriteOptions
from datetime import datetime, timezone
import cantools
import re
import time  # Added to use time.sleep for rate limiting

def parse_can_message(line, db):
    """
    Parse a CAN message line, decode it, and return a list of InfluxDB Points.

    Args:
        line (str): A single line representing a CAN message.
        db (cantools.database.Database): Loaded CAN database.

    Returns:
        list: A list of InfluxDB Point objects for each signal in the CAN message.
    """
    pattern = r'\s*(\d+)\s+(\w+)(?:\s+X)?\s+(\d+)\s+([0-9\s]+)\s+(\d+\.\d+)\s+([RX])'
    match = re.match(pattern, line)
    if not match:
        return [f"Error: Invalid format for line: {line.strip()}"]

    index, can_id, dlc, data_bytes, timestamp, direction = match.groups()
    can_id_int = int(can_id)

    try:
        message = db.get_message_by_frame_id(can_id_int)
    except KeyError:
        return [f"Error: No message found for CAN ID {can_id_int}"]

    try:
        data_list = bytes(int(byte) for byte in data_bytes.split() if byte)
        decoded_data = message.decode(data_list)
    except Exception as e:
        return [f"Error: Decoding error for CAN ID {can_id_int} - {str(e)}"]

    points = []
    for signal_name, value in decoded_data.items():
        try:
            signal = message.get_signal_by_name(signal_name)
            description = signal.comment if signal.comment else "No description available"
            unit = signal.unit if signal.unit else "N/A"
            if isinstance(value, cantools.database.can.signal.NamedSignalValue):
                signal_label = value.name
                raw_value = float(value.value)
            else:
                signal_label = str(value)
                raw_value = float(value)
        except AttributeError:
            description = "No description available"
            unit = "N/A"
            signal_label = str(value)
            raw_value = float(value)

        now = datetime.now(timezone.utc)
        point = (
            Point("canBus")
            .tag("signalName", signal_name)
            .tag("messageName", message.name)
            .tag("rawCAN", can_id)
            .field("sensorReading", raw_value)
            .field("unit", unit)
            .field("description", description)
            .field("signalLabel", signal_label)
            .time(now)
        )
        points.append(point)

    return points

def process_lines(lines, db, write_api, bucket, messages_per_second=400):
    """
    Process a list of CAN message lines sequentially, rate limiting to exactly
    'messages_per_second' messages per second, and write Points to InfluxDB in batches.

    Args:
        lines (list): List of CAN message lines as strings.
        db (cantools.database.Database): Loaded CAN database.
        write_api (influxdb_client.WriteApi): InfluxDB Write API.
        bucket (str): InfluxDB bucket name.
        messages_per_second (int): Number of messages to process per second.
    """
    batch_points = []
    start_time = time.time()
    message_count = 0

    for idx, line in enumerate(lines):
        try:
            points = parse_can_message(line, db)
            if points and isinstance(points[0], str) and points[0].startswith("Error:"):
                print(f"Line {idx}: {points[0]}")
            else:
                batch_points.extend(points)
                message_count += 1

            # Once we have processed 'messages_per_second' messages, flush and wait
            if message_count >= messages_per_second:
                if batch_points:
                    write_api.write(bucket=bucket, org="WFR", record=batch_points)
                    batch_points = []  # Reset the batch
                elapsed = time.time() - start_time
                if elapsed < 1:
                    time.sleep(1 - elapsed)  # Wait the remaining time of the 1s interval
                start_time = time.time()
                message_count = 0
        except Exception as e:
            print(f"Error processing line {idx}: {str(e)}")

    # Write any remaining points after processing all lines
    if batch_points:
        write_api.write(bucket=bucket, org="WFR", record=batch_points)

def main():
    from influxdb_client.client.write_api import SYNCHRONOUS

    # Load CAN database
    dbc_file = 'testing_data/20240129 Gen5 CAN DB.dbc'
    try:
        db = cantools.database.load_file(dbc_file)
        print(f"Loaded DBC file: {dbc_file}")
    except Exception as e:
        print(f"Failed to load DBC file: {str(e)}")
        return

    # InfluxDB setup with batching options
    influx_url = "http://35.183.158.105:8086"  # Replace with your InfluxDB URL
    with open('influx_token.txt', 'r') as f:
        token = f.read().strip()

    bucket = "ourCar"
    client = InfluxDBClient(url=influx_url, token=token, org="WFR")
    # Adjust flush_interval to match our 1s rate control if desired.
    write_api = client.write_api(write_options=WriteOptions(batch_size=400, flush_interval=1000))

    # Read CAN message lines
    with open('testing_data/CanTraceJuly11.txt', 'r') as f:
        lines = f.read().split('\n')

    # Process lines and write to InfluxDB at a rate of exactly 400 messages per second
    process_lines(lines, db, write_api, bucket, messages_per_second=400)
    print("Data successfully written to InfluxDB.")

if __name__ == "__main__":
    main()