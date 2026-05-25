/**
 * dashboard.js — Lógica do dashboard de sentimentos
 * 
 * Responsável por:
 * - Configurar a tela de seleção inicial e capturar inputs de simulação
 * - Buscar dados da API Flask passando parâmetros de simulação
 * - Alternar abas do painel (Tabs) e gerenciar estados visuais
 * - Renderizar gráficos Chart.js gerais e dinâmicos específicos por categoria
 * - Controlar a exibição progressiva ("Carregar Mais") de listas e tabelas
 * - Implementar filtros locais reativos
 */

// ── Estado Global ──────────────────────────────────────────────────────
let dadosOriginais = null;      // Dados completos recebidos da API
let chartSentimentos = null;    // Instância Chart.js - Doughnut
let chartEmocoes = null;        // Instância Chart.js - Bar
let chartEvolucao = null;       // Instância Chart.js - Line
let chartCustom1 = null;        // Instância Chart.js - Custom 1
let chartCustom2 = null;        // Instância Chart.js - Custom 2

let categoriaSelecionada = null; // Categoria atual (playstore, youtube, etc)

// Controles locais de paginação ("Carregar Mais")
let posComentariosExibidos = 5;
let negComentariosExibidos = 5;
let tabelaExibida = 10;

const NOMES_CATEGORIAS = {
    playstore: { 
        nome: 'Google Play Store', 
        emoji: '📱', 
        targetLabel: 'ID do Pacote (ex: com.whatsapp)', 
        targetPlaceholder: 'com.whatsapp',
        keyLabel: 'API Key do Console Google Play',
        keyPlaceholder: 'AIzaSy...'
    },
    youtube: { 
        nome: 'YouTube Canais', 
        emoji: '📺', 
        targetLabel: 'URL do Vídeo ou Canal', 
        targetPlaceholder: 'https://youtube.com/watch?v=...',
        keyLabel: 'API Key do YouTube Data v3',
        keyPlaceholder: 'AIzaSy...'
    },
    instagram: { 
        nome: 'Instagram Posts', 
        emoji: '📸', 
        targetLabel: 'Hashtag ou Link do Post', 
        targetPlaceholder: '#devlife',
        keyLabel: 'Meta Graph Access Token',
        keyPlaceholder: 'EAACW...'
    },
    amazon: { 
        nome: 'Amazon E-commerce', 
        emoji: '📦', 
        targetLabel: 'ASIN do Produto (ex: B08N5WRWNW)', 
        targetPlaceholder: 'B08N5WRWNW',
        keyLabel: 'Amazon PA-API Key',
        keyPlaceholder: 'AKIAI...'
    }
};

// ── Cores Globais ──────────────────────────────────────────────────────
const CORES = {
    positivo: '#4ade80',
    negativo: '#f87171',
    neutro: '#fbbf24',
    positivo_bg: 'rgba(74, 222, 128, 0.15)',
    negativo_bg: 'rgba(248, 113, 113, 0.15)',
    neutro_bg: 'rgba(251, 191, 36, 0.15)',
};

const CORES_EMOCOES = {
    satisfacao: '#4ade80',
    frustracao: '#f87171',
    raiva: '#ef4444',
    confianca: '#60a5fa',
    duvida: '#fbbf24',
    surpresa: '#a78bfa',
    gratidao: '#34d399',
    decepcao: '#fb923c',
    indefinido: '#94a3b8',
};

// Configuração Global Chart.js
Chart.defaults.color = '#94a3b8';
Chart.defaults.borderColor = 'rgba(148, 163, 184, 0.08)';
Chart.defaults.font.family = "'Inter', sans-serif";

// ── Inicialização ─────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    inicializarTelaSelecao();
    configurarAbas();
    configurarFiltros();
    configurarRetry();
    configurarCarregarMais();
    inicializarSandbox();
});

/**
 * Configura os ouvintes de evento da tela de seleção de categoria.
 */
function inicializarTelaSelecao() {
    const cards = document.querySelectorAll('.category-card');
    const simCard = document.getElementById('simulation-inputs-card');
    const btnStart = document.getElementById('btn-start-analysis');
    const btnClearCache = document.getElementById('btn-clear-global-cache');
    const btnBack = document.getElementById('btn-back-to-selection');
    const btnErrorBack = document.getElementById('btn-error-back');

    cards.forEach(card => {
        card.addEventListener('click', () => {
            // Remove seleção anterior
            cards.forEach(c => c.classList.remove('selected'));
            
            // Adiciona seleção ao atual
            card.classList.add('selected');
            categoriaSelecionada = card.dataset.category;

            // Mostra inputs de simulação com textos específicos
            const info = NOMES_CATEGORIAS[categoriaSelecionada];
            
            document.getElementById('sim-title').textContent = `Configurar Integração com ${info.nome}`;
            document.getElementById('lbl-sim-target').textContent = info.targetLabel;
            document.getElementById('sim-target').placeholder = info.targetPlaceholder;
            document.getElementById('sim-target').value = '';
            document.getElementById('lbl-sim-key').textContent = info.keyLabel;
            document.getElementById('sim-key').placeholder = info.keyPlaceholder;
            document.getElementById('sim-key').value = '';
            
            simCard.classList.remove('hidden');

            // Ativa botão de envio
            btnStart.disabled = false;
            btnStart.textContent = `Iniciar Análise para ${info.nome}`;
            btnStart.classList.add('glow');
        });
    });

    btnStart.addEventListener('click', () => {
        if (categoriaSelecionada) {
            carregarDados(categoriaSelecionada);
        }
    });

    btnClearCache.addEventListener('click', async () => {
        if (confirm('Deseja realmente limpar todos os caches (em memória e banco de dados SQLite)? Isso forçará novas chamadas à IA.')) {
            try {
                const response = await fetch('/api/limpar-cache', { method: 'POST' });
                const res = await response.json();
                alert(res.mensagem || res.erro);
            } catch (error) {
                alert('Erro ao limpar cache: ' + error.message);
            }
        }
    });

    btnBack.addEventListener('click', voltarParaSelecao);
    btnErrorBack.addEventListener('click', voltarParaSelecao);
}

/**
 * Configura as abas de navegação do dashboard.
 */
function configurarAbas() {
    const tabButtons = document.querySelectorAll('.tab-button');
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            tabButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');

            const targetPaneId = button.dataset.tab;
            const panes = document.querySelectorAll('.tab-pane');
            panes.forEach(pane => {
                if (pane.id === targetPaneId) {
                    pane.classList.remove('hidden');
                } else {
                    pane.classList.add('hidden');
                }
            });
        });
    });
}

/**
 * Configura botões de carregamento progressivo local ("Carregar Mais").
 */
function configurarCarregarMais() {
    document.getElementById('btn-load-more-pos').addEventListener('click', () => {
        posComentariosExibidos += 5;
        aplicarFiltros();
    });
    
    document.getElementById('btn-load-more-neg').addEventListener('click', () => {
        negComentariosExibidos += 5;
        aplicarFiltros();
    });

    document.getElementById('btn-load-more-table').addEventListener('click', () => {
        tabelaExibida += 10;
        aplicarFiltros();
    });
}

/**
 * Retorna para a tela de seleção inicial de categoria.
 */
function voltarParaSelecao() {
    mostrarDashboard(false);
    mostrarErro(false);
    limparFiltros();

    // Reset abas para geral ativa
    const tabButtons = document.querySelectorAll('.tab-button');
    tabButtons.forEach(btn => btn.classList.remove('active'));
    tabButtons[0].classList.add('active');
    document.getElementById('tab-geral').classList.remove('hidden');
    document.getElementById('tab-custom').classList.add('hidden');
    document.getElementById('tab-feed').classList.add('hidden');
    document.getElementById('tab-sandbox').classList.add('hidden');

    // Reset Sandbox elements
    const textarea = document.getElementById('sandbox-textarea');
    if (textarea) textarea.value = '';
    const resultCard = document.getElementById('sandbox-result-card');
    if (resultCard) resultCard.classList.add('hidden');
    const loadingCard = document.getElementById('sandbox-loading');
    if (loadingCard) loadingCard.classList.add('hidden');

    const selectionScreen = document.getElementById('category-selection-screen');
    selectionScreen.classList.remove('hidden');

    // Reset classes de tema e inputs
    document.body.className = '';
    
    const cards = document.querySelectorAll('.category-card');
    cards.forEach(c => c.classList.remove('selected'));
    
    document.getElementById('simulation-inputs-card').classList.add('hidden');
    
    const btnStart = document.getElementById('btn-start-analysis');
    btnStart.disabled = true;
    btnStart.textContent = 'Selecione uma categoria primeiro';
    btnStart.classList.remove('glow');
    
    categoriaSelecionada = null;
    dadosOriginais = null;
}

/**
 * Busca os dados processados da API Flask para a categoria informada,
 * passando os parâmetros simulados de conexão.
 */
async function carregarDados(categoria) {
    document.getElementById('category-selection-screen').classList.add('hidden');
    mostrarErro(false);
    
    // Captura inputs de simulação
    const targetIdVal = document.getElementById('sim-target').value;
    const apiKeyVal = document.getElementById('sim-key').value;
    
    // Configura classe de tema do Body
    document.body.className = 'theme-' + categoria;

    // Reset pagination counters
    posComentariosExibidos = 5;
    negComentariosExibidos = 5;
    tabelaExibida = 10;
    
    // Progress Checklist
    atualizarProgresso(0, 'step-load', 'Carregando base de dados JSON...');
    mostrarLoading(true);

    try {
        await delay(300);
        atualizarProgresso(25, 'step-cache', 'Consultando cache local SQLite...');
        
        // Monta URL com parâmetros de simulação
        const url = `/api/dados/${categoria}?target_id=${encodeURIComponent(targetIdVal)}&api_key=${encodeURIComponent(apiKeyVal)}`;
        const response = await fetch(url);
        
        await delay(300);
        atualizarProgresso(50, 'step-ai', 'Processando novos comentários com IA...');
        
        const dados = await response.json();

        if (dados.erro) {
            throw new Error(dados.erro);
        }

        await delay(300);
        atualizarProgresso(85, 'step-stats', 'Calculando estatísticas e renderizando...');
        
        await delay(200);
        atualizarProgresso(100, '', 'Finalizado!');
        await delay(100);

        dadosOriginais = dados;
        
        // Configura títulos do cabeçalho do Dashboard
        const infoCat = NOMES_CATEGORIAS[categoria];
        document.getElementById('dashboard-category-name').textContent = infoCat.nome;
        document.getElementById('dashboard-category-icon').textContent = infoCat.emoji;

        // Renderiza tudo
        renderizarDashboard(dados);
        renderizarBannerPerformance(dados.performance);

        mostrarLoading(false);
        mostrarDashboard(true);

    } catch (error) {
        console.error('Erro ao carregar dados:', error);
        mostrarLoading(false);
        mostrarErro(true, error.message);
    }
}

/**
 * Renderiza o banner de otimização de performance.
 */
function renderizarBannerPerformance(perf) {
    const banner = document.getElementById('performance-banner');
    if (!perf || perf.total_comentarios === 0) {
        banner.classList.add('hidden');
        return;
    }

    banner.classList.remove('hidden');
    
    // Preenche estatísticas
    document.getElementById('perf-time').textContent = `${perf.tempo_execucao_ms} ms`;
    
    const percCache = ((perf.comentarios_do_cache / perf.total_comentarios) * 100).toFixed(0);
    document.getElementById('perf-cache-count').textContent = `${perf.comentarios_do_cache}/${perf.total_comentarios} (${percCache}%)`;
    document.getElementById('perf-ia-count').textContent = perf.comentarios_da_ia;

    // Economia estimada: 15s por lote de 25 comentários processados na IA
    const lotesSalvos = Math.ceil(perf.comentarios_do_cache / 25);
    const economiaSegundos = lotesSalvos * 15;
    
    const savingText = document.getElementById('perf-saving');
    savingText.textContent = `${economiaSegundos} s`;
}

/**
 * Atualiza o painel e barra de progresso.
 */
function atualizarProgresso(porcentagem, activeStepId, logMsg) {
    document.getElementById('progress-bar-fill').style.width = `${porcentagem}%`;
    document.getElementById('loading-log').textContent = logMsg;

    const steps = ['step-load', 'step-cache', 'step-ai', 'step-stats'];
    let stepEncontrado = false;

    steps.forEach(stepId => {
        const el = document.getElementById(stepId);
        if (!el) return;

        if (stepId === activeStepId) {
            el.className = 'step-item active';
            el.querySelector('.step-status-icon').textContent = '🔵';
            stepEncontrado = true;
        } else if (!stepEncontrado && activeStepId !== '') {
            el.className = 'step-item completed';
            el.querySelector('.step-status-icon').textContent = '✅';
        } else {
            el.className = 'step-item';
            el.querySelector('.step-status-icon').textContent = '⚪';
        }
    });

    if (porcentagem === 100) {
        steps.forEach(stepId => {
            const el = document.getElementById(stepId);
            if (el) {
                el.className = 'step-item completed';
                el.querySelector('.step-status-icon').textContent = '✅';
            }
        });
    }
}

function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// ── Controle de Visibilidade ──────────────────────────────────────────
function mostrarLoading(visivel) {
    const overlay = document.getElementById('loading-overlay');
    if (visivel) {
        overlay.classList.remove('fade-out', 'hidden');
    } else {
        overlay.classList.add('fade-out');
        setTimeout(() => overlay.classList.add('hidden'), 400);
    }
}

function mostrarErro(visivel, mensagem = '') {
    const errorState = document.getElementById('error-state');
    const errorMsg = document.getElementById('error-message');
    if (visivel) {
        errorState.classList.remove('hidden');
        errorMsg.textContent = mensagem;
    } else {
        errorState.classList.add('hidden');
    }
}

function mostrarDashboard(visivel) {
    const dashboard = document.getElementById('main-dashboard');
    if (visivel) {
        dashboard.classList.remove('hidden');
    } else {
        dashboard.classList.add('hidden');
    }
}

// ── Renderização Principal ────────────────────────────────────────────
function renderizarDashboard(dados) {
    const { avaliacoes, estatisticas } = dados;

    renderizarKPIs(estatisticas);
    renderizarGraficoSentimentos(estatisticas.contagem_sentimentos);
    renderizarGraficoEmocoes(estatisticas.contagem_emocoes);
    renderizarGraficoEvolucao(estatisticas.evolucao_por_data);
    renderizarPontosRecorrentes(estatisticas);
    renderizarComentariosRepresentativos(avaliacoes);
    renderizarTabela(avaliacoes);
    popularFiltroEmocoes(estatisticas.contagem_emocoes);
    
    // Renderiza gráficos dinâmicos específicos da plataforma
    renderizarGraficosEspecificos(estatisticas, categoriaSelecionada);
}

// ── KPI Cards ─────────────────────────────────────────────────────────
function renderizarKPIs(estatisticas) {
    document.getElementById('kpi-total-valor').textContent = estatisticas.total_avaliacoes;
    document.getElementById('kpi-media-valor').textContent = estatisticas.media_estrelas.toFixed(1);
    
    const sentimentos = estatisticas.contagem_sentimentos;
    document.getElementById('kpi-positivo-valor').textContent = sentimentos.positivo || 0;
    document.getElementById('kpi-negativo-valor').textContent = sentimentos.negativo || 0;
    document.getElementById('kpi-neutro-valor').textContent = sentimentos.neutro || 0;
}

// ── Gráfico de Sentimentos (Doughnut) ─────────────────────────────────
function renderizarGraficoSentimentos(contagem) {
    const ctx = document.getElementById('grafico-sentimentos').getContext('2d');

    if (chartSentimentos) chartSentimentos.destroy();

    const labels = ['Positivo', 'Negativo', 'Neutro'];
    const valores = [contagem.positivo || 0, contagem.negativo || 0, contagem.neutro || 0];

    chartSentimentos = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: valores,
                backgroundColor: [CORES.positivo, CORES.negativo, CORES.neutro],
                borderWidth: 2,
                borderColor: '#111827',
                hoverOffset: 4,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '68%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 16,
                        usePointStyle: true,
                        pointStyleWidth: 10,
                        font: { size: 12, weight: '500' },
                    },
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.9)',
                    padding: 12,
                    cornerRadius: 8,
                    callbacks: {
                        label: (ctx) => {
                            const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                            const pct = total > 0 ? ((ctx.raw / total) * 100).toFixed(1) : 0;
                            return ` ${ctx.label}: ${ctx.raw} (${pct}%)`;
                        },
                    },
                },
            },
            animation: {
                animateRotate: true,
                duration: 800,
            },
        },
    });
}

// ── Gráfico de Emoções (Bar Horizontal) ───────────────────────────────
function renderizarGraficoEmocoes(contagem) {
    const ctx = document.getElementById('grafico-emocoes').getContext('2d');

    if (chartEmocoes) chartEmocoes.destroy();

    const labels = Object.keys(contagem);
    const valores = Object.values(contagem);
    const cores = labels.map(l => CORES_EMOCOES[l] || '#94a3b8');

    chartEmocoes = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels.map(l => l.charAt(0).toUpperCase() + l.slice(1)),
            datasets: [{
                label: 'Quantidade',
                data: valores,
                backgroundColor: cores.map(c => c + '40'),
                borderColor: cores,
                borderWidth: 1.5,
                borderRadius: 6,
                barPercentage: 0.7,
            }],
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.9)',
                    padding: 12,
                    cornerRadius: 8,
                },
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1,
                        font: { size: 12 },
                    },
                    grid: {
                        color: 'rgba(148, 163, 184, 0.06)',
                    },
                },
                y: {
                    ticks: {
                        font: { size: 12, weight: '500' },
                    },
                    grid: { display: false },
                },
            },
            animation: {
                duration: 800,
                delay: (ctx) => ctx.dataIndex * 80,
            },
        },
    });
}

// ── Gráfico de Evolução (Line) ────────────────────────────────────────
function renderizarGraficoEvolucao(evolucao) {
    const ctx = document.getElementById('grafico-evolucao').getContext('2d');

    if (chartEvolucao) chartEvolucao.destroy();

    const labels = evolucao.map(e => {
        const [year, month, day] = e.data.split('-');
        return `${day}/${month}`;
    });

    chartEvolucao = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Positivo',
                    data: evolucao.map(e => e.positivo),
                    borderColor: CORES.positivo,
                    backgroundColor: CORES.positivo + '10',
                    tension: 0.35,
                    borderWidth: 2.5,
                    pointRadius: 3,
                    pointBackgroundColor: CORES.positivo,
                    fill: true,
                },
                {
                    label: 'Negativo',
                    data: evolucao.map(e => e.negativo),
                    borderColor: CORES.negativo,
                    backgroundColor: CORES.negativo + '10',
                    tension: 0.35,
                    borderWidth: 2.5,
                    pointRadius: 3,
                    pointBackgroundColor: CORES.negativo,
                    fill: true,
                },
                {
                    label: 'Neutro',
                    data: evolucao.map(e => e.neutro),
                    borderColor: CORES.neutro,
                    backgroundColor: CORES.neutro + '10',
                    tension: 0.35,
                    borderWidth: 2.5,
                    pointRadius: 3,
                    pointBackgroundColor: CORES.neutro,
                    fill: true,
                }
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        padding: 16,
                        usePointStyle: true,
                        pointStyleWidth: 12,
                        font: { size: 12, weight: '500' },
                    },
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.9)',
                    padding: 12,
                    cornerRadius: 8,
                },
            },
            scales: {
                x: {
                    ticks: { font: { size: 11 } },
                    grid: { color: 'rgba(148, 163, 184, 0.06)' },
                },
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1,
                        font: { size: 12 },
                    },
                    grid: { color: 'rgba(148, 163, 184, 0.06)' },
                },
            },
            animation: { duration: 1000 },
        },
    });
}

// ── Gráficos Exclusivos por Categoria ───────────────────────────────
function renderizarGraficosEspecificos(estatisticas, categoria) {
    const title1 = document.getElementById('custom-chart-title-1');
    const title2 = document.getElementById('custom-chart-title-2');
    
    const ctx1 = document.getElementById('grafico-custom-1').getContext('2d');
    const ctx2 = document.getElementById('grafico-custom-2').getContext('2d');

    if (chartCustom1) chartCustom1.destroy();
    if (chartCustom2) chartCustom2.destroy();

    const metrics = estatisticas.metricas_plataforma;

    if (categoria === 'playstore') {
        title1.textContent = 'Média de Estrelas por Versão do App';
        title2.textContent = 'Sentimentos por Versão do Android';

        const versoes = Object.keys(metrics.sentimento_por_versao);
        const estrelas = versoes.map(v => metrics.sentimento_por_versao[v].media_estrelas);
        const totais = versoes.map(v => metrics.sentimento_por_versao[v].total);

        // Chart 1: Bar & Line combinados (Média de estrelas por Versão)
        chartCustom1 = new Chart(ctx1, {
            type: 'bar',
            data: {
                labels: versoes,
                datasets: [
                    {
                        type: 'line',
                        label: 'Média de Estrelas',
                        data: estrelas,
                        borderColor: '#60a5fa',
                        borderWidth: 2,
                        fill: false,
                        yAxisID: 'y-estrelas',
                        pointRadius: 4
                    },
                    {
                        label: 'Quantidade de Reviews',
                        data: totais,
                        backgroundColor: 'rgba(16, 185, 129, 0.2)',
                        borderColor: '#10b981',
                        borderWidth: 1.5,
                        yAxisID: 'y-reviews',
                        borderRadius: 4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    'y-estrelas': {
                        type: 'linear',
                        position: 'left',
                        min: 1,
                        max: 5,
                        title: { display: true, text: 'Estrelas' }
                    },
                    'y-reviews': {
                        type: 'linear',
                        position: 'right',
                        beginAtZero: true,
                        grid: { drawOnChartArea: false },
                        title: { display: true, text: 'Frequência' }
                    }
                }
            }
        });

        // Chart 2: Stacked Bar de sentimentos por Android OS
        const osList = Object.keys(metrics.sentimento_por_android);
        chartCustom2 = new Chart(ctx2, {
            type: 'bar',
            data: {
                labels: osList,
                datasets: [
                    {
                        label: 'Positivo',
                        data: osList.map(os => metrics.sentimento_por_android[os].positivo || 0),
                        backgroundColor: CORES.positivo
                    },
                    {
                        label: 'Neutro',
                        data: osList.map(os => metrics.sentimento_por_android[os].neutro || 0),
                        backgroundColor: CORES.neutro
                    },
                    {
                        label: 'Negativo',
                        data: osList.map(os => metrics.sentimento_por_android[os].negativo || 0),
                        backgroundColor: CORES.negativo
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { stacked: true },
                    y: { stacked: true, beginAtZero: true }
                }
            }
        });

    } else if (categoria === 'youtube') {
        title1.textContent = 'Distribuição de Sentimentos por Duração do Vídeo';
        title2.textContent = 'Sentimentos por Tema do Vídeo';

        const faixas = Object.keys(metrics.sentimento_por_duracao);
        const temas = Object.keys(metrics.sentimento_por_tema);

        // Chart 1: Stacked Bar por Duração
        chartCustom1 = new Chart(ctx1, {
            type: 'bar',
            data: {
                labels: faixas,
                datasets: [
                    {
                        label: 'Positivo',
                        data: faixas.map(f => metrics.sentimento_por_duracao[f].positivo || 0),
                        backgroundColor: CORES.positivo
                    },
                    {
                        label: 'Neutro',
                        data: faixas.map(f => metrics.sentimento_por_duracao[f].neutro || 0),
                        backgroundColor: CORES.neutro
                    },
                    {
                        label: 'Negativo',
                        data: faixas.map(f => metrics.sentimento_por_duracao[f].negativo || 0),
                        backgroundColor: CORES.negativo
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { stacked: true },
                    y: { stacked: true, beginAtZero: true }
                }
            }
        });

        // Chart 2: Temas de Vídeo (Horizontal Stacked Bar)
        chartCustom2 = new Chart(ctx2, {
            type: 'bar',
            data: {
                labels: temas,
                datasets: [
                    {
                        label: 'Positivo',
                        data: temas.map(t => metrics.sentimento_por_tema[t].positivo || 0),
                        backgroundColor: CORES.positivo
                    },
                    {
                        label: 'Neutro',
                        data: temas.map(t => metrics.sentimento_por_tema[t].neutro || 0),
                        backgroundColor: CORES.neutro
                    },
                    {
                        label: 'Negativo',
                        data: temas.map(t => metrics.sentimento_por_tema[t].negativo || 0),
                        backgroundColor: CORES.negativo
                    }
                ]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { stacked: true },
                    y: { stacked: true }
                }
            }
        });

    } else if (categoria === 'instagram') {
        title1.textContent = 'Comparação de Sentimento: Reels vs Feed Post';
        title2.textContent = 'Popularidade de Hashtags no Engajamento';

        const midias = Object.keys(metrics.sentimento_por_midia);
        const tags = Object.keys(metrics.sentimento_por_hashtag);

        // Chart 1: Comparative Bar
        chartCustom1 = new Chart(ctx1, {
            type: 'bar',
            data: {
                labels: midias.map(m => m === 'reels' ? '🎬 Reels' : '🖼️ Feed Post'),
                datasets: [
                    {
                        label: 'Positivo',
                        data: midias.map(m => metrics.sentimento_por_midia[m].positivo || 0),
                        backgroundColor: CORES.positivo
                    },
                    {
                        label: 'Neutro',
                        data: midias.map(m => metrics.sentimento_por_midia[m].neutro || 0),
                        backgroundColor: CORES.neutro
                    },
                    {
                        label: 'Negativo',
                        data: midias.map(m => metrics.sentimento_por_midia[m].negativo || 0),
                        backgroundColor: CORES.negativo
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });

        // Chart 2: Horizontal Bar (Frequência Hashtags)
        chartCustom2 = new Chart(ctx2, {
            type: 'bar',
            data: {
                labels: tags,
                datasets: [{
                    label: 'Número de Menções',
                    data: tags.map(t => metrics.sentimento_por_hashtag[t].total),
                    backgroundColor: 'rgba(168, 85, 247, 0.4)',
                    borderColor: '#a855f7',
                    borderWidth: 1.5,
                    borderRadius: 4
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } }
            }
        });

    } else if (categoria === 'amazon') {
        title1.textContent = 'Prazo Médio de Entrega por Estrelas (Dias)';
        title2.textContent = 'Sentimentos Associados ao Estado da Embalagem';

        const estrelasLabels = ['1 ⭐', '2 ⭐', '3 ⭐', '4 ⭐', '5 ⭐'];
        const dias = [1, 2, 3, 4, 5].map(est => metrics.media_entrega_por_estrelas[String(est)] || 0);
        
        const embalagens = Object.keys(metrics.sentimento_embalagem);

        // Chart 1: Line Chart (Dias de Entrega vs Avaliação)
        chartCustom1 = new Chart(ctx1, {
            type: 'line',
            data: {
                labels: estrelasLabels,
                datasets: [{
                    label: 'Dias de Entrega Médios',
                    data: dias,
                    borderColor: '#f97316',
                    backgroundColor: 'rgba(249, 115, 22, 0.1)',
                    borderWidth: 2.5,
                    tension: 0.2,
                    pointRadius: 4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { 
                        beginAtZero: true,
                        title: { display: true, text: 'Dias Úteis' }
                    }
                }
            }
        });

        // Chart 2: Doughnut / Stacked Bar (Qualidade de Embalagem)
        chartCustom2 = new Chart(ctx2, {
            type: 'bar',
            data: {
                labels: embalagens.map(emb => emb.charAt(0).toUpperCase() + emb.slice(1)),
                datasets: [
                    {
                        label: 'Positivo',
                        data: embalagens.map(emb => metrics.sentimento_embalagem[emb].positivo || 0),
                        backgroundColor: CORES.positivo
                    },
                    {
                        label: 'Neutro',
                        data: embalagens.map(emb => metrics.sentimento_embalagem[emb].neutro || 0),
                        backgroundColor: CORES.neutro
                    },
                    {
                        label: 'Negativo',
                        data: embalagens.map(emb => metrics.sentimento_embalagem[emb].negativo || 0),
                        backgroundColor: CORES.negativo
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { stacked: true },
                    y: { stacked: true }
                }
            }
        });
    }
}

// ── Pontos Recorrentes ────────────────────────────────────────────────
function renderizarPontosRecorrentes(estatisticas) {
    const listaPos = document.getElementById('lista-pontos-positivos');
    const listaNeg = document.getElementById('lista-pontos-negativos');

    listaPos.innerHTML = estatisticas.pontos_positivos_recorrentes.length
        ? estatisticas.pontos_positivos_recorrentes.map(p =>
            `<li>
                <span>${p.ponto}</span>
                <span class="points-badge">${p.frequencia}x</span>
            </li>`
        ).join('')
        : '<li style="color: var(--text-muted)">Nenhum ponto positivo identificado</li>';

    listaNeg.innerHTML = estatisticas.pontos_negativos_recorrentes.length
        ? estatisticas.pontos_negativos_recorrentes.map(p =>
            `<li>
                <span>${p.ponto}</span>
                <span class="points-badge">${p.frequencia}x</span>
            </li>`
        ).join('')
        : '<li style="color: var(--text-muted)">Nenhum ponto negativo identificado</li>';
}

// ── Comentários Representativos (Com paginação "Mostrar Mais") ────────
function renderizarComentariosRepresentativos(avaliacoes) {
    // Filtra positivos e ordena por confiança
    const positivos = avaliacoes
        .filter(a => a.analise.sentimento === 'positivo')
        .sort((a, b) => b.analise.confianca - a.analise.confianca);

    // Filtra negativos e ordena por criticidade
    const negativos = avaliacoes
        .filter(a => a.analise.sentimento === 'negativo')
        .sort((a, b) => {
            const prioridade = { alto: 3, medio: 2, baixo: 1 };
            return (prioridade[b.analise.nivel_criticidade] || 0) -
                   (prioridade[a.analise.nivel_criticidade] || 0);
        });

    const containerPos = document.getElementById('comentarios-positivos');
    const containerNeg = document.getElementById('comentarios-negativos');

    // Exibe fatias baseadas no contador de exibição
    const visiveisPos = positivos.slice(0, posComentariosExibidos);
    const visiveisNeg = negativos.slice(0, negComentariosExibidos);

    containerPos.innerHTML = visiveisPos.map(a => criarCardComentario(a, 'positivo')).join('');
    containerNeg.innerHTML = visiveisNeg.map(a => criarCardComentario(a, 'negativo')).join('');

    // Ajusta visibilidade do botão de Carregar Mais Positivos
    const btnPos = document.getElementById('btn-load-more-pos');
    if (positivos.length > posComentariosExibidos) {
        btnPos.classList.remove('hidden');
        btnPos.textContent = `Mostrar Mais Positivos (+${Math.min(5, positivos.length - posComentariosExibidos)})`;
    } else {
        btnPos.classList.add('hidden');
    }

    // Ajusta visibilidade do botão de Carregar Mais Negativos
    const btnNeg = document.getElementById('btn-load-more-neg');
    if (negativos.length > negComentariosExibidos) {
        btnNeg.classList.remove('hidden');
        btnNeg.textContent = `Mostrar Mais Críticos (+${Math.min(5, negativos.length - negComentariosExibidos)})`;
    } else {
        btnNeg.classList.add('hidden');
    }
}

function criarCardComentario(avaliacao, tipo) {
    const estrelas = '★'.repeat(avaliacao.estrelas) + '☆'.repeat(5 - avaliacao.estrelas);
    return `
        <div class="comment-card comment-card-${tipo}">
            <div class="comment-header">
                <span class="comment-user">${avaliacao.usuario}</span>
                <span class="comment-stars">${estrelas}</span>
            </div>
            <p class="comment-text">"${avaliacao.comentario}"</p>
            <p class="comment-summary">📌 ${avaliacao.analise.resumo}</p>
        </div>
    `;
}

// ── Tabela de Avaliações (Com paginação "Carregar Mais") ──────────────
function renderizarTabela(avaliacoes) {
    const tbody = document.getElementById('tbody-avaliacoes');
    
    // Fatia de acordo com a paginação da tabela
    const visiveis = avaliacoes.slice(0, tabelaExibida);

    tbody.innerHTML = visiveis.map(a => {
        const estrelas = '★'.repeat(a.estrelas) + '☆'.repeat(5 - a.estrelas);
        const dataFormatada = new Date(a.data + 'T12:00:00').toLocaleDateString('pt-BR');

        return `
            <tr>
                <td>${a.usuario}</td>
                <td style="color: #fbbf24">${estrelas}</td>
                <td class="td-comentario" title="${a.comentario}">${a.comentario}</td>
                <td><span class="badge badge-${a.analise.sentimento}">${a.analise.sentimento}</span></td>
                <td>${a.analise.emocao}</td>
                <td><span class="badge badge-${a.analise.nivel_criticidade}">${a.analise.nivel_criticidade}</span></td>
                <td>${dataFormatada}</td>
            </tr>
        `;
    }).join('');

    // Ajusta botão de Carregar Mais Tabela
    const btnTable = document.getElementById('btn-load-more-table');
    if (avaliacoes.length > tabelaExibida) {
        btnTable.classList.remove('hidden');
        btnTable.textContent = `Carregar Mais Avaliações (+${Math.min(10, avaliacoes.length - tabelaExibida)})`;
    } else {
        btnTable.classList.add('hidden');
    }
}

// ── Filtros ───────────────────────────────────────────────────────────
function configurarFiltros() {
    document.getElementById('filtro-data-inicio').addEventListener('change', aplicarFiltros);
    document.getElementById('filtro-data-fim').addEventListener('change', aplicarFiltros);
    document.getElementById('filtro-sentimento').addEventListener('change', aplicarFiltros);
    document.getElementById('filtro-emocao').addEventListener('change', aplicarFiltros);
    document.getElementById('btn-limpar-filtros').addEventListener('click', limparFiltros);
}

function configurarRetry() {
    document.getElementById('btn-retry').addEventListener('click', () => {
        mostrarErro(false);
        if (categoriaSelecionada) {
            carregarDados(categoriaSelecionada);
        }
    });
}

function popularFiltroEmocoes(contagemEmocoes) {
    const select = document.getElementById('filtro-emocao');
    
    // Reseta select para ter apenas "Todas"
    select.innerHTML = '<option value="todos">Todas</option>';
    
    const opcoes = Object.keys(contagemEmocoes).sort((a, b) => a.localeCompare(b, 'pt-BR'));
    opcoes.forEach(emocao => {
        const option = document.createElement('option');
        option.value = emocao;
        option.textContent = emocao.charAt(0).toUpperCase() + emocao.slice(1);
        select.appendChild(option);
    });
}

function aplicarFiltros() {
    if (!dadosOriginais) return;

    const dataInicio = document.getElementById('filtro-data-inicio').value;
    const dataFim = document.getElementById('filtro-data-fim').value;
    const sentimento = document.getElementById('filtro-sentimento').value;
    const emocao = document.getElementById('filtro-emocao').value;

    let filtradas = [...dadosOriginais.avaliacoes];

    // Filtro por data início
    if (dataInicio) {
        filtradas = filtradas.filter(a => a.data >= dataInicio);
    }

    // Filtro por data fim
    if (dataFim) {
        filtradas = filtradas.filter(a => a.data <= dataFim);
    }

    // Filtro por sentimento
    if (sentimento !== 'todos') {
        filtradas = filtradas.filter(a => a.analise.sentimento === sentimento);
    }

    // Filtro por emoção
    if (emocao !== 'todos') {
        filtradas = filtradas.filter(a => a.analise.emocao === emocao);
    }

    // Recalcular estatísticas localmente para os dados filtrados
    const estatisticasFiltradas = calcularEstatisticasLocal(filtradas);

    // Re-renderizar com dados filtrados (respeitando paginação ativa)
    renderizarKPIs(estatisticasFiltradas);
    renderizarGraficoSentimentos(estatisticasFiltradas.contagem_sentimentos);
    renderizarGraficoEmocoes(estatisticasFiltradas.contagem_emocoes);
    renderizarGraficoEvolucao(estatisticasFiltradas.evolucao_por_data);
    renderizarPontosRecorrentes(estatisticasFiltradas);
    renderizarComentariosRepresentativos(filtradas);
    renderizarTabela(filtradas);
    
    // Atualizar gráficos customizados
    renderizarGraficosEspecificos(estatisticasFiltradas, categoriaSelecionada);
}

/**
 * Calcula estatísticas no frontend para os dados filtrados.
 * Evita fazer nova requisição ao backend ao aplicar filtros.
 */
function calcularEstatisticasLocal(avaliacoes) {
    const total = avaliacoes.length;
    const mediaEstrelas = total > 0
        ? avaliacoes.reduce((sum, a) => sum + a.estrelas, 0) / total
        : 0;

    const contagemSentimentos = { positivo: 0, negativo: 0, neutro: 0 };
    avaliacoes.forEach(a => {
        const s = a.analise.sentimento;
        if (s in contagemSentimentos) contagemSentimentos[s]++;
    });

    const contagemEmocoes = {};
    avaliacoes.forEach(a => {
        const e = a.analise.emocao;
        contagemEmocoes[e] = (contagemEmocoes[e] || 0) + 1;
    });

    const pontosPos = {};
    avaliacoes.forEach(a => {
        a.analise.pontos_positivos.forEach(p => {
            const key = p.toLowerCase().trim();
            if (key) pontosPos[key] = (pontosPos[key] || 0) + 1;
        });
    });
    const pontosPositivosRecorrentes = Object.entries(pontosPos)
        .map(([ponto, frequencia]) => ({ ponto, frequencia }))
        .sort((a, b) => b.frequencia - a.frequencia)
        .slice(0, 10);

    const pontosNeg = {};
    avaliacoes.forEach(a => {
        a.analise.pontos_negativos.forEach(p => {
            const key = p.toLowerCase().trim();
            if (key) pontosNeg[key] = (pontosNeg[key] || 0) + 1;
        });
    });
    const pontosNegativosRecorrentes = Object.entries(pontosNeg)
        .map(([ponto, frequencia]) => ({ ponto, frequencia }))
        .sort((a, b) => b.frequencia - a.frequencia)
        .slice(0, 10);

    const evolucaoMap = {};
    avaliacoes.forEach(a => {
        if (!evolucaoMap[a.data]) {
            evolucaoMap[a.data] = { data: a.data, positivo: 0, negativo: 0, neutro: 0 };
        }
        const s = a.analise.sentimento;
        if (s in evolucaoMap[a.data]) evolucaoMap[a.data][s]++;
    });
    const evolucaoPorData = Object.values(evolucaoMap).sort((a, b) => a.data.localeCompare(b.data));

    // Re-calcula métricas de plataforma localmente para a categoria ativa
    const metricas_plataforma = {};
    if (categoriaSelecionada === 'playstore') {
        const sent_versao = {};
        const sent_android = {};
        avaliacoes.forEach(a => {
            if (a.versao_app) {
                const v = a.versao_app;
                if (!sent_versao[v]) sent_versao[v] = { positivo: 0, negativo: 0, neutro: 0, total: 0, soma_estrelas: 0 };
                sent_versao[v][a.analise.sentimento]++;
                sent_versao[v].total++;
                sent_versao[v].soma_estrelas += a.estrelas;
            }
            if (a.android_version) {
                const os = a.android_version;
                if (!sent_android[os]) sent_android[os] = { positivo: 0, negativo: 0, neutro: 0 };
                sent_android[os][a.analise.sentimento]++;
            }
        });
        
        metricas_plataforma.sentimento_por_versao = {};
        Object.entries(sent_versao).forEach(([v, info]) => {
            metricas_plataforma.sentimento_por_versao[v] = {
                positivo: info.positivo,
                negativo: info.negativo,
                neutro: info.neutro,
                total: info.total,
                media_estrelas: info.total > 0 ? Number((info.soma_estrelas / info.total).toFixed(2)) : 0
            };
        });
        metricas_plataforma.sentimento_por_android = sent_android;

    } else if (categoriaSelecionada === 'youtube') {
        const sent_duracao = {
            "Curto (<10 min)": { positivo: 0, negativo: 0, neutro: 0 },
            "Médio (10-25 min)": { positivo: 0, negativo: 0, neutro: 0 },
            "Longo (>25 min)": { positivo: 0, negativo: 0, neutro: 0 }
        };
        const sent_tema = {};
        
        avaliacoes.forEach(a => {
            if (a.duracao_minutos !== null) {
                const d = a.duracao_minutos;
                const faixa = d < 10 ? "Curto (<10 min)" : (d <= 25 ? "Médio (10-25 min)" : "Longo (>25 min)");
                sent_duracao[faixa][a.analise.sentimento]++;
            }
            if (a.categoria_video) {
                const t = a.categoria_video;
                if (!sent_tema[t]) sent_tema[t] = { positivo: 0, negativo: 0, neutro: 0 };
                sent_tema[t][a.analise.sentimento]++;
            }
        });
        metricas_plataforma.sentimento_por_duracao = sent_duracao;
        metricas_plataforma.sentimento_por_tema = sent_tema;

    } else if (categoriaSelecionada === 'instagram') {
        const sent_midia = {
            "reels": { positivo: 0, negativo: 0, neutro: 0 },
            "post": { positivo: 0, negativo: 0, neutro: 0 }
        };
        const sent_tag = {};
        
        avaliacoes.forEach(a => {
            if (a.tipo_midia && a.tipo_midia in sent_midia) {
                sent_midia[a.tipo_midia][a.analise.sentimento]++;
            }
            if (a.hashtag_principal) {
                const tag = a.hashtag_principal;
                if (!sent_tag[tag]) sent_tag[tag] = { positivo: 0, negativo: 0, neutro: 0, total: 0 };
                sent_tag[tag][a.analise.sentimento]++;
                sent_tag[tag].total++;
            }
        });
        metricas_plataforma.sentimento_por_midia = sent_midia;
        metricas_plataforma.sentimento_por_hashtag = sent_tag;

    } else if (categoriaSelecionada === 'amazon') {
        const estrelas_entrega = { 1: [], 2: [], 3: [], 4: [], 5: [] };
        const sent_embalagem = {
            "excelente": { positivo: 0, negativo: 0, neutro: 0 },
            "frágil": { positivo: 0, negativo: 0, neutro: 0 },
            "danificada": { positivo: 0, negativo: 0, neutro: 0 }
        };

        avaliacoes.forEach(a => {
            if (a.dias_entrega !== null && a.estrelas in estrelas_entrega) {
                estrelas_entrega[a.estrelas].push(a.dias_entrega);
            }
            if (a.embalagem_status && a.embalagem_status in sent_embalagem) {
                sent_embalagem[a.embalagem_status][a.analise.sentimento]++;
            }
        });
        
        metricas_plataforma.media_entrega_por_estrelas = {};
        for (let i = 1; i <= 5; i++) {
            const arr = estrelas_entrega[i];
            metricas_plataforma.media_entrega_por_estrelas[String(i)] = arr.length > 0
                ? Number((arr.reduce((a, b) => a + b, 0) / arr.length).toFixed(1))
                : 0.0;
        }
        metricas_plataforma.sentimento_embalagem = sent_embalagem;
    }

    return {
        total_avaliacoes: total,
        media_estrelas: mediaEstrelas,
        contagem_sentimentos: contagemSentimentos,
        contagem_emocoes: contagemEmocoes,
        pontos_positivos_recorrentes: pontosPositivosRecorrentes,
        pontos_negativos_recorrentes: pontosNegativosRecorrentes,
        evolucao_por_data: evolucaoPorData,
        metricas_plataforma: metricas_plataforma
    };
}

function limparFiltros() {
    document.getElementById('filtro-data-inicio').value = '';
    document.getElementById('filtro-data-fim').value = '';
    document.getElementById('filtro-sentimento').value = 'todos';
    document.getElementById('filtro-emocao').value = 'todos';

    // Reseta paginação local
    posComentariosExibidos = 5;
    negComentariosExibidos = 5;
    tabelaExibida = 10;

    if (dadosOriginais) {
        renderizarDashboard(dadosOriginais);
    }
}

/**
 * Inicializa a funcionalidade de Sandbox (análise de comentário avulso em tempo real)
 */
function inicializarSandbox() {
    const btnAnalise = document.getElementById('btn-sandbox-analisar');
    const textarea = document.getElementById('sandbox-textarea');
    const resultCard = document.getElementById('sandbox-result-card');
    const loadingCard = document.getElementById('sandbox-loading');

    if (!btnAnalise || !textarea) return;

    btnAnalise.addEventListener('click', async () => {
        const texto = textarea.value.trim();
        if (!texto) {
            alert('Por favor, digite um comentário antes de analisar.');
            return;
        }

        // Oculta card de resultado e mostra loading
        resultCard.classList.add('hidden');
        loadingCard.classList.remove('hidden');
        btnAnalise.disabled = true;

        try {
            const response = await fetch('/api/analisar-avulso', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ texto: texto })
            });

            const data = await response.json();

            if (!response.ok || data.erro) {
                throw new Error(data.erro || 'Erro ao processar análise da IA.');
            }

            // Popular dados no card
            const badgeSentimento = document.getElementById('sandbox-badge-sentimento');
            const badgeCriticidade = document.getElementById('sandbox-badge-criticidade');
            const valEmocao = document.getElementById('sandbox-val-emocao');
            const valConfianca = document.getElementById('sandbox-val-confianca');
            const valResumo = document.getElementById('sandbox-val-resumo');
            const listPositivos = document.getElementById('sandbox-list-positivos');
            const listNegativos = document.getElementById('sandbox-list-negativos');

            // Reset classes
            badgeSentimento.className = 'badge';
            badgeCriticidade.className = 'badge';

            // Sentimento
            badgeSentimento.textContent = data.sentimento;
            badgeSentimento.classList.add(`badge-${data.sentimento}`);

            // Criticidade
            badgeCriticidade.textContent = `Criticidade: ${data.nivel_criticidade}`;
            badgeCriticidade.classList.add(`badge-${data.nivel_criticidade}`);

            // Emoção e Confiança
            valEmocao.textContent = data.emocao.charAt(0).toUpperCase() + data.emocao.slice(1);
            valConfianca.textContent = `${(data.confianca * 100).toFixed(0)}%`;

            // Resumo
            valResumo.textContent = data.resumo;

            // Listas de Aspectos
            listPositivos.innerHTML = data.pontos_positivos && data.pontos_positivos.length
                ? data.pontos_positivos.map(p => `<li>${p}</li>`).join('')
                : '<li class="no-bullet" style="color: var(--text-muted);">Nenhum aspecto positivo</li>';

            listNegativos.innerHTML = data.pontos_negativos && data.pontos_negativos.length
                ? data.pontos_negativos.map(p => `<li>${p}</li>`).join('')
                : '<li class="no-bullet" style="color: var(--text-muted);">Nenhum problema citado</li>';

            // Mostrar card de resultado
            resultCard.classList.remove('hidden');

        } catch (error) {
            console.error('Erro na análise Sandbox:', error);
            alert('Falha na análise: ' + error.message);
        } finally {
            loadingCard.classList.add('hidden');
            btnAnalise.disabled = false;
        }
    });
}
