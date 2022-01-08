import re

VICTIM_NAME: re.Pattern = re.compile(r'[\'"](.*?)[\'"]')
KILLER_NAME: re.Pattern = re.compile(r'killed by Player [\'"](.*?)[\'"]')
WEAPON: re.Pattern = re.compile(r"with (.*?) from")
MELEE_WEAPON: re.Pattern = re.compile(r"with (.*)")
COORDS: re.Pattern = re.compile(r"pos=<(.*?)>")
DISTANCE: re.Pattern = re.compile(r"from ([0-9.]+) meters")
TIME: re.Pattern = re.compile(r"(\d+:\d+:\d+)")
