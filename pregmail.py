from flask import Blueprint, current_app, request, jsonify
from flask_mail import Message
from flask_mail import Mail
import base64
from db_connection import get_db_connection

email_bp = Blueprint('email', __name__)

mail = Mail()

def get_patient_email(patient_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("EXEC [preg].[GetPatientEmail] @patientID = ?", patient_id)
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        return row[0]
    return None

@email_bp.route('/send-email', methods=['POST'])
def send_email():

    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data received'}), 400
        
        patient_id = data.get('patientID')
        pdf_base64 = data.get('pdfBase64')
        email = data.get('email')  # Try to get email from input

        print("ID:", patient_id)

        if not patient_id or not pdf_base64:
            return jsonify({'error': 'Missing required fields'}), 400

        # If email not provided in JSON, get it from the DB using patientID
        if not email:
            email = get_patient_email(patient_id)
            if not email:
                return jsonify({'error': 'Email not found for patient'}), 404

        # Clean and decode PDF base64
        if isinstance(pdf_base64, str) and pdf_base64.startswith('data:'):
            pdf_base64 = pdf_base64.split(',')[1]

        try:
            pdf_data = base64.b64decode(pdf_base64)
        except Exception as e:
            return jsonify({'error': f'Invalid PDF data: {str(e)}'}), 400

        # Create and send email
        msg = Message(
            subject="High Risk Patient Report",
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[email],
            body="Please find attached your pregnancy thyroid risk assessment report."
        )
        msg.attach("report.pdf", "application/pdf", pdf_data)
        mail.send(msg)
        
        return jsonify({'message': f'Email sent to {email} successfully!'})

    except Exception as e:
        current_app.logger.error(f"Email sending error: {str(e)}")
        return jsonify({'error': f'Failed to send email: {str(e)}'}), 500
