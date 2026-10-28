import json
from database import get_db_connection

def get_cohort_analytics():
    """
    Aggregates XAI explanation logs across all student prediction records in SQLite
    to identify class-wide risk patterns, top negative impact factors, and risk distribution.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT p.study_hours, p.attendance, p.past_grade, p.assignment_completion,
               p.sleep_hours, p.extracurricular_score, p.predicted_score,
               p.performance_category, p.shap_json, s.name as student_name, s.department
        FROM prediction_logs p
        JOIN students s ON p.student_id = s.id
        ORDER BY p.timestamp DESC
    ''')
    logs = cursor.fetchall()
    conn.close()

    if not logs:
        # Fallback default empty summary if database logs are empty
        return {
            'total_students_evaluated': 0,
            'category_counts': {'Excellence': 0, 'On Track': 0, 'Moderate Risk': 0, 'High Risk': 0},
            'avg_score': 0,
            'cohort_feature_averages': {},
            'cohort_shap_averages': {},
            'top_class_risk_factors': [],
            'insights_summary': 'No prediction logs registered in database yet. Run predictions to activate cohort insights.'
        }

    total_count = len(logs)
    scores = []
    category_counts = {'Excellence': 0, 'On Track': 0, 'Moderate Risk': 0, 'High Risk': 0}
    
    feature_keys = ['study_hours', 'attendance', 'past_grade', 'assignment_completion', 'sleep_hours', 'extracurricular_score']
    feature_totals = {k: 0.0 for k in feature_keys}
    shap_totals = {k: 0.0 for k in feature_keys}
    negative_impact_counts = {k: 0 for k in feature_keys}

    for log in logs:
        scores.append(log['predicted_score'])
        cat = log['performance_category']
        if cat in category_counts:
            category_counts[cat] += 1
            
        for k in feature_keys:
            feature_totals[k] += log[k]
            
        try:
            shaps = json.loads(log['shap_json'])
            for k in feature_keys:
                s_val = float(shaps.get(k, 0))
                shap_totals[k] += s_val
                if s_val < -1.0: # Significant negative impact
                    negative_impact_counts[k] += 1
        except Exception:
            pass

    avg_score = round(sum(scores) / total_count, 1)
    cohort_feature_averages = {k: round(v / total_count, 1) for k, v in feature_totals.items()}
    cohort_shap_averages = {k: round(v / total_count, 2) for k, v in shap_totals.items()}

    # Rank risk factors by how many students are pulled down by them
    feature_labels = {
        'study_hours': 'Low Weekly Study Hours',
        'attendance': 'Low Class Attendance',
        'past_grade': 'Weak Past Academic Foundation',
        'assignment_completion': 'Incomplete Assignment Submissions',
        'sleep_hours': 'Systemic Sleep Deficit',
        'extracurricular_score': 'Low Campus Engagement'
    }

    risk_factors_ranked = []
    for k, count in sorted(negative_impact_counts.items(), key=lambda x: x[1], reverse=True):
        pct = round((count / total_count) * 100, 1)
        risk_factors_ranked.append({
            'feature': k,
            'label': feature_labels.get(k, k),
            'affected_student_count': count,
            'affected_percentage': pct,
            'avg_shap_impact': cohort_shap_averages[k]
        })

    # Summary Insights NLP
    top_risk = risk_factors_ranked[0] if risk_factors_ranked else None
    high_risk_pct = round((category_counts['High Risk'] / total_count) * 100, 1)
    
    if top_risk and top_risk['affected_percentage'] > 0:
        summary_text = (
            f"Across {total_count} evaluated records, the class average score is **{avg_score}%**. "
            f"**{top_risk['label']}** emerges as the single largest class-wide vulnerability, negatively impacting "
            f"**{top_risk['affected_percentage']}%** of students. "
            f"Currently, **{high_risk_pct}%** of students require urgent educator intervention."
        )
    else:
        summary_text = f"Across {total_count} evaluated records, overall student cohort performance is healthy with an average predicted score of **{avg_score}%**."

    return {
        'total_students_evaluated': total_count,
        'category_counts': category_counts,
        'avg_score': avg_score,
        'cohort_feature_averages': cohort_feature_averages,
        'cohort_shap_averages': cohort_shap_averages,
        'top_class_risk_factors': risk_factors_ranked,
        'insights_summary': summary_text
    }
