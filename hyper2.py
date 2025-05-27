import joblib
from flask import Flask, request, jsonify
from db_connection import get_db_connection
import pyodbc

app = Flask(__name__)

# Load the trained model
model = joblib.load('hyperNew_tsh_predictor_model.pkl')

@app.route('/predict_tsh', methods=['POST'])
def predict_tsh():
    try:

        print(request.form)

        # Get user data from the frontend
        tsh1 = float(request.form['tsh1'])
        patient_id = request.form['patient_id']  # Assuming the patient's ID is passed from the frontend

        # Fetch patient health parameters using stored procedure
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Call the stored procedure to fetch health parameters for the patient
        cursor.execute("EXEC TSH_GetHealthParameters @PatientID = ?", patient_id)
        row = cursor.fetchone()
        conn.close()

        if not row:
            return jsonify({'error': 'User data not found'}), 404

        # Unpack patient data
        age = row[0]
        gender = row[1]
        weight = row[2]
        height = row[3]
        diabetes = row[4]
        cholesterol = row[5]
        blood_pressure = row[6]
        pregnancy = row[7]

        # Encode categorical values
        gender_m = 1 if gender == 'Male' else 0
        diabetes_y = 1 if diabetes == 'Yes' else 0
        cholesterol_y = 1 if cholesterol == 'Yes' else 0
        blood_pressure_y = 1 if blood_pressure == 'Yes' else 0
        pregnancy_y = 1 if pregnancy == 'Yes' else 0

        # Prepare input data for model prediction
        input_data = [[age, gender_m, weight, height, diabetes_y, cholesterol_y, blood_pressure_y, pregnancy_y, tsh1]]

        # Predict TSH3 value
        predicted_tsh3 = model.predict(input_data)[0]
        return jsonify({'predicted_tsh3': f"{predicted_tsh3:.2f} mIU/L"})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
