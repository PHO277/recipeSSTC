// 全局状态管理
let appState = {
    isLoggedIn: false,
    currentUser: null,
    currentTab: 'generate',
    isLoading: false
};

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    checkConnectionStatus();
    
    // 键盘事件监听
    document.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            if (document.activeElement.id === 'username' || document.activeElement.id === 'password') {
                login();
            } else if (document.activeElement.id === 'recipe-input') {
                generateRecipe();
            }
        }
    });
});

// 初始化应用
function initializeApp() {
    console.log('🚀 Recipe App Flask Version Initializing...');
    
    // 检查是否有保存的登录状态
    checkSavedLogin();
    
    // 设置默认状态
    showHomePage();
    
    console.log('✅ App initialized successfully');
}

// 检查保存的登录状态
function checkSavedLogin() {
    const savedUser = localStorage.getItem('recipeApp_user');
    if (savedUser) {
        try {
            const userData = JSON.parse(savedUser);
            if (userData.username) {
                // 自动登录
                appState.isLoggedIn = true;
                appState.currentUser = userData.username;
                showLoggedInView();
                showMessage('Welcome back, ' + userData.username + '!', 'success');
            }
        } catch (e) {
            console.log('Invalid saved user data');
            localStorage.removeItem('recipeApp_user');
        }
    }
}

// 登录功能
async function login() {
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value.trim();
    const messageEl = document.getElementById('login-message');
    
    // 输入验证
    if (!username || !password) {
        showMessage('Please enter both username and password', 'error', messageEl);
        return;
    }
    
    // 显示加载状态
    const loginBtn = document.querySelector('#login-form button');
    const originalText = loginBtn.innerHTML;
    loginBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Logging in...';
    loginBtn.disabled = true;
    
    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // 登录成功
            appState.isLoggedIn = true;
            appState.currentUser = username;
            
            // 保存登录状态
            localStorage.setItem('recipeApp_user', JSON.stringify({ username }));
            
            // 显示成功消息
            showMessage('Login successful! Welcome ' + username, 'success', messageEl);
            
            // 延迟显示主界面
            setTimeout(() => {
                showLoggedInView();
                loadDefaultTab();
            }, 1000);
            
        } else {
            showMessage(result.message || 'Login failed', 'error', messageEl);
        }
        
    } catch (error) {
        console.error('Login error:', error);
        showMessage('Connection error. Please try again.', 'error', messageEl);
    } finally {
        // 恢复按钮状态
        loginBtn.innerHTML = originalText;
        loginBtn.disabled = false;
    }
}

// 登出功能
async function logout() {
    try {
        await fetch('/api/logout', { method: 'POST' });
    } catch (error) {
        console.log('Logout request failed:', error);
    }
    
    // 清除本地状态
    appState.isLoggedIn = false;
    appState.currentUser = null;
    localStorage.removeItem('recipeApp_user');
    
    // 重置界面
    showHomePage();
    clearForms();
    
    showMessage('You have been logged out', 'success');
}

// 显示登录后界面
function showLoggedInView() {
    document.getElementById('home-page').style.display = 'none';
    document.getElementById('login-form').style.display = 'none';
    document.getElementById('user-info').style.display = 'block';
    document.getElementById('nav-menu').style.display = 'block';
    document.getElementById('app-interface').style.display = 'block';
    
    // 更新用户信息
    document.getElementById('user-name').textContent = appState.currentUser;
    
    // 设置默认活跃标签
    showTab('generate');
}

// 显示主页
function showHomePage() {
    document.getElementById('home-page').style.display = 'block';
    document.getElementById('login-form').style.display = 'block';
    document.getElementById('user-info').style.display = 'none';
    document.getElementById('nav-menu').style.display = 'none';
    document.getElementById('app-interface').style.display = 'none';
}

// 标签页切换
function showTab(tabName) {
    // 更新状态
    appState.currentTab = tabName;
    
    // 隐藏所有标签页
    document.querySelectorAll('.tab-pane').forEach(pane => {
        pane.classList.remove('active');
    });
    
    // 移除所有导航链接的活跃状态
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    
    // 显示选中的标签页
    const targetTab = document.getElementById(tabName + '-tab');
    if (targetTab) {
        targetTab.classList.add('active');
    }
    
    // 激活对应的导航链接
    const targetNav = document.querySelector(`[onclick="showTab('${tabName}')"]`);
    if (targetNav) {
        targetNav.classList.add('active');
    }
    
    // 加载标签页内容
    loadTabContent(tabName);
    
    console.log(`📄 Switched to tab: ${tabName}`);
}

// 加载标签页内容
async function loadTabContent(tabName) {
    switch(tabName) {
        case 'generate':
            // 生成页面已经在HTML中，无需额外加载
            break;
        case 'my-recipes':
            await loadMyRecipes();
            break;
        case 'discover':
            await loadDiscover();
            break;
        case 'statistics':
            await loadStatistics();
            break;
        case 'settings':
            loadSettings();
            break;
    }
}

// 生成食谱功能
async function generateRecipe() {
    const input = document.getElementById('recipe-input').value.trim();
    const cuisineType = document.getElementById('cuisine-type').value;
    const difficulty = document.getElementById('difficulty').value;
    const prepTime = document.getElementById('prep-time').value;
    
    if (!input) {
        showMessage('Please describe what you want to cook', 'error');
        return;
    }
    
    // 显示加载状态
    showLoading(true);
    const generateBtn = document.getElementById('generate-btn');
    const originalText = generateBtn.innerHTML;
    generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
    generateBtn.disabled = true;
    
    try {
        const requestData = {
            input: input,
            cuisine: cuisineType,
            difficulty: difficulty,
            prepTime: prepTime
        };
        
        const response = await fetch('/api/generate-recipe', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            displayRecipe(result.recipe);
            
            // 保存到本地历史记录
            saveRecipeToHistory({
                input: input,
                recipe: result.recipe,
                timestamp: new Date().toISOString()
            });
            
        } else {
            showMessage('Failed to generate recipe. Please try again.', 'error');
        }
        
    } catch (error) {
        console.error('Generate recipe error:', error);
        showMessage('Connection error. Please check your internet connection.', 'error');
    } finally {
        showLoading(false);
        generateBtn.innerHTML = originalText;
        generateBtn.disabled = false;
    }
}

// 显示生成的食谱
function displayRecipe(recipeHTML) {
    const resultDiv = document.getElementById('recipe-result');
    resultDiv.innerHTML = recipeHTML;
    
    // 添加保存按钮
    const saveBtn = document.createElement('button');
    saveBtn.className = 'btn-primary';
    saveBtn.innerHTML = '<i class="fas fa-save"></i> Save Recipe';
    saveBtn.style.marginTop = '20px';
    saveBtn.onclick = () => saveCurrentRecipe();
    
    resultDiv.appendChild(saveBtn);
    
    // 滚动到结果区域
    resultDiv.scrollIntoView({ behavior: 'smooth' });
}

// 保存当前食谱
function saveCurrentRecipe() {
    const recipeContent = document.getElementById('recipe-result').innerHTML;
    const input = document.getElementById('recipe-input').value;
    
    const recipe = {
        id: Date.now(),
        title: input.substring(0, 50) + '...',
        content: recipeContent,
        createdAt: new Date().toISOString(),
        tags: []
    };
    
    let savedRecipes = JSON.parse(localStorage.getItem('savedRecipes') || '[]');
    savedRecipes.unshift(recipe);
    
    // 限制保存数量
    if (savedRecipes.length > 50) {
        savedRecipes = savedRecipes.slice(0, 50);
    }
    
    localStorage.setItem('savedRecipes', JSON.stringify(savedRecipes));
    showMessage('Recipe saved successfully!', 'success');
}

// 加载我的食谱
async function loadMyRecipes() {
    const savedRecipes = JSON.parse(localStorage.getItem('savedRecipes') || '[]');
    const listEl = document.getElementById('my-recipes-list');
    
    if (savedRecipes.length === 0) {
        listEl.innerHTML = `
            <div class="no-content">
                <i class="fas fa-book-open"></i>
                <p>No recipes saved yet. Generate some recipes to get started!</p>
            </div>
        `;
        return;
    }
    
    listEl.innerHTML = savedRecipes.map(recipe => `
        <div class="recipe-card" style="margin-bottom: 20px;">
            <h3>${recipe.title}</h3>
            <p><small>Saved on ${new Date(recipe.createdAt).toLocaleDateString()}</small></p>
            <div style="margin-top: 15px;">
                <button onclick="viewRecipe('${recipe.id}')" class="btn-primary" style="margin-right: 10px;">
                    <i class="fas fa-eye"></i> View
                </button>
                <button onclick="deleteRecipe('${recipe.id}')" class="btn-secondary">
                    <i class="fas fa-trash"></i> Delete
                </button>
            </div>
        </div>
    `).join('');
}

// 查看食谱详情
function viewRecipe(recipeId) {
    const savedRecipes = JSON.parse(localStorage.getItem('savedRecipes') || '[]');
    const recipe = savedRecipes.find(r => r.id == recipeId);
    
    if (recipe) {
        // 可以创建模态框显示完整食谱
        alert('Recipe viewer will be implemented soon!');
    }
}

// 删除食谱
function deleteRecipe(recipeId) {
    if (confirm('Are you sure you want to delete this recipe?')) {
        let savedRecipes = JSON.parse(localStorage.getItem('savedRecipes') || '[]');
        savedRecipes = savedRecipes.filter(r => r.id != recipeId);
        localStorage.setItem('savedRecipes', JSON.stringify(savedRecipes));
        loadMyRecipes(); // 重新加载列表
        showMessage('Recipe deleted successfully', 'success');
    }
}

// 加载发现页面
async function loadDiscover() {
    const discoverEl = document.getElementById('discover-content');
    discoverEl.innerHTML = `
        <div class="discover-grid">
            <div class="feature-card">
                <i class="fas fa-fire"></i>
                <h3>Trending Recipes</h3>
                <p>Coming soon...</p>
            </div>
            <div class="feature-card">
                <i class="fas fa-users"></i>
                <h3>Community Favorites</h3>
                <p>Coming soon...</p>
            </div>
            <div class="feature-card">
                <i class="fas fa-star"></i>
                <h3>Chef Recommendations</h3>
                <p>Coming soon...</p>
            </div>
        </div>
    `;
}

// 加载统计页面
async function loadStatistics() {
    const statsEl = document.getElementById('statistics-content');
    const savedRecipes = JSON.parse(localStorage.getItem('savedRecipes') || '[]');
    
    statsEl.innerHTML = `
        <div class="settings-grid">
            <div class="setting-item">
                <h3><i class="fas fa-book"></i> Saved Recipes</h3>
                <p style="font-size: 2em; color: var(--primary-color); font-weight: bold;">${savedRecipes.length}</p>
            </div>
            <div class="setting-item">
                <h3><i class="fas fa-clock"></i> Total Cooking Time</h3>
                <p style="font-size: 2em; color: var(--success-color); font-weight: bold;">Coming Soon</p>
            </div>
            <div class="setting-item">
                <h3><i class="fas fa-chart-line"></i> Favorite Cuisine</h3>
                <p style="font-size: 2em; color: var(--warning-color); font-weight: bold;">Analyzing...</p>
            </div>
        </div>
    `;
}

// 加载设置页面
function loadSettings() {
    const settingsEl = document.getElementById('settings-content');
    
    // 设置事件监听器
    setTimeout(() => {
        const languageSelect = document.getElementById('language-select');
        const themeSelect = document.getElementById('theme-select');
        
        if (languageSelect) {
            languageSelect.addEventListener('change', (e) => {
                localStorage.setItem('app_language', e.target.value);
                showMessage('Language setting saved', 'success');
            });
            
            // 加载保存的语言设置
            const savedLang = localStorage.getItem('app_language');
            if (savedLang) {
                languageSelect.value = savedLang;
            }
        }
        
        if (themeSelect) {
            themeSelect.addEventListener('change', (e) => {
                localStorage.setItem('app_theme', e.target.value);
                applyTheme(e.target.value);
                showMessage('Theme setting saved', 'success');
            });
            
            // 加载保存的主题设置
            const savedTheme = localStorage.getItem('app_theme');
            if (savedTheme) {
                themeSelect.value = savedTheme;
                applyTheme(savedTheme);
            }
        }
    }, 100);
}

// 应用主题
function applyTheme(theme) {
    if (theme === 'dark') {
        document.body.classList.add('dark-theme');
    } else {
        document.body.classList.remove('dark-theme');
    }
}

// 显示加载状态
function showLoading(show) {
    const loadingEl = document.getElementById('loading');
    if (loadingEl) {
        loadingEl.style.display = show ? 'block' : 'none';
    }
}

// 显示消息
function showMessage(message, type = 'info', targetEl = null) {
    if (!targetEl) {
        // 创建全局消息提示
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        messageDiv.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            ${message}
        `;
        messageDiv.style.position = 'fixed';
        messageDiv.style.top = '20px';
        messageDiv.style.right = '20px';
        messageDiv.style.zIndex = '9999';
        messageDiv.style.minWidth = '300px';
        messageDiv.style.padding = '15px';
        messageDiv.style.borderRadius = '8px';
        
        document.body.appendChild(messageDiv);
        
        // 自动移除
        setTimeout(() => {
            messageDiv.remove();
        }, 4000);
    } else {
        targetEl.className = `message ${type}`;
        targetEl.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
            ${message}
        `;
    }
}

// 保存食谱到历史记录
function saveRecipeToHistory(recipe) {
    let history = JSON.parse(localStorage.getItem('recipeHistory') || '[]');
    history.unshift(recipe);
    
    // 限制历史记录数量
    if (history.length > 100) {
        history = history.slice(0, 100);
    }
    
    localStorage.setItem('recipeHistory', JSON.stringify(history));
}

// 清除表单
function clearForms() {
    document.getElementById('username').value = '';
    document.getElementById('password').value = '';
    document.getElementById('recipe-input').value = '';
    document.getElementById('recipe-result').innerHTML = '';
}

// 加载默认标签页
function loadDefaultTab() {
    showTab('generate');
}

// 检查连接状态
function checkConnectionStatus() {
    fetch('/api/test')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                document.getElementById('connection-status').textContent = 'Connected';
                document.getElementById('connection-status').className = 'status-connected';
            }
        })
        .catch(error => {
            document.getElementById('connection-status').textContent = 'Disconnected';
            document.getElementById('connection-status').className = 'status-disconnected';
        });
}

// 工具函数
function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// 导出函数供全局使用
window.appFunctions = {
    login,
    logout,
    showTab,
    generateRecipe,
    viewRecipe,
    deleteRecipe
};

console.log('🎯 JavaScript loaded successfully!');
