import os
import numpy as np
import pandas as pd
import joblib
import shap
from config import Config
from services.nlp_explanation import generate_nlp_explanation

def load_ml_artifacts():
    if not (os.path.exists(Config.MODEL_PATH) and os.path.exists(Config.SCALER_PATH) and os.path.exists(Config.EXPLAINER_PATH)):
        print("ML Model artifacts not found. Training model automatically...")
        from models.train_model import train_and_save_model
        train_and_save_model()
        
    model = joblib.load(Config.MODEL_PATH)
    scaler = joblib.load(Config.SCALER_PATH)
    explainer = joblib.load(Config.EXPLAINER_PATH)
    return model, scaler, explainer

def predict_student_performance(feature_dict):
    """
    Accepts feature_dict with keys:
    ['study_hours', 'attendance', 'past_grade', 'assignment_completion', 'sleep_hours', 'extracurricular_score']
    Returns prediction score, category, SHAP waterfall data, and NLP explanations.
    """
    model, scaler, explainer = load_ml_artifacts()
    
    feature_cols = ['study_hours', 'attendance', 'past_grade', 'assignment_completion', 'sleep_hours', 'extracurricular_score']
    
    # Input validation / default fill
    input_values = [float(feature_dict.get(col, 0)) for col in feature_cols]
    input_df = pd.DataFrame([input_values], columns=feature_cols)
    
    # Preprocess & Predict
    scaled_input = scaler.transform(input_df)
    predicted_score = float(model.predict(scaled_input)[0])
    predicted_score = float(np.clip(predicted_score, 0.0, 100.0))
    
    # Determine Performance Category
    if predicted_score >= 85.0:
        category = 'Excellence'
        risk_level = 'Low'
    elif predicted_score >= 70.0:
        category = 'On Track'
        risk_level = 'Low-Moderate'
    elif predicted_score >= 55.0:
        category = 'Moderate Risk'
        risk_level = 'Medium'
    else:
        category = 'High Risk'
        risk_level = 'High'
        
    # SHAP Explanation calculation
    try:
        shap_values_raw = explainer(scaled_input)
        if hasattr(shap_values_raw, 'values'):
            shap_vec = shap_values_raw.values[0]
            base_value = float(shap_values_raw.base_values[0]) if hasattr(shap_values_raw.base_values, '__len__') else float(shap_values_raw.base_values)
        else:
            shap_vec = shap_values_raw[0]
            base_value = float(explainer.expected_value)
    except Exception as e:
        print(f"SHAP calculation fallback due to: {e}")
        # Fallback tree feature importances approximation
        feature_importances = model.feature_importances_
        shap_vec = (scaled_input[0] - scaler.mean_) * feature_importances * 10
        base_value = 70.0

    shap_dict = {}
    for col, val in zip(feature_cols, shap_vec):
        shap_dict[col] = float(val)

    # Generate Natural Language Explanation & Interventions
    explanation = generate_nlp_explanation(feature_dict, shap_dict, predicted_score, category)

    return {
        'predicted_score': round(predicted_score, 2),
        'performance_category': category,
        'risk_level': risk_level,
        'base_value': round(base_value, 2),
        'features': feature_dict,
        'shap_values': shap_dict,
        'nlp_explanation': explanation['summary'],
        'factor_breakdown': explanation['factor_breakdown'],
        'interventions': explanation['interventions']
    }
