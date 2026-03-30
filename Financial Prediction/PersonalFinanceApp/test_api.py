#!/usr/bin/env python3
"""
Simple API test script to verify backend endpoints are working
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"

def test_health_check():
    """Test health check endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Health Check: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_stock_recommendations():
    """Test stock recommendations endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/stocks/recommendations")
        print(f"Stock Recommendations: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data.get('recommendations', []))} recommendations")
        return response.status_code == 200
    except Exception as e:
        print(f"Stock recommendations failed: {e}")
        return False

def test_financial_summary():
    """Test financial summary endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/financial/summary")
        print(f"Financial Summary: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Summary data: {data.get('summary', {})}")
        return response.status_code == 200
    except Exception as e:
        print(f"Financial summary failed: {e}")
        return False

def test_dashboard_data():
    """Test dashboard data endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/dashboard")
        print(f"Dashboard Data: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Dashboard totals: {data.get('totals', {})}")
        return response.status_code == 200
    except Exception as e:
        print(f"Dashboard data failed: {e}")
        return False

def test_portfolio():
    """Test portfolio endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/portfolio")
        print(f"Portfolio: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Found {len(data.get('holdings', []))} holdings")
        return response.status_code == 200
    except Exception as e:
        print(f"Portfolio failed: {e}")
        return False

def main():
    """Run all API tests"""
    print("Testing Personal Finance App API...")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health_check),
        ("Stock Recommendations", test_stock_recommendations),
        ("Financial Summary", test_financial_summary),
        ("Dashboard Data", test_dashboard_data),
        ("Portfolio", test_portfolio),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\nTesting {test_name}...")
        success = test_func()
        results.append((test_name, success))
    
    print("\n" + "=" * 50)
    print("Test Results:")
    for test_name, success in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"\nOverall: {passed}/{total} tests passed")

if __name__ == "__main__":
    main() 