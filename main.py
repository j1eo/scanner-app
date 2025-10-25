# main.py

from barcode_scanner import load_database, get_bottle_info, scan_barcode
from sla_engine import evaluate_sla

def main():
    print("=== Sistema de Evaluación de Botellas (SLA-Vision con Cámara) ===\n")

    df = load_database()

    while True:
        print("\n--- NUEVA BOTELLA ---")
        barcode = scan_barcode()
        if not barcode:
            print("⚠️ No se detectó ningún código. Intente nuevamente o presione Ctrl+C para salir.")
            continue

        record = get_bottle_info(barcode, df)
        if not record:
            print(f"❌ Código {barcode} no encontrado en la base de datos.\n")
            continue

        print(f"\n➡️  Cliente: {record['Customer_Code']}")
        print(f"➡️  Categoría: {record['Category']}")
        print(f"➡️  Política SLA: {record['SLA_Reuse_Policy']}\n")

        try:
            fill = float(input("Ingrese el porcentaje de llenado (%): "))
        except ValueError:
            print("⚠️ Valor inválido. Intente nuevamente.\n")
            continue

        seal = input("¿La botella está sellada o abierta? (sealed/opened): ").strip().lower()
        cleanliness = input("Estado de limpieza (Excellent/Good/Fair/Poor): ").strip().capitalize()

        # Evaluación SLA
        action, color = evaluate_sla(
            record["Customer_Code"],
            record["SLA_Reuse_Policy"],
            fill,
            seal,
            cleanliness
        )

        print(f"\n🔍 Resultado Final: {color} {action}")
        print("--------------------------------------------------------")

if __name__ == "__main__":
    main()
