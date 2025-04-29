import cv2
import tkinter as tk
from tkinter import filedialog, simpledialog, ttk
from PIL import Image, ImageTk
import pandas as pd
import argparse


class VideoAnnotator:
    def __init__(self, root, video_path):
        self.root = root
        self.root.title("Video Annotator")
        self.root.overrideredirect(True)
        self.root.overrideredirect(False)
        self.root.attributes('-fullscreen', True)

        # Video variables
        self.video_path = video_path
        self.cap = cv2.VideoCapture(
            self.video_path) if self.video_path else None
        self.playing = False
        self.frame = None
        self.scale_factor_x = 1
        self.scale_factor_y = 1
        self.frame_step = 1  # Default frame step
        self.clicks = []
        self.frame_idx = 0

        # UI Elements
        self.canvas = tk.Canvas(root)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.on_left_click)
        self.canvas.bind("<Button-3>", self.on_right_click)
        self.root.bind("<Escape>", self.close_app)

        self.load_btn = tk.Button(
            root, text="Load Video", command=self.load_video)
        self.load_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.play_btn = tk.Button(root, text="Play", command=self.toggle_play)
        self.play_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.stop_btn = tk.Button(root, text="Stop", command=self.stop_video)
        self.stop_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.label_entry = tk.Entry(root)
        self.label_entry.pack(side=tk.LEFT, padx=5, pady=5)
        self.label_entry.insert(0, "Enter label")

        self.save_btn = tk.Button(
            root, text="Save Clicks", command=self.save_clicks)
        self.save_btn.pack(side=tk.LEFT, padx=5, pady=5)

        # self.frame_rate_slider = ttk.Scale(
        #     root, from_=1, to=60, orient=tk.HORIZONTAL, command=self.set_frame_step)

        self.frame_rate_slider = tk.Scale(root, from_=1, to=60, orient="horizontal",
                                          label="Frame Rate (n-th frame)", command=lambda val: self.set_frame_step(int(val)))

        self.frame_rate_slider.set(1)
        self.frame_rate_slider.pack(side=tk.LEFT, padx=5, pady=5)

        self.save_btn = tk.Button(root, text="Quit", command=self.close_app)
        self.save_btn.pack(side=tk.LEFT, padx=5, pady=5)

        if self.cap and self.cap.isOpened():
            self.load_first_frame()

        # Ensure first frame is displayed immediately
        self.root.after(100, self.update_loop)

    def close_app(self, event=None):
        self.save_clicks()
        self.cap.release()
        self.root.destroy()

    def load_video(self):
        self.video_path = filedialog.askopenfilename(
            filetypes=[("MP4 files", "*.mp4"), ("AVI files", "*.avi")])
        if self.video_path:
            self.cap = cv2.VideoCapture(self.video_path)
            if not self.cap.isOpened():
                print("Error: Could not open video.")
                return

            self.load_first_frame()

    def load_first_frame(self):
        if self.cap:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Reset to first frame
            ret, self.frame = self.cap.read()
            if ret:
                self.root.update_idletasks()  # Force update of the window dimensions
                self.display_frame()

    def update_loop(self):
        if self.playing and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Restart video
                return

            self.frame = frame
            self.display_frame()
        self.root.after(30, self.update_loop)  # Refresh every 30ms

    def display_frame(self):
        if self.frame is None:
            return

        win_width = self.root.winfo_width()
        win_height = self.root.winfo_height()

        self.scale_factor_x = win_width / \
            self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.scale_factor_y = win_height / \
            self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

        frame_resized = cv2.resize(self.frame, (win_width, win_height))
        frame_resized = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
        frame_resized = cv2.putText(frame_resized, "Frame: " + str(
            self.frame_idx), (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
        img = Image.fromarray(frame_resized)
        imgtk = ImageTk.PhotoImage(image=img)

        self.canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
        self.canvas.imgtk = imgtk  # Prevent garbage collection

    def toggle_play(self):
        self.playing = not self.playing
        self.play_btn.config(text="Pause" if self.playing else "Play")

    def stop_video(self):
        if self.cap:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Reset video
            self.load_first_frame()
        self.playing = False
        self.play_btn.config(text="Play")

    def on_left_click(self, event):
        if self.frame is None or not self.video_path:
            return

        label = self.label_entry.get()
        # frame_idx = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
        frame_idx = self.frame_idx

        x_orig = int(event.x / self.scale_factor_x)
        y_orig = int(event.y / self.scale_factor_y)

        self.clicks.append((self.video_path, frame_idx, x_orig, y_orig, label))
        print(
            f"Saved: {self.video_path}, Frame: {frame_idx}, X: {x_orig}, Y: {y_orig}, Label: {label}")

        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx + self.frame_step)
        self.frame_idx = frame_idx + self.frame_step

        ret, self.frame = self.cap.read()
        if ret:
            self.display_frame()

    def on_right_click(self, event):
        if self.clicks:
            removed_click = self.clicks.pop()
            print(f"Removed: {removed_click}")

        # frame_idx = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
        frame_idx = self.frame_idx
        new_frame_idx = max(0, frame_idx - self.frame_step)
        self.frame_idx = new_frame_idx
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, new_frame_idx)
        ret, self.frame = self.cap.read()
        if ret:
            self.display_frame()

    def save_clicks(self):
        df = pd.DataFrame(self.clicks, columns=[
                          "VideoFile", "Frame", "X", "Y", "Label"])
        df.to_csv("clicks.csv", index=False)
        print("Saved clicks to clicks.csv")

    def set_frame_step(self, value):
        self.frame_step = int(float(value))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Video Annotation Tool")
    parser.add_argument("--video", type=str,
                        help="Path to video file", default=None)
    args = parser.parse_args()

    root = tk.Tk()
    app = VideoAnnotator(root, args.video)
    root.mainloop()
