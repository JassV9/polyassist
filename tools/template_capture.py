import cv2
import os
import time
from polysistia.capture.mss_backend import MSSBackend

def main():
    print("Template Capture Tool")
    print("---------------------")

    save_dir = input("Enter category (tiles, units, buildings, icons): ")
    save_path = f"polysistia/vision/templates/{save_dir}"
    os.makedirs(save_path, exist_ok=True)

    capture = MSSBackend()

    print("Capturing templates in 3 seconds. Switch to game window...")
    time.sleep(3)

    frame = capture.grab()

    cv2.imshow("Select Template", frame)

    # Let user select multiple regions
    while True:
        roi = cv2.selectROI("Select Template", frame, fromCenter=False)
        if roi == (0, 0, 0, 0):
            break

        x, y, w, h = roi
        template = frame[y:y+h, x:x+w]

        name = input("Enter template name: ")
        cv2.imwrite(f"{save_path}/{name}.png", template)
        print(f"Saved {name}.png to {save_path}")

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
