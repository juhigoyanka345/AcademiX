/**
 * Chart rendering module using Chart.js
 */
const AppCharts = {
    waterfallChartInstance: null,
    cohortChartInstance: null,
    donutChartInstance: null,
    historyChartInstance: null,

    renderWaterfall(canvasId, shapData, baseValue, finalScore) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        if (this.waterfallChartInstance) {
            this.waterfallChartInstance.destroy();
        }

        const featureLabels = {
            'study_hours': 'Study Hours',
            'attendance': 'Attendance Rate',
            'past_grade': 'Past Grade',
            'assignment_completion': 'Assignments',
            'sleep_hours': 'Sleep Duration',
            'extracurricular_score': 'Extracurriculars'
        };

        const labels = ['Base Model Average'];
        const values = [baseValue];
        const backgroundColors = ['#6366f1'];
        
        let runningTotal = baseValue;

        Object.keys(shapData).forEach(key => {
            const shapVal = shapData[key];
            labels.push(featureLabels[key] || key);
            values.push(shapVal);
            if (shapVal >= 0) {
                backgroundColors.push('#10b981');
            } else {
                backgroundColors.push('#f43f5e');
            }
            runningTotal += shapVal;
        });

        labels.push('Final Predicted Score');
        values.push(finalScore);
        backgroundColors.push('#a855f7');

        this.waterfallChartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Score Contribution (%)',
                    data: values,
                    backgroundColor: backgroundColors,
                    borderRadius: 6
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const val = context.raw;
                                const sign = val > 0 ? '+' : '';
                                return ` Impact: ${sign}${val.toFixed(2)}%`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: '#94a3b8' }
                    },
                    y: {
                        grid: { display: false },
                        ticks: { color: '#f3f4f6', font: { weight: 'bold' } }
                    }
                }
            }
        });
    },

    renderCohortImpact(canvasId, shapAverages) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        if (this.cohortChartInstance) {
            this.cohortChartInstance.destroy();
        }

        const featureLabels = {
            'study_hours': 'Study Hours',
            'attendance': 'Attendance',
            'past_grade': 'Past Grade',
            'assignment_completion': 'Assignments',
            'sleep_hours': 'Sleep',
            'extracurricular_score': 'Extracurriculars'
        };

        const labels = Object.keys(shapAverages).map(k => featureLabels[k] || k);
        const values = Object.values(shapAverages);
        const colors = values.map(v => v >= 0 ? '#10b981' : '#f43f5e');

        this.cohortChartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Mean Class Impact (%)',
                    data: values,
                    backgroundColor: colors,
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
                    x: { grid: { display: false }, ticks: { color: '#f3f4f6' } }
                }
            }
        });
    },

    renderRiskDonut(canvasId, categoryCounts) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        if (this.donutChartInstance) {
            this.donutChartInstance.destroy();
        }

        this.donutChartInstance = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Excellence', 'On Track', 'Moderate Risk', 'High Risk'],
                datasets: [{
                    data: [
                        categoryCounts['Excellence'] || 0,
                        categoryCounts['On Track'] || 0,
                        categoryCounts['Moderate Risk'] || 0,
                        categoryCounts['High Risk'] || 0
                    ],
                    backgroundColor: ['#10b981', '#3b82f6', '#f59e0b', '#f43f5e'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom', labels: { color: '#cbd5e1' } }
                },
                cutout: '70%'
            }
        });
    }
};
