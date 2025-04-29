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
        self.root.attributes('-fullscreen', True)

        # Video variables
        self.video_path = video_path
        self.cap = cv2.VideoCapture(self.video_path) if self.video_path else None
        self.playing = False
        self.frame = None
        self.scale_factor_x = 1
        self.scale_factor_y = 1
        self.frame_step = 1
        self.clicks = []
        self.frame_idx = 0
        self.max_annotations = 1  # Max number of annotations per frame
        self.current_annotations = 0  # Number of annotations made so far for the current frame

        # UI Elements
        self.canvas = tk.Canvas(root)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.on_left_click)
        self.canvas.bind("<Button-3>", self.on_right_click)
        self.root.bind("<Escape>", self.close_app)

        controls_frame = tk.Frame(root)
        controls_frame.pack(fill=tk.X)

        self.load_btn = tk.Button(controls_frame, text="Load Video", command=self.load_video)
        self.load_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.play_btn = tk.Button(controls_frame, text="Play", command=self.toggle_play)
        self.play_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.stop_btn = tk.Button(controls_frame, text="Stop", command=self.stop_video)
        self.stop_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.prev_btn = tk.Button(controls_frame, text="Previous Frame", command=self.prev_frame)
        self.prev_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.next_btn = tk.Button(controls_frame, text="Next Frame", command=self.advance_frame)
        self.next_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.toggle_table_btn = tk.Button(controls_frame, text="Hide Table", command=self.toggle_table)
        self.toggle_table_btn.pack(side=tk.LEFT, padx=5, pady=5)

        self.label_entry = tk.Entry(controls_frame)
        self.label_entry.pack(side=tk.LEFT, padx=5, pady=5)
        self.label_entry.insert(0, "Enter label")

        self.frame_rate_slider = tk.Scale(controls_frame, from_=1, to=60, orient="horizontal",
                                          label="Frame Step", command=lambda val: self.set_frame_step(int(val)))
        self.frame_rate_slider.set(1)
        self.frame_rate_slider.pack(side=tk.LEFT, padx=5, pady=5)

        self.quit_btn = tk.Button(controls_frame, text="Quit", command=self.close_app)
        self.quit_btn.pack(side=tk.LEFT, padx=5, pady=5)

        # Bind arrow keys
        self.root.bind("<Right>", lambda e: self.advance_frame())
        self.root.bind("<Left>", lambda e: self.prev_frame())
        self.root.bind("t", lambda e: self.toggle_table())
        self.root.bind("q", lambda e: self.close_app())

        # Bind number keys for setting max annotations
        self.root.bind("1", lambda e: self.set_max_annotations(1))
        self.root.bind("2", lambda e: self.set_max_annotations(2))
        self.root.bind("3", lambda e: self.set_max_annotations(3))
        self.root.bind("4", lambda e: self.set_max_annotations(4))
        self.root.bind("5", lambda e: self.set_max_annotations(5))

        # Table to display points
        self.table = ttk.Treeview(root, columns=("Frame", "X", "Y", "Label"), show="headings")
        for col in ("Frame", "X", "Y", "Label"):
            self.table.heading(col, text=col)
            self.table.column(col, width=100)
        self.table.pack(fill=tk.BOTH, expand=True)
        self.table.bind('<Double-1>', self.edit_table_entry)

        # Row counter for alternating colors
        self.row_count = 0

        # Configure the tags for alternating row colors
        self.table.tag_configure('odd', background='white')
        self.table.tag_configure('even', background='#ededed')

        if self.cap and self.cap.isOpened():
            self.load_first_frame()

        self.root.after(30, self.update_loop)

    def set_max_annotations(self, number):
        """Set the maximum number of annotations allowed per frame."""
        self.max_annotations = number
        self.current_annotations = 0  # Reset counter for the current frame
        print(f"Max annotations per frame set to {number}")

    def close_app(self, event=None):
        self.save_clicks()
        if self.cap:
            self.cap.release()
        self.root.destroy()

    def load_video(self):
        self.video_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.avi *.MP4")])
        if self.video_path:
            self.cap = cv2.VideoCapture(self.video_path)
            if self.cap.isOpened():
                self.load_first_frame()

    def load_first_frame(self):
        if self.cap:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, self.frame = self.cap.read()
            if ret:
                self.root.update_idletasks()
                self.display_frame()

    def update_loop(self):
        if self.playing and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                return
            self.frame = frame
            self.display_frame()
        self.root.after(30, self.update_loop)

    def display_frame(self):
        if self.frame is None:
            return

        win_width = self.root.winfo_width()
        orig_width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        orig_height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

        self.scale_factor_x = win_width / orig_width
        scaled_height = int(orig_height * self.scale_factor_x)
        self.scale_factor_y = scaled_height / orig_height

        frame_resized = cv2.resize(self.frame, (win_width, scaled_height))
        frame_resized = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
        frame_resized = cv2.putText(frame_resized, f"Frame: {self.frame_idx}", (20, 40),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

        img = Image.fromarray(frame_resized)
        imgtk = ImageTk.PhotoImage(image=img)

        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
        self.canvas.imgtk = imgtk

    def toggle_play(self):
        self.playing = not self.playing
        self.play_btn.config(text="Pause" if self.playing else "Play")

    def stop_video(self):
        if self.cap:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self.load_first_frame()
        self.playing = False
        self.play_btn.config(text="Play")

    def advance_frame(self):
        if not self.cap:
            return
        self.frame_idx += self.frame_step
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_idx)
        ret, self.frame = self.cap.read()
        if ret:
            self.display_frame()
        
    def toggle_table(self):
        if self.table.winfo_viewable():
            self.table.pack_forget()
            self.toggle_table_btn.config(text="Show Table")
        else:
            self.table.pack(fill=tk.BOTH, expand=True)
            self.toggle_table_btn.config(text="Hide Table")

        # Apply row colors
        self.table.tag_configure('odd', background='white')
        self.table.tag_configure('even', background='lightgray')

        # Force window layout update and redraw the frame
        self.root.update_idletasks()
        self.display_frame()

    def prev_frame(self):
        if not self.cap:
            return
        self.frame_idx = max(0, self.frame_idx - self.frame_step)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_idx)
        ret, self.frame = self.cap.read()
        if ret:
            self.display_frame()

    def overwrite_click_if_exists(self, frame_idx, x_orig, y_orig, label):
        for i, (video, frame, _, _, _) in enumerate(self.clicks):
            if frame == frame_idx:
                self.clicks[i] = (self.video_path, frame_idx, x_orig, y_orig, label)
                # Update the table too
                for item in self.table.get_children():
                    if int(self.table.item(item)['values'][0]) == frame_idx:
                        self.table.item(item, values=(frame_idx, x_orig, y_orig, label))
                        return True
        return False


    def on_left_click(self, event):
        if self.frame is None or not self.video_path:
            return

        label = self.label_entry.get()
        frame_idx = self.frame_idx

        x_orig = int(event.x / self.scale_factor_x)
        y_orig = int(event.y / self.scale_factor_y)

        # Add the click as a new entry for the frame
        new_click = (self.video_path, frame_idx, x_orig, y_orig, label)
        self.clicks.append(new_click)

        # Alternate row color by setting the tag
        row_tag = 'odd' if self.row_count % 2 == 0 else 'even'
        self.table.insert('', 'end', values=(frame_idx, x_orig, y_orig, label), tags=(row_tag,))
        
        # Increment row count and annotation count
        self.row_count += 1
        self.current_annotations += 1

        # Provide visual feedback for the click on the canvas
        self.canvas.create_oval(
            event.x - 5, event.y - 5, event.x + 5, event.y + 5, 
            outline="red", width=2
        )

        print(f"Saved: Frame {frame_idx}, X: {x_orig}, Y: {y_orig}, Label: {label}")

        # Optional: Update the frame after click
        if self.current_annotations >= self.max_annotations:
            self.current_annotations = 0
            self.advance_frame()

    def on_right_click(self, event):
        selected_item = self.table.selection()
        if selected_item:
            self.table.delete(selected_item)
            if self.clicks:
                self.clicks.pop()
        self.frame_idx = max(0, self.frame_idx - self.frame_step)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame_idx)
        ret, self.frame = self.cap.read()
        if ret:
            self.display_frame()

    def edit_table_entry(self, event):
        selected_item = self.table.focus()
        if not selected_item:
            return
        column = self.table.identify_column(event.x)
        column_idx = int(column.replace('#', '')) - 1

        old_value = self.table.item(selected_item)['values'][column_idx]
        new_value = simpledialog.askstring("Edit", f"Current value: {old_value}\nEnter new value:")

        if new_value is not None:
            current_values = list(self.table.item(selected_item)['values'])
            current_values[column_idx] = new_value
            self.table.item(selected_item, values=current_values)

            idx = self.table.index(selected_item)
            click = list(self.clicks[idx])
            click[column_idx + 1] = new_value
            self.clicks[idx] = tuple(click)

    def save_clicks(self):
        df = pd.DataFrame(self.clicks, columns=["VideoFile", "Frame", "X", "Y", "Label"])
        df.to_csv("clicks.csv", index=False)
        print("Saved clicks to clicks.csv")

    def set_frame_step(self, value):
        self.frame_step = int(value)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Video Annotation Tool")
    parser.add_argument("--video", type=str, help="Path to video file", default=None)
    args = parser.parse_args()

    root = tk.Tk()
    app = VideoAnnotator(root, args.video)
    root.mainloop()
