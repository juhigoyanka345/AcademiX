def generate_nlp_explanation(feature_dict, shap_dict, predicted_score, category):
    """
    Generates plain-language XAI explanations and targeted interventions
    based on individual SHAP contribution values.
    """
    feature_labels = {
        'study_hours': 'Weekly Study Hours',
        'attendance': 'Class Attendance',
        'past_grade': 'Past Semester Grade',
        'assignment_completion': 'Assignment Completion Rate',
        'sleep_hours': 'Daily Sleep Hours',
        'extracurricular_score': 'Extracurricular Participation'
    }

    # Sort SHAP contributions
    sorted_shaps = sorted(shap_dict.items(), key=lambda item: item[1], reverse=True)
    positives = [item for item in sorted_shaps if item[1] > 0.5]
    negatives = [item for item in sorted_shaps if item[1] < -0.5]
    negatives_sorted = sorted(negatives, key=lambda item: item[1]) # Most negative first

    # Core Summary Sentence
    summary = f"The student is predicted to achieve **{predicted_score:.1f}%** ({category}). "
    
    if positives and negatives:
        top_pos = feature_labels.get(positives[0][0], positives[0][0])
        top_neg = feature_labels.get(negatives_sorted[0][0], negatives_sorted[0][0])
        summary += f"Performance is strongly boosted by high **{top_pos}** (+{positives[0][1]:.1f}%), but severely pulled down by low **{top_neg}** ({negatives_sorted[0][1]:.1f}%)."
    elif positives:
        top_pos = feature_labels.get(positives[0][0], positives[0][0])
        summary += f"The primary driver pushing performance up is **{top_pos}** (+{positives[0][1]:.1f}%)."
    elif negatives:
        top_neg = feature_labels.get(negatives_sorted[0][0], negatives_sorted[0][0])
        summary += f"Performance is predominantly hindered by low **{top_neg}** ({negatives_sorted[0][1]:.1f}%)."
    else:
        summary += "Performance is balanced near average historical standards."

    # Detailed Factor Bullet Points
    factor_breakdown = []
    for feat, val in sorted_shaps:
        name = feature_labels.get(feat, feat)
        actual_val = feature_dict.get(feat, 0)
        shap_val = val
        impact_type = "positive" if shap_val > 0 else "negative" if shap_val < 0 else "neutral"
        
        if feat == 'attendance':
            unit_str = f"{actual_val}%"
        elif feat == 'study_hours':
            unit_str = f"{actual_val} hrs/week"
        elif feat == 'past_grade' or feat == 'assignment_completion':
            unit_str = f"{actual_val}%"
        elif feat == 'sleep_hours':
            unit_str = f"{actual_val} hrs/night"
        else:
            unit_str = f"{actual_val}/10 score"

        sign = "+" if shap_val > 0 else ""
        factor_breakdown.append({
            'feature': feat,
            'label': name,
            'value_display': unit_str,
            'shap_val': round(shap_val, 2),
            'impact_type': impact_type,
            'text': f"**{name}** ({unit_str}) contributed {sign}{shap_val:.1f}% to final grade prediction."
        })

    # Recommended Interventions
    interventions = []
    for feat, val in negatives_sorted[:3]:
        name = feature_labels.get(feat, feat)
        actual_val = feature_dict.get(feat, 0)
        
        if feat == 'attendance' and actual_val < 75:
            interventions.append({
                'feature': feat,
                'priority': 'HIGH',
                'title': 'Mandatory Attendance Monitoring',
                'action': f"Current attendance is {actual_val}%. Increasing attendance above 80% is estimated to recover up to +{abs(val):.1f}% in overall score."
            })
        elif feat == 'assignment_completion' and actual_val < 80:
            interventions.append({
                'feature': feat,
                'priority': 'HIGH',
                'title': 'Assignment & Task Completion Support',
                'action': f"Assignment submission rate is {actual_val}%. Providing tutoring or extension reminders can boost score by +{abs(val):.1f}%."
            })
        elif feat == 'study_hours' and actual_val < 15:
            interventions.append({
                'feature': feat,
                'priority': 'MEDIUM',
                'title': 'Guided Study Hours Plan',
                'action': f"Student studies {actual_val} hrs/week. Recommended target: 18-22 hrs/week to reclaim lost points."
            })
        elif feat == 'sleep_hours' and actual_val < 6:
            interventions.append({
                'feature': feat,
                'priority': 'MEDIUM',
                'title': 'Wellness & Sleep Hygiene Counseling',
                'action': f"Sleep deficit ({actual_val} hrs/night) causes cognitive fatigue. Adjusting routine to 7+ hrs improves academic retention."
            })
        elif feat == 'past_grade' and actual_val < 60:
            interventions.append({
                'feature': feat,
                'priority': 'HIGH',
                'title': 'Foundational Subject Review',
                'action': f"Past grade foundation ({actual_val}%) shows gaps. Schedule remedial coursework in core subjects."
            })

    if not interventions:
        interventions.append({
            'feature': 'general',
            'priority': 'LOW',
            'title': 'Maintain Current Trajectory',
            'action': 'Student is performing consistently well. Encourage continued study routines and peer mentoring opportunities.'
        })

    return {
        'summary': summary,
        'factor_breakdown': factor_breakdown,
        'interventions': interventions
    }
