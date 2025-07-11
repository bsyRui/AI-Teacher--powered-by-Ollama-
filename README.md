# NGZZ TEACHER
---
Ngzz teacher is an AI-powered teacher runned by ollama v3 from Meta, Its light-weight and perfect for obsidian run-time.
Once you choose the folder you want:

## How to Use

Once you download or clone this project, you don't need to install anything manually. Just follow these steps:
### 📦 1. Setup & Run

Instead of running the Python file directly, use the provided setup script. It will:

    Create a virtual environment (if it doesn't exist)

    Install all required Python packages (requests, etc.)

    Install tkinter depending on your Linux distro

    Run the program.py

### ✅ Recommended way:

./run_program.sh

    If the file isn't executable yet, run this first:

chmod +x run_program.sh

### 🧠 2. How to Use the Program

Once program.py launches:

    Press "Generate New Lesson" (top button).

    Answer the questions by typing your response under the line that starts with:

    **Answer:**

    Then click "Check Answer" to get feedback from the AI.

### 🗂️ Language & Folder Setup

Choose your language at line 11: 
```LANGUAGE = "French"```

Choose your folder path at line 18:
```BASE_SAVE_DIR = "your/path/folder/to/store"```

Example:

    ``` BASE_SAVE_DIR = "/home/ngzz/Documents/Notepad/Main/01_Knowledge/Languages"```

![folderStructure](imgs/folderStructure.png)

You don’t need to manually create the language folders – the program does it for you!