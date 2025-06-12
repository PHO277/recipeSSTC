import pyttsx3
import threading

class TextToSpeech:
    def __init__(self):
        self.engine = None
        self.speaking = False
        self.stop_requested = False
        self._init_engine()

    def _init_engine(self):
        try:
            if self.engine:
                self.engine.stop()
                del self.engine
        except:
            pass
        
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', 150)
        self.engine.setProperty('volume', 0.9)

    def speak(self, text):
        if text is None:  # Pause signal
            self.stop_requested = True
            if self.speaking and self.engine:
                try:
                    self.engine.stop()
                except:
                    pass
            return
        
        self.stop_requested = False
        if not self.speaking:
            self.speaking = True
            try:
                self._init_engine()  # 重新初始化引擎
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception as e:
                print(f"TTS Error: {e}")
            finally:
                self.speaking = False