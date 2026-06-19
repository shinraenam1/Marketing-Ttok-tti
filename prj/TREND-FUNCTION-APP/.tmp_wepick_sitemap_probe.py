import requests
for url in [
  'https://letter.wepick.kr/sitemap.xml',
  'https://letter.wepick.kr/sitemap_index.xml',
  'https://letter.wepick.kr/post-sitemap.xml',
  'https://letter.wepick.kr/sitemap-post.xml'
]:
  try:
    r=requests.get(url,timeout=10)
    print(url, r.status_code, r.text[:180].replace('\n',' '))
  except Exception as e:
    print(url, 'ERR', e)
