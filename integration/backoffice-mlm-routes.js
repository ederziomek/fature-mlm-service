// Integração MLM para o backoffice-final
// Este arquivo deve ser adicionado ao projeto backoffice-final

const express = require('express');
const axios = require('axios');
const router = express.Router();

// URL do serviço MLM
const MLM_SERVICE_URL = process.env.MLM_SERVICE_URL || 'http://localhost:5000';

// Cache simples para otimização
const cache = new Map();
const CACHE_TTL = 5 * 60 * 1000; // 5 minutos

function getCacheKey(endpoint, params = {}) {
    return `${endpoint}_${JSON.stringify(params)}`;
}

function getFromCache(key) {
    const cached = cache.get(key);
    if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
        return cached.data;
    }
    cache.delete(key);
    return null;
}

function setCache(key, data) {
    cache.set(key, {
        data,
        timestamp: Date.now()
    });
}

// Endpoint para estatísticas gerais MLM
router.get('/stats', async (req, res) => {
    try {
        const cacheKey = getCacheKey('mlm_stats');
        const cached = getFromCache(cacheKey);
        
        if (cached) {
            return res.json({
                status: 'success',
                data: cached,
                cache: 'hit'
            });
        }
        
        const response = await axios.get(`${MLM_SERVICE_URL}/api/v1/mlm/summary`, {
            timeout: 10000
        });
        
        setCache(cacheKey, response.data.data);
        
        res.json({
            status: 'success',
            data: response.data.data,
            cache: 'miss'
        });
        
    } catch (error) {
        console.error('Erro ao buscar estatísticas MLM:', error.message);
        
        // Retornar dados mock em caso de erro
        res.json({
            status: 'success',
            data: {
                total_affiliates: 0,
                total_levels: 5,
                total_volume: 0,
                total_commissions: 0,
                active_affiliates: 0,
                last_sync: null
            },
            error: 'Serviço MLM indisponível - dados mock',
            cache: 'error'
        });
    }
});

// Endpoint para hierarquia de afiliado específico
router.get('/hierarchy/:affiliateId', async (req, res) => {
    try {
        const { affiliateId } = req.params;
        const cacheKey = getCacheKey('hierarchy', { affiliateId });
        const cached = getFromCache(cacheKey);
        
        if (cached) {
            return res.json({
                status: 'success',
                data: cached,
                cache: 'hit'
            });
        }
        
        const response = await axios.get(`${MLM_SERVICE_URL}/api/v1/mlm/hierarchy/${affiliateId}`, {
            timeout: 15000
        });
        
        setCache(cacheKey, response.data.data);
        
        res.json({
            status: 'success',
            data: response.data.data,
            cache: 'miss'
        });
        
    } catch (error) {
        console.error(`Erro ao buscar hierarquia para ${req.params.affiliateId}:`, error.message);
        
        res.status(500).json({
            status: 'error',
            message: 'Erro ao carregar hierarquia MLM',
            error: error.message
        });
    }
});

// Endpoint para estatísticas de afiliado específico
router.get('/affiliate/:affiliateId/stats', async (req, res) => {
    try {
        const { affiliateId } = req.params;
        const cacheKey = getCacheKey('affiliate_stats', { affiliateId });
        const cached = getFromCache(cacheKey);
        
        if (cached) {
            return res.json({
                status: 'success',
                data: cached,
                cache: 'hit'
            });
        }
        
        const response = await axios.get(`${MLM_SERVICE_URL}/api/v1/mlm/stats/${affiliateId}`, {
            timeout: 10000
        });
        
        setCache(cacheKey, response.data.data);
        
        res.json({
            status: 'success',
            data: response.data.data,
            cache: 'miss'
        });
        
    } catch (error) {
        console.error(`Erro ao buscar estatísticas para ${req.params.affiliateId}:`, error.message);
        
        // Retornar estrutura vazia em caso de erro
        res.json({
            status: 'success',
            data: {
                affiliate_id: parseInt(req.params.affiliateId),
                levels: [],
                summary: {
                    total_downline: 0,
                    total_volume: 0,
                    total_commissions: 0,
                    active_levels: 0
                }
            },
            error: 'Serviço MLM indisponível - dados vazios',
            cache: 'error'
        });
    }
});

// Endpoint para comissões de afiliado
router.get('/affiliate/:affiliateId/commissions', async (req, res) => {
    try {
        const { affiliateId } = req.params;
        const { start_date, end_date, level, status } = req.query;
        
        const params = new URLSearchParams();
        if (start_date) params.append('start_date', start_date);
        if (end_date) params.append('end_date', end_date);
        if (level) params.append('level', level);
        if (status) params.append('status', status);
        
        const cacheKey = getCacheKey('commissions', { affiliateId, ...req.query });
        const cached = getFromCache(cacheKey);
        
        if (cached) {
            return res.json({
                status: 'success',
                data: cached,
                cache: 'hit'
            });
        }
        
        const url = `${MLM_SERVICE_URL}/api/v1/mlm/commissions/${affiliateId}?${params.toString()}`;
        const response = await axios.get(url, {
            timeout: 10000
        });
        
        setCache(cacheKey, response.data.data);
        
        res.json({
            status: 'success',
            data: response.data.data,
            cache: 'miss'
        });
        
    } catch (error) {
        console.error(`Erro ao buscar comissões para ${req.params.affiliateId}:`, error.message);
        
        res.status(500).json({
            status: 'error',
            message: 'Erro ao carregar comissões',
            error: error.message
        });
    }
});

// Endpoint para sincronização manual
router.post('/sync', async (req, res) => {
    try {
        const response = await axios.post(`${MLM_SERVICE_URL}/api/v1/sync/manual`, {}, {
            timeout: 60000 // 1 minuto para sincronização
        });
        
        // Limpar cache após sincronização
        cache.clear();
        
        res.json({
            status: 'success',
            data: response.data.data,
            message: 'Sincronização MLM executada com sucesso'
        });
        
    } catch (error) {
        console.error('Erro na sincronização MLM:', error.message);
        
        res.status(500).json({
            status: 'error',
            message: 'Erro na sincronização MLM',
            error: error.message
        });
    }
});

// Endpoint para status do serviço MLM
router.get('/service/status', async (req, res) => {
    try {
        const [healthResponse, syncResponse] = await Promise.allSettled([
            axios.get(`${MLM_SERVICE_URL}/health`, { timeout: 5000 }),
            axios.get(`${MLM_SERVICE_URL}/api/v1/sync/status`, { timeout: 5000 })
        ]);
        
        const health = healthResponse.status === 'fulfilled' ? healthResponse.value.data : null;
        const sync = syncResponse.status === 'fulfilled' ? syncResponse.value.data : null;
        
        res.json({
            status: 'success',
            data: {
                service_available: !!health,
                health: health,
                sync: sync,
                cache_size: cache.size
            }
        });
        
    } catch (error) {
        console.error('Erro ao verificar status do serviço MLM:', error.message);
        
        res.json({
            status: 'success',
            data: {
                service_available: false,
                error: error.message,
                cache_size: cache.size
            }
        });
    }
});

// Middleware para limpar cache periodicamente
setInterval(() => {
    const now = Date.now();
    for (const [key, value] of cache.entries()) {
        if (now - value.timestamp > CACHE_TTL) {
            cache.delete(key);
        }
    }
}, CACHE_TTL);

module.exports = router;

