import cv2
import numpy as np
import ezdxf
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from scipy.interpolate import splprep, splev

class ContourApp:
    def __init__(self, master):
        self.master = master
        master.title("Contour Capture System")

        # Initialize camera and variables
        self.cap = cv2.VideoCapture(0)
        self.image = None
        self.contour = None
        self.pixels_per_mm = None
        self.is_capturing = False
        self.threshold_value = 245  # Default threshold value

        # Create UI elements
        self.capture_button = tk.Button(master, text="Capture Image", command=self.capture_image)
        self.capture_button.pack()

        self.discard_button = tk.Button(master, text="Discard Image", command=self.discard_image, state=tk.DISABLED)
        self.discard_button.pack()

        self.offset_label = tk.Label(master, text="Offset Value (mm):")
        self.offset_label.pack()
        self.offset_entry = tk.Entry(master)
        self.offset_entry.insert(0, "2.0")
        self.offset_entry.pack()

        self.smooth_label = tk.Label(master, text="Smoothing Factor:")
        self.smooth_label.pack()
        self.smooth_entry = tk.Entry(master)
        self.smooth_entry.insert(0, "0.001")
        self.smooth_entry.pack()

        self.curviness_label = tk.Label(master, text="Curviness Factor:")
        self.curviness_label.pack()
        self.curviness_entry = tk.Entry(master)
        self.curviness_entry.insert(0, "100000")  # Default curviness factor
        self.curviness_entry.pack()

        self.threshold_label = tk.Label(master, text="Threshold Value:")
        self.threshold_label.pack()
        self.threshold_slider = tk.Scale(master, from_=0, to=255, orient=tk.HORIZONTAL, command=self.update_threshold)
        self.threshold_slider.set(self.threshold_value)
        self.threshold_slider.pack()

        self.scale_label = tk.Label(master, text="Scaling Factor:")
        self.scale_label.pack()
        self.scale_entry = tk.Entry(master)
        self.scale_entry.insert(0, "0.002")  # Default scaling factor
        self.scale_entry.pack()

        self.process_button = tk.Button(master, text="Process Image", command=self.process_image)
        self.process_button.pack()

        self.export_button = tk.Button(master, text="Export to DXF", command=self.export_dxf)
        self.export_button.pack()

        self.canvas = tk.Canvas(master, width=500, height=500)
        self.canvas.pack()

        # Start updating the camera feed
        self.update_camera_feed()

    def update_camera_feed(self):
        if not self.is_capturing:
            # Read a frame from the camera
            ret, frame = self.cap.read()
            if ret:
                self.display_image(frame)
            self.master.after(10, self.update_camera_feed)  # Continuously update

    def update_threshold(self, value):
        self.threshold_value = int(value)

    def capture_image(self):
        if not self.is_capturing:
            ret, frame = self.cap.read()
            if ret:
                self.image = frame
                self.pixels_per_mm = calibrate_scaling_factor(self.image)
                self.is_capturing = True
                self.discard_button.config(state=tk.NORMAL)
                self.display_image(self.image)
                messagebox.showinfo("Success", "Image captured successfully.")
            else:
                messagebox.showerror("Error", "Failed to capture image from camera.")

    def discard_image(self):
        self.image = None
        self.contour = None
        self.is_capturing = False
        self.discard_button.config(state=tk.DISABLED)
        self.update_camera_feed()

    def process_image(self):
        if self.image is None:
            messagebox.showerror("Error", "No image to process.")
            return

        try:
            offset_value_mm = float(self.offset_entry.get())
            smoothing_factor = float(self.smooth_entry.get())
            curviness_factor = float(self.curviness_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid offset, smoothing, or curviness factor.")
            return

        offset_value_pixels = int(self.pixels_per_mm * offset_value_mm)
        self.contour = detect_contours_sobel(self.image, self.threshold_value)

        if self.contour is None or len(self.contour) == 0:
            messagebox.showerror("Error", "No contour detected in the image.")
            return

        offset_cont = offset_contour(self.contour, offset_value_pixels, self.image.shape)
        self.contour = smooth_contour(offset_cont, smoothing_factor, curviness_factor)
        preview_img = preview_contour(self.image, self.contour)
        self.display_image(preview_img)
        messagebox.showinfo("Success", "Image processed successfully.")

    def export_dxf(self):
        if self.contour is None:
            messagebox.showerror("Error", "No contour to export.")
            return

        try:
            scale_factor = float(self.scale_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid scaling factor.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".dxf", filetypes=[("DXF files", "*.dxf")])
        if file_path:
            export_to_dxf([self.contour], file_path, self.pixels_per_mm, scale_factor)
            messagebox.showinfo("Success", f"DXF file exported successfully as '{file_path}'.")

    def display_image(self, cv_image):
        scale_percent = 50
        width = int(cv_image.shape[1] * scale_percent / 100)
        height = int(cv_image.shape[0] * scale_percent / 100)
        resized = cv2.resize(cv_image, (width, height), interpolation=cv2.INTER_AREA)
        cv2_im = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(cv2_im)
        imgtk = ImageTk.PhotoImage(image=img)
        self.canvas.create_image(250, 250, image=imgtk)
        self.canvas.image = imgtk  # Keep a reference to prevent garbage collection

    def __del__(self):
        if self.cap.isOpened():
            self.cap.release()

def detect_contours_sobel(image, threshold_value):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    grad_x = cv2.Sobel(blurred, cv2.CV_64F, 1, 0, ksize=5)
    grad_y = cv2.Sobel(blurred, cv2.CV_64F, 0, 1, ksize=5)
    grad_magnitude = cv2.magnitude(grad_x, grad_y)
    grad_magnitude = cv2.convertScaleAbs(grad_magnitude)
    _, thresh = cv2.threshold(grad_magnitude, threshold_value, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        return max(contours, key=cv2.contourArea)
    return None

def calibrate_scaling_factor(image):
    image_height, image_width = image.shape[:2]
    bed_width_mm = 457.2  # 18 inches in mm
    pixels_per_mm = image_width / bed_width_mm
    return pixels_per_mm

def offset_contour(contour, offset_value_pixels, image_shape):
    offset_contour = []
    for point in contour:
        offset_point = (point[0][0] + offset_value_pixels, point[0][1] + offset_value_pixels)
        offset_contour.append([offset_point])
    return np.array(offset_contour, dtype=np.int32)

def smooth_contour(contour, smoothing_factor, curviness_factor):
    epsilon = smoothing_factor * cv2.arcLength(contour, True)
    simplified_contour = cv2.approxPolyDP(contour, epsilon, True).reshape(-1, 2)
    
    if len(simplified_contour) < 4:
        return contour
    
    tck, _ = splprep([simplified_contour[:, 0], simplified_contour[:, 1]], s=curviness_factor)
    num_points = 100
    smooth_points = splev(np.linspace(0, 1, num_points), tck)
    
    smoothed_contour = np.vstack(smooth_points).T
    smoothed_contour = smoothed_contour.reshape(-1, 1, 2).astype(np.int32)
    
    return smoothed_contour

def preview_contour(image, contour):
    preview_img = image.copy()
    if contour is not None and len(contour) > 0:
        cv2.drawContours(preview_img, [contour], -1, (0, 255, 0), 2)
    return preview_img

def export_to_dxf(contours, file_path, pixels_per_mm, scale_factor):
    doc = ezdxf.new()
    msp = doc.modelspace()
    
    for contour in contours:
        polyline_points = []
        for point in contour:
            # Convert pixel coordinates to mm by dividing by pixels_per_mm
            x, y = point[0][0] / pixels_per_mm, point[0][1] / pixels_per_mm
            
            # Apply scaling factor
            x_scaled = x * scale_factor
            y_scaled = y * scale_factor
            polyline_points.append((x_scaled, y_scaled))
        
        # Pass the points to the add_lwpolyline function
        msp.add_lwpolyline(polyline_points)
    
    # Save the DXF file
    doc.saveas(file_path)


def main():
    root = tk.Tk()
    app = ContourApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()
