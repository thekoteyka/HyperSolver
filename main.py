import os
import subprocess
import base64
import tkinter as tk
import pyperclip
import re
from openai import OpenAI
from typing import Literal

MODELS = {
    '2.5 flash': 'google/gemini-2.5-flash', # Default $2.5
    '3 flash': 'google/gemini-3-flash-preview', # $3
    '3.1 pro': 'google/gemini-3.1-pro-preview', # expensive $14
    '2.5 pro': 'google/gemini-2.5-pro' # $11
}
REASONING_EFFORTS = Literal[
    'minimal', 'low', 'medium', 'high', 'none'
]


MODELNOW = '3 flash'
REASONING: REASONING_EFFORTS = 'none'


def renderOutput(text):
    root = tk.Tk()
    root.title("Solver")
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
    currentDir = os.path.dirname(os.path.abspath(__file__))
    screenPath = f"{currentDir}/screen.png"

    if os.path.exists(screenPath):
        os.remove(screenPath)
    savePath = os.path.join(currentDir, "screen.png")
    
    try:
        subprocess.run(["screencapture", "-i", savePath], check=True)
        with open(screenPath, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        return (e, )
    
def solve(image: str):
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1/",
        api_key=open('keyz').readline(),
    )

    if REASONING == 'none': 
        reasosing_effort = None
    else:
        reasosing_effort = REASONING

    response = client.chat.completions.create(
        model = MODELS[MODELNOW],
        messages = [
                {
                    "role": "user",
                    "content": [
                    {
                        "type": "text",
                        "text": "Реши задачу на фото. Строго запрещено использовать LaTeX math mode. В конце напиши \"Ответ: <ответ>\". Если дробь возможно сделать десятичной -  сделай"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                        "url": f"data:image/png;base64,{image}"
                        }
                    }
                    ]
                }
                ],
        reasoning_effort = reasosing_effort,
        # extra_body = {"reasoning": {"enabled": True}}
    )
    return response.choices[0].message.content
    
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
    try:
        solution = solve(screenshot)
    except Exception as e:
        copyAnswer("Error")
        renderOutput(e)

    if solution is not None:
        copyAnswer(solution)
        renderOutput(solution)
    
if __name__ == "__main__":
    main()