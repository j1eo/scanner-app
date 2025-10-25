# barcode_scanner.py

import cv2
from pyzbar.pyzbar import decode
import pandas as pd

def load_database(path="database.csv"):
    """Carga la base de datos de botellas desde un archivo CSV."""
    return pd.read_csv(path)

def scan_barcode():
    """Escanea código de barras usando la cámara y pyzbar."""
    cap = cv2.VideoCapture(0)
    print("\n📸 Escanea el código de barras de la botella (presiona 'q' para salir).")

    detected_code = None
    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        # Decodifica códigos detectados
        barcodes = decode(frame)
        for barcode in barcodes:
            detected_code = barcode.data.decode('utf-8')
            (x, y, w, h) = barcode.rect
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 2)
            cv2.putText(frame, detected_code, (x, y-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,0), 2)
            print(f"\n✅ Código detectado: {detected_code}")
            cap.release()
            cv2.destroyAllWindows()
            return detected_code

        cv2.imshow('Escáner de Botellas', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return None

def get_bottle_info(barcode, df):
    """Obtiene los datos de la botella a partir del código escaneado."""
    record = df[df["Bottle_ID"] == barcode]
    if record.empty:
        return None
    return record.iloc[0].to_dict()
