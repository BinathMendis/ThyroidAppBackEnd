from flask import Blueprint, Flask, request, jsonify
import joblib
import numpy as np
import time
import re
import ollama
from flask_cors import CORS  # Import Flask-CORS
from db_connection import get_db_connection  # Importing the DB connection helper

# Initialize Flask app
rec_bp = Blueprint("rec", __name__)

# Load the model, scaler, and label encoders
model = joblib.load("food_recommendation_model_medical.pkl")  # Model for food recommendations
scaler = joblib.load("scaler_medical.pkl")  # Scaler for input data
label_encoders = joblib.load("label_encoders_medical.pkl")  # Label encoders for categorical features

# Define Category Identifier
Category_identifier = {
    1: ["Low BMI & Low TSH"],
    2: ["Low BMI & Normal TSH"],
    3: ["Low BMI & High TSH"],
    4: ["Normal BMI & Low TSH"],
    5: ["Normal BMI & Normal TSH"],
    6: ["Normal BMI & High TSH"],
    7: ["High BMI & Low TSH"],
    8: ["High BMI & Normal TSH"],
    9: ["High BMI & High TSH"]
}

# Define Food Recommendations
food_recommendations = {
    1: ["Chicken curry", "Fish ambul thiyal", "Rice", "Coconut sambol", "Gotu kola salad", "Cowpea curry", "Papaya", "Yogurt", "Bananas", "Green gram porridge"],
    2: ["Mutton curry", "Parippu (lentils)", "Jackfruit curry", "Kiri bath", "Mango", "Wood apple juice", "Coconut roti", "Milk rice", "Fresh curd", "Eggs"],
    3: ["Beef curry", "Red rice", "Pumpkin curry", "Winged bean stir-fry", "Coconut milk", "Kurakkan roti", "Pineapple", "Butter", "Cheese", "Banana porridge"],
    4: ["Fish curry", "String hoppers", "Pol sambol", "Dhal curry", "Papaya", "Fresh coconut", "Gotu kola sambol", "Yogurt", "Green beans stir-fry", "Chicken liver curry"],
    5: ["Rice and curry", "Boiled vegetables", "Egg hoppers", "Avocado juice", "Herbal porridge", "Grilled fish", "Cowpea salad", "Buffalo curd", "Coconut water", "Pineapple curry"],
    6: ["Red rice", "Mushroom curry", "Brinjal moju", "Lentil soup", "Jackfruit stir-fry", "Sprouted mung beans", "Butter", "Fresh milk", "Chicken soup", "Banana smoothie"],
    7: ["Grilled fish", "Vegetable soup", "Herbal tea", "Steamed vegetables", "Green gram curry", "Gotu kola porridge", "Bitter gourd salad", "Yogurt", "Low-fat cheese", "Guava"],
    8: ["Boiled manioc", "Stir-fried vegetables", "Lean chicken curry", "Black tea", "Red rice", "Wood apple smoothie", "Spinach curry", "Fresh coconut water", "Grilled prawns", "Eggplant curry"],
    9: ["Brown rice", "Kidney bean curry", "Mushroom soup", "Vegetable porridge", "Low-fat curd", "Herbal tea", "Bitter gourd stir-fry", "Pumpkin seeds", "Coconut milk stew", "Pineapple curry"]
}

# Helper function to fetch data using the stored procedure
def fetch_patient_data(patient_id):
    conn = get_db_connection()  # Get database connection from db_connection.py
    cursor = conn.cursor()
    cursor.execute("EXEC Food_GetPatientInputData @PatientID=?", patient_id)
    
    # Fetch the first row of data
    row = cursor.fetchone()
    conn.close()
    
    if row:
        # Return the data as a dictionary
        return {
            "Age": row.Age,
            "Gender": row.Gender,
            "Weight": row.Weight,
            "Height": row.Height,
            "Diabetes": row.Diabetes,
            "Cholesterol": row.Cholesterol,
            "BloodPressure": row.BloodPressure,
            "Pregnancy": row.Pregnancy,
            "TSH": row.input_parameter
        }
    else:
        return None

# Function to predict food category and recommendations
def predict_food_category(age, gender, tsh_value, weight, height, diabetes, cholesterol, bp, pregnancy):
    # Encode gender
    gender_encoded = label_encoders["Gender"].transform([gender])[0]
    
    # Calculate BMI
    bmi = weight / ((height / 100) ** 2)

    # Prepare the input features for scaling
    input_features = np.array([[age, gender_encoded, tsh_value, bmi, diabetes, cholesterol, bp, pregnancy]])

    # Scale the input features
    scaled_input = scaler.transform(input_features)
    
    # Predict the food category using the trained model
    predicted_category = model.predict(scaled_input)[0]

    # Retrieve the category description and recommended foods
    category_description = Category_identifier.get(predicted_category, ["Unknown Category"])
    recommended_foods = food_recommendations.get(predicted_category, ["No recommendations available"])

    return predicted_category, category_description, recommended_foods

# Function to get clinical advice based on recommended foods
def get_clinical_advice(recommended_foods, medical_conditions):
    print("Fetching clinical advice, please wait...")
    time.sleep(2)

    # Constructing the prompt for the Llama model
    prompt = f"""
    You are a clinical nutrition expert. Provide detailed advice on how to incorporate the following foods into a diet: {', '.join(recommended_foods)}.
    
    Consider the following medical conditions:
    - BMI: {medical_conditions.get('BMI', 'Unknown')}
    - Diabetes: {'Yes' if medical_conditions.get('Diabetes') else 'No'}
    - Cholesterol: {'Yes' if medical_conditions.get('Cholesterol') else 'No'}
    - Blood Pressure: {'Yes' if medical_conditions.get('Blood Pressure') else 'No'}
    - Pregnancy: {'Yes' if medical_conditions.get('Pregnancy') else 'No'}
    - TSH Level: {medical_conditions.get('TSH Report 1 (mIU/L)', 'Unknown')} mIU/L

    For each food, provide the following:
    --Give Clinical Advice for the patient to follow when consuming the food item with TSH level of the patient and BMI. 
    --Get the medical conditions of a patient to give overall advice to this part. 
    --Provide a detailed explanation of the benefits of the food item for the patient.

    """

    # Send the prompt to the Llama model (assuming `ollama.chat` is the method to communicate with Llama)
    response = ollama.chat(model="deepseek-r1:1.5b", messages=[{"role": "user", "content": prompt}])
    advice = response['message']['content']

    # Remove any <think> tags and their content from the response
    advice_cleaned = re.sub(r"<think>.*?</think>", "", advice, flags=re.DOTALL).strip()
    advice_cleaned = re.sub(r"[*#]", "", advice_cleaned).strip()
    advice_cleaned = re.sub(r"(?m)^\s*-\s*", "", advice_cleaned).strip()

    return advice_cleaned

# Function to insert prediction and clinical advice into the database
def insert_prediction_and_advice(patient_id, predicted_category, category_description, recommended_foods, clinical_advice):
    conn = get_db_connection()  # Get the database connection
    cursor = conn.cursor()

    # Prepare the SQL command to execute the stored procedure
    cursor.execute("""
        EXEC InsertPredictionAndAdvice 
            @PatientID = ?, 
            @PredictedCategory = ?, 
            @CategoryDescription = ?, 
            @RecommendedFoods = ?, 
            @ClinicalAdvice = ?
    """, (patient_id, predicted_category, category_description, ', '.join(recommended_foods), clinical_advice))

    # Commit the transaction
    conn.commit()
    cursor.close()
    conn.close()

@rec_bp.route('/food_recommendations', methods=['GET'])
def get_food_recommendations():
    # Fetch the patient_id from query parameters
    patient_id = request.args.get('patient_id')
    
    if not patient_id:
        return jsonify({"error": "Patient ID is required"}), 400
    
    # Fetch patient data from the database using the stored procedure
    patient_data = fetch_patient_data(patient_id)
    
    if not patient_data:
        return jsonify({"error": "Patient not found"}), 404

    # Use the patient data to get food recommendations
    predicted_category, category_desc, recommended_foods = predict_food_category(
        patient_data["Age"], patient_data["Gender"], patient_data["TSH"], patient_data["Weight"],
        patient_data["Height"], patient_data["Diabetes"], patient_data["Cholesterol"],
        patient_data["BloodPressure"], patient_data["Pregnancy"]
    )

    # Get clinical advice based on the recommended foods and patient medical conditions
    medical_conditions = {
        'BMI': 'Normal',
        'Diabetes': patient_data["Diabetes"],
        'Cholesterol': patient_data["Cholesterol"],
        'Blood Pressure': patient_data["BloodPressure"],
        'Pregnancy': patient_data["Pregnancy"],
        'TSH Report 1 (mIU/L)': patient_data["TSH"]
    }
    advice = get_clinical_advice(recommended_foods, medical_conditions)

    # Ensure all int64 values are converted to native Python int
    predicted_category = int(predicted_category)
    category_desc = [str(item) for item in category_desc]  # Ensure list elements are strings
    recommended_foods = [str(item) for item in recommended_foods]  # Ensure list elements are strings

    # Insert prediction and clinical advice into the database
    insert_prediction_and_advice(patient_id, predicted_category, category_desc[0], recommended_foods, advice)

    return jsonify({
        "predicted_category": predicted_category,
        "category_description": category_desc[0],
        "recommended_foods": recommended_foods,
        "clinical_advice": advice
    })
