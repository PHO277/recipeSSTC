import tkinter as tk
from tkinter import ttk, scrolledtext
import markdown
import threading
import queue
from bs4 import BeautifulSoup
import re

class ModernRecipeGUI:
    def __init__(self, root, generate_callback, audio_callback):
        self.root = root
        self.root.title("🍳 AI Recipe Generator & Nutrition Analyzer")
        self.root.geometry("1200x1000")
        self.root.configure(bg='#f8f9fa')
        
        # Color scheme
        self.colors = {
            'primary': '#2c3e50',
            'secondary': '#3498db',
            'accent': '#e74c3c',
            'success': '#27ae60',
            'warning': '#f39c12',
            'light': '#ecf0f1',
            'dark': '#34495e',
            'white': '#ffffff',
            'gradient_start': '#667eea',
            'gradient_end': '#764ba2'
        }
        
        self.generate_callback = generate_callback
        self.audio_callback = audio_callback
        self.generation_thread = None
        self.audio_thread = None
        self.stop_generation = False
        self.stop_audio = False
        self.audio_playing = False
        self.plain_text = ""
        
        self.setup_styles()
        self.setup_gui()
        
    def setup_styles(self):
        """Configure modern styles for ttk widgets"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure button styles
        style.configure('Modern.TButton',
                       background=self.colors['secondary'],
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       padding=(20, 10))
        
        style.map('Modern.TButton',
                 background=[('active', self.colors['primary']),
                           ('pressed', self.colors['dark'])])
        
        style.configure('Accent.TButton',
                       background=self.colors['accent'],
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       padding=(15, 8))
        
        style.map('Accent.TButton',
                 background=[('active', '#c0392b'),
                           ('pressed', '#a93226')])
        
        style.configure('Success.TButton',
                       background=self.colors['success'],
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       padding=(15, 8))
        
        # Configure combobox styles
        style.configure('Modern.TCombobox',
                       fieldbackground='white',
                       background=self.colors['light'],
                       borderwidth=1,
                       relief='solid')

    def setup_gui(self):
        # Main container with padding
        main_frame = tk.Frame(self.root, bg='#f8f9fa', padx=30, pady=20)
        main_frame.pack(fill='both', expand=True)
        
        # Header
        self.create_header(main_frame)
        
        # Input section
        self.create_input_section(main_frame)
        
        # Output section
        self.create_output_section(main_frame)
        
        # Setup queues for thread communication
        self.result_queue = queue.Queue()
        self.error_queue = queue.Queue()
        self.root.after(100, self.check_queue)

    def create_header(self, parent):
        """Create modern header with gradient-like effect"""
        header_frame = tk.Frame(parent, bg='#f8f9fa', height=120)
        header_frame.pack(fill='x', pady=(0, 10))
        header_frame.pack_propagate(False)
        
        # Title with icon
        title_label = tk.Label(header_frame, 
                              text="🍳 AI Recipe Generator", 
                              font=('Segoe UI', 28, 'bold'),
                              fg=self.colors['primary'],
                              bg='#f8f9fa')
        title_label.pack(side='top', pady=(10, 5))
        
        subtitle_label = tk.Label(header_frame,
                                 text="Generate personalized recipes with AI-powered nutrition analysis",
                                 font=('Segoe UI', 12),
                                 fg=self.colors['dark'],
                                 bg='#f8f9fa')
        subtitle_label.pack(side='top')

    def create_input_section(self, parent):
        """Create modern input section with cards"""
        input_frame = tk.Frame(parent, bg='#f8f9fa')
        input_frame.pack(fill='x', pady=(0, 0))
        
        # Input card
        card_frame = tk.Frame(input_frame, bg='white', relief='solid', bd=1)
        card_frame.pack(fill='x', padx=5, pady=5)
        
        # Card header
        card_header = tk.Frame(card_frame, bg=self.colors['primary'], height=50)
        card_header.pack(fill='x')
        card_header.pack_propagate(False)
        
        header_label = tk.Label(card_header,
                               text="🥘 Recipe Configuration",
                               font=('Segoe UI', 14, 'bold'),
                               fg='white',
                               bg=self.colors['primary'])
        header_label.pack(side='left', padx=20, pady=0)
        
        # Card content
        content_frame = tk.Frame(card_frame, bg='white', padx=30, pady=10)
        content_frame.pack(fill='both', expand=True)
        
        # Ingredients input with icon
        ingredients_frame = tk.Frame(content_frame, bg='white')
        ingredients_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(ingredients_frame, 
                text="🥬 Available Ingredients",
                font=('Segoe UI', 12, 'bold'),
                fg=self.colors['primary'],
                bg='white').pack(anchor='w')
        
        tk.Label(ingredients_frame,
                text="Enter ingredients separated by commas (e.g., chicken breast, spinach, tomatoes)",
                font=('Segoe UI', 9),
                fg=self.colors['dark'],
                bg='white').pack(anchor='w', pady=(2, 8))
        
        self.ingredients_entry = tk.Entry(ingredients_frame, 
                                        font=('Segoe UI', 11),
                                        relief='solid', 
                                        bd=1,
                                        bg='#fbfcfd',
                                        fg=self.colors['dark'])
        self.ingredients_entry.pack(fill='x', ipady=8)
        
        # Preferences row
        prefs_frame = tk.Frame(content_frame, bg='white')
        prefs_frame.pack(fill='x', pady=(0, 15))
        
        # Dietary preferences
        diet_frame = tk.Frame(prefs_frame, bg='white')
        diet_frame.pack(side='left', fill='x', expand=True, padx=(0, 15))
        
        tk.Label(diet_frame,
                text="🌱 Dietary Preference",
                font=('Segoe UI', 12, 'bold'),
                fg=self.colors['primary'],
                bg='white').pack(anchor='w')
        
        self.diet_var = tk.StringVar(value="None")
        diets = ["None", "Low-Carb", "Vegan", "Gluten-Free", "Keto", "Mediterranean", "Paleo"]
        self.diet_dropdown = ttk.Combobox(diet_frame, 
                                        textvariable=self.diet_var, 
                                        values=diets, 
                                        state="readonly",
                                        style='Modern.TCombobox',
                                        font=('Segoe UI', 10))
        self.diet_dropdown.pack(fill='x', pady=(8, 0), ipady=5)
        
        # Goals
        goal_frame = tk.Frame(prefs_frame, bg='white')
        goal_frame.pack(side='right', fill='x', expand=True)
        
        tk.Label(goal_frame,
                text="🎯 Health Goal",
                font=('Segoe UI', 12, 'bold'),
                fg=self.colors['primary'],
                bg='white').pack(anchor='w')
        
        self.goal_var = tk.StringVar(value="None")
        goals = ["None", "Muscle Gain", "Weight Loss", "General Health", "Energy Boost", "Heart Health"]
        self.goal_dropdown = ttk.Combobox(goal_frame,
                                        textvariable=self.goal_var,
                                        values=goals,
                                        state="readonly",
                                        style='Modern.TCombobox',
                                        font=('Segoe UI', 10))
        self.goal_dropdown.pack(fill='x', pady=(8, 0), ipady=5)
        
        # Generate button
        button_frame = tk.Frame(content_frame, bg='white')
        button_frame.pack(pady=(10, 0))
        
        self.generate_button = ttk.Button(button_frame,
                                        text="✨ Generate Recipe",
                                        command=self.generate_recipe,
                                        style='Modern.TButton')
        self.generate_button.pack(side='left', padx=(0, 15))
        
        # Audio button (initially hidden)
        self.audio_button = ttk.Button(button_frame,
                                     text="🔊 Play Recipe Audio",
                                     command=self.toggle_audio,
                                     style='Success.TButton',
                                     state='disabled')
        self.audio_button.pack(side='left')

    def create_output_section(self, parent):
        """Create modern output section with recipe and nutrition cards"""
        output_frame = tk.Frame(parent, bg='#f8f9fa')
        output_frame.pack(fill='both', expand=True)
        
        # Create notebook for tabbed interface
        self.notebook = ttk.Notebook(output_frame)
        self.notebook.pack(fill='both', expand=True, pady=(10, 0))
        
        # Recipe tab
        recipe_frame = tk.Frame(self.notebook, bg='white')
        self.notebook.add(recipe_frame, text='📋 Recipe')
        
        # Nutrition tab
        nutrition_frame = tk.Frame(self.notebook, bg='white')
        self.notebook.add(nutrition_frame, text='📊 Nutrition Analysis')
        
        # Setup recipe display
        self.setup_recipe_tab(recipe_frame)
        
        # Setup nutrition display
        self.setup_nutrition_tab(nutrition_frame)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready to generate your perfect recipe! 🚀")
        status_bar = tk.Label(output_frame,
                            textvariable=self.status_var,
                            font=('Segoe UI', 10),
                            fg=self.colors['dark'],
                            bg=self.colors['light'],
                            relief='sunken',
                            bd=1)
        status_bar.pack(fill='x', pady=(10, 0), ipady=5)

    def setup_recipe_tab(self, parent):
        """Setup the recipe display tab"""
        # Recipe content with scrollbar
        recipe_scroll_frame = tk.Frame(parent, bg='white')
        recipe_scroll_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        self.recipe_text = scrolledtext.ScrolledText(recipe_scroll_frame,
                                                   wrap=tk.WORD,
                                                   font=('Segoe UI', 11),
                                                   bg='#fbfcfd',
                                                   fg=self.colors['dark'],
                                                   relief='solid',
                                                   bd=1,
                                                   padx=15,
                                                   pady=15)
        self.recipe_text.pack(fill='both', expand=True)
        
        # Configure text tags for formatting
        self.recipe_text.tag_configure('title', font=('Segoe UI', 16, 'bold'), foreground=self.colors['primary'])
        self.recipe_text.tag_configure('heading', font=('Segoe UI', 13, 'bold'), foreground=self.colors['secondary'])
        self.recipe_text.tag_configure('ingredient', font=('Segoe UI', 10), foreground=self.colors['dark'])
        self.recipe_text.tag_configure('step', font=('Segoe UI', 10), foreground=self.colors['dark'])

    def setup_nutrition_tab(self, parent):
        """Setup the nutrition analysis tab"""
        nutrition_main = tk.Frame(parent, bg='white')
        nutrition_main.pack(fill='both', expand=True, padx=20, pady=20)
    
        # 创建Canvas和Scrollbar
        canvas = tk.Canvas(nutrition_main, bg='white')
        scrollbar = ttk.Scrollbar(nutrition_main, orient="vertical", command=canvas.yview)
        self.nutrition_container = tk.Frame(canvas, bg='white')
    
        self.nutrition_container.bind(
        "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
    
        canvas.create_window((0, 0), window=self.nutrition_container, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
    
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
        # 绑定鼠标滚轮
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind("<MouseWheel>", _on_mousewheel)
    
        # Default message
        default_msg = tk.Label(self.nutrition_container,
                          text="🍎 Nutrition analysis will appear here after generating a recipe",
                          font=('Segoe UI', 12),
                          fg=self.colors['dark'],
                          bg='white')
        default_msg.pack(expand=True)

    def create_nutrition_cards(self, nutrition_data):
        """Create visual nutrition cards with fixed 3 per row and equal width"""
        # Clear existing content
        for widget in self.nutrition_container.winfo_children():
            widget.destroy()

        # Parse nutrition data
        nutrition_info = self.parse_nutrition_data(nutrition_data)

        if not nutrition_info:
            error_label = tk.Label(self.nutrition_container,
                              text="❌ Unable to parse nutrition data",
                              font=('Segoe UI', 12),
                              fg=self.colors['accent'],
                              bg='white')
            error_label.pack(expand=True)
            return

        # Create cards grid - fixed 3 columns layout
        cards_frame = tk.Frame(self.nutrition_container, bg='white')
        cards_frame.pack(fill='both', expand=True, pady=20)

        # Configure grid to have 3 equal-width columns
        for col in range(3):
            cards_frame.grid_columnconfigure(col, weight=1, uniform="nutrition")

        # Nutrition cards
        colors = [self.colors['secondary'], self.colors['success'], self.colors['warning'],
              self.colors['accent'], self.colors['primary'], '#9b59b6', '#1abc9c']
        icons = ['⚡', '💪', '🧈', '🌾', '🍃', '🍯', '🧂']

        # Place items in a 3-column grid, up to 3 items per row
        items = list(nutrition_info.items())
        for i, (key, value) in enumerate(items):
            row = i // 3  # Integer division to place in rows
            col = i % 3   # Modulo to place in one of three columns

            card = tk.Frame(cards_frame, bg=colors[i % len(colors)], relief='solid', bd=1)
            card.grid(row=row, column=col, sticky='nsew', padx=5, pady=5)

            # Card content
            content = tk.Frame(card, bg=colors[i % len(colors)], padx=15, pady=12)
            content.pack(fill='both', expand=True)

            # Icon and title
            header_frame = tk.Frame(content, bg=colors[i % len(colors)])
            header_frame.pack(fill='x')

            icon_label = tk.Label(header_frame,
                             text=icons[i % len(icons)],
                             font=('Segoe UI', 16),
                             bg=colors[i % len(colors)],
                             fg='white')
            icon_label.pack(side='left')

            title_label = tk.Label(header_frame,
                              text=key.title(),
                              font=('Segoe UI', 11, 'bold'),
                              bg=colors[i % len(colors)],
                              fg='white')
            title_label.pack(side='left', padx=(8, 0))

            # Value
            value_label = tk.Label(content,
                              text=value,
                              font=('Segoe UI', 14, 'bold'),
                              bg=colors[i % len(colors)],
                              fg='white')
            value_label.pack(anchor='w', pady=(3, 0))

        # Ensure rows expand properly
        cards_frame.grid_rowconfigure('all', weight=1)

    def parse_nutrition_data(self, nutrition_text):
        """Parse nutrition data from text"""
        nutrition_info = {}
        lines = nutrition_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if ':' in line:
                # Remove markdown formatting and extract key-value pairs
                clean_line = re.sub(r'[*-]', '', line).strip()
                if ':' in clean_line:
                    key, value = clean_line.split(':', 1)
                    nutrition_info[key.strip()] = value.strip()
        
        return nutrition_info

    def display_recipe(self, recipe_text):
        """Display recipe with proper formatting"""
        self.recipe_text.delete(1.0, tk.END)
        
        lines = recipe_text.split('\n')
        current_pos = 1.0
        
        for line in lines:
            line = line.strip()
            if not line:
                self.recipe_text.insert(tk.END, '\n')
                continue
                
            # Title detection
            if line.startswith('**Title**:') or 'Recipe' in line and line.startswith('#'):
                title = re.sub(r'[*#]', '', line).replace('Title:', '').strip()
                self.recipe_text.insert(tk.END, f"🍽️ {title}\n", 'title')
            
            # Section headers
            elif line.startswith('**') and line.endswith('**:'):
                header = re.sub(r'[*:]', '', line).strip()
                self.recipe_text.insert(tk.END, f"{header}\n", 'heading')
                self.recipe_text.insert(tk.END, "─" * len(header) + "\n", 'heading')
            
            # Ingredients and steps
            elif line.startswith('-') or line.startswith('•'):
                item = line[1:].strip()
                self.recipe_text.insert(tk.END, f"• {item}\n", 'ingredient')
            
            elif re.match(r'^\d+\.', line):
                step = re.sub(r'^\d+\.', '', line).strip()
                step_num = re.match(r'^\d+', line).group()
                self.recipe_text.insert(tk.END, f"{step_num}. {step}\n", 'step')
            
            else:
                self.recipe_text.insert(tk.END, f"{line}\n")
        
        self.recipe_text.see(1.0)

    def generate_recipe(self):
        """Handle recipe generation"""
        if self.generate_button['text'] == "⏹️ Stop Generation":
            self.stop_generation = True
            self.status_var.set("Generation stopped by user")
            self.generate_button.config(text="✨ Generate Recipe")
            return

        ingredients = self.ingredients_entry.get().strip()
        diet = self.diet_var.get()
        goal = self.goal_var.get()
        
        if not ingredients:
            self.status_var.set("❌ Please enter some ingredients first!")
            return

        self.generate_button.config(text="⏹️ Stop Generation")
        self.audio_button.config(state='disabled')
        self.status_var.set("🔄 AI is crafting your perfect recipe...")
        
        # Clear previous content
        self.recipe_text.delete(1.0, tk.END)
        self.recipe_text.insert(1.0, "🤖 AI Chef is working on your recipe...\n\nIngredients being analyzed...\nOptimizing for your dietary preferences...\nCalculating nutrition facts...")
        
        for widget in self.nutrition_container.winfo_children():
            widget.destroy()
        loading_label = tk.Label(self.nutrition_container,
                               text="📊 Analyzing nutritional content...",
                               font=('Segoe UI', 12),
                               fg=self.colors['dark'],
                               bg='white')
        loading_label.pack(expand=True)
        
        self.stop_generation = False
        self.generation_thread = threading.Thread(target=self._generate_recipe_thread, args=(ingredients, diet, goal))
        self.generation_thread.start()

    def _generate_recipe_thread(self, ingredients, diet, goal):
        """Background thread for recipe generation"""
        try:
            recipe, nutrition = self.generate_callback(ingredients, diet, goal)
            self.result_queue.put((recipe, nutrition))
        except Exception as e:
            self.error_queue.put(str(e))

    def check_queue(self):
        """Check for results from background threads"""
        try:
            recipe, nutrition = self.result_queue.get_nowait()
            if not self.stop_generation:
                self.plain_text = recipe
                self.display_recipe(recipe)
                self.create_nutrition_cards(nutrition)
                self.audio_button.config(state="normal")
                self.status_var.set("✅ Recipe generated successfully! Ready to cook! 👨‍🍳")
            self.generate_button.config(text="✨ Generate Recipe")
        except queue.Empty:
            pass

        try:
            error = self.error_queue.get_nowait()
            if not self.stop_generation:
                self.recipe_text.delete(1.0, tk.END)
                self.recipe_text.insert(1.0, f"❌ Error generating recipe:\n\n{error}\n\nPlease try again with different ingredients or check your internet connection.")
                self.status_var.set("❌ Error occurred during generation")
                self.audio_button.config(state="disabled")
            self.generate_button.config(text="✨ Generate Recipe")
        except queue.Empty:
            pass

        self.root.after(100, self.check_queue)

    def toggle_audio(self):
        """Handle audio playback toggle"""
        if self.audio_button['text'] == "🔊 Play Recipe Audio":
            # Extract clean text for TTS
            recipe_content = self.plain_text.split("## Nutrition Facts")[0].strip()
            clean_text = BeautifulSoup(markdown.markdown(recipe_content), "html.parser").get_text()
            
            self.stop_audio = False
            self.audio_playing = True
            self.audio_button.config(text="⏸️ Pause Audio")
            self.status_var.set("🔊 Playing recipe audio...")
            
            self.audio_thread = threading.Thread(target=self._play_audio_thread, args=(clean_text,))
            self.audio_thread.start()
        else:
            self.stop_audio = True
            self.audio_callback(None)  # Signal pause
            self.audio_button.config(text="🔊 Play Recipe Audio")
            self.audio_playing = False
            self.status_var.set("⏸️ Audio paused")

    def _play_audio_thread(self, text):
        """Background thread for audio playback"""
        try:
            self.audio_callback(text)
            if not self.stop_audio:
                self.root.after(0, lambda: self.audio_button.config(text="🔊 Play Recipe Audio"))
                self.root.after(0, lambda: self.status_var.set("✅ Audio playback completed"))
        except Exception:
            self.root.after(0, lambda: self.audio_button.config(text="🔊 Play Recipe Audio"))
            self.root.after(0, lambda: self.status_var.set("❌ Audio playback failed"))
        finally:
            self.audio_playing = False

# For backward compatibility, keep the original class name as an alias
RecipeGUI = ModernRecipeGUI