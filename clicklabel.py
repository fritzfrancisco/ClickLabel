import cv2
import os
import tkinter as tk
from tkinter import filedialog, simpledialog
import pandas as pd
from PIL import Image, ImageTk
import time
import argparse

class VideoPlayer:
    def __init__(self, root, video_path, frame_rate=60, clicks_required=1, click_delay=1):
        self.cap = cv2.VideoCapture(video_path)
        self.filename = os.path.basename(video_path)
        self.root = root
        self.frame_index = 0
        self.playing = False
        self.direction = 1  # 1 for forward, -1 for backward
        self.saved_clicks = []  # List to store clicked positions: [(frame, x, y)]
        self.labels = {}  # Dictionary to store labels: {(frame, x, y): label}
        self.frame_rate = frame_rate  # Frame skip rate
        self.clicks_required = clicks_required  # Number of clicks required to advance the frame
        self.clicks_in_current_frame = 0  # Track number of clicks for the current frame
        self.cursor_x, self.cursor_y = 0, 0
        self.last_click_time = 0  # Time of the last click
        self.click_delay = click_delay  # Minimum time between clicks in seconds
        self.double_click_detected = False  # Flag to track double-clicks

        # Get screen size and resize video display accordingly
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight() - 200  # Leave space for controls

        video_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        video_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        scale_factor = min(screen_width / video_width, screen_height / video_height)
        self.display_width = int(video_width * scale_factor)
        self.display_height = int(video_height * scale_factor)

        # Setup canvas for video display
        self.canvas = tk.Canvas(root, width=self.display_width, height=self.display_height)
        self.canvas.pack()

        # Bind mouse and key events
        self.canvas.bind("<Button-1>", self.left_click_start)
        self.canvas.bind("<ButtonRelease-1>", self.left_click_stop)
        self.canvas.bind("<Button-3>", self.right_click_start)
        self.canvas.bind("<ButtonRelease-3>", self.right_click_stop)
        self.canvas.bind("<Double-Button-1>", self.add_label)  # Double-click to add label
        self.canvas.bind("<Motion>", self.update_cursor_location)
        self.root.bind("q", lambda e: self.close_application())
        self.root.bind("n", lambda e: self.manual_advance())  # Advance manually

    def manual_advance(self):
        self.frame_index += self.frame_rate
        self.clicks_in_current_frame = 0

    def play_video(self):
        if self.cap.isOpened():
            # Set the current frame position
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_index)
            ret, frame = self.cap.read()

            if ret:
                # Resize frame to fit display size once
                frame_resized = cv2.resize(frame, (self.display_width, self.display_height))
                frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)  # Convert to RGB only once

                img = Image.fromarray(frame_rgb)
                imgtk = ImageTk.PhotoImage(image=img)

                # Update the canvas image only when necessary
                self.canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
                self.canvas.image = imgtk

                # Draw labels and clicks
                self.draw_labels()
                self.draw_saved_clicks()

                # Display the current frame number
                self.canvas.create_text(
                    10, 10, anchor=tk.NW, text=f"Frame: {self.frame_index}", fill="blue", font=("Helvetica", 16, "bold")
                )

            if self.clicks_in_current_frame >= self.clicks_required:
                if self.direction == 1:
                    self.frame_index += self.frame_rate
                elif self.direction == -1:
                    self.frame_index -= self.frame_rate
                self.clicks_in_current_frame = 0
                if self.frame_index < 0:
                    self.frame_index = 0
            elif not ret:
                self.playing = False

        self.root.after(10, self.play_video)  # Reduced the delay for better responsiveness

    def save_cursor_location_continuous(self, event):
        current_time = time.time()
        # Skip processing if the delay threshold is not met
        if current_time - self.last_click_time < self.click_delay:
            return

        self.saved_clicks.append((self.frame_index, event.x, event.y))
        self.clicks_in_current_frame += 1
        self.last_click_time = current_time

        # No need for repeated 'after' calls inside this method
        if self.playing and self.direction == 1:
            self.save_cursor_location_continuous(event)  # Remove unnecessary `after` calls.

    def start(self):
        self.playing = True

    def pause(self):
        self.playing = False

    def left_click_start(self, event):
        self.double_click_detected = False
        self.root.after(250, lambda: self.handle_single_click(event))  # Delay to check for double-click

    def handle_single_click(self, event):
        if not self.double_click_detected:
            self.direction = 1
            self.start()
            self.save_cursor_location_continuous(event)

    def left_click_stop(self, event):
        self.pause()

    def right_click_stop(self, event):
        self.pause()  # Stop playback
        
    def right_click_start(self, event):
        # Start reverse playback and remove clicks for the current frame
        self.direction = -1  # Reverse direction
        self.start()  # Start playback in reverse
        self.remove_clicks_continuous(event)  # Begin the continuous removal process

    def remove_clicks_continuous(self, event=None):
        current_time = time.time()
        if current_time - self.last_click_time < self.click_delay:
            return  # Skip if click delay threshold not met

        if self.direction == -1:
            self.saved_clicks = [(frame, x, y) for frame, x, y in self.saved_clicks if frame != self.frame_index]
            self.clicks_in_current_frame += 1
            self.last_click_time = current_time

            self.frame_index -= self.frame_rate
            self.clicks_in_current_frame = 0
            if self.frame_index < 0:
                self.frame_index = 0

            # Render the updated frame for reverse playback
            if self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_index)
                ret, frame = self.cap.read()
                if ret:
                    frame_resized = cv2.resize(frame, (self.display_width, self.display_height))
                    frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)

                    img = Image.fromarray(frame_rgb)
                    imgtk = ImageTk.PhotoImage(image=img)
                    self.canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
                    self.canvas.image = imgtk

                    # Draw labels and clicks
                    self.draw_labels()
                    self.draw_saved_clicks()

            if self.playing and self.direction == -1:
                self.root.after(30, self.remove_clicks_continuous)

    def update_cursor_location(self, event):
        self.cursor_x, self.cursor_y = event.x, event.y

    def add_label(self, event):
        self.double_click_detected = True
        label = simpledialog.askstring("Input", "Enter label:", parent=self.root)
        if label:
            click_position = (self.frame_index, event.x, event.y)
            self.labels[click_position] = label

    def draw_labels(self):
        for (frame, x, y), label in self.labels.items():
            if frame == self.frame_index:
                self.canvas.create_text(x, y, text=label, fill="red", font=("Helvetica", 12))

    def draw_saved_clicks(self):
        for frame, x, y in self.saved_clicks:
            if frame == self.frame_index:
                self.canvas.create_oval(x - 5, y - 5, x + 5, y + 5, fill="blue", outline="white")

    def save_clicks_to_csv(self):
        # Save labeled positions to a CSV
        labeled_data = [(self.filename, frame, x, y, label) for (frame, x, y), label in self.labels.items()]
        click_data = [(self.filename, frame, x, y, "") for frame, x, y in self.saved_clicks]

        # Merge both data sets
        combined_data = labeled_data + click_data
        df = pd.DataFrame(combined_data, columns=['VideoFile', 'Frame', 'X', 'Y', 'Label'])
        df.to_csv("saved_clicks.csv", index=False)
        print("Saved clicks and labels saved to saved_clicks.csv")

    def set_frame_rate(self, new_rate):
        if new_rate > 0:
            self.frame_rate = new_rate
            print(f"Frame rate updated to every {new_rate}-th frame.")
        else:
            print("Frame rate must be greater than 0.")

    def set_clicks_required(self, new_clicks_required):
        self.clicks_required = new_clicks_required
        print(f"Clicks required to advance frame updated to {self.clicks_required}.")

    def close_application(self):
        self.root.destroy()

def setup_controls(root, video_player):
    control_frame = tk.Frame(root)
    control_frame.pack(fill=tk.X)

    play_button = tk.Button(control_frame, text="Play", command=video_player.start)
    play_button.pack(side="left")

    pause_button = tk.Button(control_frame, text="Pause", command=video_player.pause)
    pause_button.pack(side="left")

    close_button = tk.Button(control_frame, text="Close", command=video_player.close_application)
    close_button.pack(side="left")

    save_button = tk.Button(root, text="Save Clicks", command=video_player.save_clicks_to_csv)
    save_button.pack(side="left")

    frame_rate_slider = tk.Scale(control_frame, from_=1, to=60, orient="horizontal", label="Frame Rate (n-th frame)",
                                 command=lambda val: video_player.set_frame_rate(int(val)))
    frame_rate_slider.set(video_player.frame_rate)
    frame_rate_slider.pack(side="left")

    clicks_required_slider = tk.Scale(control_frame, from_=1, to=10, orient="horizontal", label="Clicks to Advance",
                                      command=lambda val: video_player.set_clicks_required(int(val)))
    clicks_required_slider.set(video_player.clicks_required)
    clicks_required_slider.pack(side="left")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Video Annotation Tool")
    parser.add_argument('-v','--video', type=str, help='Path to the video file')
    args = parser.parse_args()
    root = tk.Tk()

    video_path = args.video
    if not video_path:
        video_path = filedialog.askopenfilename(title="Select a Video", filetypes=("MP4 Files", "*.mp4"))
        if not video_path:
            exit()

    video_player = VideoPlayer(root, video_path)
    setup_controls(root, video_player)
    video_player.play_video()
    root.mainloop()
