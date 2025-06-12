import re

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
            'sodium': r'sodium[:\s]*(\d+(?:\.\d+)?)\s*mg'
        }

    def parse_nutrition(self, llm_output):
        """Enhanced nutrition parsing with better formatting and error handling"""
        try:
            # Split the output to find nutrition section
            sections = llm_output.split("## Nutrition Facts")
            if len(sections) < 2:
                # Try alternative section headers
                sections = llm_output.split("Nutrition Facts")
                if len(sections) < 2:
                    sections = llm_output.split("**Nutrition")
                    if len(sections) < 2:
                        return self._generate_fallback_nutrition()
            
            nutrition_section = sections[1].strip()
            
            # Extract nutrition facts using multiple methods
            nutrition_data = self._extract_nutrition_data(nutrition_section)
            
            if not nutrition_data:
                return self._generate_fallback_nutrition()
            
            # Format the nutrition data for display
            return self._format_nutrition_display(nutrition_data)
            
        except Exception as e:
            print(f"Nutrition parsing error: {e}")
            return self._generate_fallback_nutrition()

    def _extract_nutrition_data(self, nutrition_text):
        """Extract nutrition data using various parsing methods"""
        nutrition_data = {}
        
        # Method 1: Parse structured list format (- Calories: 350 kcal)
        lines = nutrition_text.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("-") or line.startswith("•"):
                # Remove list markers and parse
                clean_line = re.sub(r'^[-•*]\s*', '', line)
                parsed = self._parse_nutrition_line(clean_line)
                if parsed:
                    nutrition_data.update(parsed)
        
        # Method 2: Use regex patterns to find nutrition values
        if not nutrition_data:
            for nutrient, pattern in self.nutrition_patterns.items():
                match = re.search(pattern, nutrition_text, re.IGNORECASE)
                if match:
                    value = match.group(1)
                    unit = self._get_nutrient_unit(nutrient)
                    nutrition_data[nutrient] = f"{value} {unit}"
        
        # Method 3: Parse key-value pairs separated by colons
        if not nutrition_data:
            for line in lines:
                if ':' in line:
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        key = re.sub(r'[^a-zA-Z\s]', '', parts[0]).strip().lower()
                        value = parts[1].strip()
                        
                        # Match common nutrition terms
                        for nutrient in self.nutrition_patterns.keys():
                            if nutrient in key or key in nutrient:
                                nutrition_data[nutrient] = value
                                break
        
        return nutrition_data

    def _parse_nutrition_line(self, line):
        """Parse a single nutrition line"""
        if ':' not in line:
            return None
        
        parts = line.split(':', 1)
        if len(parts) != 2:
            return None
        
        key = parts[0].strip().lower()
        value = parts[1].strip()
        
        # Map common nutrition terms to standard names
        key_mappings = {
            'calories': 'calories',
            'kcal': 'calories',
            'cal': 'calories',
            'protein': 'protein',
            'fat': 'fat',
            'total fat': 'fat',
            'carbs': 'carbohydrates',
            'carbohydrates': 'carbohydrates',
            'carbohydrate': 'carbohydrates',
            'fiber': 'fiber',
            'dietary fiber': 'fiber',
            'sugar': 'sugar',
            'sugars': 'sugar',
            'sodium': 'sodium',
            'salt': 'sodium'
        }
        
        for term, standard_key in key_mappings.items():
            if term in key:
                return {standard_key: value}
        
        return None

    def _get_nutrient_unit(self, nutrient):
        """Get the standard unit for a nutrient"""
        units = {
            'calories': 'kcal',
            'protein': 'g',
            'fat': 'g',
            'carbohydrates': 'g',
            'fiber': 'g',
            'sugar': 'g',
            'sodium': 'mg'
        }
        return units.get(nutrient, 'g')

    def _format_nutrition_display(self, nutrition_data):
        """Format nutrition data for better display"""
        if not nutrition_data:
            return self._generate_fallback_nutrition()
        
        # Order nutrients logically
        nutrient_order = ['calories', 'protein', 'fat', 'carbohydrates', 'fiber', 'sugar', 'sodium']
        formatted_lines = []
        
        for nutrient in nutrient_order:
            if nutrient in nutrition_data:
                value = nutrition_data[nutrient]
                # Clean up the value formatting
                clean_value = re.sub(r'\s+', ' ', value).strip()
                formatted_lines.append(f"- {nutrient.title()}: {clean_value}")
        
        # Add any additional nutrients not in the standard order
        for nutrient, value in nutrition_data.items():
            if nutrient not in nutrient_order:
                clean_value = re.sub(r'\s+', ' ', value).strip()
                formatted_lines.append(f"- {nutrient.title()}: {clean_value}")
        
        return "\n".join(formatted_lines) if formatted_lines else self._generate_fallback_nutrition()

    def _generate_fallback_nutrition(self):
        """Generate fallback nutrition information when parsing fails"""
        return """- Calories: Not available
- Protein: Not available  
- Fat: Not available
- Carbohydrates: Not available
- Fiber: Not available
- Sugar: Not available
- Sodium: Not available"""

    def calculate_nutrition_score(self, nutrition_data, goal="General Health"):
        """Calculate a nutrition score based on health goals"""
        try:
            # Extract numeric values
            values = {}
            for line in nutrition_data.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.replace('-', '').strip().lower()
                    # Extract numeric value
                    numbers = re.findall(r'\d+(?:\.\d+)?', value)
                    if numbers:
                        values[key] = float(numbers[0])
            
            if not values:
                return "Unable to calculate nutrition score"
            
            # Simple scoring based on goals
            score_components = []
            
            if goal == "Muscle Gain":
                if 'protein' in values:
                    protein_score = min(values['protein'] / 30 * 100, 100)  # 30g+ protein = 100%
                    score_components.append(f"Protein: {protein_score:.0f}%")
            
            elif goal == "Weight Loss":
                if 'calories' in values:
                    cal_score = max(100 - (values['calories'] - 400) / 10, 0)  # Lower calories = higher score
                    score_components.append(f"Calorie Control: {cal_score:.0f}%")
            
            elif goal == "Heart Health":
                if 'sodium' in values:
                    sodium_score = max(100 - (values['sodium'] - 600) / 20, 0)  # Lower sodium = higher score
                    score_components.append(f"Heart Health: {sodium_score:.0f}%")
            
            return " | ".join(score_components) if score_components else "Nutrition analysis complete"
            
        except Exception:
            return "Nutrition score calculation unavailable"