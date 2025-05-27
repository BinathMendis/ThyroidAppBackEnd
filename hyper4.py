from flask import Flask, request, jsonify
import pyodbc
import joblib
from db_connection import get_db_connection

app = Flask(__name__)

# Load the trained model
model = joblib.load('hypoNew_tsh_predictor_model.pkl')

# Track My Health Route - Getting parameters from the DB using SP and predicting TSH
@app.route('/track_health', methods=['POST'])
def track_health():
    # Get the PatientID and input parameter from the request
    data = request.get_json()
    print("Received data:", data)

    # Extract patient_id and input_parameter from the JSON data
    patient_id = data.get('patient_id')
    input_parameter = data.get('input_parameter')

    if not patient_id or input_parameter is None:
        return jsonify({"message": "Missing patient_id or input_parameter"}), 400

    # Query the database to get the patient's health parameters using the stored procedure
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("EXEC TSH_GetHealthParameters @PatientID = ?", patient_id)
    row = cursor.fetchone()

    if row:
        # Access values using index-based retrieval
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

        # Prepare input data matching the model features
        input_data = [[age, gender_m, weight, height, diabetes_y, cholesterol_y, blood_pressure_y, pregnancy_y, input_parameter]]

        # Predict the next TSH value
        try:
            predicted_tsh3 = model.predict(input_data)[0]
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
                "predicted_tsh": round(predicted_tsh3, 2)
            }
            return jsonify(result), 200
        except Exception as e:
            return jsonify({"message": f"Prediction error: {str(e)}"}), 500
    else:
        return jsonify({"message": "Patient not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)
