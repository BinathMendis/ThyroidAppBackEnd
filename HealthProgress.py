# app.py
from flask import Flask, request, jsonify,Blueprint
import pyodbc
from datetime import datetime
from db_connection import get_db_connection

health_bp = Blueprint("health", __name__)

# Database configuration

@health_bp.route('/api/tsh-records', methods=['POST'])
def add_tsh_record():
    data = request.json
    patient_id = data['patientId']
    entry_date = data['entryDate']
    current_weight = data['currentWeight']
    tsh_value = data['tshValue']
    target_tsh_value = data['targetTSHValue']  # Now passed from frontend
    notes = data.get('notes', '')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            EXEC InsertTSHRecord 
            @PatientID=?, 
            @EntryDate=?, 
            @CurrentWeight=?, 
            @TSHValue=?, 
            @TargetTSHValue=?, 
            @Notes=?
            """,
            (patient_id, entry_date, current_weight, tsh_value, target_tsh_value, notes))
        
        record_id = cursor.fetchval()
        conn.commit()
        
        return jsonify({
            'success': True,
            'recordId': record_id
        }), 201
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@health_bp.route('/api/tsh-records/<int:patient_id>', methods=['GET'])
def get_tsh_records(patient_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("EXEC GetPatientTSHRecords @PatientID=?", (patient_id,))
        columns = [column[0] for column in cursor.description]
        records = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        return jsonify({
            'success': True,
            'records': records
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()
