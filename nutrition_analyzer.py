import re
import json

class NutritionAnalyzer:
    def __init__(self):
        """Initialize the nutrition analyzer with standard nutrition patterns"""
        self.nutrition_patterns = {
            'calories': r'calories?[:\s]*(\d+(?:\.\d+)?)\s*(?:kcal|cal)?',
            'protein': r'protein[:\s]*(\d+(?:\.\d+)?)\s*g',
            'fat': r'fat[:\s]*(\d+(?:\.\d+)?)\s*g',
            'carbohydrates': r'carbohydrates?[:\s]*(\d+(?:\.\d+)?)\s*g',
            'fiber': r'fiber[:\s]*(\d+(?:\.\d+)?)\s*g',
            'sugar': r'sugar[:\s]*(\d+(?:\.\d+)?)\s*g',
            'sodium': r'sodium[:\s]*(\d+(?:\.\d+)?)\s*mg',
            'vitamin a': r'vitamin a[:\s]*(\d+(?:\.\d+)?)\s*IU',
            'calcium': r'calcium[:\s]*(\d+(?:\.\d+)?)\s*mg',
            'iron': r'iron[:\s]*(\d+(?:\.\d+)?)\s*mg'
        }

    def parse_nutrition(self, llm_output):
        """Parse JSON-formatted nutrition data"""
        try:
            # llm_output is expected to be a JSON dict, extract 'nutrition' field
            nutrition_data = llm_output.get('nutrition', {})
            
            if not nutrition_data:
                return self._generate_fallback_nutrition()
            
            return self._format_nutrition_display(nutrition_data)
            
        except Exception as e:
            print(f"Nutrition parsing error: {e}")
            return self._generate_fallback_nutrition()

    def _format_nutrition_display(self, nutrition_data):
        """Format JSON nutrition data for display"""
        if not nutrition_data:
            return self._generate_fallback_nutrition()
        
        nutrient_order = ['Calories', 'Protein', 'Carbohydrates', 'Fat', 'Fiber', 'Sugar', 'Sodium', 'Vitamin A', 'Calcium', 'Iron']
        formatted_lines = []
        
        for nutrient in nutrient_order:
            if nutrient in nutrition_data:
                value = nutrition_data[nutrient]
                formatted_lines.append(f"- {nutrient}: {value}")
        
        return "\n".join(formatted_lines) if formatted_lines else self._generate_fallback_nutrition()

    def _generate_fallback_nutrition(self):
        """Generate fallback nutrition information when parsing fails"""
        return """- Calories: Not available
- Protein: Not available
- Carbohydrates: Not available
- Fat: Not available
- Fiber: Not available
- Sugar: Not available
- Sodium: Not available
- Vitamin A: Not available
- Calcium: Not available
- Iron: Not available"""

    