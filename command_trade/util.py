seconds_per_unit = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800, "M": 2592000, "y": 31536000} # assume 1 month = 30days, 1 year = 365 days

def convert_to_seconds(s): # ex: 15m, 1s, 1y, 1M, ...
    return int(s[:-1]) * seconds_per_unit[s[-1]]