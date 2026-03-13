ipv6 scan analysis. 

Set up environment:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

```bash
psql -h localhost -p 6789 -U lyspfan
```

pgadmin4 browser access from local:
```bash
ssh ss -L 9876:localhost:9876
# database name is lyspfan 
```

Process data: 
```bash
nohup python3 main.py /mnt/usb/combined-48s-r1-s56.csv.bz2 /mnt/usb/combined-48s-r2-s60.csv.bz2 /mnt/usb/combined-48s-r3-output.csv.bz2 &
```