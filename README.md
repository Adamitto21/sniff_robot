docker compose up -d --build

docker compose up -d

docker exec -it sniff_ros2 bash

docker compose down

test ruchu kol:

python3 -c "
import serial, json, time
ser = serial.Serial('/dev/ttyCH343USB0', 115200, timeout=1)
ser.write((json.dumps({'T':1,'L':0.3,'R':0.3}) + '\n').encode('utf-8'))
time.sleep(2)
ser.write((json.dumps({'T':0}) + '\n').encode('utf-8'))
ser.close()
"

