import eel
import os
import sys
from queue import Queue

class ChatBot:
    started = False
    userinputQueue = Queue()

    # OS-specific imports and mouse functions
    if sys.platform == "win32":
        import win32api
        import win32con

        def move_mouse(x, y):
            win32api.SetCursorPos((x, y))

        def click():
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

    elif sys.platform == "darwin":
        import Quartz  # FIX: Import Quartz properly
        from Quartz.CoreGraphics import (
            CGEventCreateMouseEvent,
            kCGEventMouseMoved,
            kCGEventLeftMouseDown,
            kCGEventLeftMouseUp,
            kCGMouseButtonLeft,
        )

        def move_mouse(x, y):
            event = CGEventCreateMouseEvent(None, kCGEventMouseMoved, (x, y), kCGMouseButtonLeft)
            Quartz.CGEventPost(0, event)

        def click():
            event_down = CGEventCreateMouseEvent(None, kCGEventLeftMouseDown, (x, y), kCGMouseButtonLeft)
            event_up = CGEventCreateMouseEvent(None, kCGEventLeftMouseUp, (x, y), kCGMouseButtonLeft)
            Quartz.CGEventPost(0, event_down)
            Quartz.CGEventPost(0, event_up)

    # FIX: These functions should be outside the OS-specific check
    def isUserInput():
        return not ChatBot.userinputQueue.empty()

    def popUserInput():
        return ChatBot.userinputQueue.get()

    def close_callback(route, websockets):
        exit()

    @eel.expose
    def getUserInput(msg):
        ChatBot.userinputQueue.put(msg)
        print(msg)
    
    def close():
        ChatBot.started = False
    
    def addUserMsg(msg):
        eel.addUserMsg(msg)
    
    def addAppMsg(msg):
        eel.addAppMsg(msg)

    def start():
        path = os.path.dirname(os.path.abspath(__file__))
        eel.init(path + r'/web', allowed_extensions=['.js', '.html'])  # FIX: Use '/' instead of '\'

        try:
            eel.start(
                'index.html',
                mode='chrome',
                host='localhost',
                port=27005,
                block=False,
                size=(350, 480),
                position=(10, 100),
                disable_cache=True,
                close_callback=ChatBot.close_callback
            )
            ChatBot.started = True

            while ChatBot.started:
                try:
                    eel.sleep(10.0)
                except:
                    break  # Main thread exited

        except:
            pass  # Handle exceptions silently
