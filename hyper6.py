from flask import Blueprint, Flask, request, jsonify
from flask_cors import CORS
import pyodbc
import joblib
from db_connection import get_db_connection

tsh_bp = Blueprint("tsh", __name__)

# Load the trained models
model_hyper = joblib.load('hyperNew_tsh_predictor_model2001.pkl')  # For TSH < 0.4
model_hypo = joblib.load('hypoNew_tsh_predictor_model2002.pkl')    # For TSH > 4

@tsh_bp.route('/track_health', methods=['POST'])
def track_health():
    # Get the PatientID and input parameter from the request
    data = request.get_json()
    print("Received data:", data)

    patient_id = data.get('patient_id')
    
    # Convert input_parameter to a float
    try:
        input_parameter = float(data.get('input_parameter'))
    except (ValueError, TypeError):
        return jsonify({"message": "Invalid input_parameter value"}), 400

    if not patient_id:
        return jsonify({"message": "Missing patient_id"}), 400

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

            # Call stored procedure to insert prediction
            cursor.execute("""
                EXEC TSH_InsertPrediction 
                @PatientID = ?, 
                @Age = ?, 
                @Gender = ?, 
                @Weight = ?, 
                @Height = ?, 
                @Diabetes = ?, 
                @Cholesterol = ?, 
                @BloodPressure = ?, 
                @Pregnancy = ?, 
                @InputParameter = ?, 
                @PredictedTSH = ?, 
                @ModelUsed = ?
            """, (patient_id, age, gender, weight, height, diabetes, cholesterol, blood_pressure, pregnancy, input_parameter, round(predicted_tsh, 2), model_used))

            conn.commit()  # Commit the transaction

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
            conn.rollback()  # Rollback transaction if there is an error
            return jsonify({"message": f"Database error: {str(e)}"}), 500
    else:
        return jsonify({"message": "Patient not found"}), 404
    

    
@tsh_bp.route('/get_patient_data', methods=['POST'])
def get_patient_data():
    data = request.get_json()
    patient_id = data.get('patient_id')

    if not patient_id:
        return jsonify({"message": "Missing patient_id"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("EXEC TSH_GetHealthParameters @PatientID = ?", patient_id)
    row = cursor.fetchone()

    if row:
        age = row[0]
        gender = row[1]
        weight = float(row[2]) if row[2] else 0.0
        height = float(row[3]) if row[3] else 0.0
        diabetes = "Yes" if row[4] else "No"
        cholesterol = "Yes" if row[5] else "No"
        blood_pressure = "Yes" if row[6] else "No"
        pregnancy = "Yes" if row[7] else "No"
        name = row[8]

        patient_data = {
 
            "Age": age,
            "Gender": gender,
            "Weight": weight,
            "Height": height,
            "Diabetes": diabetes,
            "Cholesterol": cholesterol,
            "BloodPressure": blood_pressure,
            "Pregnancy": pregnancy,
            "Name": name
        }

        return jsonify({"patient_data": patient_data}), 200
    else:
        return jsonify({"message": "Patient not found"}), 404


@tsh_bp.route('/api/get-latest-tsh', methods=['GET'])
def get_latest_tsh():
    patient_id = request.args.get('patient_id')

    if not patient_id:
        return jsonify({"error": "Missing patient_id"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("EXEC GetLatestTSHPrediction @PatientID = ?", patient_id)
        row = cursor.fetchone()

        if row:
            result = {
                "input_tsh": row.Entered_TSHValue,
                "predicted_tsh": row.Predicted_TSHValue,
                "date": row.LoggedDate
            }
        else:
            result = {"message": "No records found for the given patient."}

        cursor.close()
        conn.close()

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500