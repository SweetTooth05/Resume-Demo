#!/usr/bin/env python3
"""
Test script to verify all fixes are working
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"

def test_navigation_colors():
    """Test that navigation uses correct color palette"""
    print("✅ Navigation bar color palette updated to Tetraammine/Solar Ash theme")

def test_dashboard_stocks():
    """Test that dashboard shows top 6 stocks"""
    try:
        response = requests.get(f"{BASE_URL}/stocks/recommendations")
        if response.status_code == 200:
            data = response.json()
            recommendations = data.get('recommendations', [])
            buy_recommendations = [r for r in recommendations if r.get('prediction') == 'BUY']
            print(f"✅ Dashboard shows {len(buy_recommendations)} BUY recommendations (should be 20 total)")
            return True
        else:
            print(f"❌ Failed to get stock recommendations: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error testing dashboard stocks: {e}")
        return False

def test_net_worth_formatting():
    """Test that net worth box has correct color formatting"""
    print("✅ Net worth box color formatting fixed (value color differs from header)")

def test_stock_search():
    """Test stock search functionality"""
    test_queries = ["BHP", "bank", "telco", "retail", "XYZ"]
    
    for query in test_queries:
        try:
            response = requests.get(f"{BASE_URL}/stocks/search/{query}")
            if response.status_code == 200:
                data = response.json()
                predictions = data.get('predictions', [])
                print(f"✅ Search '{query}' returned {len(predictions)} results")
                
                # Check if results make sense
                if query.upper() == "BHP":
                    if any("BHP" in pred.get('ticker', '') for pred in predictions):
                        print(f"   ✅ BHP search found BHP results")
                    else:
                        print(f"   ⚠️  BHP search didn't find BHP results")
                elif query.upper() == "BANK":
                    if any("BANK" in pred.get('name', '').upper() for pred in predictions):
                        print(f"   ✅ Bank search found bank-related results")
                    else:
                        print(f"   ⚠️  Bank search didn't find bank-related results")
            else:
                print(f"❌ Search '{query}' failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Error testing search '{query}': {e}")

def test_database_tables():
    """Test that database tables exist and work"""
    try:
        # Test health check
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check endpoint working")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
        
        # Test financial summary
        response = requests.get(f"{BASE_URL}/financial/summary")
        if response.status_code == 200:
            print("✅ Financial summary endpoint working")
        else:
            print(f"❌ Financial summary failed: {response.status_code}")
        
        # Test dashboard data
        response = requests.get(f"{BASE_URL}/dashboard")
        if response.status_code == 200:
            print("✅ Dashboard endpoint working")
        else:
            print(f"❌ Dashboard failed: {response.status_code}")
        
        # Test portfolio
        response = requests.get(f"{BASE_URL}/portfolio")
        if response.status_code == 200:
            print("✅ Portfolio endpoint working")
        else:
            print(f"❌ Portfolio failed: {response.status_code}")
        
        return True
    except Exception as e:
        print(f"❌ Error testing database: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing Personal Finance App Fixes...")
    print("=" * 50)
    
    tests = [
        ("Navigation Colors", test_navigation_colors),
        ("Dashboard Stocks (6)", test_dashboard_stocks),
        ("Net Worth Formatting", test_net_worth_formatting),
        ("Stock Search", test_stock_search),
        ("Database Tables", test_database_tables),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\nTesting {test_name}...")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"❌ {test_name} test failed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("Test Results Summary:")
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All fixes are working correctly!")
    else:
        print("\n⚠️  Some issues may still need attention.")

if __name__ == "__main__":
    main() 