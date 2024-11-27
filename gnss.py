import datetime
import random

# Define GNSS data structure
class GNSSData:
    def __init__(self, utc_time, latitude, longitude, speed, course, mode):
        self.utc_time = utc_time
        self.latitude = latitude
        self.longitude = longitude
        self.speed = speed
        self.course = course
        self.mode = mode

# Simulate GNSS data
def simulate_gnss_data():
    # Generate random values for latitude, longitude, speed, and course
    latitude = 47.28524 + (random.uniform(-0.001, 0.001)) * 100
    longitude = 8.56525 + (random.uniform(-0.001, 0.001)) * 100
    speed = random.uniform(0.0, 1.0)
    course = random.uniform(0.0, 360.0)

    # Create GNSS data object
    gnss_data = GNSSData(
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        latitude,
        longitude,
        speed,
        course,
        "A"
    )

    return gnss_data

# Parse GNSS data into InfluxDB format
def parse_gnss_to_influx(gnss_data):
    influx_format = f"location,device_id= device123 latency={gnss_data.latitude},longitude={gnss_data.longitude},speed={gnss_data.speed},course={gnss_data.course},fix_status=1,mode={gnss_data.mode} 1039477200000000000"
    return influx_format

# Simulate GNSS data and parse it into InfluxDB format
def main():
    gnss_data = simulate_gnss_data()
    influx_format = parse_gnss_to_influx(gnss_data)
    print(influx_format)

if __name__ == "__main__":
    main()

# Output:
# location,device_id= device123 latency=47.28524,longitude=8.56525,speed=0.004,course=77.52,fix_status=1,mode=A 1039477200000000000
