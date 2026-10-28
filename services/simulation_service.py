from services.predictor_service import predict_student_performance

def run_whatif_simulation(baseline_features, modified_features):
    """
    Compares baseline student parameters against a modified scenario.
    Returns score delta, percentage improvement, and updated XAI explanation.
    """
    # Predict baseline
    baseline_result = predict_student_performance(baseline_features)
    
    # Predict modified
    simulated_result = predict_student_performance(modified_features)
    
    baseline_score = baseline_result['predicted_score']
    simulated_score = simulated_result['predicted_score']
    score_delta = round(simulated_score - baseline_score, 2)
    percent_change = round(((simulated_score - baseline_score) / (baseline_score if baseline_score > 0 else 1.0)) * 100, 2)
    
    # Identify modified feature(s)
    changed_features = []
    for k in baseline_features:
        orig_v = float(baseline_features[k])
        mod_v = float(modified_features.get(k, orig_v))
        if abs(orig_v - mod_v) > 0.001:
            changed_features.append({
                'feature': k,
                'from_value': orig_v,
                'to_value': mod_v,
                'delta': round(mod_v - orig_v, 2)
            })
            
    return {
        'baseline_score': baseline_score,
        'simulated_score': simulated_score,
        'score_delta': score_delta,
        'percent_change': percent_change,
        'baseline_category': baseline_result['performance_category'],
        'simulated_category': simulated_result['performance_category'],
        'changed_features': changed_features,
        'baseline_waterfall': baseline_result['shap_values'],
        'simulated_waterfall': simulated_result['shap_values'],
        'simulated_interventions': simulated_result['interventions']
    }
