import requests
import pandas as pd
import io
import json

df = pd.DataFrame({
    'Name': ['Test Intern'],
    'Email': ['test@test.com'],
    'INT ID': ['INT123'],
    'Tech Viva': [90]
})

output = io.BytesIO()
with pd.ExcelWriter(output, engine='openpyxl') as writer:
    df.to_excel(writer, index=False)
output.seek(0)

res = requests.post(
    'http://localhost:5000/api/upload-interns',
    data={'manager_id': 'test_man', 'batch_id': 'test'},
    files={'file': ('test.xlsx', output.read(), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
)

print("STATUS:", res.status_code)
try:
    print("RESPONSE:", json.dumps(res.json(), indent=2))
except:
    print("RESPONSE (raw):", res.text)
