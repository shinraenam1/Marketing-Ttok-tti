import urllib.request, re

url = 'https://static12.samsungcard.com/js/personal/event/ing/UHPPBE1401M0.js?ver=20150406'
data = urllib.request.urlopen(url, timeout=15).read().decode('utf-8', errors='ignore')

# Find all function definitions
fns = re.findall(r'(\w+)\s*:\s*function\s*\(', data)
print("Functions:", fns)

# Find main list load function (GoBrwsEvnLst)
idx = data.find('GoBrwsEvnLst')
if idx != -1:
    print("\n--- GoBrwsEvnLst ---")
    print(data[idx:idx+600])

# Find SHPPBE1402S09
idx = data.find('SHPPBE1402S09')
if idx != -1:
    print("\n--- SHPPBE1402S09 context ---")
    print(data[max(0,idx-300):idx+500])
