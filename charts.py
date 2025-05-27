from flask import Flask, jsonify,Blueprint
import pyodbc
from flask_cors import CORS
from db_connection import get_db_connection

chart_bp = Blueprint("chart", __name__)

@chart_bp.route("/api/patient_trends/<string:patient_id>", methods=["GET"])
def get_patient_trends(patient_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("EXEC GetPatientTrends ?", patient_id)
        rows = cursor.fetchall()
        
        trends = []
        for row in rows:
            trends.append({
                "date": row.date,
                "tsh_value": float(row.tsh_value),
                "weight": float(row.weight)
            })
        
        return jsonify(trends)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    finally:
        cursor.close()
        conn.close()
