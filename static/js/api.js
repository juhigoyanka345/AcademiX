/**
 * API Client for Student Performance Predictor & XAI Backend
 */
const API = {
    async predict(payload) {
        try {
            const response = await fetch('/api/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            return await response.json();
        } catch (error) {
            console.error('API Predict Error:', error);
            throw error;
        }
    },

    async simulate(baseline, modified) {
        try {
            const response = await fetch('/api/simulate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ baseline, modified })
            });
            return await response.json();
        } catch (error) {
            console.error('API Simulate Error:', error);
            throw error;
        }
    },

    async getCohortAnalytics() {
        try {
            const response = await fetch('/api/cohort/analytics');
            return await response.json();
        } catch (error) {
            console.error('API Cohort Error:', error);
            throw error;
        }
    },

    async getStudentHistory(studentId) {
        try {
            const response = await fetch(`/api/students/${studentId}/history`);
            return await response.json();
        } catch (error) {
            console.error('API History Error:', error);
            throw error;
        }
    },

    async createIntervention(payload) {
        try {
            const response = await fetch('/api/interventions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            return await response.json();
        } catch (error) {
            console.error('API Intervention Error:', error);
            throw error;
        }
    }
};
