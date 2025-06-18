# components/map_search.py
import streamlit as st
import folium
from utils.translations import get_translation
from streamlit_folium import st_folium
import requests
import json
from datetime import datetime
import random


class MapSearch:
    def __init__(self):
        # 地图API密钥
        try:
            self.amap_key = st.secrets.get("AMAP_API_KEY", "")
        except:
            self.amap_key = ""

        # 初始化 DeepSeek
        try:
            from llm_interface import LLMInterface
            deepseek_key = st.secrets.get("DEEPSEEK_API_KEY", "")
            if deepseek_key:
                self.llm = LLMInterface(deepseek_key)
            else:
                self.llm = None
        except:
            self.llm = None

        # 初始化用户位置
        if 'user_location' not in st.session_state:
            st.session_state.user_location = [39.9042, 116.4074]  # 默认北京

        self.user_location = st.session_state.user_location

        # 初始化搜索状态
        if 'search_results' not in st.session_state:
            st.session_state.search_results = []
        if 'search_dish' not in st.session_state:
            st.session_state.search_dish = ""
        if 'cuisine_info' not in st.session_state:
            st.session_state.cuisine_info = {}

    def render_map_page(self):
        """渲染地图搜索页面"""
        lang = st.session_state.get('language', 'zh')
        
        st.title(f"🗺️ 餐厅地图搜索")
        st.markdown(f"### 搜索您想吃的菜品，智能推荐附近餐厅")

        if not self.amap_key:
            st.info("ℹ️ 提示：当前使用模拟数据模式。配置API密钥以使用真实地图数据。")

        # 创建两列布局
        col1, col2 = st.columns([1, 2])

        with col1:
            self._render_search_panel()

        with col2:
            self._render_map()

        # 在主区域显示搜索结果
        self._render_search_results()

    def _render_search_panel(self):
        """渲染搜索面板"""
        st.markdown("#### 🔍 搜索菜品")

        # 搜索输入
        dish_name = st.text_input(
            "输入菜品名称",
            placeholder="例如：番茄炒蛋、麻婆豆腐、寿司...",
            key="dish_search_input"
        )

        # 搜索选项
        with st.expander("高级选项", expanded=False):
            search_radius = st.slider(
                "搜索范围（公里）",
                min_value=1,
                max_value=10,
                value=3,
                key="search_radius"
            )

            price_range = st.select_slider(
                "价格范围",
                options=["💰", "💰💰", "💰💰💰", "💰💰💰💰"],
                value="💰💰",
                key="price_range"
            )

            min_rating = st.slider(
                "最低评分",
                min_value=0.0,
                max_value=5.0,
                value=3.5,
                step=0.5,
                key="min_rating"
            )

        # 搜索按钮
        btn_col1, btn_col2 = st.columns(2)
        
        with btn_col1:
            if st.button("🔍 搜索餐厅", type="primary", use_container_width=True):
                if dish_name:
                    with st.spinner("正在搜索相关餐厅..."):
                        self._execute_search(dish_name, st.session_state.get('search_radius', 3))
                else:
                    st.warning("请输入菜品名称")

        with btn_col2:
            if st.button("🎲 随机推荐", use_container_width=True):
                random_dishes = ["宫保鸡丁", "糖醋排骨", "鱼香肉丝", "麻辣香锅", "寿司", "拉面", "披萨", "汉堡"]
                random_dish = random.choice(random_dishes)
                st.info(f"🎲 随机推荐：{random_dish}")
                with st.spinner(f"正在搜索 {random_dish} 相关餐厅..."):
                    self._execute_search(random_dish, st.session_state.get('search_radius', 3))

    def _execute_search(self, dish_name, radius):
        """执行搜索"""
        try:
            # 1. AI分析菜品
            cuisine_info = self._analyze_dish_cuisine(dish_name)
            
            # 2. 构建搜索关键词
            keywords = self._build_search_keywords(dish_name, cuisine_info)
            
            # 3. 搜索餐厅
            all_results = []
            for keyword in keywords[:3]:
                results = self._call_map_api(keyword, radius)
                all_results.extend(results)
            
            # 4. 去重并排序
            unique_results = self._deduplicate_results(all_results)
            ranked_results = self._rank_results(unique_results, dish_name, cuisine_info)
            
            # 5. 保存结果
            st.session_state.search_results = ranked_results
            st.session_state.search_dish = dish_name
            st.session_state.cuisine_info = cuisine_info
            
            if ranked_results:
                st.success(f"找到 {len(ranked_results)} 家相关餐厅！")
            else:
                st.warning("没有找到相关餐厅，请尝试其他关键词。")
                
        except Exception as e:
            st.error(f"搜索失败：{str(e)}")
            st.session_state.search_results = []

    def _analyze_dish_cuisine(self, dish_name):
        """分析菜品类型"""
        if self.llm:
            try:
                return self._ai_analyze_dish(dish_name)
            except:
                return self._fallback_analyze_dish(dish_name)
        else:
            return self._fallback_analyze_dish(dish_name)

    def _ai_analyze_dish(self, dish_name):
        """AI分析菜品"""
        prompt = f"""
        请分析菜品"{dish_name}"，返回JSON格式的结果：
        {{
            "cuisine_type": "菜系类型（如：中餐、日料、韩餐、西餐、火锅等）",
            "restaurant_types": ["推荐的餐厅类型列表，至少3个"],
            "search_keywords": ["搜索关键词列表，用于查找相关餐厅"],
            "dish_characteristics": {{
                "spicy_level": "辣度（0-5）",
                "price_range": "价格区间（低/中/高）",
                "cooking_method": "烹饪方式"
            }},
            "similar_dishes": ["相似菜品列表"],
            "recommended_restaurant_names": ["推荐的餐厅名称模式"]
        }}
        只返回JSON，不要其他说明。
        """

        response = self.llm.client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个美食专家，擅长分析菜品和推荐餐厅。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )

        result = response.choices[0].message.content.strip()
        if result.startswith("```json"):
            result = result[7:]
        if result.endswith("```"):
            result = result[:-3]

        cuisine_info = json.loads(result.strip())
        cuisine_info['confidence'] = 0.95
        cuisine_info['analysis_method'] = 'deepseek_ai'
        
        return cuisine_info

    def _fallback_analyze_dish(self, dish_name):
        """备用分析方法"""
        cuisine_rules = {
            "中餐": ["炒", "煮", "蒸", "炖", "烧", "宫保", "鱼香", "麻婆", "糖醋", "红烧", "麻辣"],
            "日料": ["寿司", "刺身", "拉面", "天妇罗", "照烧", "味增", "日本", "日式"],
            "韩餐": ["泡菜", "烤肉", "石锅", "冷面", "拌饭", "韩国", "韩式"],
            "西餐": ["披萨", "意面", "汉堡", "牛排", "沙拉", "薯条", "西式"],
            "火锅": ["火锅", "串串", "麻辣烫", "冒菜"]
        }

        detected_cuisine = "中餐"
        restaurant_types = ["中餐厅", "中国餐厅"]

        for cuisine, keywords in cuisine_rules.items():
            if any(keyword in dish_name for keyword in keywords):
                detected_cuisine = cuisine
                if cuisine == "中餐":
                    restaurant_types = ["中餐厅", "中国餐厅", "家常菜", "川菜"]
                elif cuisine == "日料":
                    restaurant_types = ["日本料理", "日料", "寿司店"]
                elif cuisine == "韩餐":
                    restaurant_types = ["韩国料理", "韩餐", "烤肉店"]
                elif cuisine == "西餐":
                    restaurant_types = ["西餐厅", "牛排馆", "披萨店"]
                elif cuisine == "火锅":
                    restaurant_types = ["火锅店", "火锅", "串串香"]
                break

        return {
            "cuisine_type": detected_cuisine,
            "restaurant_types": restaurant_types,
            "search_keywords": restaurant_types,
            "confidence": 0.85,
            "analysis_method": "rule_based"
        }

    def _build_search_keywords(self, dish_name, cuisine_info):
        """构建搜索关键词"""
        keywords = []
        
        if cuisine_info.get('search_keywords'):
            keywords.extend(cuisine_info['search_keywords'][:3])
        
        keywords.extend(cuisine_info["restaurant_types"][:2])
        keywords.append(cuisine_info["cuisine_type"])
        
        if cuisine_info.get('recommended_restaurant_names'):
            keywords.extend(cuisine_info['recommended_restaurant_names'][:2])
        
        return list(dict.fromkeys(keywords))

    def _call_map_api(self, keyword, radius):
        """调用地图API"""
        if not self.amap_key:
            return self._get_mock_restaurants(keyword)

        try:
            radius = float(radius) if radius else 3
            url = "https://restapi.amap.com/v3/place/around"
            
            lat, lng = self.user_location
            
            params = {
                'key': self.amap_key,
                'keywords': keyword,
                'location': f"{lng},{lat}",
                'radius': int(radius * 1000),
                'types': '050000',
                'sortrule': 'distance',
                'offset': 25,
                'page': 1,
                'extensions': 'all'
            }

            response = requests.get(url, params=params, timeout=5)
            data = response.json()

            if data['status'] == '1':
                pois = data.get('pois', [])
                results = []
                
                for poi in pois:
                    restaurant = {
                        'id': poi.get('id', ''),
                        'name': poi.get('name', ''),
                        'address': poi.get('address', ''),
                        'location': poi.get('location', ''),
                        'tel': poi.get('tel', ''),
                        'distance': int(float(poi.get('distance', 0))),
                        'biz_ext': poi.get('biz_ext', {})
                    }
                    
                    biz_ext = restaurant['biz_ext']
                    restaurant['rating'] = float(biz_ext.get('rating', 0)) if biz_ext.get('rating') else random.uniform(3.5, 5.0)
                    restaurant['avg_price'] = float(biz_ext.get('cost', 0)) if biz_ext.get('cost') else random.randint(30, 200)
                    
                    results.append(restaurant)
                
                return results
            else:
                return self._get_mock_restaurants(keyword)

        except Exception as e:
            return self._get_mock_restaurants(keyword)

    def _get_mock_restaurants(self, keyword):
        """生成模拟餐厅数据"""
        restaurant_templates = {
            "火锅": ["海底捞火锅", "小龙坎火锅", "蜀大侠火锅", "大龙燚火锅", "德庄火锅"],
            "川菜": ["眉州东坡", "陈麻婆豆腐", "巴国布衣", "蜀香园", "川味观"],
            "日料": ["将太无二", "鮨然", "隐泉日料", "一风堂拉面", "味千拉面"],
            "西餐": ["王品牛排", "豪客来", "必胜客", "萨莉亚", "新元素"],
            "中餐": ["老北京炸酱面", "东来顺", "全聚德", "便宜坊", "花家怡园"]
        }
        
        default_names = [f"老王{keyword}馆", f"{keyword}大师", f"正宗{keyword}", f"{keyword}食府"]
        
        restaurant_names = default_names
        for cuisine, names in restaurant_templates.items():
            if cuisine in keyword:
                restaurant_names = names
                break

        mock_restaurants = []
        base_lat, base_lng = self.user_location

        for i, name in enumerate(restaurant_names[:8]):
            lat_offset = random.uniform(-0.03, 0.03)
            lng_offset = random.uniform(-0.03, 0.03)
            
            lat = base_lat + lat_offset
            lng = base_lng + lng_offset
            distance = int(((lat - base_lat) ** 2 + (lng - base_lng) ** 2) ** 0.5 * 111000)

            mock_restaurants.append({
                'id': f'mock_{keyword}_{i}',
                'name': name,
                'address': f"模拟地址 - {random.choice(['东路', '西街', '南巷', '北大道'])}{random.randint(1, 999)}号",
                'location': f"{lng},{lat}",
                'tel': f"{random.choice(['010', '021', '020', '0755'])}-{random.randint(10000000, 99999999)}",
                'rating': round(random.uniform(3.5, 5.0), 1),
                'avg_price': random.randint(30, 200),
                'distance': distance
            })

        return mock_restaurants

    def _deduplicate_results(self, results):
        """去重"""
        seen = set()
        unique = []
        for restaurant in results:
            restaurant_id = restaurant.get('id', restaurant.get('name', ''))
            if restaurant_id not in seen:
                seen.add(restaurant_id)
                unique.append(restaurant)
        return unique

    def _rank_results(self, results, dish_name, cuisine_info):
        """智能排序"""
        for restaurant in results:
            score = 0
            name = restaurant.get('name', '')

            # 餐厅类型匹配
            for restaurant_type in cuisine_info.get('restaurant_types', []):
                if restaurant_type in name:
                    score += 25
                    break

            # AI推荐餐厅名称模式
            if cuisine_info.get('recommended_restaurant_names'):
                for pattern in cuisine_info['recommended_restaurant_names']:
                    if pattern in name:
                        score += 15
                        break

            # 评分权重
            rating = float(restaurant.get('rating', 0))
            score += rating * 5

            # 距离权重
            distance = int(restaurant.get('distance', 1000))
            score += max(0, 30 - distance / 100)

            # 价格匹配
            if cuisine_info.get('dish_characteristics', {}).get('price_range'):
                price_range = cuisine_info['dish_characteristics']['price_range']
                avg_price = restaurant.get('avg_price', 50)

                if price_range in ['低', 'Low'] and avg_price < 50:
                    score += 10
                elif price_range in ['中', 'Medium'] and 50 <= avg_price <= 100:
                    score += 10
                elif price_range in ['高', 'High'] and avg_price > 100:
                    score += 10

            restaurant['match_score'] = score
            restaurant['suggested_for'] = dish_name
            restaurant['cuisine_match'] = cuisine_info['cuisine_type']

            if cuisine_info.get('confidence', 0) > 0.9:
                restaurant['ai_recommended'] = True

        return sorted(results, key=lambda x: x['match_score'], reverse=True)

    def _render_map(self):
        """渲染地图"""
        st.markdown("#### 🗺️ 餐厅位置")

        # 城市选择
        cities = ["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "西安"]
        city = st.selectbox("选择城市", cities, key="city_select")

        city_locations = {
            "北京": [39.9042, 116.4074],
            "上海": [31.2304, 121.4737],
            "广州": [23.1291, 113.2644],
            "深圳": [22.5431, 114.0579],
            "杭州": [30.2741, 120.1551],
            "成都": [30.5728, 104.0668],
            "武汉": [30.5928, 114.3055],
            "西安": [34.2658, 108.9541]
        }

        if city in city_locations:
            self.user_location = city_locations[city]
            st.session_state.user_location = self.user_location

        # 创建地图
        m = folium.Map(
            location=self.user_location,
            zoom_start=13,
            tiles='OpenStreetMap',
            control_scale=True
        )

        # 用户位置标记
        folium.Marker(
            location=self.user_location,
            popup="您的位置",
            tooltip="您在这里",
            icon=folium.Icon(color='green', icon='user', prefix='fa')
        ).add_to(m)

        # 餐厅标记
        if st.session_state.search_results:
            st.info(f"🔍 在地图上显示 {len(st.session_state.search_results)} 个搜索结果")
            
            bounds = []
            for idx, restaurant in enumerate(st.session_state.search_results[:10]):
                if 'location' in restaurant:
                    try:
                        lng, lat = map(float, restaurant['location'].split(','))
                        
                        html = f"""
                        <div style="font-family: Arial; width: 200px;">
                            <h4 style="color: #2196F3; margin: 5px 0;">{restaurant['name']}</h4>
                            <p style="margin: 5px 0;"><b>地址:</b> {restaurant.get('address', '未知')}</p>
                            <p style="margin: 5px 0;"><b>评分:</b> ⭐ {restaurant.get('rating', '暂无')}</p>
                            <p style="margin: 5px 0;"><b>人均:</b> ¥{restaurant.get('avg_price', '未知')}</p>
                            <p style="margin: 5px 0;"><b>推荐:</b> {restaurant.get('suggested_for', '')}</p>
                        </div>
                        """

                        popup = folium.Popup(html=html, max_width=250)
                        color = 'red' if idx < 3 else 'blue'

                        folium.Marker(
                            location=[lat, lng],
                            popup=popup,
                            tooltip=f"{idx + 1}. {restaurant['name']}",
                            icon=folium.Icon(color=color, icon='cutlery', prefix='fa')
                        ).add_to(m)

                        bounds.append([lat, lng])

                    except Exception as e:
                        st.warning(f"无法解析餐厅位置: {restaurant['name']}")

            if bounds:
                bounds.append(self.user_location)
                m.fit_bounds(bounds)

        # 显示地图
        st_folium(m, width=700, height=500, key="restaurant_map")

    def _render_search_results(self):
        """渲染搜索结果"""
        if not st.session_state.search_results:
            return

        st.markdown("---")
        st.markdown("## 🍽️ 搜索结果")

        # AI分析结果
        if st.session_state.cuisine_info:
            cuisine_info = st.session_state.cuisine_info
            dish_name = st.session_state.search_dish

            with st.expander("🤖 AI分析结果", expanded=True):
                ai_col1, ai_col2 = st.columns(2)
                
                with ai_col1:
                    st.markdown(f"**搜索菜品**: {dish_name}")
                    st.markdown(f"**识别菜系**: {cuisine_info['cuisine_type']}")
                    analysis_method = 'AI智能分析' if cuisine_info.get('analysis_method') == 'deepseek_ai' else '规则匹配'
                    st.markdown(f"**分析方法**: {analysis_method}")
                    st.markdown(f"**置信度**: {cuisine_info.get('confidence', 0) * 100:.1f}%")

                with ai_col2:
                    if cuisine_info.get('dish_characteristics'):
                        chars = cuisine_info['dish_characteristics']
                        st.markdown("**菜品特征**:")
                        if chars.get('spicy_level'):
                            try:
                                spicy_num = int(float(chars['spicy_level']))
                                st.markdown(f"- 辣度: {'🌶️' * spicy_num}")
                            except:
                                st.markdown(f"- 辣度: {chars['spicy_level']}")
                        if chars.get('price_range'):
                            st.markdown(f"- 价格: {chars['price_range']}")
                        if chars.get('cooking_method'):
                            st.markdown(f"- 烹饪: {chars['cooking_method']}")

                if cuisine_info.get('similar_dishes'):
                    st.markdown(f"**相似菜品**: {', '.join(cuisine_info['similar_dishes'][:5])}")

        # 餐厅列表
        st.info(f"📊 找到 {len(st.session_state.search_results)} 家相关餐厅")

        for idx, restaurant in enumerate(st.session_state.search_results[:10]):
            with st.container():
                # 餐厅标题
                ai_badge = "🤖 " if restaurant.get('ai_recommended') else ""
                st.markdown(f"### {ai_badge}{idx + 1}. {restaurant['name']}")
                
                # 餐厅信息
                info_parts = []
                info_parts.append(f"📍 {restaurant.get('address', '地址未知')}")
                info_parts.append(f"⭐ {restaurant.get('rating', 'N/A')}")
                info_parts.append(f"💰 人均 ¥{restaurant.get('avg_price', 'N/A')}")
                
                if 'distance' in restaurant:
                    distance = restaurant['distance']
                    if distance < 1000:
                        info_parts.append(f"📏 {distance}m")
                    else:
                        info_parts.append(f"📏 {distance / 1000:.1f}km")
                
                st.markdown(" | ".join(info_parts))

                # 操作按钮
                btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)
                
                with btn_col1:
                    if st.button("📋 查看详情", key=f"detail_btn_{idx}"):
                        self._show_restaurant_detail(restaurant, idx)
                
                with btn_col2:
                    if st.button("🧭 导航", key=f"nav_btn_{idx}"):
                        self._show_navigation(restaurant, idx)
                
                with btn_col3:
                    if st.button("⭐ 收藏", key=f"fav_btn_{idx}"):
                        self._add_to_favorites(restaurant)
                
                with btn_col4:
                    if restaurant.get('tel'):
                        st.markdown(f"📞 {restaurant['tel']}")

                st.divider()

    def _show_restaurant_detail(self, restaurant, idx):
        """显示餐厅详情"""
        with st.expander(f"🍽️ {restaurant['name']} - 详细信息", expanded=True):
            detail_col1, detail_col2 = st.columns(2)
            
            with detail_col1:
                st.markdown("**基本信息**")
                st.write(f"📍 地址: {restaurant.get('address', '未知')}")
                st.write(f"📞 电话: {restaurant.get('tel', '未知')}")
                st.write(f"⭐ 评分: {restaurant.get('rating', '暂无')}")
                st.write(f"💰 人均: ¥{restaurant.get('avg_price', '未知')}")

            with detail_col2:
                st.markdown("**推荐信息**")
                st.write(f"🍽️ 推荐菜品: {restaurant.get('suggested_for', '')}")
                st.write(f"🏷️ 菜系匹配: {restaurant.get('cuisine_match', '')}")
                if restaurant.get('ai_recommended'):
                    st.write("🤖 AI推荐")
                if 'distance' in restaurant:
                    distance = restaurant['distance']
                    if distance < 1000:
                        st.write(f"📏 距离: {distance}m")
                    else:
                        st.write(f"📏 距离: {distance / 1000:.1f}km")

    def _show_navigation(self, restaurant, idx):
        """显示导航选项"""
        if 'location' in restaurant:
            location = restaurant['location']
            restaurant_name = restaurant['name']
            
            with st.expander(f"🚗 {restaurant_name} - 导航选项", expanded=True):
                st.markdown("**选择导航方式:**")

                lng, lat = location.split(',')
                amap_url = f"https://uri.amap.com/navigation?to={location},{restaurant_name}&mode=car&policy=1&src=myapp&coordinate=gaode&callnative=0"
                baidu_url = f"http://api.map.baidu.com/direction?destination=latlng:{lat},{lng}|name:{restaurant_name}&mode=driving&src=webapp.baidu.openAPIdemo"
                tx_url = f"https://apis.map.qq.com/uri/v1/routeplan?type=drive&to={restaurant_name}&tocoord={lat},{lng}"

                st.markdown(f"- [📍 高德导航]({amap_url})")
                st.markdown(f"- [📍 百度导航]({baidu_url})")
                st.markdown(f"- [📍 腾讯导航]({tx_url})")

    def _add_to_favorites(self, restaurant):
        """添加到收藏"""
        if 'favorites' not in st.session_state:
            st.session_state.favorites = []

        if not any(fav['id'] == restaurant['id'] for fav in st.session_state.favorites):
            st.session_state.favorites.append(restaurant)
            st.success(f"已收藏 {restaurant['name']}")

            # 如果用户已登录，保存到数据库
            if st.session_state.get('logged_in') and st.session_state.get('db_manager'):
                try:
                    favorite_data = {
                        'restaurant': restaurant,
                        'saved_at': datetime.now(),
                        'dish_searched': st.session_state.get('search_dish', ''),
                        'type': 'restaurant_favorite'
                    }
                    st.session_state.db_manager.save_recipe(st.session_state.username, favorite_data)
                except Exception as e:
                    st.warning("收藏保存到云端失败，仅保存在本地")
        else:
            st.warning(f"{restaurant['name']} 已在收藏中")
