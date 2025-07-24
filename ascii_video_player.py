#!/usr/bin/env python3

import os
import sys
import time
import cv2
from PIL import Image
import numpy as np
import platform

def interpolate_frames(frame1, frame2, factor):
    """
    Interpolate between two frames
    
    Args:
        frame1: First frame
        frame2: Second frame
        factor: Interpolation factor (0.0 to 1.0)
        
    Returns:
        Interpolated frame
    """
    if frame1 is None or frame2 is None:
        return frame1 if frame1 is not None else frame2
        
    # Linear interpolation between frames
    return cv2.addWeighted(frame1, 1 - factor, frame2, factor, 0)

def frame_to_ascii(frame, width=80):
    """
    Convert a video frame to ASCII art
    
    Args:
        frame: OpenCV video frame (numpy array)
        width: Width of the ASCII art in characters
        
    Returns:
        ASCII art string representation of the frame
    """
    # Convert BGR to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Calculate height to maintain aspect ratio
    height, width_orig = gray.shape
    aspect_ratio = height / width_orig
    new_height = int(aspect_ratio * width * 0.43)  # Adjust for terminal character aspect ratio
    
    # Resize the image
    resized = cv2.resize(gray, (width, new_height))
    
    # Convert to PIL Image for easier processing
    img = Image.fromarray(resized)
    
    # Define ASCII characters from lightest to darkest (inverted)
    chars = "    :;;##"
    
    # Convert pixels to ASCII characters (inverted mapping)
    pixels = list(img.getdata())
    char_length = len(chars)
    ascii_str = ''.join([chars[min(pixel // 25, char_length - 1)] for pixel in pixels])
    
    # Split the string into lines based on the width
    ascii_img = '\n'.join([ascii_str[i:i+width] for i in range(0, len(ascii_str), width)])
    
    return ascii_img

def play_video(video_path, max_duration=20, ascii_width=80, interpolation_factor=2):
    """
    Play a video as ASCII art in the terminal
    
    Args:
        video_path: Path to the video file
        max_duration: Maximum duration to play in seconds (optional)
        ascii_width: Width of the ASCII art in characters
    """
    # Open the video file
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"[!] Error: Could not open video file {video_path}")
        return
    
    # Get video properties
    original_fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / original_fps
    
    # Increase FPS by interpolation factor
    fps = original_fps * interpolation_factor
    
    # Calculate frame delay based on FPS
    frame_delay = 1 / fps
    
    # Calculate max frames based on max_duration
    max_frames = int(fps * max_duration) if max_duration else frame_count
    
    print(f"[*] ASCII Video Player")
    print(f"[*] Video: {video_path}")
    print(f"[*] FPS: {fps:.2f}")
    print(f"[*] Duration: {min(duration, max_duration):.2f} seconds")
    print(f"[*] Press Ctrl+C to stop")
    time.sleep(2)
    
    try:
        frame_index = 0
        start_time = time.time()
        
        # Read the first frame
        ret, prev_frame = cap.read()
        if not ret:
            print("[!] Error: Could not read the first frame")
            return
            
        # For interpolation
        current_frame = None
        
        # Frame counter for original video frames
        original_frame_index = 0
        
        while frame_index < max_frames:
            # For original frames
            if frame_index % interpolation_factor == 0:
                # Save the previous frame
                prev_frame = current_frame if current_frame is not None else prev_frame
                
                # Read a new frame
                ret, current_frame = cap.read()
                if not ret:
                    break
                    
                original_frame_index += 1
            else:
                # Calculate interpolation factor for in-between frames
                interp_factor = (frame_index % interpolation_factor) / interpolation_factor
                
                # Create interpolated frame
                frame = interpolate_frames(prev_frame, current_frame, interp_factor)
            
            # Calculate the target time for this frame
            target_time = start_time + (frame_index / fps)
            current_time = time.time()
            
            # Skip frame if we're already behind schedule by more than one frame
            if current_time > target_time + frame_delay:
                frame_index += 1
                continue
                
            # Clear the screen using ANSI escape codes (more efficient than os.system)
            # Move cursor to top-left and clear screen
            sys.stdout.write("\033[H\033[J")
            
            # Use the appropriate frame
            display_frame = current_frame if frame_index % interpolation_factor == 0 else frame
            
            # Convert frame to ASCII
            ascii_frame = frame_to_ascii(display_frame, width=ascii_width)
            
            # Print frame information
            sys.stdout.write(f"Frame: {frame_index+1}/{min(frame_count, max_frames)} | ")
            sys.stdout.write(f"Time: {(frame_index/fps):.2f}s\n")
            
            # Print the ASCII frame
            sys.stdout.write(ascii_frame)
            sys.stdout.flush()
            
            # Calculate how much time to wait until the next frame should be displayed
            current_time = time.time()
            sleep_time = max(0, target_time - current_time)
            
            # Wait for the next frame (if needed)
            if sleep_time > 0:
                time.sleep(sleep_time)
            
            frame_index += 1
            
        # Calculate actual playback time
        elapsed_time = time.time() - start_time
        fps_achieved = frame_index / elapsed_time if elapsed_time > 0 else 0
        
        # Clear the screen after playback using ANSI escape codes
        sys.stdout.write("\033[H\033[J")
        print(f"[+] Playback completed")
        print(f"[+] Frames played: {frame_index}")
        print(f"[+] Actual FPS: {fps_achieved:.2f}")
        
    except KeyboardInterrupt:
        print("\n[!] Playback interrupted")
    finally:
        # Release resources
        cap.release()

if __name__ == "__main__":
    # Check if video file is provided as argument
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
    else:
        video_path = "video.mp4"  # Default video file
    
    # Check if video file exists
    if not os.path.exists(video_path):
        print(f"[!] Error: Video file '{video_path}' not found")
        print(f"[!] Usage: python {sys.argv[0]} [video_file]")
        sys.exit(1)
    
    # Set up terminal for ANSI escape codes on Windows if needed
    if platform.system() == 'Windows':
        # Enable ANSI escape sequences on Windows
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    
    # Play the video with 3x frame interpolation for smoother playback
    play_video(video_path, interpolation_factor=3)