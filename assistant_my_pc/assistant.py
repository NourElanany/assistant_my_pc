#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
            Jarvis AI Assistant - النسخة الكاملة مع واجهة مستخدم عصرية
===============================================================================
الوصف:
- مساعد صوتي متقدم يدعم العديد من الوظائف:
    • فتح وإغلاق التطبيقات (Notepad, CMD, Calculator، إلخ).
    • تشغيل الموسيقى، الفيديو، قراءة الملفات، البحث في ويكيبيديا وجوجل، وغيرها.
    • حساب تعبيرات رياضية، تحويل العملات ودرجات الحرارة، قراءة ملفات PDF.
    • وظائف إضافية مثل الترجمة، النكت، التذكيرات، معلومات النظام، البطارية، إلخ.
- الواجهة مقسمة إلى تبويبات (Notebook) للأقسام:
    • System (النظام)
    • Media (الإعلام)
    • Web (الويب)
    • Tools (الأدوات)
===============================================================================
"""

# ============================ استيراد المكتبات الأساسية ============================
import pyttsx3
import datetime
import os
import random
import requests
import wikipedia
import webbrowser
import sys
import platform
import math
import threading
import time

import numpy as np
import wave
import sounddevice as sd
import vlc


import tkinter as tk
from tkinter import simpledialog, filedialog, Scrollbar
from tkinter import Text, Label, Frame, Tk, LabelFrame
# استخدام أزرار tkinter لتخصيص الألوان بسهولة
from tkinter import Button as tkButton, Entry as tkEntry

from tkinter import ttk

# ============================ متغيرات عامة ============================
root = None           # سيتم تهيئته في الدالة main()
text_results = None   # نافذة عرض النتائج


vlc_player = None


# ============================ تهيئة محرك النطق ============================
if platform.system() == 'Windows':
    engine = pyttsx3.init('sapi5')
elif platform.system() == 'Darwin':  # macOS
    engine = pyttsx3.init('nsss')
else:
    engine = pyttsx3.init('espeak')

voices = engine.getProperty("voices")
if voices:
    engine.setProperty('voice', voices[0].id)



# ============================ كلاس لتسجيل الصوت ============================
class AudioRecorder:
    def __init__(self, fs=44100, channels=2):
        self.fs = fs
        self.channels = channels
        self.recording = []
        self.stream = None
        self.recording_active = False

    def callback(self, indata, frames, time, status):
        if status:
            print(status)
        self.recording.append(indata.copy())

    def start(self):
        self.recording = []
        self.recording_active = True
        self.stream = sd.InputStream(samplerate=self.fs, channels=self.channels, callback=self.callback)
        self.stream.start()
        speak("Recording started. / بدء تسجيل الصوت.")

    def stop(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.recording_active = False
            audio_data = np.concatenate(self.recording, axis=0)
            filename = filedialog.asksaveasfilename(defaultextension=".wav", filetypes=[("WAV Files", "*.wav")], title="Save Audio Recording / حفظ تسجيل الصوت")
            if filename:
                with wave.open(filename, 'wb') as wf:
                    wf.setnchannels(self.channels)
                    wf.setsampwidth(2)  # 16-bit
                    wf.setframerate(self.fs)
                    wf.writeframes(audio_data.tobytes())
                speak("Audio recording saved. / تم حفظ تسجيل الصوت.")
            else:
                speak("Audio recording cancelled. / تم إلغاء تسجيل الصوت.")

global audio_recorder
audio_recorder = AudioRecorder()

# ============================ الدوال الأساسية ============================
def update_results(message):
    """
    تحديث نافذة النتائج بالنص المُرسل.
    """
    global text_results
    try:
        if text_results is not None:
            text_results.insert(tk.END, message + "\n")
            text_results.see(tk.END)
    except Exception as e:
        print("Error updating results:", e)

def speak(audio):
    """
    النطق بالنص وإظهار الرسالة في وحدة النتائج.
    """
    engine.say(audio)
    print(audio)
    engine.runAndWait()
    update_results(audio)

def wish():
    """
    تحية المستخدم ونطق رسالة ترحيبية.
    """
    hour = int(datetime.datetime.now().hour)
    if 0 <= hour <= 12:
        speak("Good morning Sir / صباح الخير")
    elif 12 < hour < 16:
        speak("Good afternoon Sir / مساء الخير")
    else:
        speak("Good evening Sir / مساء الخير")
    speak("I am Jarvis. I can help you with daily tasks. Please use the buttons provided. / أنا جارفيس. يمكنني مساعدتك في المهام اليومية. استخدم الأزرار الموجودة.")

def search_wikipedia_command():
    """
    تنفيذ بحث في ويكيبيديا بعد طلب استعلام من المستخدم.
    """
    query = simpledialog.askstring("Wikipedia Search", "Enter search term for Wikipedia / أدخل استعلام ويكيبيديا:")
    if query:
        process_query("wikipedia " + query)

def search_google_command():
    """
    تنفيذ بحث في جوجل بعد طلب استعلام من المستخدم.
    """
    query = simpledialog.askstring("Google Search", "Enter search query / أدخل استعلام البحث:")
    if query:
        process_query("search google " + query)

# ============================ دالة معالجة الأوامر ============================
def process_query(query):
    """
    معالجة أمر المستخدم وتنفيذ الوظيفة المناسبة بناءً على الكلمات المفتاحية.
    تشمل هذه الدالة أوامر النظام (حوالي 15 أمر)، أوامر الوسائط والإعلام (حوالي 15 أمر)، أوامر الويب والبحث (حوالي 15 أمر)، وأوامر الأدوات والحسابات (حوالي 25 أمر).
    """
    query_lower = query.lower()

    # --- أوامر النظام ---
    if "open notepad" in query_lower or "افتح المفكرة" in query_lower:
        if platform.system() == 'Windows':
            npath = r'C:\Windows\System32\notepad.exe'
            try:
                os.startfile(npath)
                speak("Please wait! Opening Notepad for you. / جاري فتح المفكرة.")
            except Exception:
                speak("Failed to open Notepad. / فشل في فتح المفكرة.")
        else:
            speak("Open Notepad command is only supported on Windows. / هذا الأمر مدعوم فقط على ويندوز.")

    elif "open cmd" in query_lower or "افتح موجه الأوامر" in query_lower:
        if platform.system() == 'Windows':
            try:
                os.system('start cmd')
                speak("Opening Command Prompt. / جاري فتح موجه الأوامر.")
            except Exception:
                speak("Failed to open Command Prompt. / فشل في فتح موجه الأوامر.")
        else:
            speak("Open CMD command is only supported on Windows. / هذا الأمر مدعوم فقط على ويندوز.")

    elif "close notepad" in query_lower or "اغلق المفكرة" in query_lower:
        if platform.system() == 'Windows':
            speak("Closing Notepad. / جاري إغلاق المفكرة.")
            os.system("taskkill /f /im notepad.exe")
        else:
            speak("Close Notepad command is only supported on Windows. / هذا الأمر مدعوم فقط على ويندوز.")

    elif "close cmd" in query_lower or "اغلق موجه الأوامر" in query_lower:
        if platform.system() == 'Windows':
            speak("Closing Command Prompt. / جاري إغلاق موجه الأوامر.")
            os.system("taskkill /f /im cmd.exe")
        else:
            speak("Close CMD command is only supported on Windows. / هذا الأمر مدعوم فقط على ويندوز.")

    elif "lock computer" in query_lower or "اقفل الكمبيوتر" in query_lower:
        if platform.system() == 'Windows':
            os.system("rundll32.exe user32.dll,LockWorkStation")
            speak("Locking the computer. / جاري قفل الكمبيوتر.")
        elif platform.system() == 'Darwin':
            speak("Locking is not implemented on macOS in this version. / لم يتم تنفيذ القفل على macOS في هذا الإصدار.")
        else:
            speak("Lock computer command is not supported on this system. / هذا الأمر غير مدعوم على هذا النظام.")

    elif "restart" in query_lower or "أعد التشغيل" in query_lower:
        if platform.system() == 'Windows':
            speak("Restarting the system. / جاري إعادة التشغيل.")
            os.system("shutdown /r /t 1")
        elif platform.system() == 'Darwin':
            speak("Restarting the system. / جاري إعادة التشغيل.")
            os.system("osascript -e 'tell app \"System Events\" to restart'")
        else:
            try:
                speak("Restarting the system. / جاري إعادة التشغيل.")
                os.system("shutdown -r now")
            except Exception:
                speak("Restart command is not supported on this system. / هذا الأمر غير مدعوم على هذا النظام.")

    elif "shutdown" in query_lower or "اغلق النظام" in query_lower:
        if platform.system() == 'Windows':
            speak("Shutting down the system. / جاري إغلاق النظام.")
            os.system("shutdown /s /t 1")
        elif platform.system() == 'Darwin':
            speak("Shutting down the system. / جاري إغلاق النظام.")
            os.system("osascript -e 'tell app \"System Events\" to shut down'")
        else:
            try:
                speak("Shutting down the system. / جاري إغلاق النظام.")
                os.system("shutdown -h now")
            except Exception:
                speak("Shutdown command is not supported on this system. / هذا الأمر غير مدعوم على هذا النظام.")

    elif "open calculator" in query_lower or "افتح الآلة الحاسبة" in query_lower:
        if platform.system() == 'Windows':
            try:
                os.startfile("calc.exe")
                speak("Opening Calculator. / جاري فتح الآلة الحاسبة.")
            except Exception:
                speak("Failed to open Calculator. / فشل في فتح الآلة الحاسبة.")
        elif platform.system() == 'Darwin':
            os.system("open -a Calculator")
            speak("Opening Calculator. / جاري فتح الآلة الحاسبة.")
        else:
            os.system("gnome-calculator &")
            speak("Opening Calculator. / جاري فتح الآلة الحاسبة.")

    elif "open file explorer" in query_lower or "افتح الملفات" in query_lower or "افتح المستعرض" in query_lower:
        if platform.system() == 'Windows':
            os.system("explorer")
            speak("Opening File Explorer. / جاري فتح مستكشف الملفات.")
        elif platform.system() == 'Darwin':
            os.system("open .")
            speak("Opening File Explorer. / جاري فتح مستكشف الملفات.")
        else:
            os.system("xdg-open .")
            speak("Opening File Explorer. / جاري فتح مستكشف الملفات.")

    elif "system info" in query_lower or "معلومات النظام" in query_lower:
        info = f"System: {platform.system()}, Release: {platform.release()}, Version: {platform.version()}"
        speak(info)

    elif "ip address" in query_lower or "عنوان الاي بي" in query_lower:
        try:
            ip = requests.get("https://api.ipify.org").text
            speak(f"Your IP address is {ip}. / عنوان الآي بي الخاص بك هو {ip}")
        except Exception:
            speak("Unable to get IP address at the moment. / غير قادر على الحصول على عنوان الآي بي حالياً.")

    elif "open task manager" in query_lower or "افتح مدير المهام" in query_lower:
        if platform.system() == 'Windows':
            try:
                os.startfile("taskmgr.exe")
                speak("Opening Task Manager. / جاري فتح مدير المهام.")
            except Exception:
                speak("Failed to open Task Manager. / فشل في فتح مدير المهام.")
        else:
            speak("Task Manager command is only supported on Windows. / هذا الأمر مدعوم فقط على ويندوز.")

    elif "log off" in query_lower or "تسجيل خروج" in query_lower:
        if platform.system() == 'Windows':
            os.system("shutdown /l")
            speak("Logging off. / جاري تسجيل الخروج.")
        else:
            speak("Log off command is only supported on Windows. / هذا الأمر مدعوم فقط على ويندوز.")

    elif "open control panel" in query_lower or "افتح لوحة التحكم" in query_lower:
        if platform.system() == 'Windows':
            os.system("control")
            speak("Opening Control Panel. / جاري فتح لوحة التحكم.")
        else:
            speak("Control Panel command is only supported on Windows. / هذا الأمر مدعوم فقط على ويندوز.")

    elif "hibernate" in query_lower or "ضع النظام في وضع السبات" in query_lower:
        if platform.system() == 'Windows':
            try:
                os.system("shutdown /h")
                speak("Hibernating the system. / جاري وضع النظام في وضع السبات.")
            except Exception:
                speak("Failed to hibernate the system. / فشل في وضع النظام في وضع السبات.")
        else:
            speak("Hibernate command is only supported on Windows. / هذا الأمر مدعوم فقط على ويندوز.")

    # --- أوامر الوسائط والإعلام ---
    elif "play music" in query_lower or "شغل الموسيقى" in query_lower:
        if platform.system() == 'Windows':
            music_dir = r'D:\Songs'  # حدث المسار حسب جهازك
        elif platform.system() == 'Darwin':
            music_dir = '/Users/yourusername/Music'
        else:
            music_dir = '/home/yourusername/Music'
        if os.path.exists(music_dir):
            songs = os.listdir(music_dir)
            if songs:
                rd = random.choice(songs)
                song_path = os.path.join(music_dir, rd)
                try:
                    if platform.system() == 'Windows':
                        os.startfile(song_path)
                    elif platform.system() == 'Darwin':
                        os.system(f"open '{song_path}'")
                    else:
                        os.system(f"xdg-open '{song_path}'")
                    speak("Playing Music. / جاري تشغيل الموسيقى.")
                except Exception:
                    speak("Failed to play music. / فشل في تشغيل الموسيقى.")
            else:
                speak("No songs found in the specified directory. / لم يتم العثور على أغانٍ في المجلد المحدد.")
        else:
            speak("Music directory not found. / لم يتم العثور على مجلد الموسيقى.")

    elif "play video" in query_lower or "شغل فيديو" in query_lower:
        video_path = filedialog.askopenfilename(title="Select Video File", filetypes=[("Video Files", "*.mp4;*.avi;*.mkv"), ("All Files", "*.*")])
        if video_path and os.path.exists(video_path):
            try:
                global vlc_player
                vlc_instance = vlc.Instance()
                vlc_player = vlc_instance.media_player_new()
                media = vlc_instance.media_new(video_path)
                vlc_player.set_media(media)
                vlc_player.play()
                speak("Playing video using VLC. / جاري تشغيل الفيديو باستخدام VLC.")
            except Exception as e:
                speak("Failed to play video. / فشل في تشغيل الفيديو: " + str(e))
        else:
            speak("Video file not found. / لم يتم العثور على ملف الفيديو.")

    elif "pause video" in query_lower or "أوقف الفيديو" in query_lower:
       
        if vlc_player is not None:
            vlc_player.pause()
            speak("Video paused. / تم إيقاف الفيديو مؤقتًا.")
        else:
            speak("No video is currently playing. / لا يوجد فيديو يعمل حاليًا.")

    elif "resume video" in query_lower or "استأنف الفيديو" in query_lower:
        
        if vlc_player is not None:
            vlc_player.play()
            speak("Video resumed. / تم استئناف الفيديو.")
        else:
            speak("No video is currently playing. / لا يوجد فيديو يعمل حاليًا.")

    elif "screenshot" in query_lower or "لقطة شاشة" in query_lower:
        try:
            import pyautogui
            screenshot = pyautogui.screenshot()
            file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Files", "*.png")], title="Save Screenshot / حفظ لقطة الشاشة")
            if file_path:
                screenshot.save(file_path)
                speak("Screenshot saved successfully. / تم حفظ لقطة الشاشة بنجاح.")
            else:
                speak("Screenshot saving cancelled. / تم إلغاء حفظ لقطة الشاشة.")
        except Exception as e:
            speak("Failed to take screenshot. / فشل في أخذ لقطة الشاشة: " + str(e))

    elif "play radio" in query_lower:
        webbrowser.open("https://www.internet-radio.com/")
        speak("Playing radio. / جاري تشغيل الراديو.")

    elif "open movies" in query_lower or "افتح الأفلام" in query_lower:
        if platform.system() == 'Windows':
            movies_dir = r'D:\Movies'
        elif platform.system() == 'Darwin':
            movies_dir = '/Users/yourusername/Movies'
        else:
            movies_dir = '/home/yourusername/Movies'
        if os.path.exists(movies_dir):
            try:
                if platform.system() == 'Windows':
                    os.startfile(movies_dir)
                elif platform.system() == 'Darwin':
                    os.system(f"open '{movies_dir}'")
                else:
                    os.system(f"xdg-open '{movies_dir}'")
                speak("Opening Movies folder. / جاري فتح مجلد الأفلام.")
            except Exception:
                speak("Failed to open Movies folder. / فشل في فتح مجلد الأفلام.")
        else:
            speak("Movies folder not found. / لم يتم العثور على مجلد الأفلام.")

    elif "open podcasts" in query_lower or "افتح البودكاست" in query_lower:
        if platform.system() == 'Windows':
            podcasts_dir = r'D:\Podcasts'
        elif platform.system() == 'Darwin':
            podcasts_dir = '/Users/yourusername/Podcasts'
        else:
            podcasts_dir = '/home/yourusername/Podcasts'
        if os.path.exists(podcasts_dir):
            try:
                if platform.system() == 'Windows':
                    os.startfile(podcasts_dir)
                elif platform.system() == 'Darwin':
                    os.system(f"open '{podcasts_dir}'")
                else:
                    os.system(f"xdg-open '{podcasts_dir}'")
                speak("Opening Podcasts folder. / جاري فتح مجلد البودكاست.")
            except Exception:
                speak("Failed to open Podcasts folder. / فشل في فتح مجلد البودكاست.")
        else:
            speak("Podcasts folder not found. / لم يتم العثور على مجلد البودكاست.")

    elif "open images" in query_lower or "افتح الصور" in query_lower:
        if platform.system() == 'Windows':
            images_dir = r'D:\Pictures'
        elif platform.system() == 'Darwin':
            images_dir = '/Users/yourusername/Pictures'
        else:
            images_dir = '/home/yourusername/Pictures'
        if os.path.exists(images_dir):
            try:
                if platform.system() == 'Windows':
                    os.startfile(images_dir)
                elif platform.system() == 'Darwin':
                    os.system(f"open '{images_dir}'")
                else:
                    os.system(f"xdg-open '{images_dir}'")
                speak("Opening Images folder. / جاري فتح مجلد الصور.")
            except Exception:
                speak("Failed to open Images folder. / فشل في فتح مجلد الصور.")
        else:
            speak("Images folder not found. / لم يتم العثور على مجلد الصور.")

    elif "record audio" in query_lower or "سجل صوت" in query_lower:
        global audio_recorder
        if not audio_recorder.recording_active:
            audio_recorder.start()
        else:
            speak("Audio recording is already in progress. / جاري تسجيل الصوت بالفعل.")

    elif "stop audio recording" in query_lower or "أوقف تسجيل الصوت" in query_lower:
        
        if audio_recorder.recording_active:
            audio_recorder.stop()
        else:
            speak("No audio recording is in progress. / لا يوجد تسجيل صوتي جارٍ.")

    elif "open vlc" in query_lower or "افتح في إل سي" in query_lower:
        if platform.system() == 'Windows':
            vlc_path = r"C:\Program Files\VideoLAN\VLC\vlc.exe"
            if os.path.exists(vlc_path):
                try:
                    os.startfile(vlc_path)
                    speak("Opening VLC Media Player. / جاري فتح VLC.")
                except Exception:
                    speak("Failed to open VLC Media Player. / فشل في فتح VLC.")
            else:
                speak("VLC Media Player not found. / لم يتم العثور على VLC.")
        elif platform.system() == 'Darwin':
            os.system("open -a VLC")
            speak("Opening VLC Media Player. / جاري فتح VLC.")
        else:
            os.system("vlc")
            speak("Opening VLC Media Player. / جاري فتح VLC.")

    elif "play streaming" in query_lower or "شغل البث" in query_lower:
        webbrowser.open("https://open.spotify.com/")
        speak("Opening Spotify Web Player. / جاري فتح مشغل Spotify على الويب.")

    elif "pause video" in query_lower or "أوقف الفيديو" in query_lower:
       
        if vlc_player is not None:
            vlc_player.pause()
            speak("Video paused. / تم إيقاف الفيديو مؤقتًا.")
        else:
            speak("No video is currently playing. / لا يوجد فيديو يعمل حاليًا.")

    elif "resume video" in query_lower or "استأنف الفيديو" in query_lower:
        
        if vlc_player is not None:
            vlc_player.play()
            speak("Video resumed. / تم استئناف الفيديو.")
        else:
            speak("No video is currently playing. / لا يوجد فيديو يعمل حاليًا.")

    elif "open sound settings" in query_lower or "افتح إعدادات الصوت" in query_lower:
        if platform.system() == 'Windows':
            try:
                os.system("mmsys.cpl")
                speak("Opening Sound Settings. / جاري فتح إعدادات الصوت.")
            except Exception:
                speak("Failed to open Sound Settings. / فشل في فتح إعدادات الصوت.")
        else:
            speak("Sound settings command is only supported on Windows. / هذا الأمر مدعوم فقط على ويندوز.")

    elif "play online video" in query_lower or "شغل فيديو اونلاين" in query_lower:
        webbrowser.open("https://www.netflix.com/")
        speak("Opening Netflix. / جاري فتح Netflix.")

    elif "increase volume" in query_lower:
        
        if vlc_player is not None:
            vol = vlc_player.audio_get_volume()
            new_vol = min(vol + 10, 100)
            vlc_player.audio_set_volume(new_vol)
            speak(f"Volume increased to {new_vol}. / تم زيادة الصوت إلى {new_vol}.")
        else:
            speak("No video is currently playing to adjust volume. / لا يوجد فيديو جارٍ لتعديل الصوت.")

    elif "decrease volume" in query_lower:
       
        if vlc_player is not None:
            vol = vlc_player.audio_get_volume()
            new_vol = max(vol - 10, 0)
            vlc_player.audio_set_volume(new_vol)
            speak(f"Volume decreased to {new_vol}. / تم تقليل الصوت إلى {new_vol}.")
        else:
            speak("No video is currently playing to adjust volume. / لا يوجد فيديو جارٍ لتعديل الصوت.")

    # --- أوامر الويب والبحث ---
    elif "search google" in query_lower or "ابحث في جوجل" in query_lower:
        speak("What should I search on Google? / ماذا تريد أن أبحث في جوجل؟")
        if query_lower.strip() not in ["search google", "ابحث في جوجل"]:
            term = query_lower.replace("search google", "").replace("ابحث في جوجل", "").strip()
            if term:
                webbrowser.open(f"https://www.google.com/search?q={term}")
                speak(f"Here are the results for {term} on Google. / هذه هي النتائج لـ {term} على جوجل.")
            else:
                speak("No search query provided. / لم يتم تقديم استعلام للبحث.")
        else:
            search_google_command()

    elif "search youtube" in query_lower or "ابحث في يوتيوب" in query_lower:
        search_term = simpledialog.askstring("YouTube Search", "Enter search query for YouTube / أدخل استعلام البحث على يوتيوب:")
        if search_term:
            webbrowser.open(f"https://www.youtube.com/results?search_query={search_term}")
            speak(f"Here are the YouTube results for {search_term} / هذه هي النتائج على يوتيوب لـ {search_term}.")
        else:
            speak("No search query provided. / لم يتم تقديم استعلام للبحث.")

    elif "wikipedia" in query_lower or "ويكيبيديا" in query_lower:
        speak("Searching in Wikipedia. / جاري البحث في ويكيبيديا.")
        search_term = query_lower.replace("wikipedia", "").replace("ويكيبيديا", "").strip()
        try:
            results = wikipedia.summary(search_term, sentences=2)
            speak(f"According to Wikipedia: {results}")
        except Exception:
            speak("Sorry, I couldn't find any results on Wikipedia. / عذراً، لم أجد نتائج في ويكيبيديا.")

    elif "open youtube" in query_lower or "افتح يوتيوب" in query_lower:
        webbrowser.open('https://www.youtube.com/')
        speak("Opening YouTube. / جاري فتح يوتيوب.")

    elif "open instagram" in query_lower or "افتح انستجرام" in query_lower:
        webbrowser.open('https://www.instagram.com/')
        speak("Opening Instagram. / جاري فتح انستجرام.")

    elif "open facebook" in query_lower or "افتح فيسبوك" in query_lower:
        webbrowser.open('https://www.facebook.com/')
        speak("Opening Facebook. / جاري فتح فيسبوك.")

    elif "open twitter" in query_lower or "افتح تويتر" in query_lower:
        webbrowser.open('https://www.twitter.com/')
        speak("Opening Twitter. / جاري فتح تويتر.")

    elif "open maps" in query_lower or "افتح الخرائط" in query_lower:
        webbrowser.open("https://www.google.com/maps")
        speak("Opening Google Maps. / جاري فتح خرائط جوجل.")

    elif "open reddit" in query_lower or "افتح ريديت" in query_lower:
        webbrowser.open("https://www.reddit.com/")
        speak("Opening Reddit. / جاري فتح ريديت.")

    elif "open linkedin" in query_lower or "افتح لينكد إن" in query_lower:
        webbrowser.open("https://www.linkedin.com/")
        speak("Opening LinkedIn. / جاري فتح لينكد إن.")

    elif "search bing" in query_lower or "ابحث في بينغ" in query_lower:
        speak("What should I search on Bing? / ماذا تريد أن أبحث في بينغ؟")
        term = query_lower.replace("search bing", "").replace("ابحث في بينغ", "").strip()
        if term:
            webbrowser.open(f"https://www.bing.com/search?q={term}")
            speak(f"Here are the results for {term} on Bing. / هذه هي النتائج لـ {term} على بينغ.")
        else:
            search_term = simpledialog.askstring("Bing Search", "Enter search query for Bing / أدخل استعلام البحث على بينغ:")
            if search_term:
                webbrowser.open(f"https://www.bing.com/search?q={search_term}")
                speak(f"Here are the results for {search_term} on Bing. / هذه هي النتائج لـ {search_term} على بينغ.")
            else:
                speak("No search query provided. / لم يتم تقديم استعلام للبحث.")

    elif "search duckduckgo" in query_lower or "ابحث في داك داك جو" in query_lower:
        speak("What should I search on DuckDuckGo? / ماذا تريد أن أبحث في DuckDuckGo؟")
        term = query_lower.replace("search duckduckgo", "").replace("ابحث في داك داك جو", "").strip()
        if term:
            webbrowser.open(f"https://duckduckgo.com/?q={term}")
            speak(f"Here are the results for {term} on DuckDuckGo. / هذه هي النتائج لـ {term} على DuckDuckGo.")
        else:
            search_term = simpledialog.askstring("DuckDuckGo Search", "Enter search query for DuckDuckGo / أدخل استعلام البحث على DuckDuckGo:")
            if search_term:
                webbrowser.open(f"https://duckduckgo.com/?q={search_term}")
                speak(f"Here are the results for {search_term} on DuckDuckGo. / هذه هي النتائج لـ {search_term} على DuckDuckGo.")
            else:
                speak("No search query provided. / لم يتم تقديم استعلام للبحث.")

    elif "open news" in query_lower or "افتح الأخبار" in query_lower:
        webbrowser.open("https://news.google.com/")
        speak("Opening Google News. / جاري فتح أخبار جوجل.")

    elif "open weather" in query_lower or "افتح الطقس" in query_lower:
        webbrowser.open("https://www.weather.com/")
        speak("Opening Weather Website. / جاري فتح موقع الطقس.")

    elif "open stackoverflow" in query_lower or "افتح ستاك أوفرفلو" in query_lower:
        webbrowser.open("https://stackoverflow.com/")
        speak("Opening StackOverflow. / جاري فتح ستاك أوفرفلو.")

    # --- أوامر الأدوات والحسابات ---
    elif "translate" in query_lower or "ترجم" in query_lower:
        text = simpledialog.askstring("Translate", "Enter text to translate / أدخل النص للترجمة:")
        if text:
            try:
                from deep_translator import GoogleTranslator
                def is_arabic(text_str):
                    for ch in text_str:
                        if '\u0600' <= ch <= '\u06FF':
                            return True
                    return False
                target_lang = 'en' if is_arabic(text) else 'ar'
                translation = GoogleTranslator(source='auto', target=target_lang).translate(text)
                speak(f"Translation: {translation}")
            except Exception as e:
                speak("Translation failed / فشل الترجمة: " + str(e))
                
    elif "joke" in query_lower or "نكتة" in query_lower:
        jokes = [
            "Why did the computer show up at work late? It had a hard drive!",
            "What do you call a computer that sings? A-Dell!",
            "ليه الكمبيوتر ما بيتعبش؟ عشان عنده معالج سريع!"
        ]
        speak(random.choice(jokes))
        
    elif "convert currency" in query_lower or "تحويل عملة" in query_lower:
        amount = simpledialog.askstring("Currency Converter", "Enter amount / أدخل المبلغ:")
        from_currency = simpledialog.askstring("Currency Converter", "Enter source currency code (e.g. USD) / أدخل رمز العملة المصدر (مثال: USD):")
        to_currency = simpledialog.askstring("Currency Converter", "Enter target currency code (e.g. EUR) / أدخل رمز العملة الهدف (مثال: EUR):")
        if amount and from_currency and to_currency:
            try:
                url = f"https://api.exchangerate-api.com/v4/latest/{from_currency.upper()}"
                response = requests.get(url)
                if response.status_code != 200:
                    raise Exception("API request failed with status " + str(response.status_code))
                data = response.json()
                rate = data["rates"].get(to_currency.upper())
                if rate:
                    converted = float(amount) * rate
                    speak(f"{amount} {from_currency.upper()} is equal to {converted} {to_currency.upper()}")
                else:
                    speak("Currency conversion rate not found / لم يتم العثور على سعر التحويل.")
            except Exception as e:
                speak("Currency conversion failed / فشل تحويل العملة: " + str(e))
                
    elif "open spotify" in query_lower or "افتح سبوتيفاي" in query_lower:
        if platform.system() == 'Windows':
            spotify_path = r"C:\Users\{username}\AppData\Roaming\Spotify\Spotify.exe"  # حدث المسار حسب الحاجة
            if os.path.exists(spotify_path):
                os.startfile(spotify_path)
                speak("Opening Spotify. / جاري فتح سبوتيفاي.")
            else:
                speak("Spotify not found. / لم يتم العثور على سبوتيفاي.")
        elif platform.system() == 'Darwin':
            os.system("open -a Spotify")
            speak("Opening Spotify. / جاري فتح سبوتيفاي.")
        else:
            speak("Open Spotify command is not supported on this system. / هذا الأمر غير مدعوم على هذا النظام.")
            
    elif "set alarm" in query_lower or "alarm" in query_lower:
        alarm_time = simpledialog.askstring("Set Alarm", "Enter alarm time in HH:MM (24-hour format):")
        alarm_msg = simpledialog.askstring("Set Alarm", "Enter alarm message:")
        if alarm_time:
            try:
                now = datetime.datetime.now()
                alarm_dt = datetime.datetime.strptime(alarm_time, "%H:%M").replace(year=now.year, month=now.month, day=now.day)
                if alarm_dt < now:
                    alarm_dt += datetime.timedelta(days=1)
                wait_time = (alarm_dt - now).total_seconds()
                speak(f"Alarm set for {alarm_time}.")
                def alarm_thread():
                    time.sleep(wait_time)
                    speak(f"Alarm: {alarm_msg}" if alarm_msg else "Alarm ringing!")
                threading.Thread(target=alarm_thread, daemon=True).start()
            except Exception as e:
                speak("Failed to set alarm: " + str(e))
                
    elif "define" in query_lower:
        word = simpledialog.askstring("Define", "Enter word to define:")
        if word:
            try:
                url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
                response = requests.get(url)
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list) and data:
                        meanings = data[0].get("meanings", [])
                        if meanings:
                            definitions = meanings[0].get("definitions", [])
                            if definitions:
                                definition = definitions[0].get("definition", "No definition found.")
                                speak(f"{word}: {definition}")
                            else:
                                speak("No definition found.")
                        else:
                            speak("No meaning found.")
                    else:
                        speak("Word not found.")
                else:
                    speak("Definition request failed.")
            except Exception as e:
                speak("Error fetching definition: " + str(e))
                
    elif "convert temperature" in query_lower:
        option = simpledialog.askstring("Temperature Conversion", "Type 'C to F' or 'F to C':")
        temp = simpledialog.askstring("Temperature Conversion", "Enter the temperature value:")
        if option and temp:
            try:
                temp_val = float(temp)
                if option.lower() == "c to f":
                    result = (temp_val * 9/5) + 32
                    speak(f"{temp_val}°C is {result}°F")
                elif option.lower() == "f to c":
                    result = (temp_val - 32) * 5/9
                    speak(f"{temp_val}°F is {result}°C")
                else:
                    speak("Invalid conversion option.")
            except Exception as e:
                speak("Temperature conversion error: " + str(e))
                
    elif "what day" in query_lower:
        day = datetime.datetime.now().strftime("%A")
        speak(f"Today is {day}")
        
    elif "read pdf" in query_lower:
        file_path = filedialog.askopenfilename(title="Select PDF File", filetypes=[("PDF Files", "*.pdf")])
        if file_path and os.path.exists(file_path):
            try:
                import PyPDF2
                with open(file_path, "rb") as pdf_file:
                    reader = PyPDF2.PdfReader(pdf_file)
                    text_content = ""
                    for page in reader.pages:
                        text_content += page.extract_text() or ""
                    if text_content:
                        speak("Reading PDF content: " + text_content[:500] + " ...")
                    else:
                        speak("No text found in PDF.")
            except Exception as e:
                speak("Failed to read PDF: " + str(e))
                
    elif "tell me a fact" in query_lower or "fact" in query_lower:
        try:
            fact_response = requests.get("https://uselessfacts.jsph.pl/random.json?language=en")
            if fact_response.status_code == 200:
                fact_data = fact_response.json()
                fact = fact_data.get("text", "No fact found.")
                speak("Here's a fact: " + fact)
            else:
                speak("Failed to retrieve a fact.")
        except Exception as e:
            speak("Error fetching fact: " + str(e))
            
    elif "open chrome" in query_lower or "افتح كروم" in query_lower:
        if platform.system() == 'Windows':
            chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            if os.path.exists(chrome_path):
                os.startfile(chrome_path)
                speak("Opening Google Chrome. / جاري فتح كروم.")
            else:
                speak("Google Chrome not found.")
        elif platform.system() == 'Darwin':
            os.system("open -a 'Google Chrome'")
            speak("Opening Google Chrome. / جاري فتح كروم.")
        else:
            os.system("google-chrome")
            speak("Opening Google Chrome. / جاري فتح كروم.")
            
    elif "open vscode" in query_lower or "افتح في اس كود" in query_lower:
        if platform.system() == 'Windows':
            code_path = r"C:\Users\{username}\AppData\Local\Programs\Microsoft VS Code\Code.exe"  # حدث المسار حسب الحاجة
            if os.path.exists(code_path):
                os.startfile(code_path)
                speak("Opening Visual Studio Code. / جاري فتح في اس كود.")
            else:
                speak("VS Code not found.")
        elif platform.system() == 'Darwin':
            os.system("open -a 'Visual Studio Code'")
            speak("Opening Visual Studio Code. / جاري فتح في اس كود.")
        else:
            os.system("code")
            speak("Opening Visual Studio Code. / جاري فتح في اس كود.")

    # --- أوامر إضافية للوصول إلى حوالي 25 أمرًا ---
    elif "open word" in query_lower or "افتح وورد" in query_lower:
        if platform.system() == 'Windows':
            try:
                os.startfile("winword.exe")
                speak("Opening Microsoft Word. / جاري فتح وورد.")
            except Exception:
                speak("Failed to open Microsoft Word. / فشل في فتح وورد.")
        else:
            speak("Open Word command is only supported on Windows. / هذا الأمر مدعوم فقط على ويندوز.")

    elif "open excel" in query_lower or "افتح إكسل" in query_lower:
        if platform.system() == 'Windows':
            try:
                os.startfile("excel.exe")
                speak("Opening Microsoft Excel. / جاري فتح إكسل.")
            except Exception:
                speak("Failed to open Microsoft Excel. / فشل في فتح إكسل.")
        else:
            speak("Open Excel command is only supported on Windows. / هذا الأمر مدعوم فقط على ويندوز.")

    elif "open powerpoint" in query_lower or "افتح باوربوينت" in query_lower:
        if platform.system() == 'Windows':
            try:
                os.startfile("powerpnt.exe")
                speak("Opening Microsoft PowerPoint. / جاري فتح باوربوينت.")
            except Exception:
                speak("Failed to open Microsoft PowerPoint. / فشل في فتح باوربوينت.")
        else:
            speak("Open PowerPoint command is only supported on Windows. / هذا الأمر مدعوم فقط على ويندوز.")

    elif "calculate" in query_lower:
        expression = simpledialog.askstring("Calculate", "Enter math expression (e.g. 2+2 or sqrt(16)):")
        if expression:
            try:
                allowed_names = {"__builtins__": None}
                allowed_names.update(math.__dict__)
                result = eval(expression, allowed_names)
                speak(f"The result is {result}")
            except Exception as e:
                speak("Calculation error: " + str(e))

    elif "open paint" in query_lower or "افتح الرسام" in query_lower:
        if platform.system() == 'Windows':
            try:
                os.startfile("mspaint.exe")
                speak("Opening Paint. / جاري فتح الرسام.")
            except Exception:
                speak("Failed to open Paint. / فشل في فتح الرسام.")
        else:
            speak("Open Paint command is only supported on Windows. / هذا الأمر مدعوم فقط على ويندوز.")

    elif "open snipping tool" in query_lower or "افتح أداة القص" in query_lower:
        if platform.system() == 'Windows':
            try:
                os.startfile("snippingtool.exe")
                speak("Opening Snipping Tool. / جاري فتح أداة القص.")
            except Exception:
                speak("Failed to open Snipping Tool. / فشل في فتح أداة القص.")
        else:
            speak("Snipping Tool command is only supported on Windows. / هذا الأمر مدعوم فقط على ويندوز.")

    elif "open disk cleanup" in query_lower or "افتح تنظيف القرص" in query_lower:
        if platform.system() == 'Windows':
            try:
                os.startfile("cleanmgr.exe")
                speak("Opening Disk Cleanup. / جاري فتح تنظيف القرص.")
            except Exception:
                speak("Failed to open Disk Cleanup. / فشل في فتح تنظيف القرص.")
        else:
            speak("Disk Cleanup command is only supported on Windows. / هذا الأمر مدعوم فقط على ويندوز.")

    elif "open system settings" in query_lower or "افتح إعدادات النظام" in query_lower:
        if platform.system() == 'Windows':
            try:
                os.system("start ms-settings:")
                speak("Opening System Settings. / جاري فتح إعدادات النظام.")
            except Exception:
                speak("Failed to open System Settings. / فشل في فتح إعدادات النظام.")
        else:
            speak("System Settings command is only supported on Windows. / هذا الأمر مدعوم فقط على ويندوز.")

    elif "open notepad++" in query_lower or "افتح نوتباد بلس بلس" in query_lower:
        if platform.system() == 'Windows':
            notepad_pp = r"C:\Program Files\Notepad++\notepad++.exe"  # حدث المسار حسب الحاجة
            if os.path.exists(notepad_pp):
                os.startfile(notepad_pp)
                speak("Opening Notepad++. / جاري فتح Notepad++.")
            else:
                speak("Notepad++ not found. / لم يتم العثور على Notepad++.")
        else:
            speak("Notepad++ command is only supported on Windows. / هذا الأمر مدعوم فقط على ويندوز.")

    elif "check disk usage" in query_lower or "فحص مساحة القرص" in query_lower:
        if platform.system() == 'Windows':
            try:
                import subprocess
                result = subprocess.check_output("wmic logicaldisk get caption,freespace,size", shell=True)
                speak("Disk Usage Info:\n" + result.decode())
            except Exception as e:
                speak("Failed to check disk usage. / فشل في فحص مساحة القرص: " + str(e))
        else:
            speak("Disk usage command is only supported on Windows. / هذا الأمر مدعوم فقط على ويندوز.")

    # --- أوامر المساعد الإضافية (التحيات والنهاية) ---
    elif "help" in query_lower:
        help_text = """Available commands include:
- System Commands: Open Notepad, Open CMD, Close Notepad, Close CMD, Open Calculator, Open File Explorer, System Info, IP Address, Open Task Manager, Log off, Open Control Panel, Hibernate, Lock Computer, Restart, Shutdown.
- Media Commands: Play Music, Play Video, Pause Video, Resume Video, Screenshot, Play Radio, Open Movies, Open Podcasts, Open Images, Record Audio, Stop Audio Recording, Open VLC, Play Streaming, Increase Volume, Decrease Volume, Open Sound Settings, Play Online Video.
- Web/Search Commands: Search Google, Search YouTube, Wikipedia, Open YouTube, Open Instagram, Open Facebook, Open Twitter, Open Maps, Open Reddit, Open LinkedIn, Search Bing, Search DuckDuckGo, Open News, Open Weather, Open StackOverflow.
- Tools/Calculator Commands: Translate, Joke, Convert Currency, Open Spotify, Set Alarm, Define, Convert Temperature, What Day, Read PDF, Tell Me a Fact, Open Chrome, Open VS Code, Open Word, Open Excel, Open PowerPoint, Calculate, Open Paint, Open Snipping Tool, Open Disk Cleanup, Open System Settings, Open Notepad++, Check Disk Usage.
"""
        speak(help_text)
    elif any(x in query_lower for x in ['nothing', 'abort', 'stop', 'exit']) or "خروج" in query_lower:
        speak("Okay. Bye Sir, have a good day. / حسناً، وداعاً.")
        root.quit()
    elif "hello" in query_lower or "مرحبا" in query_lower:
        speak("Hello Sir / مرحباً")
    elif "bye" in query_lower or "مع السلامة" in query_lower or "وداعا" in query_lower:
        speak("Bye Sir, have a good day. / وداعاً.")
        root.quit()
    elif "what's up" in query_lower or "how are you" in query_lower or "كيف حالك" in query_lower:
        stMsgs = ['Just doing my thing!', 'I am fine!', 'Nice!', 'I am full of energy!']
        speak(random.choice(stMsgs))
    else:
        speak("Sorry, I don't understand that command. / عذراً، لم أفهم الأمر.")

# ============================ واجهة المستخدم ModernUI ============================
class ModernUI:
    def __init__(self, root):
        self.root = root
        # تعريف ألوان الواجهة
        self.colors = {
            'bg': '#2B2B2B',
            'toolbar': '#333333',
            'tab_bg': '#424242',
            'tab_fg': '#FFFFFF',
            'tab_active_bg': '#5A5A5A',
            'btn_bg': '#4CAF50',
            'btn_hover': '#455A64',
            'btn_fg': '#FFFFFF'
        }
        self.setup_ui()

    def setup_ui(self):
        self.root.title("JARVIS AI Assistant")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        self.root.configure(bg=self.colors['bg'])

        # شريط الأدوات العلوي
        self.toolbar = Frame(self.root, bg=self.colors['toolbar'], height=40)
        self.toolbar.pack(fill='x', padx=5, pady=5)

        self.search_bar = tkEntry(self.toolbar, font=('Arial', 12), width=40)
        self.search_bar.pack(side='left', padx=10, pady=5)
        self.search_bar.bind('<Return>', self.quick_search)

        control_buttons = [
            ('⏹️ Exit', self.root.quit),
            ('🔍 Search', self.quick_search),
            ('🌓 Toggle Theme', self.toggle_theme)
        ]
        for text, cmd in control_buttons:
            tkButton(self.toolbar, text=text, command=cmd, bg=self.colors['btn_bg'], fg=self.colors['btn_fg'],
                     font=("Arial", 11), relief='flat', bd=0, padx=8, pady=8).pack(side='right', padx=5)

        # منطقة عرض النتائج
        self.result_frame = Frame(self.root, bg=self.colors['bg'])
        self.result_frame.pack(fill='both', expand=True, padx=10, pady=10)
        global text_results
        text_results = Text(self.result_frame, font=("Arial", 12), bg="#252526", fg="#d4d4d4", wrap='word')
        text_results.pack(side='left', fill='both', expand=True)
        scrollbar = Scrollbar(self.result_frame, command=text_results.yview)
        scrollbar.pack(side='right', fill='y')
        text_results.config(yscrollcommand=scrollbar.set)

        # إنشاء Notebook للتبويبات
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        self.tabs = {
            'system': self.create_tab("⚙️ System", self.system_commands()),
            'media': self.create_tab("🎵 Media", self.media_commands()),
            'web': self.create_tab("🌐 Web", self.web_commands()),
            'tools': self.create_tab("🛠️ Tools", self.tools_commands())
        }

    def create_tab(self, name, content):
        tab = Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(tab, text=name)
        # وضع محتوى التبويب داخل الإطار المُنشأ
        content.pack(in_=tab, fill='both', expand=True, padx=10, pady=10)
        return tab

    def system_commands(self):
        frame = Frame(self.root, bg=self.colors['bg'])
        commands = [
            ('📝 Notepad', 'open notepad', '#4CAF50'),
            ('💻 CMD', 'open cmd', '#2196F3'),
            ('📁 Explorer', 'open file explorer', '#9C27B0'),
            ('🔒 Lock', 'lock computer', '#FF5722'),
            ('⚡ Restart', 'restart', '#FFC107'),
            ('⏻ Shutdown', 'shutdown', '#F44336')
        ]
        for idx, (text, cmd, color) in enumerate(commands):
            tkButton(frame, text=text, command=lambda c=cmd: process_query(c),
                     bg=color, fg="white", font=("Arial", 11), relief='flat', bd=0, padx=8, pady=8).grid(
                         row=idx // 2, column=idx % 2, padx=10, pady=10, sticky='nsew')
        return frame

    def media_commands(self):
        frame = Frame(self.root, bg=self.colors['bg'])
        media_commands = [
            ('🎵 Play Music', 'play music', '#E91E63'),
            ('🎥 Play Video', 'play video', '#673AB7'),
            ('📸 Screenshot', 'screenshot', '#009688'),
            ('📻 Radio', 'play radio', '#FF9800')
        ]
        for idx, (text, cmd, color) in enumerate(media_commands):
            tkButton(frame, text=text, command=lambda c=cmd: process_query(c),
                     bg=color, fg="white", font=("Arial", 11), relief='flat', bd=0, padx=8, pady=8).grid(
                         row=idx // 2, column=idx % 2, padx=10, pady=10, sticky='nsew')
        return frame

    def web_commands(self):
        frame = Frame(self.root, bg=self.colors['bg'])
        web_commands = [
            ('🌐 Google', 'search google', '#03A9F4'),
            ('📺 YouTube', 'open youtube', '#FF0000'),
            ('📚 Wikipedia', 'wikipedia', '#008CBA'),
            ('🗺️ Maps', 'open maps', '#4CAF50')
        ]
        for idx, (text, cmd, color) in enumerate(web_commands):
            tkButton(frame, text=text, command=lambda c=cmd: process_query(c),
                     bg=color, fg="white", font=("Arial", 11), relief='flat', bd=0, padx=8, pady=8).grid(
                         row=idx // 2, column=idx % 2, padx=10, pady=10, sticky='nsew')
        return frame

    def tools_commands(self):
        frame = Frame(self.root, bg=self.colors['bg'])
        tools_commands = [
            ('🖩 Calculator', 'open calculator', '#00BCD4'),
            ('📂 Read File', 'read file', '#795548'),
            ('💱 Convert Currency', 'convert currency', '#8BC34A'),
            ('⏰ Set Alarm', 'set alarm', '#FF9800'),
            ('🔍 Define', 'define', '#E91E63'),
            ('🌡️ Temp Converter', 'convert temperature', '#FFC107')
        ]
        for idx, (text, cmd, color) in enumerate(tools_commands):
            tkButton(frame, text=text, command=lambda c=cmd: process_query(c),
                     bg=color, fg="white", font=("Arial", 11), relief='flat', bd=0, padx=8, pady=8).grid(
                         row=idx // 2, column=idx % 2, padx=10, pady=10, sticky='nsew')
        return frame

    def quick_search(self, event=None):
        query = self.search_bar.get()
        if query.strip() != "":
            process_query(query)
            self.search_bar.delete(0, tk.END)

    def toggle_theme(self):
        if self.colors['bg'] == '#2B2B2B':
            self.colors = {
                'bg': '#FFFFFF',
                'toolbar': '#E0E0E0',
                'tab_bg': '#F5F5F5',
                'tab_fg': '#000000',
                'tab_active_bg': '#E0E0E0',
                'btn_bg': '#00796B',
                'btn_hover': '#004D40',
                'btn_fg': '#FFFFFF'
            }
        else:
            self.colors = {
                'bg': '#2B2B2B',
                'toolbar': '#333333',
                'tab_bg': '#424242',
                'tab_fg': '#FFFFFF',
                'tab_active_bg': '#5A5A5A',
                'btn_bg': '#4CAF50',
                'btn_hover': '#455A64',
                'btn_fg': '#FFFFFF'
            }
        self.refresh_ui()

    def refresh_ui(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.setup_ui()

# ============================ نقطة دخول التطبيق ============================
def main():
    global root
    root = Tk()
    app = ModernUI(root)
    wish()
    root.mainloop()

if __name__ == "__main__":
    main()
