import json

data = json.load(open('output/all_card_events_20260619_150458.json', encoding='utf-8'))
total = sum(d['count'] for d in data)
print(f'총 이벤트: {total}건')
for d in data:
    company = d['card_company']
    count = d['count']
    e = d['events'][0]
    title = e['title'][:40]
    date = e['date_range']
    print(f'  [{company}] {count}건 | 예시: {title} / {date}')
