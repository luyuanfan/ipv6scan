Connect to PSQL:
```bash
psql -h localhost -p 6789 -U lyspfan
```

pgadmin4 browser access from local:
```bash
ssh ss -L 9876:localhost:9876
# database name is lyspfan 
```

Auto password:
```bash
echo "localhost:6789:*:lyspfan:lyspfan" > ~/.pgpass
chmod 600 ~/.pgpass
```

View first 30 lines:
```sql
SELECT * FROM $CSV LIMIT 30;
```

**Remove comments on top of the files before import**

## Import CSV files
Take `small.csv` as example:
```bash
# drop old table and index
./import/small.sh
```

Take `medium.csv` as example:
```bash
# drop old table and index
./import/medium.sh
```

## Import compressed CSV files
```bash
# drop old table and index
./import/full.sh
```

## Import CAIDA's pfx2as dataset
[Link to all datasets](https://publicdata.caida.org/datasets/routing/routeviews6-prefix2as/)
```bash
# drop old table
./import/pfx2as.sh
```

## Import CAIDA's as2org dataset
Preprocess data:
```bash
# dataset must be requested
# drop old table
./import/as2org.sh
```