import tkinter as tk
from gui import ModernRecipeGUI  # Import the enhanced GUI
from llm_interface import LLMInterface
from nutrition_analyzer import NutritionAnalyzer
from text_to_speech import TextToSpeech
import sys
import os


class EnhancedRecipeApp:
    def __init__(self):
        # 修复Windows高DPI模糊问题
        try:
            import ctypes
            # 告知Windows应用程序支持高DPI
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
    
        self.root = tk.Tk()
        
        # Set window icon if available
        try:
            if sys.platform.startswith('win'):
                # Windows
                self.root.iconbitmap(default='recipe_icon.ico')
            else:
                # Linux/Mac - use a simple emoji as window icon
                pass
        except:
            pass
        
        # Center the window on screen
        self.center_window()
        
        # Initialize components
        self.llm = LLMInterface(api_key="sk-2f84eddd839241049be5239b80c8516f")  # Replace with your DeepSeek API key
        self.nutrition = NutritionAnalyzer()
        self.tts = TextToSpeech()
        
        # Initialize the modern GUI
        self.gui = ModernRecipeGUI(self.root, self.generate_recipe, self.play_audio)
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def center_window(self):
        """Center the window on the screen"""
        self.root.update_idletasks()
        width = 1200
        height = 800
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def generate_recipe(self, ingredients, diet, goal):
        """Generate recipe with enhanced error handling and logging"""
        try:
            # Generate recipe using LLM
            llm_output = self.llm.generate_recipe_and_nutrition(ingredients, diet, goal)
            
            # Parse nutrition information
            nutrition = self.nutrition.parse_nutrition(llm_output)
            
            # Extract recipe part (everything before nutrition facts)
            if "## Nutrition Facts" in llm_output:
                recipe = llm_output.split("## Nutrition Facts")[0].strip()
            else:
                # Fallback if format is different
                recipe = llm_output.strip()
            
            return recipe, nutrition
            
        except Exception as e:
            # Enhanced error handling
            error_recipe = f"""**Title**: Recipe Generation Error

**Error Details**:
- {str(e)}

**Troubleshooting**:
- Check your internet connection
- Verify API key is valid
- Try with simpler ingredient list
- Ensure ingredients are food items

**Suggested Actions**:
1. Try again with different ingredients
2. Check the status bar for more information
3. Contact support if problem persists"""
            
            error_nutrition = "- Calories: Not available\n- Protein: Not available\n- Fat: Not available\n- Carbohydrates: Not available"
            return error_recipe, error_nutrition

    def play_audio(self, text):
        """Play audio with enhanced error handling"""
        try:
            self.tts.speak(text)
        except Exception as e:
            print(f"Audio playback error: {e}")
            # Could show a popup or status message here

    def on_closing(self):
        """Handle application closing"""
        try:
            # Stop any ongoing TTS
            if hasattr(self.tts, 'engine') and self.tts.engine:
                self.tts.engine.stop()
        except:
            pass
        
        # Destroy the window
        self.root.quit()
        self.root.destroy()

    def run(self):
        """Start the application"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.on_closing()
        except Exception as e:
            print(f"Application error: {e}")
            self.on_closing()

def main():
    """Main entry point"""
    try:
        app = EnhancedRecipeApp()
        app.run()
    except Exception as e:
        print(f"Failed to start application: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()