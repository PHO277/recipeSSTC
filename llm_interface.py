from openai import OpenAI
import json
import re

class LLMInterface:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    def generate_recipe_and_nutrition(self, ingredients, diet, goal, language="en", cuisine=None, cooking_time=None, difficulty=None, servings=2):
        prompt = f"""
        You are a professional chef and certified nutritionist with expertise in creating delicious, healthy recipes. Create a detailed, creative recipe using these ingredients: {ingredients}. All text content (recipe name, description, ingredients, instructions, etc.) must be in the user's preferred language ({language}), but the JSON field names must be in English.

        Requirements:
        - Dietary preference: {diet} (if empty, ignore this constraint)
        - Health goal: {goal} (if empty, focus on general nutrition)
        - Cuisine: {cuisine if cuisine else 'any'}
        - Cooking time: {cooking_time if cooking_time else 'any'}
        - Difficulty: {difficulty if difficulty else 'medium'}
        - Servings: {servings}
        - Provide accurate nutritional estimates based on USDA data
        - Output must be in JSON format with English field names

        Format the response EXACTLY as follows, with field names in English and content in {language}:
        ```json
        {{
            "title": "[Creative, appetizing recipe name in {language}]",
            "description": "[Brief description in {language} highlighting dietary preferences, health goals, and cuisine]",
            "ingredients": [
                "[Ingredient 1 with specific quantity in {language}, e.g., '2 large chicken breasts (6 oz each)']",
                "[Ingredient 2 with specific quantity in {language}]",
                "..."
            ],
            "instructions": [
                "[Complete sentence for step 1 in {language} with timing and technique tips]",
                "[Complete sentence for step 2 in {language} with specific actions]",
                "..."
            ],
            "nutrition": {{
                "Calories": "[Total per serving] kcal",
                "Protein": "[Amount] g",
                "Carbohydrates": "[Amount] g",
                "Fat": "[Amount] g",
                "Fiber": "[Amount] g",
                "Sugar": "[Amount] g",
                "Sodium": "[Amount] mg",
                "Vitamin A": "[Amount] IU",
                "Calcium": "[Amount] mg",
                "Iron": "[Amount] mg"
            }},
            "serves": {servings},
            "prep_time": "[Minutes] min",
            "cook_time": "[Minutes] min",
            "difficulty": "[Easy/Medium/Hard in {language}]"
        }}
        ```

        Additional considerations:
        - Strictly adhere to dietary preferences (e.g., vegan, gluten-free)
        - Optimize for health goals:
          * Muscle Gain: High protein, moderate carbs, healthy fats
          * Weight Loss: Lower calories, high fiber, lean proteins
          * Energy Boost: Complex carbs, B-vitamins
          * Heart Health: Low sodium, omega-3s, minimal saturated fat
        - Use precise measurements and cooking techniques
        - Ensure all content text is in {language}, but JSON field names remain in English
        """
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system",
                        "content": f"""You are a world-class chef and nutritionist creating recipes in {language}. 
                        Your recipes are delicious, nutritionally optimized, and formatted in JSON with English field names. 
                        Use precise measurements and provide detailed instructions in {language}. Return the response strictly within ```json\n...\n```."""
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.9,
                max_tokens=2500,
                stream=False
            )
            raw_content = response.choices[0].message.content
            # Extract JSON content from ```json ... ``` block
            json_match = re.search(r'```json\n(.*?)\n```', raw_content, re.DOTALL)
            if not json_match:
                print(f"Invalid JSON block: {raw_content}")
                raise Exception("API response does not contain valid JSON block")
            json_content = json_match.group(1)
            return json.loads(json_content)
        except Exception as e:
            print(f"API error: {str(e)}")
            raise Exception(f"API call failed: {str(e)}")
