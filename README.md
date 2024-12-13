# Create README.md in your root directory
echo "# GPS NMEA Sender Application for MK5 OBU

This application reads GPS data from the gps/gps_fix topic in a rosbag and populates GPS NMEA sentences to an MK5 OBU. This tool is primarily designed as a test bench suite for generating virtual vehicles around EGO vehicles for traffic simulation and studying their intersections.

## Setup Instructions on MK5 Board

### 1. File Modifications
Replace or modify the following files with the versions provided in \`change_files_on_OBU\` directory:
- \`/etc/chrony.conf\`
- \`/etc/systemd/system/gpsdatetime.service\`
- \`/etc/systemd/system/chrony.service\`
- \`/etc/systemd/system/gpsd.service\`
- \`/mnt/rw/example1609/obu.conf\`

Create a new file:
- \`/etc/systemd/system/netcat-gps.service\`

### 2. Service Management
Execute the following commands in order on the OBU

\`\`\`bash
# Stop Services
systemctl stop chrony.service
systemctl stop gpsdatetime.service
systemctl stop gpsd.service
systemctl stop netcat-gps.service

# Reload daemon
systemctl daemon-reload

# Enable and start netcat-gps service
systemctl enable netcat-gps.service
systemctl start netcat-gps.service

# Enable and start gpsd service
systemctl enable gpsd.service
systemctl start gpsd.service
\`\`\`

### 3. Run GPS NMEA Sender
Navigate to the scripts directory and run the sender:
\`\`\`bash
cd src/gps_nmea_sender_2/scripts
python2 gps_nmea_sender_2.py
\`\`\`

### 4. Start Remaining Services
\`\`\`bash
systemctl enable gpsdatetime.service
systemctl start gpsdatetime.service
systemctl enable chrony.service
systemctl start chrony.service

Check teh GPS Output with: gpspipe -r
\`\`\`

### 5. Start OBU
\`\`\`bash
/mnt/rw/example1609/rc.example1609 start obu
\`\`\`

### 6. Verify Output
Monitor the output using:
\`\`\`bash
tcpdump -i cw-mon-txa -xx 
tcpdump -i cw-mon-txa -xx || grep " 00 *14"
\`\`\`
" > README.md
