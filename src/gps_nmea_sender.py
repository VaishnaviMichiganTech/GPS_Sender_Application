#!/usr/bin/env python3
import rosbag
import socket
import time
import pytz
from datetime import datetime, timezone
from tkinter import Tk, filedialog
from geomag import geomag

def calculate_magnetic_variation(lat, lon, alt):
    """
    Calculate magnetic variation using the World Magnetic Model.
    """
    wmm = geomag.GeoMag()
    mag_data = wmm.GeoMag(lat, lon, alt)
    return mag_data.dec  # Magnetic declination in degrees

def select_file():
    # Hide the main tk window
    root = Tk()
    root.withdraw()

    # Open file window and return slected path
    file_path = filedialog.askopenfilename()
    return file_path

def decimal_degrees_to_dms(dd, is_latitude):
    degrees = int(dd)
    minutes = (dd - degrees) * 60
    return "{:02d}{:07.4f}".format(abs(degrees), abs(minutes))

def calculate_checksum(sentence):
    """
    Calculate the NMEA checksum (XOR of all bytes between $ and *).
    """
    checksum = 0
    for char in sentence:
        checksum ^= ord(char)
    return "{:02X}".format(checksum)

def generate_nmea_from_gpsfix(msg):
    # print(msg)
    utc = pytz.UTC
    now = datetime.now(timezone.utc) #fromtimestamp(msg.header.stamp.to_sec(), utc)
    date = now.strftime("%d%m%y")
    time_str = now.strftime("%H%M%S.%f")[:-4]
    
    lat = decimal_degrees_to_dms(msg.latitude, True)
    lat_dir = 'N' if msg.latitude >= 0 else 'S'
    lon = decimal_degrees_to_dms(msg.longitude, False)
    lon_dir = 'E' if msg.longitude >= 0 else 'W'
    
    fix_type = '1' if msg.status.status > 0 else '0'
    num_sats = '{:02d}'.format(msg.status.satellites_used)
    hdop = '{:.1f}'.format(msg.hdop)
    alt = '{:.1f}'.format(msg.altitude)

    magnetic_variation = calculate_magnetic_variation(msg.latitude, msg.longitude, msg.altitude)
    direction = 'E' if magnetic_variation >= 0 else 'W'
    mag_variation_abs = abs(magnetic_variation)
    geoid_sep = getattr(msg, 'geoid_separation', 0.0)    

    # Construct GPGGA
    gga_body = "GPGGA,{},{},{},{},{},{},{},{},{},M,{:.1f},M,,".format(
        time_str, lat, lat_dir, lon, lon_dir, fix_type, num_sats, hdop, alt, geoid_sep)
    checksum_gga = calculate_checksum(gga_body)
    gga_sentence = f"${gga_body}*{checksum_gga}\r\n"
    print(gga_sentence)
    
    # Construct GPRMC
    lat_rmc = lat[:-1]
    lon_rmc = lon[:-1]
    speed_knots = msg.speed * 1.94384  # Convert m/s to knots
    course = msg.track if msg.track else 0.0
    rmc_body = "GPRMC,{},{},{},{},{},{},{:.1f},{:.1f},{},{:.2f},{}".format(
        time_str, 'A' if msg.status.status > 0 else 'V', lat_rmc, lat_dir, lon_rmc, lon_dir, speed_knots, course, date, mag_variation_abs, direction)
    checksum_rmc = calculate_checksum(rmc_body)
    rmc_sentence = f"${rmc_body}*{checksum_rmc}\r\n"
    print(rmc_sentence)
    
    # Construct GPZDA
    zda_body = "GPZDA,{},{:02d},{:02d},{},00,00".format(
        time_str, now.day, now.month, now.year)
    checksum_zda = calculate_checksum(zda_body)
    zda_sentence = f"${zda_body}*{checksum_zda}\r\n"
    print(zda_sentence)
    
    return gga_sentence + rmc_sentence + zda_sentence

def send_nmea_from_bag(bag_file, topic, obu_ip, gpsd_port):
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((obu_ip, gpsd_port))
            try:
                bag = rosbag.Bag(bag_file)
                for topic, msg, t in bag.read_messages(topics=[topic]):
                    nmea_sentence = generate_nmea_from_gpsfix(msg)
                    nmea_bytes = nmea_sentence.encode()
                    print(type(nmea_bytes))
                    print(nmea_bytes)
                    sock.sendall(nmea_bytes)
                    print("Sent: {}".format(nmea_bytes.strip()))
                    time.sleep(1)  # Adjust this delay as needed
                bag.close()
            finally:
                sock.close()
        except Exception as e:
            print("Error: {}".format(e))
            print("Attempting to reconnect in 5 seconds...")
            time.sleep(5)

if __name__ == "__main__":
    bag_file = select_file()
    gps_topic = "/gps/gps"
    obu_ip = "192.168.222.220"
    gpsd_port = 5000
    
    send_nmea_from_bag(bag_file, gps_topic, obu_ip, gpsd_port)
