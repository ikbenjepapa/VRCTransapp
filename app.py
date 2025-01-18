import openai
import os
from dotenv import load_dotenv
from pythonosc.udp_client import SimpleUDPClient
from tkinter import Tk, Text, Label, Button, ttk, StringVar
import speech_recognition as sr
import threading

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

VRCHAT_IP = "127.0.0.1"
VRCHAT_PORT = 9000
osc_client = SimpleUDPClient(VRCHAT_IP, VRCHAT_PORT)

language_map = {
    "Afrikaans": "af-ZA",
    "Albanian": "sq-AL",
    "Amharic": "am-ET",
    "Arabic": "ar-SA",
    "Arabic (Egypt)": "ar-EG",
    "Arabic (Gulf)": "ar-KW",
    "Arabic (Levant)": "ar-LB",
    "Armenian": "hy-AM",
    "Azerbaijani": "az-AZ",
    "Bengali": "bn-BD",
    "Bulgarian": "bg-BG",
    "Catalan": "ca-ES",
    "Chinese (Mandarin)": "zh-CN",
    "Chinese (Taiwan)": "zh-TW",
    "Croatian": "hr-HR",
    "Czech": "cs-CZ",
    "Danish": "da-DK",
    "Dutch": "nl-NL",
    "English (US)": "en-US",
    "English (UK)": "en-GB",
    "English (Australia)": "en-AU",
    "English (Canada)": "en-CA",
    "English (India)": "en-IN",
    "Finnish": "fi-FI",
    "French": "fr-FR",
    "German": "de-DE",
    "Greek": "el-GR",
    "Gujarati": "gu-IN",
    "Hebrew": "he-IL",
    "Hindi": "hi-IN",
    "Hungarian": "hu-HU",
    "Icelandic": "is-IS",
    "Indonesian": "id-ID",
    "Irish": "ga-IE",
    "Italian": "it-IT",
    "Japanese": "ja-JP",
    "Kannada": "kn-IN",
    "Khmer": "km-KH",
    "Korean": "ko-KR",
    "Latvian": "lv-LV",
    "Lithuanian": "lt-LT",
    "Malay": "ms-MY",
    "Malayalam": "ml-IN",
    "Marathi": "mr-IN",
    "Nepali": "ne-NP",
    "Norwegian Bokmål": "nb-NO",
    "Persian": "fa-IR",
    "Polish": "pl-PL",
    "Portuguese (Brazil)": "pt-BR",
    "Portuguese (Portugal)": "pt-PT",
    "Romanian": "ro-RO",
    "Russian": "ru-RU",
    "Serbian": "sr-RS",
    "Sinhala": "si-LK",
    "Slovak": "sk-SK",
    "Slovenian": "sl-SI",
    "Spanish": "es-ES",
    "Swahili": "sw-KE",
    "Swedish": "sv-SE",
    "Tamil": "ta-IN",
    "Telugu": "te-IN",
    "Thai": "th-TH",
    "Turkish": "tr-TR",
    "Ukrainian": "uk-UA",
    "Urdu": "ur-PK",
    "Vietnamese": "vi-VN",
    "Zulu": "zu-ZA"
}

request_count = 0
MAX_REQUESTS = 100

def check_limit():
    """
    Check if the request count exceeds the maximum allowed.
    """
    global request_count
    if request_count >= MAX_REQUESTS:
        return False
    request_count += 1
    return True

def remaining_requests():
    """
    Return the remaining number of requests.
    """
    return MAX_REQUESTS - request_count

def transcribe_audio(language_code, mic_label):
    """
    Capture and transcribe audio input using SpeechRecognition with a specified language.
    """
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        mic_label.config(text="Listening... Speak now!", fg="red")
        mic_label.update()
        try:
            audio = recognizer.listen(source, timeout=5)
            text = recognizer.recognize_google(audio, language=language_code)
            mic_label.config(text="Microphone ready.", fg="green")
            return text
        except sr.WaitTimeoutError:
            mic_label.config(text="No speech detected. Try again.", fg="orange")
            return None
        except sr.UnknownValueError:
            mic_label.config(text="Could not understand audio.", fg="orange")
            return None
        except Exception as e:
            mic_label.config(text=f"Error: {e}", fg="red")
            return None

def translate_text(text, input_language, target_language):
    """
    Translate text using OpenAI's ChatGPT.
    """
    if not check_limit():
        return "Testing limit reached. Contact the developer for more access."
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a helpful translator. Do not interpret or answer questions. Only translate the text."
                },
                {"role": "user", "content": f"Translate this from {input_language} to {target_language}: {text}"}
            ]
        )
        translated_text = response['choices'][0]['message']['content'].strip()
        return translated_text
    except Exception as e:
        print(f"Error during translation: {e}")
        return None

def send_to_chatbox(output_text):
    """
    Send text to VRChat Chatbox via OSC.
    """
    try:
        if not output_text:
            return
        osc_client.send_message("/chatbox/input", [output_text, True])
    except Exception as e:
        print(f"Error sending to Chatbox: {e}")

def start_translation(input_language, target_language, input_text_box, result_label, mic_label, remaining_label, mic=False):
    """
    Start the translation process.
    """
    if mic:
        input_lang_code = language_map.get(input_language)
        input_text = transcribe_audio(input_lang_code, mic_label)
        if not input_text:
            return
    else:
        input_text = input_text_box.get("1.0", "end").strip()

    if not input_text:
        result_label.config(text="No input provided.")
        return

    translated_text = translate_text(input_text, input_language, target_language)
    if translated_text:
        output_text = f"{translated_text} ({input_text})"
        result_label.config(text=output_text, fg="blue")
        send_to_chatbox(output_text)
    else:
        result_label.config(text="Translation failed.", fg="red")

    remaining_label.config(text=f"Remaining Requests: {remaining_requests()}")

def create_gui():
    """
    Create the GUI for the application.
    """
    root = Tk()
    root.title("VRChat Translator")
    root.geometry("600x700")
    root.configure(bg="#f5f5f5")

    style = ttk.Style()
    style.configure("TLabel", background="#f5f5f5", font=("Helvetica", 12))
    style.configure("TButton", font=("Helvetica", 12), padding=5)
    style.configure("TCombobox", padding=5)

    # Input Language Selection
    Label(root, text="Select Input Language:", bg="#f5f5f5", font=("Helvetica", 14)).pack(pady=10)
    input_language_var = StringVar()
    input_language_combo = ttk.Combobox(root, textvariable=input_language_var, values=list(language_map.keys()), state="readonly")
    input_language_combo.set("English (US)")
    input_language_combo.pack(pady=5)

    # Target Language Selection
    Label(root, text="Select Target Language:", bg="#f5f5f5", font=("Helvetica", 14)).pack(pady=10)
    target_language_var = StringVar()
    target_language_combo = ttk.Combobox(root, textvariable=target_language_var, values=list(language_map.keys()), state="readonly")
    target_language_combo.set("Japanese")
    target_language_combo.pack(pady=5)

    # Input Text Box
    Label(root, text="Enter Text (or leave blank and use microphone):", bg="#f5f5f5", font=("Helvetica", 14)).pack(pady=10)
    input_text_box = Text(root, height=6, width=50, font=("Helvetica", 12))
    input_text_box.pack(pady=10)

    # Microphone Status Label
    mic_label = Label(root, text="Microphone ready.", bg="#f5f5f5", fg="green", font=("Helvetica", 12))
    mic_label.pack(pady=5)

    # Remaining Requests Label
    remaining_label = Label(root, text=f"Remaining Requests: {remaining_requests()}", bg="#f5f5f5", fg="blue", font=("Helvetica", 12))
    remaining_label.pack(pady=5)

    # Buttons for Translate and Microphone
    button_frame = ttk.Frame(root)
    button_frame.pack(pady=20)

    translate_button = ttk.Button(button_frame, text="Translate Text", command=lambda: start_translation(
        input_language_var.get(),
        target_language_var.get(),
        input_text_box,
        result_label,
        mic_label,
        remaining_label
    ))
    translate_button.pack(side="left", padx=10)

    mic_button = ttk.Button(button_frame, text="Use Microphone", command=lambda: threading.Thread(target=start_translation, args=(
        input_language_var.get(),
        target_language_var.get(),
        input_text_box,
        result_label,
        mic_label,
        remaining_label,
        True
    )).start())
    mic_button.pack(side="right", padx=10)

    # Result Label
    result_label = Label(root, text="", bg="#f5f5f5", wraplength=400, font=("Helvetica", 12))
    result_label.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    create_gui()
