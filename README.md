# Tesla Inventory Search

## How to run

### Ad-hoc execution

```
python search.py 5551234567
```

### cron job

Runs every 30 min, outputs to stdout

```
EDITOR=nano crontab -e
0,30 * * * * python path/to/search.py 5551234567 > /proc/$(cat /var/run/crond.pid)/fd/1 2>&1
```
