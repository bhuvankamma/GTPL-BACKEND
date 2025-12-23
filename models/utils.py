import datetime

def row_to_dict(row):
    out = {}
    for k, v in row.items():
        if isinstance(v, (datetime.date, datetime.datetime)):
            out[k] = v.isoformat()
        else:
            out[k] = v
    return out
