from openai import OpenAI

class LLMInterface:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    def generate_recipe_and_nutrition(self, ingredients, diet, goal):
        # Enhanced prompt for better formatting and more comprehensive recipes
        prompt = f"""
        You are a professional chef and certified nutritionist with expertise in creating delicious, healthy recipes. 
        Create a detailed, creative recipe using these ingredients: {ingredients}.
        
        Requirements:
        - Dietary preference: {diet} (if "None", ignore this constraint)
        - Health goal: {goal} (if "None", focus on general nutrition)
        - Recipe should be practical and achievable for home cooks
        - Include cooking tips and techniques
        - Provide accurate nutritional estimates
        
        Please format your response EXACTLY as follows:

        **Title**: [Creative, appetizing recipe name]

        **Ingredients**:
        - [Ingredient 1 with specific quantity, e.g., "2 large chicken breasts (6 oz each)"]
        - [Ingredient 2 with specific quantity]
        - [Continue for all ingredients, including seasonings and garnishes]

        **Instructions**:
        1. [Detailed step 1 with cooking technique and timing]
        2. [Detailed step 2 with temperature/heat level specifics]
        3. [Continue with clear, numbered steps]
        4. [Include plating and serving suggestions]

        **Chef's Tips**:
        - [Professional tip 1 for better results]
        - [Professional tip 2 for flavor enhancement]
        - [Substitution suggestions if needed]

        **Serving Information**:
        - Serves: [Number of people]
        - Prep time: [Minutes]
        - Cook time: [Minutes]
        - Difficulty: [Easy/Medium/Hard]

        ## Nutrition Facts
        - Calories: [Total per serving] kcal
        - Protein: [Amount] g
        - Fat: [Amount] g  
        - Carbohydrates: [Amount] g
        - Fiber: [Amount] g
        - Sugar: [Amount] g
        - Sodium: [Amount] mg

        Additional considerations:
        - If dietary preference is specified, ensure the recipe strictly adheres to it
        - If health goal is specified, optimize the recipe accordingly:
          * Muscle Gain: High protein, moderate carbs, healthy fats
          * Weight Loss: Lower calories, high fiber, lean proteins
          * General Health: Balanced macronutrients, plenty of vegetables
          * Energy Boost: Complex carbs, B-vitamins, moderate caffeine if appropriate
          * Heart Health: Low sodium, omega-3 fatty acids, minimal saturated fat
        - Base nutritional calculations on standard USDA nutritional data
        - Consider portion sizes and cooking methods in nutritional calculations
        """
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system", 
                        "content": """You are a world-class chef and nutritionist. You create restaurant-quality recipes 
                        that are adapted for home cooking. Your recipes are known for being both delicious and nutritionally 
                        optimized. You always provide accurate nutritional information and helpful cooking tips. 
                        Format your responses exactly as requested, using clear structure and specific measurements."""
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=1.0,  # Add some creativity while maintaining consistency
                max_tokens=2000,  # Ensure complete responses
                stream=False
            )
            return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"API call failed: {str(e)}.")

    def get_recipe_suggestions(self, ingredients):
        """Get quick recipe name suggestions based on ingredients"""
        prompt = f"""
        Based on these ingredients: {ingredients}
        
        Suggest 3 creative recipe names that could be made with these ingredients. 
        Respond with just the names, one per line, no additional formatting.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "You are a creative chef who suggests innovative recipe names."},
                    {"role": "user", "content": prompt}
                ],
                temperature=1.0,
                max_tokens=150,
                stream=False
            )
            return response.choices[0].message.content.strip().split('\n')
        except:
            return [f"Delicious {ingredients.split(',')[0].strip().title()} Dish"]