import cv2
from ultralytics import YOLO

# 1️⃣ Load a pretrained YOLO model (has 'bottle' class)
model = YOLO("yolov8n.pt")  # or yolov8s.pt for better accuracy

def main():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("❌ No se pudo abrir la cámara.")
        return

    print("\n📸 Mostrando cámara (presiona 'q' para salir)...")

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        # 2️⃣ Run YOLO detection on the frame
        results = model(frame, verbose=False)
        bottle_found = False

        for box in results[0].boxes:
            cls_id = int(box.cls)
            cls_name = model.names[cls_id]

            if cls_name == "bottle":
                bottle_found = True
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])

                # 3️⃣ Draw bounding box
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"Bottle ({conf*100:.1f}%)", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        if not bottle_found:
            cv2.putText(frame, "No bottle detected", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        # 4️⃣ Show result
        cv2.imshow("YOLO Bottle Detector", frame)

        # Press q to quit
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("📴 Cámara cerrada.")

if __name__ == "__main__":
    main()
