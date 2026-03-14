import speech_recognition as sr
import webbrowser
import pyttsx3
import musiclibary 
import requests
from openai import OpenAI
import threading
import time
import cv2
import base64
import spotipy
from spotipy.oauth2 import SpotifyOAuth

def speak(text):
    engine.say(text)
    engine.runAndWait()

NEWS_API_KEY = ""
OPENAI_API_KEY = ''

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id="",
    client_secret="",
    redirect_uri="",
    scope="user-read-playback-state,user-modify-playback-state"
))

engine = pyttsx3.init()
recognizer = sr.Recognizer()

def start_reminder_thread(seconds, message):
    def reminder_job():
        time.sleep(seconds)
        thread_engine = pyttsx3.init()
        thread_engine.say(f"Reminder: {message}")
        thread_engine.runAndWait()

    
    t = threading.Thread(target=reminder_job)
    t.start()

def cam():
    try:
        speak("Taking a photo now")
        
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            speak("Could not access camera")
            return
        
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            speak("Failed to capture image")
            return
        
        image_path = "captured_photo.jpg"
        cv2.imwrite(image_path, frame)
        
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe what you see in this image in one or two sentences."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=300
        )
        
        description = response.choices[0].message.content
        print(f"Image description: {description}")
        speak(description)
        
    except Exception as e:
        print(f"Camera error: {e}")
        speak("I had trouble with the camera")

def process_ai(command):
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        completion = client.chat.completions.create(
            model="gpt-5-nano", 
            messages=[
                {"role": "system", "content": "You are a virtual assistant named Bob. Give short responses."},
                {"role": "user", "content": command}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        return "I am having trouble connecting."

def processCommand(c):
    c = c.lower()
    
    if "open google" in c:
        webbrowser.open("https://google.com")
    elif "open youtube" in c:
        webbrowser.open("https://youtube.com")
    elif "open instagram" in c:
        webbrowser.open("https://instagram.com")
        
    elif c.startswith("play"):
        try:
            song_parts = c.split(" ")
            if len(song_parts) > 1:
                song = song_parts[1]
                link = musiclibary.music.get(song)
                if link:
                    webbrowser.open(link)
                else:
                    speak("Song not found in library.")
        except Exception as e:
            speak("Error playing song.")

    elif "news" in c:
        params = {"country": "in", "apiKey": NEWS_API_KEY}
        r = requests.get("https://newsapi.org/v2/top-headlines", params=params)
        if r.status_code == 200:
            data = r.json()
            articles = data.get("articles", [])[:3]
            for article in articles:
                speak(article.get("title"))
    elif "camera" in c or "cam" in c or "take a photo" in c or "take a picture" in c:
        cam()
    
    elif "remind me" in c:
        try:
            words = c.split()
            
            wait_time = 0
            multiplier = 1 
            
            if "minute" in c:
                multiplier = 60
                index = words.index("minute") if "minute" in words else words.index("minutes")
                wait_time = int(words[index - 1]) * multiplier
                
            elif "second" in c:
                index = words.index("second") if "second" in words else words.index("seconds")
                wait_time = int(words[index - 1])
            
            if "to" in words:
                msg_start = words.index("to") + 1
                message = " ".join(words[msg_start:])
            else:
                message = "Time is up!"

            speak(f"Setting a reminder for {wait_time // multiplier} {'minutes' if multiplier == 60 else 'seconds'}.")
            
            start_reminder_thread(wait_time, message)

        except Exception as e:
            print(f"REMINDER ERROR: {e}")
            speak("I couldn't set that reminder. Please say it like: Remind me in 10 seconds to check the stove.")
    
    else:
        output = process_ai(c)
        print(output)
        speak(output)

if __name__ == "__main__":
    speak("Bob is now online. ")
    
    while True:
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                print("Listening for wake word 'Bob'...")
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=3)
            
            wake_word = recognizer.recognize_google(audio).lower()
            
            if "bob" in wake_word:
                speak("Yes?")
                with sr.Microphone() as source:
                    print("Bob is listening for command...")
                    audio_command = recognizer.listen(source)
                    command = recognizer.recognize_google(audio_command)
                    print(f"User said: {command}")
                    processCommand(command)

        except sr.UnknownValueError:
            print("Could not understand audio")
        except Exception as e:
            print(f"Error: {e}")
