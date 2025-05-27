from flask import Blueprint, request, jsonify
import joblib
import pandas as pd
from db_connection import get_db_connection

preg_bp = Blueprint("pregnancy", __name__, url_prefix="/pregnancy")
model = joblib.load('pregnancy_risk_model2.joblib')


def preprocess_input(data: pd.DataFrame) -> pd.DataFrame:
    required_cols = ['TPOAb', 'TgAb', 'TSHRAB', 'Age', 'Smoker', 'Family_History']
    missing = [c for c in required_cols if c not in data.columns]
    if missing:
        raise ValueError(f'Missing columns: {", ".join(missing)}')

    for col in ['TPOAb', 'TgAb', 'TSHRAB', 'Age']:
        data[col] = pd.to_numeric(data[col], errors='coerce')
    data['Smoker'] = data['Smoker'].map({'No': 0, 'Yes': 1})
    data['Family_History'] = data['Family_History'].map({'No': 0, 'Yes': 1})

    return data[required_cols]


def insert_prediction_to_db(data: dict, prediction: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            EXEC preg.InsertPregnancyRisk 
              @Patient_ID=?, @TPOAb=?, @TgAb=?, @TSHRAB=?, @Age=?, 
              @Smoker=?, @Family_History=?, @Predicted_Risk=?
            """,
            data['Patient_ID'], data['TPOAb'], data['TgAb'], data['TSHRAB'],
            data['Age'], data['Smoker'], data['Family_History'], prediction
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()


@preg_bp.route('/patient/<string:patient_id>', methods=['GET'])
def get_patient_details(patient_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("EXEC preg.GetBasicPatientDetails @PatientID=?", patient_id)
        row = cursor.fetchone()
        if not row:
            return jsonify({'error': 'Patient not found'}), 404

        cols = [col[0] for col in cursor.description]
        patient_data = dict(zip(cols, row))
        return jsonify(patient_data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@preg_bp.route('/predict', methods=['POST'])
def predict():
    try:
        payload = request.get_json()
        df = pd.DataFrame([payload])
        df_proc = preprocess_input(df)
        prediction = model.predict(df_proc)[0]
        risk = int(prediction)

        # prepare insert data
        insert_data = df_proc.iloc[0].to_dict()
        insert_data['Patient_ID'] = payload['Patient_ID']
        insert_prediction_to_db(insert_data, risk)

        return jsonify({'predicted_risk': risk}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
