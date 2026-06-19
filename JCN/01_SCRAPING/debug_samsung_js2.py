import urllib.request

url = 'https://static12.samsungcard.com/js/personal/event/ing/UHPPBE1401M0.js?ver=20150406'
data = urllib.request.urlopen(url, timeout=15).read().decode('utf-8', errors='ignore')

# Find the main event list loading section
# Look for scard.ajax service calls
import re
service_calls = re.findall(r'service\s*:\s*["\'](\w+)["\']', data)
print("Service calls:", service_calls)

# Find pgeNo usage
idx = data.find('pgeNo')
while idx != -1:
    print(f"\n--- pgeNo at {idx} ---")
    print(data[max(0, idx-200):idx+400])
    idx = data.find('pgeNo', idx+1)
