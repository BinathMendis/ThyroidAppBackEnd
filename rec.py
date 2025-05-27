from flask import Flask, request, jsonify
import joblib
import pandas as pd
from db_connection import get_db_connection  # Import the database connection function
from sklearn.preprocessing import LabelEncoder

# Load the saved model, label encoders, and scaler
model = joblib.load("food_recommendation_model45.pkl")
label_encoders = joblib.load("label_encoders45.pkl")
scaler = joblib.load("scaler45.pkl")

# Initialize Flask app
app = Flask(__name__)

# Function to preprocess and make prediction from input data
def predict_food_category(input_data):
    """
    Function to predict food category based on patient input data.
    """
    # Prepare the data (similar to the training process)
    patient_data = pd.DataFrame(input_data)

    # Encode categorical variables using the label encoder (if they are not already encoded)
    # Check and encode categorical columns if needed
    if 'Gender' in input_data:
        patient_data['Gender'] = label_encoders['Gender'].transform(patient_data['Gender'])
    
    if 'Diabetes (Y/N)' in input_data:
        # Handle True/False or 1/0 as necessary
        patient_data['Diabetes (Y/N)'] = patient_data['Diabetes (Y/N)'].replace({True: 'Y', False: 'N'})
        patient_data['Diabetes (Y/N)'] = label_encoders['Diabetes (Y/N)'].transform(patient_data['Diabetes (Y/N)'])
    
    if 'Cholesterol (Y/N)' in input_data:
        patient_data['Cholesterol (Y/N)'] = patient_data['Cholesterol (Y/N)'].replace({True: 'Y', False: 'N'})
        patient_data['Cholesterol (Y/N)'] = label_encoders['Cholesterol (Y/N)'].transform(patient_data['Cholesterol (Y/N)'])
    
    if 'Blood Pressure (Y/N)' in input_data:
        patient_data['Blood Pressure (Y/N)'] = patient_data['Blood Pressure (Y/N)'].replace({True: 'Y', False: 'N'})
        patient_data['Blood Pressure (Y/N)'] = label_encoders['Blood Pressure (Y/N)'].transform(patient_data['Blood Pressure (Y/N)'])
    
    if 'Pregnancy (Y/N)' in input_data:
        patient_data['Pregnancy (Y/N)'] = patient_data['Pregnancy (Y/N)'].replace({True: 'Y', False: 'N'})
        patient_data['Pregnancy (Y/N)'] = label_encoders['Pregnancy (Y/N)'].transform(patient_data['Pregnancy (Y/N)'])

    # Calculate BMI
    patient_data['BMI'] = patient_data['Weight (kg)'] / ((patient_data['Height (cm)'] / 100) ** 2)

    # Select features (including 'BMI') for the model
    features = [
        "Age", "Gender", "Weight (kg)", "Height (cm)", 
        "Diabetes (Y/N)", "Cholesterol (Y/N)", "Blood Pressure (Y/N)", 
        "Pregnancy (Y/N)", "TSH Report 1 (mIU/L)", "BMI"
    ]
    
    # Ensure the DataFrame has the same columns expected by the model
    X = patient_data[features]

    # Apply scaling
    X_scaled = scaler.transform(X)

    # Predict food category (This should match the model’s training categories)
    prediction = model.predict(X_scaled)

    return prediction[0]  # Return the predicted food category number

# API route to get food category prediction
@app.route('/predict_food_category', methods=['GET'])
def predict():
    # Retrieve patientID from query parameters
    patient_id = request.args.get('patientID')

    # Check if patientID is provided
    if not patient_id:
        return jsonify({"error": "patientID is required."}), 400

    # Retrieve input data by calling the stored procedure with patientID
    conn = get_db_connection()
    cursor = conn.cursor()

    # Execute stored procedure with patientID as a parameter
    try:
        cursor.execute("EXEC Food_GetPatientInputData @PatientID = ?", (patient_id,))
        result = cursor.fetchone()  # Assuming the SP returns one row of data
        
        if result:
            age = result[0]
            gender = result[1]  # Already encoded (1 for Male, 0 for Female)
            weight = result[2]
            height = result[3]
            diabetes = result[4]  # 1 for Yes, 0 for No
            cholesterol = result[5]  # 1 for Yes, 0 for No
            blood_pressure = result[6]  # 1 for Yes, 0 for No
            pregnancy = result[7]  # 1 for Yes, 0 for No
            tsh_report = result[8]  # The extra input parameter (TSH Report 1)
        else:
            return jsonify({"error": "No data returned for the given patientID."}), 404
    except Exception as e:
        return jsonify({"error": f"Error executing stored procedure: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()

    # Create the input data for prediction (using numerical values directly)
    input_data = {
        "Age": [age],
        "Gender": [gender],  # No encoding needed, already 1 for Male or 0 for Female
        "Weight (kg)": [weight],
        "Height (cm)": [height],
        "Diabetes (Y/N)": [diabetes],  # 1 for Yes, 0 for No
        "Cholesterol (Y/N)": [cholesterol],  # 1 for Yes, 0 for No
        "Blood Pressure (Y/N)": [blood_pressure],  # 1 for Yes, 0 for No
        "Pregnancy (Y/N)": [pregnancy],  # 1 for Yes, 0 for No
        "TSH Report 1 (mIU/L)": [tsh_report]
    }

    # Make food category prediction
    food_category = predict_food_category(input_data)

    # Convert predicted category back to food name (use label encoder for this)
    food_category_name = label_encoders['Food Category'].inverse_transform([food_category])[0]

    return jsonify({
        "patientID": patient_id,
        "age": age,
        "gender": gender,
        "weight": weight,
        "height": height,
        "diabetes": diabetes,
        "cholesterol": cholesterol,
        "blood_pressure": blood_pressure,
        "pregnancy": pregnancy,
        "tsh_report": tsh_report,
        "predicted_food_category": food_category_name
    })

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
