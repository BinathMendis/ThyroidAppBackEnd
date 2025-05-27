from flask import Flask, request, jsonify
import pyodbc
from db_connection import get_db_connection

app = Flask(__name__)

# Track My Health Route - Getting parameters from the DB using SP
@app.route('/track_health', methods=['POST'])
def track_health():
    # Get the PatientID and input parameter from the request
    data = request.get_json()  # This retrieves the JSON data sent in the request
    print("Received data:", data)  # This will show you the raw data in the console

    # Extract patient_id and input_parameter from the JSON data
    patient_id = data.get('patient_id')
    input_parameter = data.get('input_parameter')

    # If patient_id or input_parameter is missing, return a 400 error
    if not patient_id or not input_parameter:
        return jsonify({"message": "Missing patient_id or input_parameter"}), 400

    # Query the database to get the patient's health parameters using the stored procedure
    conn = get_db_connection()
    cursor = conn.cursor()

    # Call the stored procedure to get health parameters
    cursor.execute("EXEC TSH_GetHealthParameters @PatientID = ?", patient_id)
    row = cursor.fetchone()

    if row:
        # Assume the stored procedure returns age, gender, etc. as required
        age = row[0]
        gender = row[1]
        weight = row[2]
        height = row[3]
        diabetes = row[4]
        cholesterol = row[5]
        blood_pressure = row[6]
        pregnancy = row[7]

        # Process the input and predicted TSH value (For now, return the fetched data)
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
        }

        return jsonify(result), 200
    else:
        return jsonify({"message": "Patient not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)
