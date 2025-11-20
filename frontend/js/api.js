// API Client for SEO Content Generator

const API_BASE_URL = 'http://localhost:5000/api';

const API = {
    /**
     * Health check
     */
    async health() {
        const response = await fetch(`${API_BASE_URL}/health`);
        if (!response.ok) throw new Error('Server not responding');
        return await response.json();
    },

    /**
     * Generar contenido
     * @param {Object} data - {topic, keywords, target_length, strategy_id?}
     */
    async generate(data) {
        const response = await fetch(`${API_BASE_URL}/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Error generating content');
        }
        
        return await response.json();
    },

    /**
     * Obtener historial
     * @param {number} limit 
     * @param {number} offset 
     */
    async history(limit = 10, offset = 0) {
        const response = await fetch(
            `${API_BASE_URL}/history?limit=${limit}&offset=${offset}`
        );
        
        if (!response.ok) throw new Error('Error fetching history');
        return await response.json();
    },

    /**
     * Obtener estadísticas
     */
    async stats() {
        const response = await fetch(`${API_BASE_URL}/stats`);
        if (!response.ok) throw new Error('Error fetching stats');
        return await response.json();
    },

    /**
     * Obtener estrategias disponibles
     */
    async strategies() {
        const response = await fetch(`${API_BASE_URL}/strategies`);
        if (!response.ok) throw new Error('Error fetching strategies');
        return await response.json();
    },

    /**
     * Obtener generación específica
     * @param {string} id 
     */
    async getGeneration(id) {
        const response = await fetch(`${API_BASE_URL}/generation/${id}`);
        if (!response.ok) throw new Error('Generation not found');
        return await response.json();
    }
};
