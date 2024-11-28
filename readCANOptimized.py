import cantools
import re
from datetime import datetime

def parse_can_message(line, db):
    """
    Parse a CAN message line, decode it, and return a list of formatted strings.

    Args:
        line (str): A single line representing a CAN message.
        db (cantools.database.Database): Loaded CAN database.

    Returns:
        list: A list of formatted strings for each signal in the CAN message.
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

    # Generate formatted strings for each signal
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
    """
    Process a list of CAN message lines sequentially.

    Args:
        lines (list): List of CAN message lines as strings.
        db (cantools.database.Database): Loaded CAN database.

    Returns:
        list: A list of all formatted strings generated from the CAN messages.
    """
    output_strings = []
    for idx, line in enumerate(lines):
        try:
            parsed_strings = parse_can_message(line, db)
            output_strings.extend(parsed_strings)
        except Exception as e:
            error_message = f"Error processing line {idx}: {str(e)}"
            print(error_message)
            output_strings.append(error_message)
    return output_strings

def main():
    # Load CAN database
    dbc_file = 'testing_data/20240129 Gen5 CAN DB.dbc'
    try:
        db = cantools.database.load_file(dbc_file)
        print(f"Loaded DBC file: {dbc_file}")
    except Exception as e:
        print(f"Failed to load DBC file: {str(e)}")
        return

    # lines is 'testing_data/CanTraceJuly11.txt' split by '\n'
    with open('testing_data/CanTraceJuly11.txt', 'r') as f:
        lines = f.read().split('\n')

    # Process lines and generate output
    output_strings = process_lines(lines, db)

    # Save to a file
    output_file = 'testing_data/CanTraceJuly11_parsed.txt'
    try:
        with open(output_file, 'w') as f:
            for line in output_strings:
                f.write(line + '\n')
        print(f"Parsed data saved to {output_file}")
    except Exception as e:
        print(f"Failed to write to file: {str(e)}")

if __name__ == "__main__":
    main()
