import re
patternZahl = r"^\d+$"
if re.match(patternZahl, "3") == None:
    print("nein")