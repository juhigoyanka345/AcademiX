/**
 * What-If Simulation Sandbox Controller
 */
document.addEventListener('DOMContentLoaded', () => {
    const simForm = document.getElementById('sim-form');
    if (!simForm) return;

    const baseScoreEl = document.getElementById('sim-base-score');
    const simScoreEl = document.getElementById('sim-target-score');
    const deltaEl = document.getElementById('sim-delta');
    const simBadgeEl = document.getElementById('sim-target-badge');
    const simSummaryEl = document.getElementById('sim-nlp-summary');

    // Attach listeners to all range inputs
    const rangeInputs = simForm.querySelectorAll('input[type="range"]');
    rangeInputs.forEach(input => {
        const valSpan = document.getElementById(`${input.id}-val`);
        input.addEventListener('input', (e) => {
            if (valSpan) {
                if (input.id.includes('attendance') || input.id.includes('grade') || input.id.includes('assignment')) {
                    valSpan.textContent = `${e.target.value}%`;
                } else if (input.id.includes('study')) {
                    valSpan.textContent = `${e.target.value} hrs/wk`;
                } else if (input.id.includes('sleep')) {
                    valSpan.textContent = `${e.target.value} hrs/day`;
                } else {
                    valSpan.textContent = `${e.target.value}/10`;
                }
            }
            triggerSimulation();
        });
    });

    async function triggerSimulation() {
        const getVal = (id) => parseFloat(document.getElementById(id).value);

        const baseline = {
            study_hours: getVal('base-study'),
            attendance: getVal('base-attendance'),
            past_grade: getVal('base-grade'),
            assignment_completion: getVal('base-assignment'),
            sleep_hours: getVal('base-sleep'),
            extracurricular_score: getVal('base-extra')
        };

        const modified = {
            study_hours: getVal('sim-study'),
            attendance: getVal('sim-attendance'),
            past_grade: getVal('sim-grade'),
            assignment_completion: getVal('sim-assignment'),
            sleep_hours: getVal('sim-sleep'),
            extracurricular_score: getVal('sim-extra')
        };

        try {
            const res = await API.simulate(baseline, modified);
            if (res.status === 'success') {
                const data = res.data;
                
                baseScoreEl.textContent = `${data.baseline_score.toFixed(1)}%`;
                simScoreEl.textContent = `${data.simulated_score.toFixed(1)}%`;

                const sign = data.score_delta >= 0 ? '+' : '';
                deltaEl.textContent = `${sign}${data.score_delta.toFixed(1)}%`;
                
                if (data.score_delta > 0) {
                    deltaEl.className = "text-2xl font-extrabold text-emerald-400";
                } else if (data.score_delta < 0) {
                    deltaEl.className = "text-2xl font-extrabold text-rose-400";
                } else {
                    deltaEl.className = "text-2xl font-extrabold text-gray-400";
                }

                if (simBadgeEl) {
                    simBadgeEl.textContent = data.simulated_category;
                }

                // Render dynamic comparison summary
                if (simSummaryEl) {
                    if (data.changed_features.length > 0) {
                        const feat = data.changed_features[0];
                        simSummaryEl.innerHTML = `Modifying <strong>${feat.feature.replace('_', ' ')}</strong> from ${feat.from_value} to ${feat.to_value} causes final score to shift by <span class="${data.score_delta >= 0 ? 'text-emerald-400' : 'text-rose-400'} font-bold">${sign}${data.score_delta}%</span>.`;
                    } else {
                        simSummaryEl.textContent = "Adjust any right-side slider to observe simulated score impact in real time.";
                    }
                }

                // Re-render simulated waterfall chart
                AppCharts.renderWaterfall('sim-waterfall-chart', data.simulated_waterfall, 70.0, data.simulated_score);
            }
        } catch (e) {
            console.error('Simulation error:', e);
        }
    }

    // Initial trigger
    triggerSimulation();
});
