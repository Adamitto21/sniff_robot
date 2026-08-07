podmieniałem binarke fabryczną esp32
4 pliki:
- bootloader.bin	program startowy — pierwszy uruchamiany po włączeniu, ładuje właściwą aplikację
- partitions.bin	mapa pamięci: gdzie kończy się aplikacja, gdzie zaczyna system plików
- boot_app0.bin	wskaźnik, którą partycję aplikacji uruchomić
- ROS_Driver.ino.bin	właściwy program sterujący robotem (1,2 MB)

i usuwałem NVS

backup'y są w folderze firmawer/backup


komenda, która powinna wrócić binarke:

python3 $ESPTOOL --port /dev/ttyCH343USB0 --baud 921600 write_flash 0 \
  ~/sniff_robot/firmware/backup/przed_fabrycznym_2026-08-04.bin


konrad
