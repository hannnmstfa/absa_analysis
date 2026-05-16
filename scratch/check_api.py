import json
import requests

try:
    with open('audit_sentimen_untuk_excel.csv', 'rb') as f:
        res = requests.post(
            'http://127.0.0.1:8001/analyze',
            files={'file': f},
            data={'text_column': 'Komentar', 'usage_col': 'Apakah Anda pernah menggunakan LuxueXPerfume?'}
        )
    if res.status_code == 200:
        data = res.json()
        segment_views = data.get('segment_views', {})
        non_user = segment_views.get('non_user', {})
        print("KEYS IN NON_USER:", non_user.keys())
        insights = non_user.get('market_insights')
        print("MARKET_INSIGHTS:", json.dumps(insights, indent=2))
    else:
        print("Error", res.status_code)
except Exception as e:
    print(e)
