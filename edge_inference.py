import os
import sys
import joblib
import pandas as pd
import numpy as np

def run_edge_demo():
    print("========================================")
    print("EDGE DEVICE INFERENCE DEMO")
    print("========================================")
    print("\nDemonstrating local offline inference on an edge device (e.g., Raspberry Pi).")
    print("Reduces network overhead by predicting RUL locally without remote server dependency.\n")

    models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
    joblib_model_path = os.path.join(models_dir, "random_forest_model.joblib")
    pkl_model_path = os.path.join(models_dir, "rf_rul_model.pkl")
    scaler_path = os.path.join(models_dir, "scaler.pkl")

    # 1. Load / export Random Forest model (.joblib)
    if not os.path.exists(joblib_model_path):
        if os.path.exists(pkl_model_path):
            model = joblib.load(pkl_model_path)
            joblib.dump(model, joblib_model_path)
            print(f"Exported trained Random Forest model to: {joblib_model_path}")
        else:
            raise FileNotFoundError(f"Trained Random Forest model not found at {pkl_model_path}")
    else:
        model = joblib.load(joblib_model_path)
        print(f"Loaded Random Forest model from: {joblib_model_path}")

    # 2. Load fitted scaler
    if os.path.exists(scaler_path):
        scaler = joblib.load(scaler_path)
        print(f"Loaded fitted preprocessing scaler from: {scaler_path}")
    else:
        scaler = None
        print("Warning: Preprocessing scaler not found, using raw input.")

    # 3. Sample edge sensor input
    temp = 68.4
    vib = 1.21
    curr = 8.9
    press = 5.0
    noise = 48.2

    # 4. Format input features exactly as expected by trained model
    df_sample = pd.DataFrame({
        "Temperature": [temp],
        "Vibration": [vib],
        "Motor_Current": [curr],
        "Pressure": [press],
        "Noise": [noise]
    })

    # 5. Apply identical preprocessing
    if scaler is not None:
        X_scaled = scaler.transform(df_sample)
    else:
        X_scaled = df_sample.values

    # 6. Run local inference
    raw_pred = model.predict(X_scaled)[0]
    predicted_rul = max(0, int(round(raw_pred)))

    # Determine status
    if predicted_rul > 180:
        status = "HEALTHY"
    elif predicted_rul > 100:
        status = "WARNING"
    else:
        status = "CRITICAL"

    print("\n----------------------------------------")
    print("Model: Random Forest")
    print(f"Temperature:   {temp} °C")
    print(f"Vibration:     {vib} mm/s")
    print(f"Motor Current: {curr} A")
    print(f"Pressure:      {press} bar")
    print(f"Noise:         {noise} dB")
    print(f"\nPredicted RUL: {predicted_rul} days")
    print(f"\nStatus:        {status}")
    print("----------------------------------------")
    print("\nInference completed locally.")
    print("========================================\n")

if __name__ == "__main__":
    run_edge_demo()
