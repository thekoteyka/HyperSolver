import os
import subprocess
import base64
import tkinter as tk
import pyperclip
import re
from openai import OpenAI
from openai.types.chat import ChatCompletion
from typing import Literal
from threading import Thread

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
REASONING: REASONING_EFFORTS = 'low'
CLOSING_DELAY: int = 20   # seconds


currentDir = os.path.dirname(os.path.abspath(__file__))

def terminateRoot(root, delay: int):
    root.after(delay*1000, lambda: root.destroy())

def makeTitle(response: ChatCompletion) -> str | None:
    usage = response.usage
    if usage is None:
        return None
    completionTokens = usage.completion_tokens
    reasoningTokens = usage.completion_tokens_details.reasoning_tokens if usage.completion_tokens_details else 0
    try:
        cost = float(usage.cost)  # type: ignore
    except:
        cost = None
    
    title = f"VISIBLE: {completionTokens} | REASONING: {reasoningTokens or '?'}"
    if isinstance(cost, float):
        title += f" | ${round(cost, 3)}"

    return title
    

def renderOutput(text: str, customClosingDelay: int | None = None, title: str | None = None):
    """
    Show text in tkinter window and close it after `CLOSING_DELAY` by default, or `customClosingDelay` if specified
    """
    root = tk.Tk()
    root.title(title or "Solution")
    root.iconify()
    text_widget = tk.Text(root, wrap="word", font=("Arial", 14))
    text_widget.insert("1.0", text)
    text_widget.config(state="disabled") 
    text_widget.pack(side="left", fill="both", expand=True)
    scrollbar = tk.Scrollbar(root, command=text_widget.yview)
    scrollbar.pack(side="right", fill="y")
    text_widget.config(yscrollcommand=scrollbar.set)
    Thread(target=terminateRoot, args=(root, customClosingDelay or CLOSING_DELAY)).run()
    root.mainloop()

def takeScreenshot():
    screenPath = f"{currentDir}/screen.png"

    if os.path.exists(screenPath):
        os.remove(screenPath)
    
    try:
        subprocess.run(["screencapture", "-i", screenPath], check=True)
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
    # print(response.usage)
    return response
    
def copyAnswer(solution: str):
    try:
        maket = r"Ответ\s*[:\-–—]?\s*(.+)"
        pyperclip.copy(re.findall(maket, solution)[-1])
    except:
        return
    
def openFile(path: str) -> None:
    if os.name == 'nt':
        os.startfile(path)
    else:
        subprocess.call(['open', path]) 
    
def checkKeyzFile() -> None:
    """
    checks if keyz file is present and have correct key in it
    """
    keyzPath = f"{currentDir}/keyz"

    if os.path.exists(keyzPath):
        with open(keyzPath) as f:
            stream = f.readline()

        if stream.startswith('sk-or-'):
            if len(stream) == 73:
                return
            if len(stream.strip()) == 73:
                with open(keyzPath, 'w') as f:
                    f.write(stream.strip())
                return
    
    with open(keyzPath, 'w') as f:
        f.write('< INSERT YOUR API KEY FROM OPENROUTER HERE AND RESTART >')
    openFile(keyzPath)
    s = f"Insert your api token from openrouter into `keyz` file. It should open automatically ( {keyzPath} )"
    print(s)
    exit()


def main():
    pyperclip.copy("")
    screenshot = takeScreenshot()
    if isinstance(screenshot, tuple):
        return
    try:
        response = solve(screenshot)
    except Exception as e:
        copyAnswer("Error")
        renderOutput(str(e))

    solution = response.choices[0].message.content

    if solution is not None:
        copyAnswer(solution)
        renderOutput(solution, title=makeTitle(response))
    
if __name__ == "__main__":
    checkKeyzFile()
    main()