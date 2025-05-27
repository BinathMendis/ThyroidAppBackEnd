from datetime import datetime
from flask import Blueprint, Flask, request, jsonify
import pyodbc
from db_connection import get_db_connection

personal_bp = Blueprint("personaldata", __name__)

@personal_bp.route('/profile-data', methods=['GET'])
def get_patient_profile():
    try:
        patient_id = request.args.get('patient_id')
        if not patient_id:
            raise BadRequest("Patient ID is required")

        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Execute stored procedure to get profile
        cursor.execute(
            "EXEC GetPatientProfileNew @PatientID=?",
            (patient_id,)
        )
        
        # Get column names from cursor description
        columns = [column[0] for column in cursor.description]
        profile_data = cursor.fetchone()
        
        conn.close()
        
        if not profile_data:
            return jsonify({
                'success': False,
                'message': 'Profile not found',
                'profile': None
            }), 404
            
        # Convert to dictionary
        profile_dict = dict(zip(columns, profile_data))
        
        # Convert SQL Server bit to Python bool
        bool_fields = [
            'HasPressure', 'HasDiabetes', 
            'HasCholesterol', 'IsPregnant'
        ]
        for field in bool_fields:
            if field in profile_dict:
                profile_dict[field] = bool(profile_dict[field])
        
        return jsonify({
            'success': True,
            'profile': {
                'age': profile_dict.get('Age'),
                'gender': profile_dict.get('Gender') or 'male',
                'weight': profile_dict.get('Weight'),
                'height': profile_dict.get('Height'),
                'hasPressure': profile_dict.get('HasPressure', False),
                'hasDiabetes': profile_dict.get('HasDiabetes', False),
                'hasCholesterol': profile_dict.get('HasCholesterol', False),
                'isPregnant': profile_dict.get('IsPregnant', False),
                'tshLevel': profile_dict.get('TSHLevel'),
                'lastUpdated': profile_dict.get('UpdateDate')
            }
        })
        
    except pyodbc.Error as db_error:
        return jsonify({
            'success': False,
            'message': f"Database error: {str(db_error)}"
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Unexpected error: {str(e)}"
        }), 500
    


    
@personal_bp.route('/profile-update', methods=['POST'])
def update_patient_profile():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = [
            'patient_id', 'age', 'gender', 
            'weight', 'height', 'tshLevel'
        ]
        missing_fields = [
            field for field in required_fields 
            if field not in data
        ]
        
        if missing_fields:
            raise BadRequest(
                f"Missing required fields: {', '.join(missing_fields)}"
            )
        
        # Prepare data for stored procedure
        current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Call stored procedure to update patient profile
        cursor.execute(
            "EXEC UpdatePatientProfile "
            "@PatientID=?, @Age=?, @Gender=?, @Weight=?, @Height=?, "
            "@HasPressure=?, @HasDiabetes=?, @HasCholesterol=?, "
            "@IsPregnant=?, @TSHLevel=?, @UpdateDate=?",
            (
                data['patient_id'],
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
        
        # Get the updated profile to return
        cursor.execute(
            "EXEC GetPatientProfileNew @PatientID=?",
            (data['patient_id'],)
        )
        columns = [column[0] for column in cursor.description]
        updated_profile = cursor.fetchone()
        
        conn.close()
        
        if not updated_profile:
            return jsonify({
                'success': False,
                'message': 'Profile not found after update'
            }), 404
            
        profile_dict = dict(zip(columns, updated_profile))
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'profile': {
                'age': profile_dict.get('Age'),
                'gender': profile_dict.get('Gender'),
                'weight': profile_dict.get('Weight'),
                'height': profile_dict.get('Height'),
                'hasPressure': bool(profile_dict.get('HasPressure', False)),
                'hasDiabetes': bool(profile_dict.get('HasDiabetes', False)),
                'hasCholesterol': bool(profile_dict.get('HasCholesterol', False)),
                'isPregnant': bool(profile_dict.get('IsPregnant', False)),
                'tshLevel': profile_dict.get('TSHLevel'),
                'lastUpdated': profile_dict.get('UpdateDate')
            }
        })
    
    except pyodbc.Error as db_error:
        return jsonify({
            'success': False,
            'message': f"Database error: {str(db_error)}"
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Unexpected error: {str(e)}"
        }), 500