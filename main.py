import os
import subprocess
import base64
import tkinter as tk
import requests
import json
import pyperclip
import re

MODELS = {
    '2.5 flash': 'google/gemini-2.5-flash', # Default $2.5
    '3 flash': 'google/gemini-3-flash-preview', # $3
    '3.1 pro': 'google/gemini-3.1-pro-preview', # expensive $14
    '2.5 pro': 'google/gemini-2.5-pro' # $11
}

MODELNOW = '3 flash'
screenPath = f"{os.path.dirname(os.path.abspath(__file__))}/screen.png"

def renderOutput(text):
    root = tk.Tk()
    root.title("Reshalo")
    root.iconify()
    text_widget = tk.Text(root, wrap="word", font=("Arial", 14))
    text_widget.insert("1.0", text)
    text_widget.config(state="disabled") 
    text_widget.pack(side="left", fill="both", expand=True)
    scrollbar = tk.Scrollbar(root, command=text_widget.yview)
    scrollbar.pack(side="right", fill="y")
    text_widget.config(yscrollcommand=scrollbar.set)
    root.mainloop()

def takeScreenshot():
    if os.path.exists(screenPath):
        os.remove(screenPath)
    currentDir = os.path.dirname(os.path.abspath(__file__))
    savePath = os.path.join(currentDir, "screen.png")
    
    try:
        subprocess.run(["screencapture", "-i", savePath], check=True)
        with open(screenPath, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        return (e, )
    
def solve(image: str):
    try:
        return requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": open('keyz').readline(),
                "Content-Type": "application/json",
            },
            data=json.dumps({
                "model": MODELS[MODELNOW],

                "messages": [
                {
                    "role": "user",
                    "content": [
                    {
                        "type": "text",
                        "text": "Реши задачу на фото. Строго запрещено использовать LaTeX math mode. В конце напиши \"Ответ: <ответ>\""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                        "url": f"data:image/png;base64,{image}"
                        }
                    },
                    ]
                }
                ],

                "reasoning_effort": "high",
            })
        )
    except Exception as e:
        return (e, )
    
def copyAnswer(solution: str):
    try:
        maket = r"Ответ\s*[:\-–—]?\s*(.+)"
        pyperclip.copy(re.findall(maket, solution)[-1])
    except:
        return

def main():
    pyperclip.copy("")
    screenshot = takeScreenshot()
    if isinstance(screenshot, tuple):
        return
    
    solution = solve(screenshot)
    if isinstance(solution, tuple):
        renderOutput(solution[0])
    else:
        copyAnswer(solution.json()["choices"][0]["message"]["content"])
        renderOutput(solution.json()["choices"][0]["message"]["content"])
    
if __name__ == "__main__":
    main()