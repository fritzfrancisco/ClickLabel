import cv2
import os
import tkinter as tk
from tkinter import filedialog, simpledialog
import pandas as pd
from PIL import Image, ImageTk
import time

class VideoPlayer:
    def __init__(self, root, video_path, frame_rate=1, clicks_required=3, click_delay=0.3):
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

        # Setup canvas for video display
        self.canvas = tk.Canvas(root, width=int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)), 
                                height=int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
        self.canvas.pack()

        # Bind mouse and key events
        self.canvas.bind("<Button-1>", self.left_click_start)
        self.canvas.bind("<ButtonRelease-1>", self.left_click_stop)
        self.canvas.bind("<Button-3>", self.right_click_start)
        self.canvas.bind("<ButtonRelease-3>", self.right_click_stop)
        self.canvas.bind("<Double-Button-1>", self.add_label)  # Double-click to add label
        self.canvas.bind("<Motion>", self.update_cursor_location)
        self.root.bind("q", lambda e: self.close_application())

    def play_video(self):
        if self.cap.isOpened():
            # Set the current frame position
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_index)
            ret, frame = self.cap.read()

            if ret:
                # Convert frame to RGB and render on the canvas
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                imgtk = ImageTk.PhotoImage(image=img)

                # Update the canvas image
                self.canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
                self.canvas.image = imgtk

                # Draw labels and clicks
                self.draw_labels()
                self.draw_saved_clicks()

                # Display the current frame number
                self.canvas.create_text(
                    10, 10, anchor=tk.NW, text=f"Frame: {self.frame_index}", fill="blue", font=("Helvetica", 16, "bold")
                )

            # Advance or reverse frame based on click count
            if self.clicks_in_current_frame >= self.clicks_required:
                if self.direction == 1:  # Forward
                    self.frame_index += self.frame_rate
                elif self.direction == -1:  # Reverse
                    self.frame_index -= self.frame_rate
                self.clicks_in_current_frame = 0  # Reset click counter
                if self.frame_index < 0:
                    self.frame_index = 0
            elif not ret:
                # Stop playback if no more frames are available
                self.playing = False

        # Schedule the next frame update
        self.root.after(30, self.play_video)

    def start(self):
        self.playing = True

    def pause(self):
        self.playing = False

    def left_click_start(self, event):
        self.direction = 1  # Play forward
        self.start()
        self.save_cursor_location_continuous(event)

    def left_click_stop(self, event):
        self.pause()

    def save_cursor_location_continuous(self, event):
        current_time = time.time()
        # Check if enough time has passed since the last click
        if current_time - self.last_click_time < self.click_delay:
            return  # Skip if the time threshold has not been reached

        # Count the click
        self.saved_clicks.append((self.frame_index, event.x, event.y))
        print(f"Saved cursor location at frame {self.frame_index}, x: {event.x}, y: {event.y}")
        self.clicks_in_current_frame += 1  # Increment click count
        print(f"Clicks in current frame: {self.clicks_in_current_frame}")

        # Update last click time
        self.last_click_time = current_time

        if self.playing and self.direction == 1:
            self.root.after(30, self.save_cursor_location_continuous, event)

    def right_click_start(self, event):
        self.direction = -1  # Play backward
        self.start()  # Start playback
        self.remove_clicks_continuous(event)  # Begin the continuous removal process

    def right_click_stop(self, event):
        self.pause()  # Stop playback

    def remove_clicks_continuous(self, event=None):
        current_time = time.time()
        if current_time - self.last_click_time < self.click_delay:
            return  # Skip if click delay threshold not met

        # Remove clicks for the current frame
        self.saved_clicks = [(frame, x, y) for frame, x, y in self.saved_clicks if frame != self.frame_index]
        print(f"Removed clicks at frame {self.frame_index}")
        self.clicks_in_current_frame += 1  # Increment right-click counter

        # Update last click time
        self.last_click_time = current_time

        # Move to the previous frame
        self.frame_index -= self.frame_rate
        self.clicks_in_current_frame = 0  # Reset click counter
        if self.frame_index < 0:
            self.frame_index = 0

        # Render the updated frame for reverse playback
        if self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_index)
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                imgtk = ImageTk.PhotoImage(image=img)
                self.canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
                self.canvas.image = imgtk

                # Draw labels and clicks
                self.draw_labels()
                self.draw_saved_clicks()

        # Continue playback in reverse if the right button is still held
        if self.playing and self.direction == -1:
            self.root.after(30, self.remove_clicks_continuous)

    def update_cursor_location(self, event):
        self.cursor_x, self.cursor_y = event.x, event.y

    def add_label(self, event):
        # Prompt the user for a label
        label = simpledialog.askstring("Input", "Enter label:", parent=self.root)
        if label:
            # Save the label with the frame and coordinates
            click_position = (self.frame_index, event.x, event.y)
            self.labels[click_position] = label
            print(f"Label '{label}' added at frame {self.frame_index}, x: {event.x}, y: {event.y}")

    def draw_labels(self):
        # Draw labels on the canvas for the current frame
        for (frame, x, y), label in self.labels.items():
            if frame == self.frame_index:
                self.canvas.create_text(x, y, text=label, fill="red", font=("Helvetica", 12))

    def draw_saved_clicks(self):
        # Visualize clicks for the current frame
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
        print("Exiting application.")
        self.root.destroy()

def setup_controls(root, video_player):
    root.title("Video Controls")

    play_button = tk.Button(root, text="Play", command=video_player.start)
    play_button.pack(side="left")

    pause_button = tk.Button(root, text="Pause", command=video_player.pause)
    pause_button.pack(side="left")

    save_button = tk.Button(root, text="Save Clicks", command=video_player.save_clicks_to_csv)
    save_button.pack(side="left")

    close_button = tk.Button(root, text="Close", command=video_player.close_application)
    close_button.pack(side="left")

    frame_rate_slider = tk.Scale(root, from_=1, to=30, orient="horizontal", label="Frame Rate (n-th frame)",
                                 command=lambda val: video_player.set_frame_rate(int(val)))
    frame_rate_slider.set(video_player.frame_rate)
    frame_rate_slider.pack(side="left")

    clicks_required_slider = tk.Scale(root, from_=1, to=10, orient="horizontal", label="Clicks Required to Advance Frame",
                                      command=lambda val: video_player.set_clicks_required(int(val)))
    clicks_required_slider.set(video_player.clicks_required)
    clicks_required_slider.pack(side="left")

if __name__ == "__main__":
    root = tk.Tk()

    video_path = filedialog.askopenfilename(title="Select a Video", filetypes=(("MP4 Files", "*.mp4"), ("All Files", "*.*")))
    if not video_path:
        print("No video file selected. Exiting...")
        exit()

    video_player = VideoPlayer(root, video_path)

    setup_controls(root, video_player)
    video_player.play_video()
    root.mainloop()
