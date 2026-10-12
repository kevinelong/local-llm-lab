import csv, io
def reconcile(text):
    balances = {}
    for row in csv.DictReader(io.StringIO(text)):
        balances[row["account"]] = int(row["cents"])
    return sorted((a, b, 1) for a, b in balances.items())
