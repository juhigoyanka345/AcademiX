/**
 * Main UI Controller & Prediction Form Handler
 */
document.addEventListener('DOMContentLoaded', () => {
    // Prediction Form logic
    const predictForm = document.getElementById('predict-form');
    if (predictForm) {
        // Slider value update listeners
        const sliders = predictForm.querySelectorAll('input[type="range"]');
        sliders.forEach(slider => {
            const display = document.getElementById(`${slider.id}-val`);
            slider.addEventListener('input', (e) => {
                if (display) {
                    if (slider.id.includes('attendance') || slider.id.includes('grade') || slider.id.includes('assignment')) {
                        display.textContent = `${e.target.value}%`;
                    } else if (slider.id.includes('study')) {
                        display.textContent = `${e.target.value} hrs/wk`;
                    } else if (slider.id.includes('sleep')) {
                        display.textContent = `${e.target.value} hrs/day`;
                    } else {
                        display.textContent = `${e.target.value}/10`;
                    }
                }
            });
        });

        predictForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = document.getElementById('btn-run-prediction');
            const originalBtnText = btn.innerHTML;
            btn.disabled = true;
            btn.innerHTML = `<i class="fas fa-spinner fa-spin mr-2"></i> Computing SHAP Explanation...`;

            const payload = {
                student_id: document.getElementById('select-student')?.value || null,
                study_hours: parseFloat(document.getElementById('p-study').value),
                attendance: parseFloat(document.getElementById('p-attendance').value),
                past_grade: parseFloat(document.getElementById('p-grade').value),
                assignment_completion: parseFloat(document.getElementById('p-assignment').value),
                sleep_hours: parseFloat(document.getElementById('p-sleep').value),
                extracurricular_score: parseFloat(document.getElementById('p-extra').value)
            };

            try {
                const res = await API.predict(payload);
                if (res.status === 'success') {
                    const data = res.data;
                    
                    // Show results panel
                    const resultsContainer = document.getElementById('prediction-results-container');
                    resultsContainer.classList.remove('hidden');
                    resultsContainer.scrollIntoView({ behavior: 'smooth' });

                    // Update Score Badge & Category
                    document.getElementById('res-predicted-score').textContent = `${data.predicted_score.toFixed(1)}%`;
                    
                    const catBadge = document.getElementById('res-category-badge');
                    catBadge.textContent = data.performance_category;
                    if (data.performance_category === 'Excellence') {
                        catBadge.className = "px-3 py-1 text-xs font-bold rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30";
                    } else if (data.performance_category === 'On Track') {
                        catBadge.className = "px-3 py-1 text-xs font-bold rounded-full bg-blue-500/20 text-blue-400 border border-blue-500/30";
                    } else if (data.performance_category === 'Moderate Risk') {
                        catBadge.className = "px-3 py-1 text-xs font-bold rounded-full bg-amber-500/20 text-amber-400 border border-amber-500/30";
                    } else {
                        catBadge.className = "px-3 py-1 text-xs font-bold rounded-full bg-rose-500/20 text-rose-400 border border-rose-500/30";
                    }

                    // Update NLP Summary
                    document.getElementById('res-nlp-summary').innerHTML = data.nlp_explanation;

                    // Render SHAP Waterfall Chart
                    AppCharts.renderWaterfall('shap-waterfall-canvas', data.shap_values, data.base_value, data.predicted_score);

                    // Render Interventions List
                    const interventionsList = document.getElementById('res-interventions-list');
                    if (interventionsList) {
                        interventionsList.innerHTML = data.interventions.map(item => `
                            <div class="p-4 rounded-xl bg-slate-800/60 border border-slate-700/50 flex items-start space-x-3">
                                <div class="p-2 rounded-lg ${item.priority === 'HIGH' ? 'bg-rose-500/20 text-rose-400' : item.priority === 'MEDIUM' ? 'bg-amber-500/20 text-amber-400' : 'bg-emerald-500/20 text-emerald-400'}">
                                    <i class="fas ${item.priority === 'HIGH' ? 'fa-exclamation-triangle' : item.priority === 'MEDIUM' ? 'fa-info-circle' : 'fa-check-circle'} text-lg"></i>
                                </div>
                                <div>
                                    <div class="flex items-center space-x-2">
                                        <span class="font-bold text-gray-200">${item.title}</span>
                                        <span class="text-xs px-2 py-0.5 rounded ${item.priority === 'HIGH' ? 'bg-rose-500/20 text-rose-400' : item.priority === 'MEDIUM' ? 'bg-amber-500/20 text-amber-400' : 'bg-emerald-500/20 text-emerald-400'} font-semibold">${item.priority}</span>
                                    </div>
                                    <p class="text-sm text-gray-400 mt-1">${item.action}</p>
                                </div>
                            </div>
                        `).join('');
                    }

                    AppUI.showToast('Prediction & SHAP breakdown computed successfully!', 'success');
                }
            } catch (err) {
                AppUI.showToast('Failed to calculate prediction.', 'error');
            } finally {
                btn.disabled = false;
                btn.innerHTML = originalBtnText;
            }
        });
    }
});

const AppUI = {
    showToast(message, type = 'success') {
        const toastContainer = document.getElementById('toast-container');
        if (!toastContainer) return;

        const toast = document.createElement('div');
        toast.className = `flex items-center space-x-3 px-4 py-3 rounded-xl shadow-lg border backdrop-blur-md transition-all transform translate-y-2 opacity-0 ${
            type === 'success' ? 'bg-emerald-950/80 border-emerald-500/40 text-emerald-200' : 'bg-rose-950/80 border-rose-500/40 text-rose-200'
        }`;
        
        toast.innerHTML = `
            <i class="fas ${type === 'success' ? 'fa-check-circle text-emerald-400' : 'fa-exclamation-circle text-rose-400'} text-lg"></i>
            <span class="text-sm font-medium">${message}</span>
        `;

        toastContainer.appendChild(toast);
        setTimeout(() => {
            toast.classList.remove('translate-y-2', 'opacity-0');
        }, 50);

        setTimeout(() => {
            toast.classList.add('opacity-0');
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }
};
