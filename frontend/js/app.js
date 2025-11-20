// SEO Content Generator - Main App Logic

// Estado global
const state = {
    currentGeneration: null,
    stats: null,
    strategies: []
};

// Inicializar app
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
    setupEventListeners();
    checkServerStatus();
});

// Inicialización
async function initializeApp() {
    await loadStrategies();
    await loadStats();
    updateQuickStats();
}

// Event Listeners
function setupEventListeners() {
    // Navegación
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });
    
    // Formulario de generación
    document.getElementById('generateForm').addEventListener('submit', handleGenerate);
    
    // Botones de resultado
    document.getElementById('copyBtn').addEventListener('click', copyContent);
    document.getElementById('downloadBtn').addEventListener('click', downloadContent);
}

// Navegación entre tabs
function switchTab(tabName) {
    // Actualizar botones
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.closest('.nav-btn').classList.add('active');
    
    // Actualizar contenido
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`tab-${tabName}`).classList.add('active');
    
    // Cargar datos si es necesario
    if (tabName === 'history') {
        loadHistory();
    } else if (tabName === 'stats') {
        loadStats();
    }
}

// Check server status
async function checkServerStatus() {
    try {
        const data = await API.health();
        document.getElementById('status').classList.add('online');
        document.getElementById('statusText').textContent = 
            `Conectado - Modo ${data.mode === 'demo' ? 'Demo' : 'Producción'}`;
    } catch (error) {
        document.getElementById('statusText').textContent = 'Desconectado';
        showToast('Error conectando con el servidor', 'error');
    }
}

// Generar contenido
async function handleGenerate(e) {
    e.preventDefault();
    
    const form = e.target;
    const topic = document.getElementById('topic').value.trim();
    const keywordsStr = document.getElementById('keywords').value.trim();
    const targetLength = parseInt(document.getElementById('targetLength').value);
    const strategyValue = document.getElementById('strategy').value;
    
    // Validar
    if (!topic || !keywordsStr) {
        showToast('Por favor completa todos los campos', 'error');
        return;
    }
    
    const keywords = keywordsStr.split(',').map(k => k.trim()).filter(k => k);
    if (keywords.length === 0) {
        showToast('Ingresa al menos una keyword', 'error');
        return;
    }
    
    // Preparar request
    const request = {
        topic,
        keywords,
        target_length: targetLength
    };
    
    if (strategyValue !== 'auto') {
        request.strategy_id = parseInt(strategyValue);
    }
    
    // UI
    const generateBtn = document.getElementById('generateBtn');
    const loading = document.getElementById('loading');
    const result = document.getElementById('result');
    
    generateBtn.disabled = true;
    loading.style.display = 'block';
    result.style.display = 'none';
    
    try {
        const data = await API.generate(request);
        state.currentGeneration = data;
        
        displayResult(data);
        showToast('¡Contenido generado exitosamente!', 'success');
        
        // Actualizar stats
        await loadStats();
        updateQuickStats();
        
    } catch (error) {
        showToast('Error generando contenido: ' + error.message, 'error');
    } finally {
        generateBtn.disabled = false;
        loading.style.display = 'none';
    }
}

// Mostrar resultado
function displayResult(data) {
    const result = document.getElementById('result');

    // Información básica (la respuesta tiene strategy_name directamente, no strategy.name)
    document.getElementById('resultStrategy').textContent = data.strategy_name || 'N/A';
    document.getElementById('resultScore').textContent = data.seo_score ? data.seo_score.toFixed(1) : 'N/A';

    // engagement_metrics está en un objeto separado
    const metrics = data.engagement_metrics || {};
    document.getElementById('resultCTR').textContent = metrics.ctr ? (metrics.ctr * 100).toFixed(2) + '%' : 'N/A';
    document.getElementById('resultPosition').textContent = metrics.search_position ? '#' + Math.round(metrics.search_position) : 'N/A';

    // Métricas detalladas
    document.getElementById('metricTime').textContent = metrics.time_on_page ? Math.round(metrics.time_on_page) + 's' : 'N/A';
    document.getElementById('metricBounce').textContent = metrics.bounce_rate ? (metrics.bounce_rate * 100).toFixed(1) + '%' : 'N/A';
    document.getElementById('metricTokens').textContent = data.tokens_used || 0;
    document.getElementById('metricGenTime').textContent = data.generation_time ? data.generation_time.toFixed(2) + 's' : 'N/A';

    // Contenido (usar marked para markdown)
    const contentDiv = document.getElementById('resultContent');
    if (typeof marked !== 'undefined') {
        contentDiv.innerHTML = marked.parse(data.content || '');
    } else {
        contentDiv.textContent = data.content || '';
    }

    result.style.display = 'block';
    result.scrollIntoView({ behavior: 'smooth' });
}

// Copiar contenido
function copyContent() {
    if (!state.currentGeneration) return;
    
    navigator.clipboard.writeText(state.currentGeneration.content)
        .then(() => showToast('Contenido copiado al portapapeles', 'success'))
        .catch(() => showToast('Error al copiar', 'error'));
}

// Descargar contenido
function downloadContent() {
    if (!state.currentGeneration) return;
    
    const blob = new Blob([state.currentGeneration.content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `article-${state.currentGeneration.id}.md`;
    a.click();
    URL.revokeObjectURL(url);
    
    showToast('Descarga iniciada', 'success');
}

// Cargar historial
async function loadHistory() {
    try {
        const data = await API.history(10, 0);
        const historyList = document.getElementById('historyList');

        if (data.total === 0) {
            historyList.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-inbox"></i>
                    <p>No hay generaciones aún</p>
                </div>
            `;
            return;
        }

        historyList.innerHTML = data.items.map(item => `
            <div class="history-item" data-id="${item.id}">
                <div class="history-item-header">
                    <h4>${item.topic}</h4>
                    <span class="history-item-date">${new Date(item.timestamp).toLocaleString()}</span>
                </div>
                <div class="history-item-meta">
                    <span class="badge">${item.strategy}</span>
                    <span>Score: ${item.seo_score.toFixed(1)}</span>
                    <span>Recompensa: ${item.reward.toFixed(3)}</span>
                </div>
                <div style="margin-top: 0.5rem; font-size: 0.875rem; color: var(--gray);">
                    <i class="fas fa-eye"></i> Click para ver contenido completo
                </div>
            </div>
        `).join('');

        // Agregar event listeners a cada item
        document.querySelectorAll('.history-item').forEach(item => {
            item.addEventListener('click', () => {
                const generationId = item.dataset.id;
                openHistoryModal(generationId);
            });
        });

    } catch (error) {
        showToast('Error cargando historial', 'error');
    }
}

// Cargar estadísticas
async function loadStats() {
    try {
        const data = await API.stats();
        state.stats = data;

        // Actualizar tarjetas con validaciones
        document.getElementById('statTotalGens').textContent = data.total_generations || 0;
        document.getElementById('statBestStrategy').textContent = (data.best_strategy && data.best_strategy.name) ? data.best_strategy.name : 'N/A';

        // avg_reward está dentro de reinforcement_learning
        const avgReward = data.reinforcement_learning && data.reinforcement_learning.avg_reward;
        document.getElementById('statAvgReward').textContent = avgReward ? avgReward.toFixed(3) : 'N/A';

        document.getElementById('statTotalTokens').textContent = data.total_tokens ? data.total_tokens.toLocaleString() : '0';

        // Actualizar tabla
        updateStrategyTable(data.strategy_performance);

        // Actualizar gráficas
        updateCharts(data);

    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Actualizar quick stats in sidebar
function updateQuickStats() {
    if (!state.stats) return;

    document.getElementById('quickTotalGens').textContent = state.stats.total_generations || 0;

    // Verificar si best_strategy existe
    if (state.stats.best_strategy && state.stats.best_strategy.name) {
        document.getElementById('quickBestStrategy').textContent = state.stats.best_strategy.name;
    } else {
        document.getElementById('quickBestStrategy').textContent = 'N/A';
    }

    // Calcular score promedio
    if (state.stats.strategy_performance && state.stats.strategy_performance.length > 0 && state.stats.total_generations > 0) {
        const avgScore = state.stats.strategy_performance.reduce((sum, s) =>
            sum + (s.avg_seo_score || 0) * (s.count || 0), 0) / state.stats.total_generations;
        document.getElementById('quickAvgScore').textContent = avgScore.toFixed(1);
    } else {
        document.getElementById('quickAvgScore').textContent = 'N/A';
    }
}

// Actualizar tabla de estrategias
function updateStrategyTable(performance) {
    const tbody = document.getElementById('strategyTableBody');

    if (!performance || performance.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" style="text-align: center; padding: 2rem; color: #6b7280;">
                    No hay datos aún. Genera contenido para ver estadísticas.
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = performance.map(strat => `
        <tr>
            <td><strong>${strat.name || 'N/A'}</strong></td>
            <td>${strat.count || 0}</td>
            <td>${strat.avg_reward ? strat.avg_reward.toFixed(3) : 'N/A'}</td>
            <td>${strat.avg_seo_score ? strat.avg_seo_score.toFixed(1) : 'N/A'}</td>
            <td>${strat.q_value ? strat.q_value.toFixed(3) : 'N/A'}</td>
        </tr>
    `).join('');
}

// Actualizar gráficas
function updateCharts(data) {
    // Verificar si Chart.js está disponible
    if (typeof Chart === 'undefined') {
        console.warn('Chart.js no está cargado. Las gráficas no se mostrarán.');
        const chartContainers = [document.getElementById('strategyChart'), document.getElementById('qvaluesChart')];
        chartContainers.forEach(canvas => {
            if (canvas) {
                const ctx = canvas.getContext('2d');
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                ctx.font = '14px system-ui';
                ctx.fillStyle = '#ef4444';
                ctx.textAlign = 'center';
                ctx.fillText('Error: Chart.js no se pudo cargar', canvas.width / 2, canvas.height / 2 - 10);
                ctx.fillStyle = '#6b7280';
                ctx.font = '12px system-ui';
                ctx.fillText('Verifica tu conexión a internet', canvas.width / 2, canvas.height / 2 + 10);
            }
        });
        return;
    }

    if (!data.strategy_performance || data.strategy_performance.length === 0) {
        // Mostrar mensaje cuando no hay datos
        const chartContainers = [document.getElementById('strategyChart'), document.getElementById('qvaluesChart')];
        chartContainers.forEach(canvas => {
            if (canvas) {
                const ctx = canvas.getContext('2d');
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                ctx.font = '16px system-ui';
                ctx.fillStyle = '#6b7280';
                ctx.textAlign = 'center';
                ctx.fillText('No hay datos para mostrar', canvas.width / 2, canvas.height / 2);
            }
        });
        return;
    }

    // Gráfica de rendimiento por estrategia
    const strategyCtx = document.getElementById('strategyChart').getContext('2d');

    if (window.strategyChart && typeof window.strategyChart.destroy === 'function') {
        window.strategyChart.destroy();
    }

    window.strategyChart = new Chart(strategyCtx, {
        type: 'bar',
        data: {
            labels: data.strategy_performance.map(s => s.name || 'N/A'),
            datasets: [{
                label: 'Recompensa Promedio',
                data: data.strategy_performance.map(s => s.avg_reward || 0),
                backgroundColor: 'rgba(99, 102, 241, 0.5)',
                borderColor: 'rgba(99, 102, 241, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 2,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 2
                    }
                },
                x: {
                    ticks: {
                        maxRotation: 45,
                        minRotation: 0
                    }
                }
            }
        }
    });

    // Gráfica de Q-values
    const qvaluesCtx = document.getElementById('qvaluesChart').getContext('2d');

    if (window.qvaluesChart && typeof window.qvaluesChart.destroy === 'function') {
        window.qvaluesChart.destroy();
    }

    const qValues = data.reinforcement_learning ? data.reinforcement_learning.q_values : [];
    const bestStrategyId = data.best_strategy ? data.best_strategy.id : -1;

    window.qvaluesChart = new Chart(qvaluesCtx, {
        type: 'bar',
        data: {
            labels: data.strategy_performance.map(s => s.name || 'N/A'),
            datasets: [{
                label: 'Q-Value',
                data: qValues,
                backgroundColor: qValues.map((_, i) =>
                    i === bestStrategyId ? 'rgba(239, 68, 68, 0.5)' : 'rgba(139, 92, 246, 0.5)'
                ),
                borderColor: qValues.map((_, i) =>
                    i === bestStrategyId ? 'rgba(239, 68, 68, 1)' : 'rgba(139, 92, 246, 1)'
                ),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            aspectRatio: 2,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 3
                    }
                },
                x: {
                    ticks: {
                        maxRotation: 45,
                        minRotation: 0
                    }
                }
            }
        }
    });
}

// Cargar estrategias
async function loadStrategies() {
    try {
        const data = await API.strategies();
        state.strategies = data.strategies;
        
        const grid = document.getElementById('strategiesGrid');
        grid.innerHTML = data.strategies.map(strat => `
            <div class="strategy-card">
                <h3>${strat.name}</h3>
                <span class="tone">Tono: ${strat.tone}</span>
                <p>${strat.description}</p>
                <h4>Mejor para:</h4>
                <ul>
                    ${strat.best_for.map(use => `<li>${use}</li>`).join('')}
                </ul>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Error loading strategies:', error);
    }
}

// Toast notifications
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const icon = type === 'success' ? 'check-circle' :
                 type === 'error' ? 'exclamation-circle' : 'info-circle';

    toast.innerHTML = `
        <i class="fas fa-${icon}"></i>
        <span>${message}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Modal para ver contenido del historial
async function openHistoryModal(generationId) {
    try {
        const generation = await API.getGeneration(generationId);

        // Crear modal
        const modalOverlay = document.createElement('div');
        modalOverlay.className = 'modal-overlay';

        modalOverlay.innerHTML = `
            <div class="modal">
                <div class="modal-header">
                    <h3>${generation.topic}</h3>
                    <button class="modal-close" onclick="closeModal()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    <div class="modal-info">
                        <div class="info-card">
                            <div class="info-label">Estrategia</div>
                            <div class="info-value" style="font-size: 1rem;">${generation.strategy_name}</div>
                        </div>
                        <div class="info-card">
                            <div class="info-label">Score SEO</div>
                            <div class="info-value score">${generation.seo_score ? generation.seo_score.toFixed(1) : 'N/A'}</div>
                        </div>
                        <div class="info-card">
                            <div class="info-label">CTR</div>
                            <div class="info-value">${generation.engagement_metrics && generation.engagement_metrics.ctr ? (generation.engagement_metrics.ctr * 100).toFixed(2) : 'N/A'}%</div>
                        </div>
                        <div class="info-card">
                            <div class="info-label">Posición</div>
                            <div class="info-value">#${generation.engagement_metrics && generation.engagement_metrics.search_position ? Math.round(generation.engagement_metrics.search_position) : 'N/A'}</div>
                        </div>
                        <div class="info-card">
                            <div class="info-label">Tiempo en Página</div>
                            <div class="info-value">${generation.engagement_metrics && generation.engagement_metrics.time_on_page ? Math.round(generation.engagement_metrics.time_on_page) : 'N/A'}s</div>
                        </div>
                        <div class="info-card">
                            <div class="info-label">Recompensa</div>
                            <div class="info-value">${generation.reward ? generation.reward.toFixed(3) : 'N/A'}</div>
                        </div>
                    </div>
                    <h4 style="margin-bottom: 1rem;">Contenido Generado:</h4>
                    <div class="modal-content" id="modalContentArea"></div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="copyModalContent('${generationId}')">
                        <i class="fas fa-copy"></i> Copiar
                    </button>
                    <button class="btn btn-secondary" onclick="downloadModalContent('${generationId}', '${generation.topic.replace(/'/g, "\\'")}')">
                        <i class="fas fa-download"></i> Descargar
                    </button>
                    <button class="btn btn-primary" onclick="closeModal()">
                        Cerrar
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(modalOverlay);

        // Renderizar contenido markdown
        const contentArea = document.getElementById('modalContentArea');
        if (typeof marked !== 'undefined') {
            contentArea.innerHTML = marked.parse(generation.content);
        } else {
            contentArea.textContent = generation.content;
        }

        // Guardar contenido en el modal para copiar/descargar
        modalOverlay.dataset.content = generation.content;

        // Cerrar modal al hacer click fuera
        modalOverlay.addEventListener('click', (e) => {
            if (e.target === modalOverlay) {
                closeModal();
            }
        });

        // Cerrar modal con tecla ESC
        const escHandler = (e) => {
            if (e.key === 'Escape') {
                closeModal();
                document.removeEventListener('keydown', escHandler);
            }
        };
        document.addEventListener('keydown', escHandler);

    } catch (error) {
        showToast('Error cargando contenido: ' + error.message, 'error');
    }
}

// Cerrar modal
function closeModal() {
    const modal = document.querySelector('.modal-overlay');
    if (modal) {
        modal.remove();
    }
}

// Copiar contenido del modal
function copyModalContent(generationId) {
    const modal = document.querySelector('.modal-overlay');
    if (!modal) return;

    const content = modal.dataset.content;
    navigator.clipboard.writeText(content)
        .then(() => showToast('Contenido copiado al portapapeles', 'success'))
        .catch(() => showToast('Error al copiar', 'error'));
}

// Descargar contenido del modal
function downloadModalContent(generationId, topic) {
    const modal = document.querySelector('.modal-overlay');
    if (!modal) return;

    const content = modal.dataset.content;
    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${topic.replace(/[^a-z0-9]/gi, '_')}-${generationId}.md`;
    a.click();
    URL.revokeObjectURL(url);

    showToast('Descarga iniciada', 'success');
}
