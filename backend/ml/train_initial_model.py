"""
Initial model training script.
Creates a basic safety score model using synthetic data.
This is intended to be run once to create an initial model.
"""
import os
import sys
import logging

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from app.ml.train_model import train_model

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """
    Main function to train an initial model.
    """
    # Define paths
    model_dir = os.path.join(os.path.dirname(__file__), 'models')
    model_path = os.path.join(model_dir, 'safety_model.joblib')

    # Create directory if it doesn't exist
    os.makedirs(model_dir, exist_ok=True)

    # Train model with a small sample size for quick initial training
    # In production, you would use a larger dataset
    print("Training initial safety score model...")
    print("This may take a few minutes...")

    try:
        train_model(
            model_output_path=model_path,
            num_samples=1000  # Small sample for initial model
        )
        print("\nInitial model training completed successfully!")
        print(f"Model saved to: {model_path}")
    except Exception as e:
        print(f"\nError during training: {e}")
        print("Please check the logs for more details.")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())