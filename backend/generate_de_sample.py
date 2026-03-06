import pandas as pd
import random

# Fixed columns required by the app
data = {
    "Name": ["John Doe", "Jane Smith", "Alice Johnson", "Bob Williams", "Charlie Brown"],
    "Email": ["john.doe@example.com", "jane.smith@example.com", "alice.j@example.com", "bob.w@example.com", "charlie.b@example.com"],
    "EmpID": ["EMP001", "EMP002", "EMP003", "EMP004", "EMP005"],
    "Capstone project (Total: 100)": [random.randint(60, 95) for _ in range(5)],
    "Internal Project (Total: 100)": [random.randint(60, 95) for _ in range(5)],
    "Internal Assessment Scores (Total: 100)": [random.randint(60, 95) for _ in range(5)],
    "External Vendor Scores (Total: 100)": [random.randint(60, 95) for _ in range(5)],
    "Mentor Feedback (Total: 100)": [random.randint(60, 95) for _ in range(5)],
    "Viva Scores (Total: 100)": [random.randint(60, 95) for _ in range(5)],
    "Presentation/Communication (Total: 100)": [random.randint(60, 95) for _ in range(5)],
    "L&D Feedback (Total: 100)": [random.randint(60, 95) for _ in range(5)],
    "General Feedback": [
        "Great progress on the DE pipeline.",
        "Needs to improve SQL optimization skills.",
        "Excellent architectural understanding.",
        "Struggling with Airflow concepts.",
        "Consistent performer, good communication."
    ]
}

df = pd.DataFrame(data)
output_path = "/home/sigmoid/Desktop/DE_Sample_Data.xlsx"
df.to_excel(output_path, index=False)
print(f"Sample generated at {output_path}")
