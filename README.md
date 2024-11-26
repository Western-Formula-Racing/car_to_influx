# car_to_influx
Convert data from the car to influxdb inputs 

# Handle GNSS Data
example:
send ```AT+UGNMEA?```

receive ```+UGNMEA: "$GPRMC,083559.00,A,4717.11437,N,00833.91522,E,0.004,77.52,091202,,,A,V*57"```

definition: $GPRMC,<UTC Time>,<Status>,<Latitude>,<N/S>,<Longitude>,<E/W>,<Speed>,<Course>,<Date>,<Magnetic Variation>,<Mag. Var. Direction>,<Mode>,<Checksum>

influx: ```location,device_id=device123 latitude=47.28524,longitude=8.56525,speed=0.004,course=77.52,fix_status=1,mode="A" 1039477200000000000```

fix status 1/True for A, valid data, mode A autonomous GNSS fix mode

| Field               | Value           | Description                                    | Possible Inputs                           |
|---------------------|-----------------|------------------------------------------------|-------------------------------------------|
| Sentence Type       | $GPRMC          | Recommended minimum data.                     | $GPRMC, $GPGGA, $GPGLL, $GPGSA, etc.      |
| UTC Time            | 083559.00       | 08:35:59.00 (HH:MM:SS.ss).                    | Any valid UTC time in HHMMSS.ss format.   |
| Status              | A               | Data valid.                                   | A (Valid), V (Invalid)                    |
| Latitude            | 4717.11437 N    | Latitude (degrees and minutes).               | Latitude in DDMM.MMMMM format.            |
| Longitude           | 00833.91522 E   | Longitude (degrees and minutes).              | Longitude in DDDMM.MMMMM format.          |
| Speed               | 0.004 knots     | Speed over ground.                            | Any valid speed in knots or km/h.         |
| Course              | 77.52°          | Course over ground.                           | Any valid course angle in degrees (0-360).|
| Date                | 091202          | 09-12-02 (day-month-year).                    | Any valid date in DDMMYY format.          |
| Magnetic Variation  | -               | Not provided.                                 | Any valid variation (degrees) or '-' for not provided. |
| Mode                | A               | Autonomous mode.                              | A (Autonomous), D (Differential), E (Estimated). |
| Navigation Warn     | V               | Warning: No valid GNSS data.                  | V (Warning), N (No warning)              |
| Checksum            | *57             | Data integrity verification.                  | Any valid checksum based on NMEA format.  |
