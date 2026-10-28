import os
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import shap

def generate_synthetic_data(n_samples=1200):
    np.random.seed(42)
    
    study_hours = np.random.uniform(2, 38, n_samples)
    attendance = np.random.uniform(45, 100, n_samples)
    past_grade = np.random.uniform(40, 98, n_samples)
    assignment_completion = np.random.uniform(35, 100, n_samples)
    sleep_hours = np.random.uniform(4, 9.5, n_samples)
    extracurricular_score = np.random.uniform(0, 10, n_samples)

    # Realistic domain outcome formula
    base_score = (
        0.28 * past_grade +
        0.28 * attendance +
        0.20 * assignment_completion +
        0.14 * (study_hours / 38.0 * 100.0) +
        0.06 * (np.clip(sleep_hours, 6, 8) / 8.0 * 100.0) +
        0.04 * (extracurricular_score / 10.0 * 100.0)
    )
    
    # Add non-linear interactions & realistic Gaussian noise
    noise = np.random.normal(0, 3.5, n_samples)
    # Penalty for severe sleep deficit (<5 hrs) or extreme low attendance (<50%)
    sleep_penalty = np.where(sleep_hours < 5.5, (5.5 - sleep_hours) * 3.0, 0)
    attendance_penalty = np.where(attendance < 55, (55 - attendance) * 0.4, 0)
    
    final_score = np.clip(base_score - sleep_penalty - attendance_penalty + noise, 20, 100)

    df = pd.DataFrame({
        'study_hours': study_hours,
        'attendance': attendance,
        'past_grade': past_grade,
        'assignment_completion': assignment_completion,
        'sleep_hours': sleep_hours,
        'extracurricular_score': extracurricular_score,
        'final_score': final_score
    })
    return df

def train_and_save_model():
    models_dir = os.path.dirname(__file__)
    os.makedirs(models_dir, exist_ok=True)
    
    print("Generating synthetic student performance dataset...")
    df = generate_synthetic_data(1200)
    
    feature_cols = ['study_hours', 'attendance', 'past_grade', 'assignment_completion', 'sleep_hours', 'extracurricular_score']
    X = df[feature_cols]
    y = df['final_score']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    print("Training Random Forest Regressor...")
    model = RandomForestRegressor(n_estimators=120, max_depth=10, random_state=42)
    model.fit(X_train_scaled, y_train)
    
    y_pred = model.predict(X_test_scaled)
    r2 = r2_score(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    print(f"Model Training Complete! R2 Score: {r2:.4f}, RMSE: {rmse:.4f}")
    
    print("Fitting SHAP TreeExplainer...")
    explainer = shap.TreeExplainer(model)
    
    # Save artifacts
    model_path = os.path.join(models_dir, 'student_model.pkl')
    scaler_path = os.path.join(models_dir, 'scaler.pkl')
    explainer_path = os.path.join(models_dir, 'explainer.pkl')
    
    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)
    joblib.dump(explainer, explainer_path)
    
    print(f"Successfully saved artifacts:\n - {model_path}\n - {scaler_path}\n - {explainer_path}")

if __name__ == '__main__':
    train_and_save_model()
