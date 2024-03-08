import customtkinter as ctk
from pytube import YouTube, Playlist
import threading
from tkinter import filedialog
import os
from PIL import Image
import requests
from io import BytesIO

ctk.set_appearance_mode("System")

def on_progress(stream, chunk, bytes_remaining):
    total_size = stream.filesize
    bytes_dload = total_size - bytes_remaining
    progress_percent = int(bytes_dload / total_size * 100)
    
    app.text_box.insert("end", " >>>")
    app.download_label.configure(text=f"{progress_percent}%")
    app.progress_bar.set(progress_percent / 100)
    app.update_idletasks()

class YouTubeDownloaderApp(ctk.CTk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("YT Playlist Downloader")
        self.geometry("640x400")
        self.grid_columnconfigure((0,1,2), weight=1)
        self.grid_rowconfigure(4, weight=1)

        # Create an entry field for the playlist link
        self.link_entry = ctk.CTkEntry(self, placeholder_text="    ... < Youtube link > ...")
        self.link_entry.grid(row=0, column=1, padx=10, pady=15, sticky="ew", columnspan=2)
        
        self.input_label = ctk.CTkLabel(self, text="Paste Youtube Link here  >>>", font=("",15))
        self.input_label.grid(row=0, column=0, sticky="ew", columnspan=1)
        
        # Create label to display thumbnail
        self.center_image = ctk.CTkLabel(self, text="", image=None, corner_radius=25)
        self.center_image.grid(row=1, column=1, rowspan=2, sticky="nsew")

        # Create a download button for playlist download video
        self.download_button_video = ctk.CTkButton(self, height=35, text="Download Playlist (Video)", font=("", 15),command=self.download_playlist_video)
        self.download_button_video.grid(row=1, column=0, padx=15, pady=5, sticky="ew")

        # Create a download button for audio
        self.download_button_audio = ctk.CTkButton(self, height=35, text="Download Playlist (Audio)", font=("", 15), command=self.download_playlist_audio)
        self.download_button_audio.grid(row=2, column=0, padx=15, pady=5, sticky="ew")
        
        # Create a button for single video download
        self.download_button_single_video = ctk.CTkButton(self, height=35, text="Download Video", font=("", 15), command=self.download_single_video)
        self.download_button_single_video.grid(row=1, column=2, padx=15, pady=5, sticky="ew")

        # Create a button for single audio download
        self.download_button_single_audio = ctk.CTkButton(self, height=35, text="Download Audio", font=("", 15), command=self.download_single_audio)
        self.download_button_single_audio.grid(row=2, column=2, padx=15, pady=5, sticky="ew")
  
        # Create a progress bar
        self.progress_bar = ctk.CTkProgressBar(self, mode="determinate", progress_color="lightgreen")
        self.progress_bar.grid(row=3, column=0, columnspan=3, padx=50, pady=10, sticky="ew")
        self.progress_bar.set(0)
        # Progress percentage counter
        self.download_label = ctk.CTkLabel(self, text="0%", font=("",15), text_color="green")
        self.download_label.grid(row=3, column=2, padx=25, sticky="e")

        # Create a text box for displaying downloaded file names
        self.text_box = ctk.CTkTextbox(self, width=400, height=200, state="normal")
        self.text_box.grid(row=4, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
        
        # Create a button to clear the text box
        self.clear_text_button = ctk.CTkButton(self, text="Clear Text Box", command=self.clear_text_box)
        self.clear_text_button.grid(row=6, column=1, padx=20, pady=10, sticky="ew")
        
        # Create a browse button for selecting the download path
        self.browse_button = ctk.CTkButton(self ,text="Download path", command=self.browse_path)
        self.browse_button.grid(row=6, column=0, padx=20, pady=10, sticky="ew")

        # Create a cancel button
        self.cancel_button = ctk.CTkButton(self, text="CANCEL", font=("",15),text_color="black",fg_color="gray", hover_color="red", command=self.cancel_download, state="disabled")
        self.cancel_button.grid(row=6, column=2, padx=20, pady=10, sticky="ew")

        # Initialize the download status, cancel flag, and download path
        self.is_downloading = False
        self.cancel_flag = False
        self.download_path = os.path.join(os.path.expanduser("~"), "Downloads")
    
    def browse_path(self):
        # Open a file dialog to select the download path
        selected_path = filedialog.askdirectory()
        if selected_path:
            self.download_path = selected_path
       
    def cancel_download(self):
        if self.is_downloading:
            self.cancel_flag = True
            self.text_box.insert("end", "\n... Cancelling all downloads ...\n")
            self.text_box.see("end")
            # Disable the cancel button during the cancellation
            self.cancel_button.configure(state="disabled")
        else:
            self.text_box.insert("end", "\nError: No download in progress.\n")
            self.text_box.see("end")

    def download_single_video(self):
        if not self.link_entry.get():
            self.text_box.insert("end", "\nEnter a video link.\n")
            self.text_box.see("end")
            return

        threading.Thread(target=self.download_single, args=("video",)).start()

    def download_single_audio(self):
        if not self.link_entry.get():
            self.text_box.insert("end", "\nEnter an audio link.\n")
            self.text_box.see("end")
            return

        threading.Thread(target=self.download_single, args=("audio",)).start()

    def download_single(self, mode="video"):
        app.download_label.configure(text=f"Downloading ({mode.capitalize()})")
        self.is_downloading = True  # Set download status to True
        self.cancel_flag = False  # Reset cancel flag
        # Enable the cancel button when a download starts
        self.cancel_button.configure(state="normal")

        try:
            p_link = self.link_entry.get()
        except Exception as e:
            self.text_box.insert("end", "Please enter valid link!")

        try:
            yt_video = YouTube(p_link)
        except Exception as e:
            self.text_box.insert("end", f"\nError: {str(e)}\n")
            self.text_box.see("end")
            self.is_downloading = False  # Reset download status
            return
        
        # Display thumbnail
        thumbnail_url = yt_video.thumbnail_url
        thumbnail_image = self.load_thumbnail(thumbnail_url)
        self.center_image.configure(image=thumbnail_image)
        
        self.text_box.insert("end", f"Files left to download: 1\n")
        app.progress_bar.set(0)
        yt_video.register_on_progress_callback(on_progress)

        try:
            if mode == "video":
                stream = yt_video.streams.get_highest_resolution()
            elif mode == "audio":
                stream = yt_video.streams.get_audio_only()
            else:
                raise ValueError("Invalid mode. Use 'video' or 'audio'.")
        except Exception as e:
            self.text_box.insert("end", f"\nError getting stream: {str(e)}\n")
            self.text_box.see("end")
            return

        # Modify the download path as needed
        download_path = self.download_path

        try:
            stream.download(download_path)
        except Exception as e:
            self.text_box.insert("end", f"\nError downloading: {str(e)}\n")
            self.text_box.see("end")

        if self.cancel_flag:
            # Stop the download process if the cancel button is pressed
            return

        # Display downloaded file name in the text box
        self.text_box.insert("end", f"\n~ {yt_video.title} ({mode.capitalize()}) downloaded successfully!\n")
        self.text_box.see("end")  # Scroll to the end

        # Reset the entry box to an empty state after download is completed
        self.link_entry.delete(0, "end")
        self.cancel_button.configure(state="disabled")

    def load_thumbnail(self, url):
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        thumbnail = ctk.CTkImage(img, size=(160,90))
        return thumbnail
    
    # The following method is for Playlist download
    def download_playlist_video(self):
        if not self.link_entry.get():
            self.text_box.insert("end", "\nEnter a Playlist link.\n")
            self.text_box.see("end")
            return
        
        threading.Thread(target=self.download_playlist, args=("video",)).start()

    def download_playlist_audio(self):
        if not self.link_entry.get():
            self.text_box.insert("end", "\nEnter a Playlist link.\n")
            self.text_box.see("end")
            return
        
        threading.Thread(target=self.download_playlist, args=("audio",)).start()

    def clear_text_box(self):
        # Clear the contents of the text box
        self.text_box.delete("1.0", "end")
        self.link_entry.delete(0, "end")
        self.center_image.configure(image=None)
        app.download_label.configure(text="0%")
        app.progress_bar.set(0)
        
        self.cancel_flag = False

    def download_playlist(self, mode="video"):
        app.download_label.configure(text=f"Downloading ({mode.capitalize()})")
        
        self.is_downloading = True  # Set download status to True
        self.cancel_flag = False  # Reset cancel flag
        # Enable the cancel button when a download starts
        self.cancel_button.configure(state="normal")
        
        try:
            p_link = self.link_entry.get()
        except Exception as e:
            self.text_box.insert("end", "Please enter valid Playlist link!")
            
        try:
            link = Playlist(p_link)
        except Exception as e:
            self.text_box.insert("end", f"\nError: {str(e)}\n")
            self.text_box.see("end")
            self.is_downloading = False  # Reset download status
            return
        try:
            num_videos = len(link.video_urls)
        except Exception as e:
            self.text_box.insert("end", "Please enter valid Playlist link!\n")

        for idx, video_url in enumerate(link.video_urls, start=1):
            if self.cancel_flag:
                # Stop the download process if the cancel button is pressed
                break

            try:
                yt_video = YouTube(video_url)
            except Exception as e:
                self.text_box.insert("end", f"\nError fetching video: {str(e)}\n")
                self.text_box.see("end")
                continue
            
            # Display thumbnail
            thumbnail_url = yt_video.thumbnail_url
            thumbnail_image = self.load_thumbnail(thumbnail_url)
            self.center_image.configure(image=thumbnail_image)

            self.text_box.insert("end", f"Files to download: {num_videos}\n")
            app.progress_bar.set(0)
            yt_video.register_on_progress_callback(on_progress)

            try:
                if mode == "video":
                    stream = yt_video.streams.get_highest_resolution()
                elif mode == "audio":
                    stream = yt_video.streams.get_audio_only()
                else:
                    raise ValueError("Invalid mode. Use 'video' or 'audio'.")
            except Exception as e:
                self.text_box.insert("end", f"\nError getting stream: {str(e)}\n")
                self.text_box.see("end")
                continue

            # Modify the download path as needed
            download_path = self.download_path

            try:
                stream.download(download_path)
            except Exception as e:
                self.text_box.insert("end", f"\nError downloading: {str(e)}\n")
                self.text_box.see("end")
                continue
            
            if self.cancel_flag:
                # Stop the download process if the cancel button is pressed
                break
            
            # Display downloaded file name in the text box
            self.text_box.insert("end", f"\n~ {yt_video.title} ({mode.capitalize()}) downloaded successfully!\n")
            self.text_box.see("end")  # Scroll to the end
            num_videos -= 1

        # Reset the entry box to an empty state after all downloads are completed
        self.link_entry.delete(0, "end")
        self.cancel_button.configure(state="disabled")
        
    def load_thumbnail(self, url):
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        thumbnail = ctk.CTkImage(img, size=(160,90))
        return thumbnail

if __name__ == "__main__":
    app = YouTubeDownloaderApp()
    app.mainloop()
