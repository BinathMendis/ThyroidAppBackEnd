# Create a new file called tsh_history.py
from flask import Blueprint, request, jsonify, current_app
from db_connection import get_db_connection

tsh_history_bp = Blueprint('tsh_history', __name__)

@tsh_history_bp.route('/tsh-history', methods=['GET'])
def get_tsh_history():
    try:
        patient_id = request.args.get('patientID')
        
        if not patient_id:
            return jsonify({'error': 'PatientID is required'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Execute the stored procedure
        cursor.execute("EXEC [dbo].[GetTSHHistory] @PatientID = ?", patient_id)
        
        # Fetch all results
        rows = cursor.fetchall()
        
        # Convert to list of dictionaries
        history = []
        for row in rows:
            history.append({
                'id': row[0],
                'patientID': row[1],
                'predictedTime': row[2].isoformat() if row[2] else None,
                'diseaseID': row[3],
                'predictedTSHValue': float(row[4]) if row[4] is not None else None,
                'loggedDate': row[5].isoformat() if row[5] else None,
                'upWeight': float(row[6]) if row[6] is not None else None,
                'upHeight': float(row[7]) if row[7] is not None else None,
                'sequence': row[8],
                'enteredTSHValue': float(row[9]) if row[9] is not None else None
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({'tshHistory': history})
    
    except Exception as e:
        current_app.logger.error(f"Error fetching TSH history: {str(e)}")
        return jsonify({'error': 'Failed to fetch TSH history'}), 500