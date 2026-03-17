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
from pynput.keyboard import Key, Controller
from pynput.mouse import Controller as MouseController
import time


"""
TODO:
curl -X GET "https://openrouter.ai/api/v1/key" \
  -H "Authorization: Bearer ..."
"""

modelsApiNames = {
  '2.5 flash': 'google/gemini-2.5-flash', # $2.5 I think better to use 3 flash for $0.5 more
    '3 flash': 'google/gemini-3-flash-preview', # $3 Good for everething
    '3.1 pro': 'google/gemini-3.1-pro-preview', # $14 Expensive
    '3 flash lite': 'google/gemini-3.1-flash-lite-preview', # $1.75 very quick, good for easy problems
}
modelsAvailable = Literal[
    '2.5 flash', '3 flash lite', '3 flash', '3.1 pro'
]

reasoningEfforts = Literal[
    'minimal', 'low', 'medium', 'high', 'none'
]


selectedModel: modelsAvailable   = '3 flash lite'
reasoningLevel: reasoningEfforts = 'minimal'
closingDelay: int = 1   # seconds | Window wont be shown if autoSubmitAnswer enabled
soundWhenDone: int|bool = True # macos only
autoSubmitAnswer: int|bool = 1 # macos only | Also auto presses continue on trenings | Removes tkinter window with answer if enabled
loopSolving: int|bool = 1 # After solving the problem, automatically start the script again. To exit press esc when choosing area for screenshot


bypassCheckKeyz = False # For whaever reason you might want to bypass check of keyz file

# Whole display screenshot insted of area screenshot
# If used with loopSolving enabled, to stop the loop put mouse in left upper corner or terminate the script
autoScreenshot: int|bool = 1


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
    Thread(target=terminateRoot, args=(root, customClosingDelay or closingDelay)).run()
    root.mainloop()

def getScreenshot() -> str:
    """
    Gets screenshot & handles errors. Returns base64 string of the image
    """
    screenPath = f"{currentDir}/screen.png"

    if os.path.exists(screenPath):
        os.remove(screenPath)
    try:
        scr = _takeScreenshot(screenPath)
        os.remove(screenPath)
        return scr
    except FileNotFoundError:  # probably pressed esc
        exit()
    except Exception as e:
        print(f"Error taking screenshot:\n{e}")
        # renderOutput(str(e), customClosingDelay=45, title="Error")
        exit()

def _takeScreenshot(screenPath: str) -> str:
    """
    Directly takes a screenshot and returns it as a base64 string
    """
    if autoScreenshot:
        subprocess.run(["screencapture", "-x", screenPath], check=True)
    else:
        subprocess.run(["screencapture", "-i", screenPath], check=True)

    with open(screenPath, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")
    
def askModel(client: OpenAI, messages, reasoning_effort: Literal['minimal', 'low', 'medium', 'high'] | None) -> ChatCompletion:
    response = client.chat.completions.create(
        model = modelsApiNames[selectedModel],
        messages = messages,
        reasoning_effort = reasoning_effort
    )
    return response
    
def solve(image: str):
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1/",
        api_key=open('keyz').readline(),
    )

    if reasoningLevel == 'none': 
        reasoning_effort = None
    else:
        reasoning_effort = reasoningLevel

    messages = [
        {
            "role": "user",
            "content": [
            {
                "type": "text",
                "text": f"Реши задачу на фото. Строго запрещено использовать LaTeX math mode. {'Если задач несколько, решай ту, около которой в поле ответа выделен курсор (окошко ввода ответа синее)' if autoScreenshot else ''} В конце напиши \"Ответ: <ответ>\". Если дробь возможно сделать десятичной -  сделай. ЕСЛИ НА КАРТИНКЕ НАПИСАНО 'ТРЕНИНГ' ТО В КОНЦЕ ОТВЕТА ДОБАВЬ !, например: Ответ: 29!"
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{image}"
                }
            }
            ]
        }
    ]

    return askModel(client, messages, reasoning_effort)

def getSystem() -> str:
    if os.name == 'nt':
        return "windows"
    else:
        return "macos"
    
def copyAnswer(solution: str):
    try:
        maket = r"Ответ\s*[:\-–—]?\s*(.+)"
        pyperclip.copy(re.findall(maket, solution)[-1])
    except:
        return
    
def openFile(path: str) -> None:
    if getSystem() == "windows":
        os.startfile(path) # type: ignore
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
    screenshot: str = getScreenshot()

    try:
        response = solve(screenshot)
    except Exception as e:
        copyAnswer("Error")
        renderOutput(str(e))

    solution = response.choices[0].message.content

    if solution is not None:
        if solution.endswith('.'):
            solution = solution[:-1]
        trening = False
        if solution.endswith('!'):
            solution = solution[:-1]
            trening = True
        copyAnswer(solution)
        if soundWhenDone and getSystem() == "macos":
            os.system('afplay /System/Library/Sounds/Tink.aiff')
        if autoSubmitAnswer and getSystem() == "macos":
            keyboard = Controller()
            with keyboard.pressed(Key.cmd):
                keyboard.press('v')
                keyboard.release('v')
            
            for i in range(2 if trening else 1):
                time.sleep(0.1)
                keyboard.press(Key.tab)
                keyboard.release(Key.tab)
                
                time.sleep(0.1)
                keyboard.press(Key.space)
                keyboard.release(Key.space)
            
            time.sleep(0.4)
            if trening:
                with keyboard.pressed(Key.shift_l):
                    keyboard.press(Key.tab)
                    keyboard.release(Key.tab)

                    keyboard.press(Key.tab)
                    keyboard.release(Key.tab)
            else:
                for i in range(5):
                    # time.sleep(0.1)
                    keyboard.press(Key.tab)
                    keyboard.release(Key.tab)
                
        if not autoSubmitAnswer:
            renderOutput(solution, title=makeTitle(response))
    
if __name__ == "__main__":
    if not bypassCheckKeyz:
        checkKeyzFile()
    if loopSolving:
        while True:
            mouseNow = MouseController().position
            if autoScreenshot:
                if mouseNow[0] < 5 and mouseNow[1] < 5: # exit if mouse in left upper corner
                    break
            main()
    else:
        main()
