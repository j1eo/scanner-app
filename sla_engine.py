# sla_engine.py

def evaluate_sla(customer, sla_policy, fill, seal, cleanliness="Good"):
    """
    Evalúa la política SLA según el cliente y condiciones de la botella.
    Retorna la acción recomendada y un color indicador.
    """
    policy = sla_policy.lower()
    fill = float(fill)
    seal = seal.lower()
    cleanliness = cleanliness.lower()

    # --- Lógica basada en patrones comunes de SLA ---
    if "discard all opened" in policy and "opened" in seal:
        return "Discard", "🔴"

    if "refill" in policy:
        if "fill < 90" in policy and fill < 90:
            return "Refill", "🟡"
        elif "fill > 60" in policy and fill > 60:
            return "Refill", "🟡"

    if "keep only if sealed" in policy and seal == "sealed" and fill >= 95:
        return "Keep", "🟢"

    if "add 1 additional sealed" in policy and 60 <= fill < 80:
        return "Add Bottle", "🔵"

    if "discard" in policy and fill < 60:
        return "Discard", "🔴"

    if "clean" in policy and cleanliness not in ["good", "excellent"]:
        return "Discard", "🔴"

    # Valor por defecto si no entra en ninguna condición
    return "Keep", "🟢"
