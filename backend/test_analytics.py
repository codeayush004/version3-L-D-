import os
from app.analytics.engine import AnalyticsEngine

def test_context():
    manager_id = 'dev@example.com'
    
    print(f"Testing for Manager: {manager_id}")
    
    # Test Organization Summary
    print("\n--- ORGANIZATION SUMMARY ---")
    summary = AnalyticsEngine.get_organization_summary(manager_id)
    print(summary)
    
    # Test College Performance (which used to be global, now filtered)
    print("\n--- COLLEGE PERFORMANCE ---")
    college_perf = AnalyticsEngine.get_college_performance(manager_id)
    print(college_perf)

if __name__ == "__main__":
    test_context()

if __name__ == "__main__":
    test_context()
