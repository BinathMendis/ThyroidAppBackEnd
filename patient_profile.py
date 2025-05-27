from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequest
import pyodbc
from datetime import datetime
from db_connection import get_db_connection

patient_profile_bp = Blueprint('patient_profile', __name__)


@patient_profile_bp.route('/first-login', methods=['GET'])
def check_first_login():
    # In a real app, you would check the user's status in the database
    # This is a simplified version
    patient_id = request.args.get('patient_id')  # Assuming user ID is passed in headers
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("EXEC CheckFirstLogin @PatientID=?", (patient_id,))
    result = cursor.fetchone()
    print(f"Check first login for patient ID: {patient_id}, result: {result}")
    conn.close()
    
    if result and result[0] == 1:
        return jsonify({'isFirstLogin': True})
    return jsonify({'isFirstLogin': False})

@patient_profile_bp.route('/profile', methods=['POST'])
def update_patient_profile():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['patient_id', 'age', 'gender', 'weight', 'height', 'tshLevel']
        for field in required_fields:
            if field not in data:
                raise BadRequest(f"Missing required field: {field}")
        
        # Prepare data for stored procedure
        patient_id = data['patient_id']
        current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"Updating profile for patient ID: {patient_id} at {current_date}")
        conn = get_db_connection()
        cursor = conn.cursor()

        print(f"Data received for profile update: {data}")
        
        # Call stored procedure to update patient profile
        cursor.execute(
            "EXEC UpdatePatientProfile "
            "@PatientID=?, @Age=?, @Gender=?, @Weight=?, @Height=?, "
            "@HasPressure=?, @HasDiabetes=?, @HasCholesterol=?, "
            "@IsPregnant=?, @TSHLevel=?, @UpdateDate=?",
            (
                patient_id,
                data['age'],
                data['gender'],
                data['weight'],
                data['height'],
                data.get('hasPressure', False),
                data.get('hasDiabetes', False),
                data.get('hasCholesterol', False),
                data.get('isPregnant', False),
                data['tshLevel'],
                current_date
            )
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Profile updated successfully'})
    
    except BadRequest as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500