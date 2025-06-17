import streamlit as st

def load_css():
    st.markdown("""

    <style>
        /* 主题色彩 */
        :root {
            --primary-color: #4CAF50;
            --secondary-color: #45a049;
            --background-color: #f5f5f5;
            --card-background: #ffffff;
            --text-color: #333333;
            --map-primary: #2196f3;
            --map-secondary: #1976d2;
        }

        /* 响应式设计 */
        @media (max-width: 768px) {
            .main > div {
                padding: 1rem;
            }
            .restaurant-info-popup {
                font-size: 0.875rem;
            }
        }

        /* 卡片样式 */
        .recipe-card {
            background: var(--card-background);
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin: 1rem 0;
            transition: transform 0.3s ease;
        }

        .recipe-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        }

        /* 营养信息网格 */
        .nutrition-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin: 1rem 0;
        }

        .nutrition-item {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem;
            border-radius: 8px;
            text-align: center;
        }

        /* 用户头像 */
        .user-avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: var(--primary-color);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            margin-right: 10px;
        }

        /* 按钮样式 */
        .stButton > button {
            background-color: var(--primary-color);
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 5px;
            font-weight: 500;
            transition: all 0.3s ease;
        }

        .stButton > button:hover {
            background-color: var(--secondary-color);
            transform: translateY(-1px);
        }

        /* 标签样式 */
        .tag {
            display: inline-block;
            background: #e0e0e0;
            padding: 0.25rem 0.75rem;
            border-radius: 15px;
            margin: 0.25rem;
            font-size: 0.875rem;
        }

        /* 评分星星 */
        .rating {
            color: #ffd700;
            font-size: 1.2rem;
        }

        /* ===== 地图搜索相关样式 ===== */

        /* 餐厅卡片样式 */
        .restaurant-card {
            background: var(--card-background);
            border-radius: 12px;
            padding: 1.25rem;
            margin-bottom: 1rem;
            border: 1px solid #e0e0e0;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .restaurant-card:hover {
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            border-color: var(--map-primary);
        }

        .restaurant-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background: var(--map-primary);
            transform: scaleY(0);
            transition: transform 0.3s ease;
        }

        .restaurant-card:hover::before {
            transform: scaleY(1);
        }

        /* 搜索解释框 */
        .search-explanation {
            background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
            border-left: 4px solid var(--map-primary);
            padding: 1rem 1.25rem;
            margin-bottom: 1.25rem;
            border-radius: 0 8px 8px 0;
            position: relative;
        }

        .search-explanation::after {
            content: '🔍';
            position: absolute;
            right: 1rem;
            top: 50%;
            transform: translateY(-50%);
            font-size: 2rem;
            opacity: 0.3;
        }

        /* 地图容器 */
        .map-container {
            border: 2px solid #e0e0e0;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            position: relative;
        }

        .map-container::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--map-primary) 0%, var(--map-secondary) 100%);
        }

        /* 餐厅信息弹窗 */
        .restaurant-info-popup {
            max-width: 280px;
            padding: 0.75rem;
        }

        .restaurant-info-popup h4 {
            color: var(--map-primary);
            margin-bottom: 0.5rem;
            font-size: 1.1rem;
        }

        .restaurant-info-popup p {
            margin: 0.25rem 0;
            font-size: 0.9rem;
            color: #555;
        }

        /* 距离标签 */
        .distance-badge {
            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.875rem;
            font-weight: 500;
            display: inline-block;
        }

        /* 价格指示器 */
        .price-indicator {
            color: #ff9800;
            font-weight: bold;
            letter-spacing: 2px;
        }

        /* 餐厅类型标签 */
        .cuisine-tag {
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
            color: white;
            padding: 0.2rem 0.6rem;
            border-radius: 12px;
            font-size: 0.8rem;
            margin-right: 0.5rem;
            display: inline-block;
        }

        /* 搜索加载动画 */
        .search-loading {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem;
        }

        .search-loading::after {
            content: '';
            width: 40px;
            height: 40px;
            border: 4px solid #f3f3f3;
            border-top: 4px solid var(--map-primary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        /* 高级搜索选项 */
        .advanced-search {
            background: #fafafa;
            border-radius: 8px;
            padding: 1rem;
            margin-top: 0.5rem;
        }

        /* 餐厅操作按钮 */
        .restaurant-actions {
            display: flex;
            gap: 0.5rem;
            margin-top: 0.75rem;
        }

        .restaurant-actions button {
            flex: 1;
            padding: 0.4rem 0.8rem;
            border: 1px solid #ddd;
            border-radius: 6px;
            background: white;
            font-size: 0.875rem;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .restaurant-actions button:hover {
            background: var(--map-primary);
            color: white;
            border-color: var(--map-primary);
            transform: translateY(-1px);
        }

        /* 地图标记样式 */
        .map-marker-label {
            background: var(--map-primary);
            color: white;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-weight: bold;
            font-size: 0.875rem;
        }

        /* 收藏成功提示 */
        .favorite-toast {
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            background: var(--primary-color);
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            animation: slideIn 0.3s ease;
        }

        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
    </style>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            // 原有的卡片动画
            const cards = document.querySelectorAll('.recipe-card');
            cards.forEach((card, index) => {
                card.style.animationDelay = `${index * 0.1}s`;
            });

            // 餐厅卡片动画
            const restaurantCards = document.querySelectorAll('.restaurant-card');
            restaurantCards.forEach((card, index) => {
                card.style.opacity = '0';
                card.style.transform = 'translateY(20px)';
                setTimeout(() => {
                    card.style.transition = 'all 0.5s ease';
                    card.style.opacity = '1';
                    card.style.transform = 'translateY(0)';
                }, index * 100);
            });
        });
    </script>
    """, unsafe_allow_html=True)