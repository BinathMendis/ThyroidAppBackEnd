from flask import Flask, request, jsonify
import pyodbc
import joblib
from db_connection import get_db_connection

app = Flask(__name__)

# Load the trained models
model_hyper = joblib.load('hyperNew_tsh_predictor_model.pkl')  # For TSH < 0.4
model_hypo = joblib.load('hypoNew_tsh_predictor_model.pkl')    # For TSH > 4

@app.route('/track_health', methods=['POST'])
def track_health():
    # Get the PatientID and input parameter from the request
    data = request.get_json()
    print("Received data:", data)

    patient_id = data.get('patient_id')
    input_parameter = data.get('input_parameter')

    if not patient_id or input_parameter is None:
        return jsonify({"message": "Missing patient_id or input_parameter"}), 400

    # Determine which model to use
    if input_parameter < 0.4:
        model = model_hyper
        model_used = "Hyperthyroidism Model"
    elif input_parameter > 4:
        model = model_hypo
        model_used = "Hypothyroidism Model"
    else:
        return jsonify({"message": "TSH levels are normal", "input_parameter": input_parameter}), 200

    print(f"Using {model_used} for prediction.")

    # Query the database for patient health parameters
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("EXEC TSH_GetHealthParameters @PatientID = ?", patient_id)
    row = cursor.fetchone()

    if row:
        # Extract patient health data
        age = row[0]
        gender = row[1]
        weight = float(row[2]) if row[2] else 0.0
        height = float(row[3]) if row[3] else 0.0
        diabetes = bool(row[4])
        cholesterol = bool(row[5])
        blood_pressure = bool(row[6])
        pregnancy = bool(row[7])

        # Encode categorical variables
        gender_m = 1 if gender.lower() == 'male' else 0
        diabetes_y = 1 if diabetes else 0
        cholesterol_y = 1 if cholesterol else 0
        blood_pressure_y = 1 if blood_pressure else 0
        pregnancy_y = 1 if pregnancy else 0

        # Prepare input data
        input_data = [[age, gender_m, weight, height, diabetes_y, cholesterol_y, blood_pressure_y, pregnancy_y, input_parameter]]

        # Predict TSH
        try:
            predicted_tsh = model.predict(input_data)[0]
            result = {
                "age": age,
                "gender": gender,
                "weight": weight,
                "height": height,
                "diabetes": diabetes,
                "cholesterol": cholesterol,
                "blood_pressure": blood_pressure,
                "pregnancy": pregnancy,
                "input_parameter": input_parameter,
                "predicted_tsh": round(predicted_tsh, 2),
                "model_used": model_used
            }
            return jsonify(result), 200
        except Exception as e:
            return jsonify({"message": f"Prediction error: {str(e)}"}), 500
    else:
        return jsonify({"message": "Patient not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)
