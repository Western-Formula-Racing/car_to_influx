from influxdb_client import Point
from datetime import datetime
import cantools
import re

def parse_can_message(line, db):
    print("\nInput: " + line)

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

    # Try to get the CAN message definition from the DBC
    try:
        message = db.get_message_by_frame_id(can_id_int)
    except KeyError:
        return [f"Error: No message found for CAN ID {can_id_int}"]

    # Parse and decode data bytes
    try:
        data_list = bytes(int(byte) for byte in data_bytes.split() if byte)
        decoded_data = message.decode(data_list)
    except Exception as e:
        return [f"Error: Decoding error for CAN ID {can_id_int} - {str(e)}"]

    # Generate InfluxDB Points for each signal
    points = []
    for signal_name, value in decoded_data.items():
        try:
            signal = message.get_signal_by_name(signal_name)
            description = signal.comment if signal.comment else "No description available"
            unit = signal.unit if signal.unit else "N/A"
        except AttributeError:
            description = "No description available"
            unit = "N/A"

        # Convert value to float if possible
        if isinstance(value, cantools.database.can.signal.NamedSignalValue):
            sensor_value = float(value.value)  # Use the numeric representation
        else:
            sensor_value = float(value)  # Use directly if already numeric

        now = datetime.now()
        point = (
            Point("canBus1")
            .tag("signalName", signal_name)
            .tag("messageName", message.name)
            .tag("rawCAN", can_id)
            .field("sensorReading", sensor_value)  # Use the converted value
            .field("unit", unit)
            .field("description", description)
            .time(now)
        )
        points.append(point)
        print(point)

    return points

def process_lines(lines, db, write_api, bucket):
    """
    Process a list of CAN message lines sequentially and write Points to InfluxDB.

    Args:
        lines (list): List of CAN message lines as strings.
        db (cantools.database.Database): Loaded CAN database.
        write_api (influxdb_client.WriteApi): InfluxDB Write API.
        bucket (str): InfluxDB bucket name.
    """
    for idx, line in enumerate(lines):
        try:
            points = parse_can_message(line, db)
            write_api.write(bucket=bucket, org="WFR", record=points)
        except Exception as e:
            print(f"Error processing line {idx}: {str(e)}")

def main():
    from influxdb_client import InfluxDBClient
    from influxdb_client.client.write_api import SYNCHRONOUS

    # Load CAN database
    dbc_file = 'testing_data/20240129 Gen5 CAN DB.dbc'
    try:
        db = cantools.database.load_file(dbc_file)
        print(f"Loaded DBC file: {dbc_file}")
    except Exception as e:
        print(f"Failed to load DBC file: {str(e)}")
        return

    # InfluxDB setup
    influx_url = "http://localhost:8086"  # Replace with your InfluxDB URL
    # token = read txt file influx_token.txt
    with open('influx_token.txt', 'r') as f:
        token = f.read().strip()

    bucket = "canBus"
    client = InfluxDBClient(url=influx_url, token=token, org="WFR")
    write_api = client.write_api(write_options=SYNCHRONOUS)

    # Read CAN message lines
    with open('testing_data/small_CanTrace.txt', 'r') as f:
        lines = f.read().split('\n')

    # Process lines and write to InfluxDB
    process_lines(lines, db, write_api, bucket)
    print("Data successfully written to InfluxDB.")

if __name__ == "__main__":
    main()
