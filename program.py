import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import os
import json
import requests
import threading
import re # For parsing answers from MD file and robust JSON extraction
import subprocess # For opening file explorer

# --- Configuration ---
LANGUAGE = "French"
OLLAMA_API_URL = "http://localhost:11434"
MODEL_NAME = "llama3.2:latest" # Ensure this model is available in your Ollama instance

# IMPORTANT: Adjust this path to where you want to save your lessons
# For example, on Windows: r"C:\Users\YourUser\Documents\Notepad\Main\01_Knowledge\Languages"
# For macOS/Linux: "/Users/YourUser/Documents/Notepad/Main/01_Knowledge/Languages"
BASE_SAVE_DIR = "/home/ngzz/Documents/Notepad/Main/01_Knowledge/Languages"
SAVE_DIR = os.path.join(BASE_SAVE_DIR, LANGUAGE, "daily-Classes")

ORDERED_MODULES = ["A1", "A2", "B1", "B2", "C1", "C2"]
MAX_LESSONS_PER_MODULE = 5 # Define how many lessons are in each module before advancing

PROGRESS_FILE = os.path.join(SAVE_DIR, "lesson_progress.json")

# --- Helper Functions ---

def load_progress():
    """Loads the current lesson progress from a JSON file."""
    if not os.path.exists(PROGRESS_FILE):
        progress = {"module": ORDERED_MODULES[0], "lesson": 1}
        save_progress(progress)
        return progress
    with open(PROGRESS_FILE, "r") as f:
        return json.load(f)

def save_progress(progress):
    """Saves the current lesson progress to a JSON file."""
    os.makedirs(SAVE_DIR, exist_ok=True)
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)

def parse_ollama_json_response(content):
    """
    Attempts to parse JSON content from Ollama, handling cases where it might be
    wrapped in markdown code blocks or embedded in other text.
    """
    # First, try to parse directly
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass # Fall through to more robust parsing

    # Try to extract JSON from markdown code block (```json ... ```)
    json_match = re.search(r"```json\s*(.*?)\s*```", content, re.DOTALL)
    if json_match:
        json_string = json_match.group(1)
        try:
            return json.loads(json_string)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON extracted from markdown block: {e}\nExtracted JSON:\n{json_string}")

    # Fallback: Try to find the first '{' and last '}' and parse content between them
    start_brace = content.find('{')
    end_brace = content.rfind('}')
    if start_brace != -1 and end_brace != -1 and end_brace > start_brace:
        json_string = content[start_brace : end_brace + 1]
        try:
            return json.loads(json_string)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON extracted by brace matching: {e}\nExtracted JSON:\n{json_string}")

    # If still no valid JSON, raise an error
    raise ValueError(f"No valid JSON found in Ollama response:\n{content}")

def generate_daily_exercises_ollama(module, lesson):
    """
    Generates lesson content and exercises using the Ollama API.
    Returns a dictionary with 'explanation_summary', 'lesson_content', and 'exercises' keys.
    """
    prompt = f"""
You are an expert {LANGUAGE} teacher. Create lesson number {lesson} for module {module} (A1, A2, B1, B2, C1, or C2).
Write a concise explanation of what the student will learn today regarding {LANGUAGE} grammar or communication skills.
Then provide a detailed text explaining the grammar concept or communication principle.
After the explanation, provide 5-7 varied exercises (fill-in-the-blanks, multiple choice, sentence correction, short answer, matching, etc.)
to practice the grammar topic.
To teach effective communication and writing, include at least one prompt for a "short reflection" or a "tiny essay" (around 50-100 words) at the end of the exercises, related to the lesson topic or a general communication skill. This will be part of the exercises.

YOUR ENTIRE RESPONSE MUST BE A SINGLE JSON OBJECT. DO NOT INCLUDE ANY OTHER TEXT, CONVERSATIONAL GREETINGS, OR EXPLANATIONS OUTSIDE THE JSON.

The 'exercises' array MUST contain 5-7 elements. EACH element in the 'exercises' array MUST be a string containing the full exercise question. Do NOT use placeholder text like 'No question text' or empty strings.

Example JSON structure:
{{
  "explanation_summary": "Today you will learn about the present simple tense for routines and habits.",
  "lesson_content": "The present simple tense is used to describe habits, routines, general truths, and scheduled events. For example, 'I eat breakfast every morning.' or 'The sun rises in the east.'",
  "exercises": [
    "Fill in the blank: I ___ (to go) to school every day.",
    "Choose the correct option: She (like/likes) pizza.",
    "Write a short reflection (50 words): Describe your daily routine using the present simple tense."
  ]
}}

Make sure the exercises match the {module} grammar level and the overall tone is professional and encouraging.
"""
    try:
        response = requests.post(
            f"{OLLAMA_API_URL}/v1/chat/completions",
            json={
                "model": MODEL_NAME,
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json"}, # Request JSON format
            },
            timeout=90,
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]

        print(f"--- Raw Ollama Response Content (for debugging) ---\n{content}\n--- End Raw Content ---")

        try:
            return parse_ollama_json_response(content)
        except ValueError as e:
            raise ValueError(f"Failed to parse Ollama JSON response: {e}")
    except requests.exceptions.ConnectionError:
        raise ConnectionError(f"Could not connect to Ollama at {OLLAMA_API_URL}. Is Ollama running?")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Ollama API request failed: {e}")

def generate_module_overview_ollama(module_name):
    """
    Generates an overview for a new module using the Ollama API.
    """
    prompt = f"""
You are an expert {LANGUAGE} teacher. Create a professional and encouraging overview for the {module_name} module.
Explain what the student will explore in this module, including key grammar points, vocabulary themes, and communication skills they will develop.
Provide a list of 5-7 main topics that will be covered.

YOUR ENTIRE RESPONSE MUST BE A SINGLE JSON OBJECT. DO NOT INCLUDE ANY OTHER TEXT, CONVERSATIONAL GREETINGS, OR EXPLANATIONS OUTSIDE THE JSON.

Example JSON structure:
{{
  "module_title": "Welcome to A2: Building on Your Basics!",
  "overview_text": "In this module, you will expand your foundational {LANGUAGE} skills...",
  "topics_covered": [
    "Past simple tense: regular & irregular verbs",
    "Present continuous: actions happening now",
    "Countable and uncountable nouns: some, any, much, many",
    "Modal verbs for ability and permission: can, can’t, must, mustn’t",
    "Comparatives and superlatives: bigger, the biggest",
    "More prepositions: under, between, next to",
    "Simple conjunctions: and, but, because",
    "Possessive 's and pronouns"
  ]
}}
"""
    try:
        response = requests.post(
            f"{OLLAMA_API_URL}/v1/chat/completions",
            json={
                "model": MODEL_NAME,
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json"},
            },
            timeout=90,
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        print(f"--- Raw Ollama Module Overview Response Content (for debugging) ---\n{content}\n--- End Raw Content ---")
        try:
            return parse_ollama_json_response(content)
        except ValueError as e:
            raise ValueError(f"Failed to parse Ollama JSON response for module overview: {e}")
    except requests.exceptions.ConnectionError:
        raise ConnectionError(f"Could not connect to Ollama at {OLLAMA_API_URL}. Is Ollama running?")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Ollama API request failed: {e}")


def get_correction_ollama(lesson_data, student_answers_parsed):
    """
    Gets detailed corrections and explanations from the Ollama API based on lesson and student answers.
    """
    exercises_text = ""
    for i, ex in enumerate(lesson_data.get("exercises", [])):
        if isinstance(ex, str):
            ex_text = ex
        elif isinstance(ex, dict):
            ex_text = ex.get("text") or ex.get("question") or "*No question text*"
            if "options" in ex and isinstance(ex["options"], list):
                ex_text += "\nOptions: " + ", ".join(ex["options"])
        else:
            ex_text = "*Invalid exercise format*"
        
        # Append student's answer if available
        student_ans = student_answers_parsed[i] if i < len(student_answers_parsed) else "No answer provided."
        exercises_text += f"Exercise {i+1}: {ex_text.strip()}\nStudent's Answer: {student_ans}\n\n"

    prompt = f"""
You are a highly professional and experienced {LANGUAGE} teacher. Your task is to provide detailed, constructive, and encouraging feedback on a student's language exercises and writing.

Here is the lesson content, the original exercises, and the student's answers for each exercise:

---
Lesson Summary:
{lesson_data.get('explanation_summary', '')}

Lesson Content:
{lesson_data.get('lesson_content', '')}

---
Exercises and Student Answers:
{exercises_text}

---
Please provide the following:
1.  **Detailed Correction for Each Exercise:** For each exercise, clearly state if the answer is correct or incorrect. If incorrect, provide the correct answer and a clear, concise explanation of *why* it's incorrect and the grammatical rule or concept that applies.
2.  **Feedback on Writing/Essays:** For any essay or reflection prompts, provide specific feedback on grammar, vocabulary, sentence structure, clarity, coherence, and overall effectiveness of communication. Suggest areas for improvement.
3.  **Overall Improvement Areas:** Summarize the student's strengths and weaknesses across all exercises. Suggest specific areas for them to focus on for future improvement (e.g., "review verb tenses," "practice sentence connectors," "expand vocabulary related to X").
4.  **Professional and Encouraging Tone:** Maintain a supportive and professional tone throughout the correction.

Respond clearly and professionally in {LANGUAGE}.
"""
    try:
        response = requests.post(
            f"{OLLAMA_API_URL}/v1/chat/completions",
            json={
                "model": MODEL_NAME,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=120, # Increased timeout for detailed corrections
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except requests.exceptions.ConnectionError:
        raise ConnectionError(f"Could not connect to Ollama at {OLLAMA_API_URL}. Is Ollama running?")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Ollama API request failed: {e}")

def save_lesson_md(module, lesson, content):
    """Saves the lesson content to a Markdown file with answer placeholders."""
    os.makedirs(SAVE_DIR, exist_ok=True)
    filename = f"{module}_lesson_{lesson}.md"
    filepath = os.path.join(SAVE_DIR, filename)

    with open(filepath, "w") as f:
        f.write(f"# {LANGUAGE} {module} Lesson {lesson}\n\n")
        f.write(f"## What you will learn today\n{content.get('explanation_summary', 'No summary provided.')}\n\n")
        f.write(f"## Lesson Content\n{content.get('lesson_content', 'No lesson content provided.')}\n\n")
        f.write("## Exercises\n\n")

        for i, ex in enumerate(content.get("exercises", []), 1):
            ex_text = ""
            if isinstance(ex, str):
                ex_text = ex
            elif isinstance(ex, dict):
                ex_text = ex.get("text") or ex.get("question")
                if ex_text is None: # If neither 'text' nor 'question' found
                    ex_text = f"ERROR: Malformed exercise object in JSON: {ex}" # Indicate error
                if "options" in ex and isinstance(ex["options"], list):
                    ex_text += "\nOptions: " + ", ".join(ex["options"])
            else:
                ex_text = f"ERROR: Unexpected exercise format in JSON: {type(ex).__name__} - {ex}" # Indicate error

            f.write(f"{i}. {ex_text.strip()}\n")
            f.write("**Your Answer:** \n\n") # Placeholder for student's answers

    return filepath

def save_module_overview_md(module_name, overview_data):
    """Saves the module overview to a Markdown file."""
    os.makedirs(SAVE_DIR, exist_ok=True)
    filename = f"{module_name}_Module_Overview.md"
    filepath = os.path.join(SAVE_DIR, filename)

    with open(filepath, "w") as f:
        f.write(f"# {overview_data.get('module_title', f'{LANGUAGE} {module_name} Module Overview')}\n\n")
        f.write(f"{overview_data.get('overview_text', 'No overview text provided.')}\n\n")
        f.write("## Topics to be Covered\n\n")
        for topic in overview_data.get("topics_covered", []):
            f.write(f"- {topic}\n")
        f.write("\n---\n")
        f.write("Start your first lesson by clicking 'Generate New Lesson'!")
    return filepath


def save_lesson_json(module, lesson, content):
    """Saves the raw lesson content (including exercises) to a JSON file."""
    os.makedirs(SAVE_DIR, exist_ok=True)
    filename = f"{module}_lesson_{lesson}.json"
    filepath = os.path.join(SAVE_DIR, filename)
    with open(filepath, "w") as f:
        json.dump(content, f, indent=2)
    return filepath

def append_correction_to_md(module, lesson, correction_text):
    """Appends the correction and explanation text to the lesson markdown file."""
    filename = f"{module}_lesson_{lesson}.md"
    filepath = os.path.join(SAVE_DIR, filename)

    with open(filepath, "a") as f:
        f.write("\n---\n")
        f.write("## Correction and Explanation\n\n")
        f.write(correction_text + "\n")

    return filepath

def read_answers_from_md(filepath, num_exercises):
    """
    Reads the student's answers from the markdown file based on the '**Your Answer:**' marker.
    Returns a list of strings, one for each answer.
    """
    answers = [""] * num_exercises
    try:
        with open(filepath, "r") as f:
            content = f.read()

        # Find all positions of the answer markers
        answer_marker_positions = [m.end() for m in re.finditer(r"\*\*Your Answer:\*\*\s*", content)]

        for i in range(num_exercises):
            if i < len(answer_marker_positions):
                start_index = answer_marker_positions[i]
                
                # Determine the end of the current answer
                end_index = len(content) # Default to end of file
                
                # Look for the next answer marker
                if (i + 1) < len(answer_marker_positions):
                    end_index = answer_marker_positions[i+1] - len("**Your Answer:** ") # Subtract marker length to get just answer content
                
                # Extract the potential answer text
                potential_answer_text = content[start_index:end_index].strip()

                # Now, refine this potential_answer_text to only include the actual answer
                # An answer ends when the next exercise number starts, or a new section starts (e.g., ##)
                # or if the block ends.
                
                # Find the start of the next exercise number (e.g., "2.", "3.")
                # This regex looks for a line starting with a number, a dot, and a space.
                next_exercise_match = re.search(r"^\d+\.\s", potential_answer_text, re.MULTILINE)
                
                # Find the start of a new markdown heading (e.g., "##", "###")
                next_heading_match = re.search(r"^#+\s", potential_answer_text, re.MULTILINE)
                
                answer_end_in_block = len(potential_answer_text)
                
                if next_exercise_match:
                    answer_end_in_block = min(answer_end_in_block, next_exercise_match.start())
                if next_heading_match:
                    answer_end_in_block = min(answer_end_in_block, next_heading_match.start())
                
                answers[i] = potential_answer_text[:answer_end_in_block].strip()
            else:
                answers[i] = "" # No answer marker found for this exercise

    except Exception as e:
        messagebox.showerror("Error Reading Answers", f"Could not read answers from MD file: {e}")
        return [""] * num_exercises # Return empty answers on error
    
    return answers

def open_file_in_explorer(path):
    """Opens the given file or directory in the default file explorer."""
    if os.path.exists(path):
        if os.name == 'nt': # Windows
            os.startfile(path)
        elif os.uname().sysname == 'Darwin': # macOS
            subprocess.call(['open', path])
        else: # Linux
            subprocess.call(['xdg-open', path])
    else:
        messagebox.showerror("Error", f"Path not found: {path}")

# --- Tkinter Application ---

class LanguageProfessorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{LANGUAGE} Language Professor")
        self.geometry("900x750")
        self.style = ttk.Style(self)
        self.style.theme_use('clam') # 'clam', 'alt', 'default', 'classic'

        self.progress = load_progress()
        self.current_lesson_data = None # To store the lesson data after generation
        self.current_md_filepath = None # To store the path of the current lesson's MD file

        self._create_widgets()
        self._load_current_lesson_display()

    def _create_widgets(self):
        # Main Frame
        main_frame = ttk.Frame(self, padding="10 10 10 10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Top Frame for Progress and Buttons
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))

        self.progress_label = ttk.Label(top_frame, text=self._get_progress_text(), font=("Arial", 12, "bold"))
        self.progress_label.pack(side=tk.LEFT, padx=5)

        self.generate_button = ttk.Button(top_frame, text="Generate New Lesson", command=self._generate_lesson_threaded)
        self.generate_button.pack(side=tk.LEFT, padx=10)

        self.next_lesson_button = ttk.Button(top_frame, text="Next Lesson/Module", command=self._next_lesson_threaded, state=tk.DISABLED)
        self.next_lesson_button.pack(side=tk.LEFT, padx=10)

        self.open_folder_button = ttk.Button(top_frame, text="Open Lesson Folder", command=lambda: open_file_in_explorer(SAVE_DIR))
        self.open_folder_button.pack(side=tk.RIGHT, padx=5)

        # Lesson Display Area
        lesson_display_frame = ttk.LabelFrame(main_frame, text="Lesson Content & Exercises (Read-Only)", padding="10 10 10 10")
        lesson_display_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.lesson_display_text = scrolledtext.ScrolledText(lesson_display_frame, wrap=tk.WORD, font=("Consolas", 11), height=25, bg="#f8f8f8", fg="#333333")
        self.lesson_display_text.pack(fill=tk.BOTH, expand=True)
        self.lesson_display_text.config(state=tk.DISABLED) # Make it read-only

        # Instructions for User
        instructions_frame = ttk.Frame(main_frame, padding="5 0 5 0")
        instructions_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(instructions_frame, text="To answer, open the .md file in your editor (e.g., Obsidian), fill in your answers after '**Your Answer:**', save, then click 'Check My Answers'.", wraplength=800, font=("Arial", 10, "italic")).pack(anchor=tk.W)
        
        self.current_file_label = ttk.Label(instructions_frame, text="", wraplength=800, font=("Arial", 9))
        self.current_file_label.pack(anchor=tk.W)


        # Submit Button (This is your "check answer" button)
        self.submit_button = ttk.Button(main_frame, text="Check My Answers & Get Correction", command=self._submit_answers_threaded)
        self.submit_button.pack(pady=10)

        # Status Bar
        self.status_label = ttk.Label(self, text="Ready.", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

    def _get_progress_text(self):
        return f"Current Progress: Module {self.progress['module']}, Lesson {self.progress['lesson']}"

    def _update_lesson_display_from_file(self, filepath):
        """Updates the main display area by reading the content of the MD file."""
        self.current_file_label.config(text=f"Current lesson file: {filepath}")
        try:
            with open(filepath, "r") as f:
                content = f.read()
            self.lesson_display_text.config(state=tk.NORMAL)
            self.lesson_display_text.delete(1.0, tk.END)
            self.lesson_display_text.insert(tk.END, content)
            self.lesson_display_text.config(state=tk.DISABLED)
        except FileNotFoundError:
            self.lesson_display_text.config(state=tk.NORMAL)
            self.lesson_display_text.delete(1.0, tk.END)
            self.lesson_display_text.insert(tk.END, "Lesson file not found. Generate a new lesson.")
            self.lesson_display_text.config(state=tk.DISABLED)
        except Exception as e:
            messagebox.showerror("Error", f"Could not load lesson file: {e}")

    def _load_current_lesson_display(self):
        """Loads and displays the last generated lesson from the MD file if it exists."""
        module = self.progress["module"]
        lesson = self.progress["lesson"]
        self.current_md_filepath = os.path.join(SAVE_DIR, f"{module}_lesson_{lesson}.md")
        self._update_lesson_display_from_file(self.current_md_filepath)
        
        # Check if correction already exists to enable Next Lesson button
        if os.path.exists(self.current_md_filepath):
            with open(self.current_md_filepath, 'r') as f:
                content = f.read()
            if "## Correction and Explanation" in content:
                self.next_lesson_button.config(state=tk.NORMAL)
            else:
                self.next_lesson_button.config(state=tk.DISABLED)
        else:
            self.next_lesson_button.config(state=tk.DISABLED)


    def _generate_lesson_threaded(self):
        """Starts lesson generation in a separate thread to keep GUI responsive."""
        self._set_ui_state(True, "Generating lesson...")
        threading.Thread(target=self._generate_lesson_task).start()

    def _generate_lesson_task(self):
        """Task for generating a new lesson."""
        module = self.progress["module"]
        lesson = self.progress["lesson"]
        try:
            self.current_lesson_data = generate_daily_exercises_ollama(module, lesson)
            self.current_md_filepath = save_lesson_md(module, lesson, self.current_lesson_data)
            save_lesson_json(module, lesson, self.current_lesson_data)
            
            self.after(0, lambda: self._update_lesson_display_from_file(self.current_md_filepath))
            self.after(0, lambda: self._set_ui_state(False, "Lesson generated. Please fill in answers in the MD file."))
            self.after(0, lambda: self.next_lesson_button.config(state=tk.DISABLED)) # Disable next lesson until answers are submitted
            self.after(0, lambda: messagebox.showinfo("Success", f"Lesson {lesson} for module {module} generated and saved to:\n{self.current_md_filepath}\n\nPlease open this file in Obsidian to write your answers."))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Generation Error", str(e)))
            self.after(0, lambda: self._set_ui_state(False, "Error during generation."))

    def _submit_answers_threaded(self):
        """Starts answer submission in a separate thread to keep GUI responsive."""
        if not self.current_lesson_data or not self.current_md_filepath:
            messagebox.showwarning("Warning", "Please generate a lesson first!")
            return

        # Check if correction already exists in the MD file
        if os.path.exists(self.current_md_filepath):
            with open(self.current_md_filepath, 'r') as f:
                content = f.read()
            if "## Correction and Explanation" in content:
                messagebox.showinfo("Already Corrected", "This lesson has already been corrected. Please generate a new lesson or advance to the next one.")
                return

        self._set_ui_state(True, "Submitting answers and getting correction...")
        threading.Thread(target=self._submit_answers_task).start()

    def _submit_answers_task(self):
        """Task for submitting answers and getting corrections."""
        module = self.progress["module"]
        lesson = self.progress["lesson"]
        
        try:
            # Determine the number of exercises from the lesson data
            num_exercises = len(self.current_lesson_data.get("exercises", []))
            student_answers_parsed = read_answers_from_md(self.current_md_filepath, num_exercises)
            
            correction = get_correction_ollama(self.current_lesson_data, student_answers_parsed)
            append_correction_to_md(module, lesson, correction)
            
            self.after(0, lambda: self._update_lesson_display_from_file(self.current_md_filepath))
            self.after(0, lambda: self._set_ui_state(False, "Correction received and appended to MD file."))
            self.after(0, lambda: self.next_lesson_button.config(state=tk.NORMAL)) # Enable next lesson button
            self.after(0, lambda: messagebox.showinfo("Success", "Answers submitted and correction received! Check the lesson display below."))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Submission Error", str(e)))
            self.after(0, lambda: self._set_ui_state(False, "Error during submission."))

    def _next_lesson_threaded(self):
        """Starts advancing to the next lesson/module in a separate thread."""
        self._set_ui_state(True, "Advancing to next lesson/module...")
        threading.Thread(target=self._next_lesson_task).start()

    def _next_lesson_task(self):
        """Task for advancing to the next lesson or module."""
        current_module_idx = ORDERED_MODULES.index(self.progress["module"])
        
        if self.progress["lesson"] < MAX_LESSONS_PER_MODULE:
            # Advance lesson within current module
            self.progress["lesson"] += 1
            save_progress(self.progress)
            self.after(0, lambda: self.progress_label.config(text=self._get_progress_text()))
            self.after(0, lambda: self._set_ui_state(False, "Ready for the next lesson. Generate it now!"))
            self.after(0, lambda: self.next_lesson_button.config(state=tk.DISABLED))
            self.after(0, lambda: self._update_lesson_display_from_file("")) # Clear display
            self.after(0, lambda: messagebox.showinfo("Progress", f"Moved to Module {self.progress['module']}, Lesson {self.progress['lesson']}. Click 'Generate New Lesson' to start!"))
        else:
            # Advance to next module
            if current_module_idx < len(ORDERED_MODULES) - 1:
                next_module = ORDERED_MODULES[current_module_idx + 1]
                self.progress["module"] = next_module
                self.progress["lesson"] = 1 # Reset lesson to 1 for the new module
                save_progress(self.progress)
                self.after(0, lambda: self.progress_label.config(text=self._get_progress_text()))
                
                # Generate and display module overview
                try:
                    overview_data = generate_module_overview_ollama(next_module)
                    overview_filepath = save_module_overview_md(next_module, overview_data)
                    self.after(0, lambda: self._update_lesson_display_from_file(overview_filepath))
                    self.after(0, lambda: self._set_ui_state(False, f"Welcome to {next_module} module! Generate your first lesson."))
                    self.after(0, lambda: self.next_lesson_button.config(state=tk.DISABLED)) # Disable until new lesson is generated
                    self.after(0, lambda: messagebox.showinfo("Module Advanced", f"Congratulations! You've completed {ORDERED_MODULES[current_module_idx]} and moved to {next_module}!\n\nCheck the display for an overview of what you'll learn."))
                except Exception as e:
                    self.after(0, lambda: messagebox.showerror("Module Overview Error", str(e)))
                    self.after(0, lambda: self._set_ui_state(False, "Error generating module overview."))
            else:
                # All modules completed
                self.after(0, lambda: self._set_ui_state(False, "All modules completed!"))
                self.after(0, lambda: messagebox.showinfo("Congratulations", "You have completed all available modules!"))
                self.after(0, lambda: self.next_lesson_button.config(state=tk.DISABLED))
                self.after(0, lambda: self.generate_button.config(state=tk.DISABLED)) # Maybe disable generate too

    def _set_ui_state(self, disabled, status_message=""):
        """Disables/enables UI elements during API calls and updates status bar."""
        state = tk.DISABLED if disabled else tk.NORMAL
        self.generate_button.config(state=state)
        self.submit_button.config(state=state)
        self.open_folder_button.config(state=state)
        self.status_label.config(text=status_message)
        
        # Next lesson button state is managed separately based on correction presence
        # and whether a new lesson needs to be generated.
        # It's re-enabled only after a correction is received for the current lesson.
        if not disabled and self.current_md_filepath and os.path.exists(self.current_md_filepath):
            with open(self.current_md_filepath, 'r') as f:
                content = f.read()
            if "## Correction and Explanation" in content:
                self.next_lesson_button.config(state=tk.NORMAL)
            else:
                self.next_lesson_button.config(state=tk.DISABLED)
        else:
            self.next_lesson_button.config(state=tk.DISABLED)


if __name__ == "__main__":
    # Ensure the save directory exists before starting the app
    os.makedirs(SAVE_DIR, exist_ok=True)
    app = LanguageProfessorApp()
    app.mainloop()
