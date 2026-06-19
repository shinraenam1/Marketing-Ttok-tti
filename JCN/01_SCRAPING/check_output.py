import json

path = 'output/all_card_events_20260619_150458.json'
data = json.load(open(path, encoding='utf-8'))

# all_card_events is a list of events
if isinstance(data, list):
    print(f'Total combined events: {len(data)}')
    from collections import Counter
    counts = Counter(e["card_company"] for e in data)
    for k, n in counts.items():
        print(f'  {k}: {n}건')
    print()
    # Show first event per company
    shown = set()
    for e in data:
        cc = e["card_company"]
        if cc not in shown:
            shown.add(cc)
            title = e["title"]
            date_range = e["date_range"]
            url = e["url"]
            print(f'[{cc}] 첫 이벤트:')
            print(f'  title: {title}')
            print(f'  date:  {date_range}')
            print(f'  url:   {url}')
else:
    total = sum(len(v) for v in data.values())
    print(f'Total combined events: {total}')
    for k, v in data.items():
        print(f'  {k}: {len(v)}건')
    print()
    for k, v in data.items():
        e = v[0]
        title = e["title"]
        date_range = e["date_range"]
        url = e["url"]
        print(f'[{k}] 첫 이벤트:')
        print(f'  title: {title}')
        print(f'  date:  {date_range}')
        print(f'  url:   {url}')
