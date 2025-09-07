// 页面加载时获取统计数据
document.addEventListener('DOMContentLoaded', function () {
    loadSystemStats();
});

// 加载系统统计数据
function loadSystemStats() {
    fetch('/api/v1/stats')
        .then(response => response.json())
        .then(data => {
            document.getElementById('catalog-count').textContent = data.ingredient_catalog_count.toLocaleString();
            document.getElementById('reference-formulas-count').textContent = data.reference_formulas_count.toLocaleString();
            document.getElementById('to-match-formulas-count').textContent = data.to_match_formulas_count.toLocaleString();
        })
        .catch(error => {
            console.error('加载统计数据失败:', error);
            // 显示错误信息
            document.getElementById('catalog-count').textContent = '错误';
            document.getElementById('reference-formulas-count').textContent = '错误';
            document.getElementById('to-match-formulas-count').textContent = '错误';
        });
}

async function logout() {
    try {
        const response = await fetch('/api/v1/auth/logout', {
            method: 'POST'
        });

        const data = await response.json();
        if (data.success) {
            window.location.href = '/';
        } else {
            window.location.href = '/';
        }
    } catch (error) {
        console.error('登出失败:', error);
        window.location.href = '/';
    }
}