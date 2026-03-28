import cv2
import json
import os
from polysistia.capture.mss_backend import MSSBackend

def main():
    print("Polysistia Calibration Wizard")
    print("------------------------------")

    capture = MSSBackend()
    frame = capture.grab()

    if frame is None or frame.size == 0:
        print("Error: Could not capture screen.")
        return

    print("Click on the center of the top-left tile (0,0) to set the grid origin.")

    origin = [0, 0]

    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            origin[0], origin[1] = x, y
            print(f"Origin set to: {x}, {y}")

    cv2.imshow("Calibration", frame)
    cv2.setMouseCallback("Calibration", on_mouse)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    # Simple template based on standard 1920x1080 resolution
    calibration_data = {
        "window_title": "The Battle of Polytopia",
        "tesseract_cmd": "C:/Program Files/Tesseract-OCR/tesseract.exe",
        "regions": {
            "turn": [850, 20, 100, 40],
            "stars": [300, 20, 150, 40],
            "score": [1500, 20, 200, 40],
            "map": [0, 80, 1920, 920]
        },
        "tile_grid": {
            "origin": origin,
            "dx": 64,
            "dy": 56,
            "rows": 11,
            "cols": 11
        },
        "resolution": [frame.shape[1], frame.shape[0]]
    }

    with open("calibration.json", "w") as f:
        json.dump(calibration_data, f, indent=2)

    print("Saved calibration to calibration.json")

if __name__ == "__main__":
    main()
