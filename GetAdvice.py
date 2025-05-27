from flask import Blueprint,Flask, request, jsonify , make_response
import pyodbc
from db_connection import get_db_connection
from flask_cors import CORS  # Import Flask-CORS

advice_bp = Blueprint("advice", __name__)


@advice_bp.route('/get_clinical_advice', methods=['GET'])
def get_clinical_advice():
    # Retrieve the patientID from query parameters
    patient_id = request.args.get('patient_id') 

    if not patient_id:
        return jsonify({"error": "Patient ID is required"}), 400

    # Establish database connection
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Execute the stored procedure
        cursor.execute("EXEC GetClinicalAdvice @PatientID=?", patient_id)
        result = cursor.fetchall()

        if len(result) == 0:
            return jsonify({"message": "No clinical advice found for the given patient ID"}), 404

        # Process the result into a dictionary (assuming clinical advice is the first column in the result)
        advice = result[0][0]  # Modify based on your SP's result structure

        # Create response and disable caching
        response = make_response(jsonify({"clinical_advice": advice}), 200)
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, proxy-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'

        return response

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()

@advice_bp.route('/get_patient_history', methods=['GET'])
def get_patient_history():
    # Retrieve the patientID from query parameters (for GET requests)
    patient_id = request.args.get('patient_id')
    
    # If not in query params, try to get from JSON body
    if not patient_id and request.is_json:
        data = request.get_json()
        patient_id = data.get('patient_id')

    if not patient_id:
        return jsonify({"error": "Patient ID is required"}), 400

    # Establish database connection
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Get clinical advice history using stored procedure
        cursor.execute("EXEC GetClinicalAdviceHistory @PatientID=?", patient_id)
        
        # Get column names from cursor description
        columns = [column[0] for column in cursor.description]
        clinical_advices = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # Create response
        response_data = {
            "clinical_advices": clinical_advices,
        }

        if not clinical_advices:
            return jsonify({"message": "No history found for the given patient ID", "patient_id": patient_id}), 404

        response = make_response(jsonify(response_data), 200)
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, proxy-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'

        return response

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    finally:
        cursor.close()
        conn.close()