import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import joblib

# 1️⃣ Cargar dataset
df = pd.read_csv("database.csv")

print("📘 Columnas disponibles:", df.columns.tolist())
print("📊 Total de registros:", len(df))

# 2️⃣ Definir columnas relevantes
target = "Recommended_Action"
non_features = ["Record_ID", "Bottle_ID", target]
features = [c for c in df.columns if c not in non_features]

print(f"🎯 Target: {target}")
print(f"🧩 Features: {features}")

# 3️⃣ Codificar variables categóricas
df = df.dropna(subset=[target])
encoders = {}

for col in features:
    if df[col].dtype == "object" or df[col].dtype.name == "category":
        enc = LabelEncoder()
        df[col] = enc.fit_transform(df[col].astype(str))
        encoders[col] = enc

target_encoder = LabelEncoder()
df[target] = target_encoder.fit_transform(df[target])

# 4️⃣ Dividir datos
X = df[features]
y = df[target]
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# 5️⃣ Entrenar modelo
model = RandomForestClassifier(
    n_estimators=300,
    random_state=42,
    class_weight="balanced_subsample",
)
model.fit(X_train, y_train)

# 6️⃣ Evaluación general
y_pred = model.predict(X_test)
print("\n📈 Model Performance:")
print("Accuracy:", round(accuracy_score(y_test, y_pred), 3))
print("\nConfusion Matrix:\n", confusion_matrix(y_test, y_pred))
print("\nClassification Report:\n", classification_report(y_test, y_pred, zero_division=0))

# 7️⃣ Guardar modelo
joblib.dump(model, "bottle_policy_model.pkl")
joblib.dump(encoders, "label_encoders.pkl")
joblib.dump(target_encoder, "target_encoder.pkl")
print("\n✅ Modelo y codificadores guardados exitosamente.")

# 8️⃣ Evaluación en muestra de 30 predicciones
print("\n🔍 Comparativa de 30 predicciones aleatorias:")

# Selecciona 30 muestras aleatorias del conjunto de prueba
sample_indices = X_test.sample(30, random_state=42).index
sample_X = X_test.loc[sample_indices]
sample_y_real = y_test.loc[sample_indices]
sample_y_pred = model.predict(sample_X)

# Crea un DataFrame de comparación
comparison = pd.DataFrame({
    "Predicted_Label": target_encoder.inverse_transform(sample_y_pred),
    "Real_Label": target_encoder.inverse_transform(sample_y_real)
}, index=sample_indices)

comparison["Match"] = comparison["Predicted_Label"] == comparison["Real_Label"]
comparison = comparison.sort_values(by="Match", ascending=False)

print(comparison.head(30).to_string())

sample_accuracy = (comparison["Match"].sum() / len(comparison)) * 100
print(f"\n✅ Exactitud en las 30 muestras: {sample_accuracy:.1f}%")
