#!/usr/bin/env python3
"""
Test script to verify XGBoost model integration
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.ml.stock_predictor import stock_predictor

def test_model_integration():
    """Test the XGBoost model integration"""
    print("🧪 Testing XGBoost Model Integration")
    print("=" * 50)
    
    # Test model loading
    print("1. Testing model loading...")
    model_info = stock_predictor.get_model_info()
    print(f"   Model loaded: {model_info['model_loaded']}")
    print(f"   Model type: {model_info['model_type']}")
    
    if model_info['model_loaded']:
        print("   ✅ Model loaded successfully!")
    else:
        print("   ❌ Model failed to load")
        return False
    
    # Test stock prediction
    print("\n2. Testing stock prediction...")
    test_tickers = ["BHP.AX", "CBA.AX", "CSL.AX"]
    
    for ticker in test_tickers:
        print(f"   Predicting {ticker}...")
        prediction = stock_predictor.predict_stock(ticker)
        
        if prediction:
            print(f"   ✅ {ticker}: {prediction['prediction']} (confidence: {prediction['confidence_score']:.2f})")
            print(f"      Current price: ${prediction['current_price']:.2f}")
        else:
            print(f"   ❌ Failed to predict {ticker}")
    
    # Test model performance
    print("\n3. Model Performance:")
    if model_info['performance']:
        for key, value in model_info['performance'].items():
            if isinstance(value, dict):
                print(f"   {key}:")
                for sub_key, sub_value in value.items():
                    print(f"     {sub_key}: {sub_value}")
            else:
                print(f"   {key}: {value}")
    
    print("\n🎉 Integration test completed!")
    return True

if __name__ == "__main__":
    test_model_integration() 