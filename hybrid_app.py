"""
混合版本：保留原有Streamlit组件，添加Flask API
这样可以同时支持Web界面和桌面打包
"""

from flask import Flask, jsonify, request, render_template
import streamlit.components.v1 as components

# 导入你的原有模块
from mongodb_manager import MongoDBManager
from llm_interface import LLMInterface
from nutrition_analyzer import NutritionAnalyzer
from components.image_input_modal import ImageInputModal

app = Flask(__name__)

# 初始化你的服务
db_manager = MongoDBManager("mongodb://localhost:27017/recipe_app")
llm_interface = LLMInterface(api_key=os.getenv("DEEPSEEK_API_KEY"))
nutrition_analyzer = NutritionAnalyzer()

@app.route('/api/generate-recipe', methods=['POST'])
def generate_recipe_real():
    """使用你原有的AI生成逻辑"""
    data = request.json
    
    try:
        # 使用你原有的LLM接口
        result = llm_interface.generate_recipe_and_nutrition(
            ingredients=data.get('ingredients', ''),
            diet=data.get('diet', ''),
            goal=data.get('goal', ''),
            language=data.get('language', 'en'),
            cuisine=data.get('cuisine', ''),
            cooking_time=data.get('cooking_time', ''),
            difficulty=data.get('difficulty', ''),
            servings=data.get('servings', 4)
        )
        
        # 使用你原有的营养分析
        nutrition_info = nutrition_analyzer.parse_nutrition(result)
        
        return jsonify({
            "success": True,
            "recipe": result.get('recipe', ''),
            "nutrition": nutrition_info
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

@app.route('/api/image-recognition', methods=['POST'])
def image_recognition():
    """使用你原有的图像识别功能"""
    try:
        files = request.files.getlist('images')
        language = request.form.get('language', 'en')
        
        # 使用你原有的图像识别逻辑
        results = image_modal.call_siliconflow_api(files, language)
        
        return jsonify({
            "success": True,
            "ingredients": results
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })
