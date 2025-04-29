# ClickLabel
A simple application to manually generate x,y coordinates from a video

## Interactive Video Annotation Tool

This Python script provides an interactive video annotation tool using the Python libraries OpenCV and Tkinter, enabling users to manually label frames and save annotations to a CSV file. It supports forward and reverse frame navigation, labeling, and click tracking, making it ideal for tasks requiring precise, frame-specific, point annotations.

## Key Features

### 1. Video Playback and Frame Control
- Loads videos using OpenCV, displaying frames on a Tkinter canvas.
- Users can play, pause, and navigate frames forward or backward.
- Frame navigation is configurable with adjustable frame-skip rates.

### 2. Click Management
- **Left-click**: Save the cursor's position (`x`, `y`) on the current frame.
- All data can be visualized in a table. Pressing the key `t` on the keyboard toggles between showing and hiding the table. The information can be edited in the table manually by clicking on the corresponding cell and changing it directly. 

### 3. Annotations and Data Export
- Stores all clicks and labels with their associated frame numbers and positions.
- Provides an option to export annotations into a CSV file for further analysis.

### 4. Customizability
- Frame-skip rate and required clicks per frame are adjustable via sliders.
- Displays the current frame number on the video.

## Installation 

### 1. Miniconda
Given that the application runs is written in Python it requires a local version of Python to be installed, in order to run it. The easiest way to achieve this is by installing [Miniconda](https://docs.anaconda.com/miniconda/) according to the [online instructions](https://docs.anaconda.com/miniconda/install/). This allows you to install and use Python without worrying about it interfering with you local operating system. 

After successfully installing Miniconda you can open a Anaconda Prompt (Windows) or use the general Terminal interface (Mac & Linux).

### 2. Create Environment 
A conda environment is a container in which your Python version and all it's dependencies are installed. Running the following command from the Anaconda Prompt or terminal will create a container named `click` and install Python Version 3.11 and all the required dependencies:

```conda create -n click python=3.11 pip pandas opencv tk pillow```

This command only needs to be run once! To remove the container simply run:

```conda remove -n click --all```

### 3. Run ClickLabel
To run the ClickLabel Python script (or any other Python script) using the designated Python version in the designated container we first need to activate the container. This is done by running the following command from an Anaconda Prompt or terminal:

```conda activate click```

After the container is activated you should see the name of the container in brackets at the beginning of the command line (i.e. ```(click)```).
Now you can navigate to the folder containing the ```clicklabel.py``` script, or simply find the absolute path to the file (i.e. C:\Downloads\clicklabel.py, /home/Sarah/clicklabel.py, etc.).  
To run the script you can then execute the following command:

```python /path/to/clicklabel.py``` or if in the same location ```python clicklabel.py```

This should open a file dialog for you to select a video file to annotate. 


## Usage
- Opens a file dialog for video selection.
- Initializes a Tkinter window for video display and controls.
- Controls include:
  - Buttons for play, pause, save annotations, and exit.
  - Sliders to adjust the frame-skip rate and the number of required clicks per frame.

This versatile script is ideal for manual annotation tasks, offering a user-friendly interface and robust features for frame-specific labeling.

## Further Information
For more information on how to set up Python, Conda and more resources please go here: [https://fritzfrancisco.thekaolab.com/assets/content/pdf/python_setup_guide_22092020.pdf](https://fritzfrancisco.thekaolab.com/assets/content/pdf/python_setup_guide_22092020.pdf)

For comments, questions or recommendations feel free to contact:  
Fritz Francisco (<a href="mailto:fritz.francisco@umb.edu">fritz.francisco@umb.edu</a>)
