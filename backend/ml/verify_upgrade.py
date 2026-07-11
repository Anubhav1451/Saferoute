#!/usr/bin/env python
"""
Verification script for the AI Safety Intelligence upgrade.
This script checks that the updated components are correctly implemented.
"""
import sys
import os
import importlib
import inspect

def check_imports():
    """Check that all necessary modules can be imported."""
    print("Checking imports...")

    try:
        from app.ml.safety_model import SafetyScoreModel, get_safety_model, predict_safety_score
        print("✓ safety_model imports successful")
    except Exception as e:
        print(f"✗ safety_model import failed: {e}")
        return False

    try:
        from app.ml.feature_engineering import engineer_features, calculate_report_features
        print("✓ feature_engineering imports successful")
    except Exception as e:
        print(f"✗ feature_engineering import failed: {e}")
        return False

    try:
        from app.ml.train_model import train_model, generate_realistic_training_data
        print("✓ train_model imports successful")
    except Exception as e:
        print(f"✗ train_model import failed: {e}")
        return False

    return True

def check_safety_model_class():
    """Check the SafetyScoreModel class for required methods."""
    print("\nChecking SafetyScoreModel class...")

    try:
        from app.ml.safety_model import SafetyScoreModel

        # Check required methods exist
        required_methods = ['__init__', 'prepare_features', 'predict', 'train', 'save_model', 'load_model']
        for method in required_methods:
            if not hasattr(SafetyScoreModel, method):
                print(f"✗ Missing method: {method}")
                return False
            print(f"✓ Method {method} exists")

        # Check __init__ signature
        sig = inspect.signature(SafetyScoreModel.__init__)
        if 'model_path' not in sig.parameters:
            print("✗ __init__ missing model_path parameter")
            return False
        print("✓ __init__ signature correct")

        return True
    except Exception as e:
        print(f"✗ SafetyScoreModel check failed: {e}")
        return False

def check_feature_engineering():
    """Check feature engineering functions."""
    print("\nChecking feature engineering...")

    try:
        from app.ml.feature_engineering import engineer_features, calculate_report_features

        # Check engineer_features exists
        if not callable(engineer_features):
            print("✗ engineer_features is not callable")
            return False
        print("✓ engineer_features is callable")

        # Check calculate_report_features exists
        if not callable(calculate_report_features):
            print("✗ calculate_report_features is not callable")
            return False
        print("✓ calculate_report_features is callable")

        # Check that calculate_report_features returns expected keys (by inspecting source)
        source = inspect.getsource(calculate_report_features)
        expected_keys = ['report_count_1h', 'report_count_24h', 'report_count_7d', 'report_count_30d',
                        'report_weighted_recent', 'report_weighted_severity']
        missing_keys = []
        for key in expected_keys:
            if key not in source:
                missing_keys.append(key)

        if missing_keys:
            print(f"✗ calculate_report_features missing keys: {missing_keys}")
            return False
        print("✓ calculate_report_features contains expected keys")

        return True
    except Exception as e:
        print(f"✗ Feature engineering check failed: {e}")
        return False

def check_training_script():
    """Check the training script functions."""
    print("\nChecking training script...")

    try:
        from app.ml.train_model import train_model, generate_realistic_training_data, train_and_evaluate_models

        # Check functions exist
        if not callable(train_model):
            print("✗ train_model is not callable")
            return False
        print("✓ train_model is callable")

        if not callable(generate_realistic_training_data):
            print("✗ generate_realistic_training_data is not callable")
            return False
        print("✓ generate_realistic_training_data is callable")

        if not callable(train_and_evaluate_models):
            print("✗ train_and_evaluate_models is not callable")
            return False
        print("✓ train_and_evaluate_models is callable")

        return True
    except Exception as e:
        print(f"✗ Training script check failed: {e}")
        return False

def check_model_file_structure():
    """Check that the models directory structure is correct."""
    print("\nChecking model directory structure...")

    model_dir = os.path.join(os.path.dirname(__file__), 'models')
    if not os.path.exists(model_dir):
        print(f"✗ Models directory does not exist: {model_dir}")
        # Try to create it
        try:
            os.makedirs(model_dir, exist_ok=True)
            print(f"✓ Created models directory: {model_dir}")
        except Exception as e:
            print(f"✗ Failed to create models directory: {e}")
            return False
    else:
        print(f"✓ Models directory exists: {model_dir}")

    backup_dir = os.path.join(model_dir, "backup")
    if not os.path.exists(backup_dir):
        print(f"ℹ Backup directory does not exist (will be created on first training): {backup_dir}")
    else:
        print(f"✓ Backup directory exists: {backup_dir}")

    log_file = os.path.join(model_dir, "training_log.csv")
    if not os.path.exists(log_file):
        print(f"ℹ Training log does not exist (will be created on first training): {log_file}")
    else:
        print(f"✓ Training log file exists: {log_file}")

    return True

def main():
    """Run all checks."""
    print("=" * 50)
    print("AI Safety Intelligence Upgrade Verification")
    print("=" * 50)

    all_passed = True

    all_passed &= check_imports()
    all_passed &= check_safety_model_class()
    all_passed &= check_feature_engineering()
    all_passed &= check_training_script()
    all_passed &= check_model_file_structure()

    print("\n" + "=" * 50)
    if all_passed:
        print("✓ All checks passed! The upgrade is ready for training.")
        print("\nNext steps:")
        print("1. Run the training script:")
        print("   cd /d D:\\saferoute-ai\\backend\\ml")
        print("   python train_model.py --samples 10000")
        print("\n2. After training, verify the model works:")
        print("   python -c \"from app.ml.safety_model import predict_safety_score; print(predict_safety_score(28.6315, 77.2167))\"")
    else:
        print("✗ Some checks failed. Please fix the issues before proceeding.")
    print("=" * 50)

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())