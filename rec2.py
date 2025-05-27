from flask import Flask, request, jsonify
import joblib
import numpy as np
from db_connection import get_db_connection  # Importing the DB connection helper

# Initialize Flask app
app = Flask(__name__)

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

@app.route('/get_food_recommendations', methods=['GET'])
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

    # Ensure all int64 values are converted to native Python int
    predicted_category = int(predicted_category)
    category_desc = [str(item) for item in category_desc]  # Ensure list elements are strings
    recommended_foods = [str(item) for item in recommended_foods]  # Ensure list elements are strings

    return jsonify({
        "predicted_category": predicted_category,
        "category_description": category_desc[0],
        "recommended_foods": recommended_foods
    })

if __name__ == '__main__':
    app.run(debug=True)
