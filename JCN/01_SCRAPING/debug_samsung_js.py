import urllib.request, re

url = 'https://static12.samsungcard.com/js/personal/event/ing/UHPPBE1401M0.js?ver=20150406'
req = urllib.request.Request(url, headers={
    'User-Agent': 'Mozilla/5.0 Chrome/124.0.0.0',
    'Referer': 'https://www.samsungcard.com/'
})
data = urllib.request.urlopen(req, timeout=15).read().decode('utf-8', errors='ignore')
print('Length:', len(data))
print('\nFirst 2000 chars:')
print(data[:2000])
