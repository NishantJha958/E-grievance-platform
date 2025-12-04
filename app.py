# =================================================================
# PYTHON BACKEND CODE (USING FLASK FRAMEWORK)
# Filename: app.py
# Final version: Includes Server-Side Validation, Official Login, AI Routing, and CORS
# =================================================================

from flask import Flask, request, jsonify
from flask_cors import CORS 
import time
import random
import logging
import re # <-- Import the regex module for validation

app = Flask(__name__)
CORS(app) 
logging.basicConfig(level=logging.INFO)

# --- MOCK DATA STORES & MAPPING ---
OFFICER_WORKLOADS = {
    'Officer_A_Water': 12, 
    'Officer_B_Water': 5,  
    'Officer_C_Roads': 9,
    'Officer_D_Roads': 15, 
}

DEPARTMENT_MAPPING = {
    'Road Maintenance': 'Public_Works_Dept',
    'Water Supply': 'Water_Supply_Dept',
    'Sanitation': 'Sanitation_Dept',
    'Public Safety': 'Law_Enforcement_Dept',
    'Illegal Construction': 'Town_Planning_Dept',
    'Public Transport': 'Transport_Dept',
    'Health Services': 'Health_Dept',
    'Education Facilities': 'Education_Dept',
    'Noise Pollution': 'Environment_Dept',
    'Electricity': 'Power_Dept',
    'Drainage': 'Water_Supply_Dept',
    'Parks': 'Urban_Development_Dept',
    'Document Delays': 'General_Admin_Dept',
    'Official Misconduct': 'Vigilance_Dept',
    'Animal Control': 'Animal_Control_Dept',
    'Tree Felling': 'Environment_Dept',
    'Traffic Signals': 'Traffic_Police_Dept',
    'Taxes': 'Revenue_Dept',
    'Social Welfare': 'Social_Welfare_Dept',
    'Cyber': 'IT_Dept',
    'Other': 'General_Admin_Dept'
}

# --- MOCK OFFICIAL DATABASE (For Login/Security) ---
OFFICIALS_DB = {
    "john.doe@gov.in": {  # <--- CHANGE this USERNAME
        "password_hash": "hashed_password_doe", # <--- CHANGE this MOCK PASSWORD
        "govt_id": "GOV1001A", # <--- CHANGE this GOVT ID
        "department": "Water_Supply_Dept",
        "name": "John Doe"
    },
    "sara.smith@gov.in": { # <--- CHANGE this USERNAME
        "password_hash": "hashed_password_smith", # <--- CHANGE this MOCK PASSWORD
        "govt_id": "GOV2002B", # <--- CHANGE this GOVT ID
        "department": "Public_Works_Dept",
        "name": "Sara Smith"
    }
}

# --- VALIDATION HELPER FUNCTION ---

def validate_citizen_input(data):
    """Performs strict server-side validation on core fields."""
    phone = data.get('phone', '')
    public_id = data.get('public_id', '')
    email = data.get('email', '')
    
    errors = {}

    # 1. Phone Number Check (Must be exactly 10 digits)
    # Regex: ^\d{10}$ ensures start (^), 10 digits (\d{10}), and end ($)
    if not re.fullmatch(r'^\d{10}$', phone):
        errors['phone'] = "Phone number must be exactly 10 digits."

    # 2. Public ID Check (Must be 10, 11, or 12 characters, alphanumeric)
    # Regex: [0-9A-Z] allows digits and uppercase letters
    if not re.fullmatch(r'^[0-9A-Z]{10,12}$', public_id):
        errors['public_id'] = "Public ID must be 10 to 12 alphanumeric characters."

    # 3. Basic Email Format Check
    # A standard regex check for email format
    if not re.fullmatch(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        errors['email'] = "Invalid email format."
        
    return errors

# --- AI PROCESSING & ROUTING LOGIC (UNCHANGED) ---

def generate_unique_id():
    """Generates a unique tracking ID."""
    return f"GRV-{int(time.time() * 1000) % 1000000}"

def ai_categorize_and_score(description, citizen_category):
    """MOCK AI function: Categorizes and assigns Priority Score (P: 1-10)."""
    keywords = description.lower()
    
    if 'pothole' in keywords or 'cracked road' in keywords:
        refined_category = 'Pothole_Major'
    elif 'leakage' in keywords or 'no water' in keywords:
        refined_category = 'Water_Leakage_Critical'
    else:
        refined_category = citizen_category
        
    critical_keywords_found = len([word for word in ['dangerous', 'urgent', 'fatal', 'flooding'] if word in keywords])
    
    priority_score = 3 + random.randint(0, 2) + critical_keywords_found * 2 
    
    if 'critical' in refined_category.lower() or 'safety' in citizen_category.lower():
        priority_score += 2
        
    priority_score = min(10, priority_score)
    
    return refined_category, priority_score

def smart_route_and_assign(refined_category, priority_score, location_coords):
    """Routes the complaint based on category, location, and load."""
    
    base_category = refined_category.split('_')[0] 
    target_department = DEPARTMENT_MAPPING.get(base_category, 'General_Admin_Dept')
    
    dept_prefix = target_department.split('_')[0]
    department_officers = {
        k: v for k, v in OFFICER_WORKLOADS.items() if k.endswith(dept_prefix.split('_')[0])
    }
    
    if not department_officers:
        return target_department, f"{target_department}_Manager"

    # Priority Override: If P >= 8, route to Manager immediately.
    if priority_score >= 8:
        return target_department, f"{target_department}_Manager"
    
    # Load Balancing: Find the least busy officer
    assigned_officer = min(department_officers, key=department_officers.get)
    
    OFFICER_WORKLOADS[assigned_officer] += 1
    
    return target_department, assigned_officer

# --- API ENDPOINTS ---

@app.route('/api/submit_complaint', methods=['POST'])
def submit_complaint():
    """Endpoint for citizen submission."""
    try:
        complaint_data = request.json
        
        # --- SERVER-SIDE VALIDATION CHECK ---
        validation_errors = validate_citizen_input(complaint_data)
        if validation_errors:
            logging.warning(f"Validation failed for citizen submission: {validation_errors}")
            # Return 400 Bad Request with specific errors
            return jsonify({
                "success": False, 
                "message": "One or more input fields failed server validation.",
                "errors": validation_errors
            }), 400
        # -----------------------------------

        tracking_id = generate_unique_id()
        
        # 1. AI Processing
        refined_category, priority_score = ai_categorize_and_score(
            complaint_data.get('description', ''),
            complaint_data.get('category', 'Other')
        )
        
        # 2. Smart Routing
        target_department, assigned_officer = smart_route_and_assign(
            refined_category, 
            priority_score, 
            complaint_data.get('location_coords', 'N/A')
        )
        
        logging.info(f"New Complaint [{tracking_id}] | P={priority_score} | Assigned to {assigned_officer}")
        
        return jsonify({
            "success": True, 
            "tracking_id": tracking_id,
            "status": "Under Review",
            "assigned_to": assigned_officer,
            "priority": priority_score 
        }), 200

    except Exception as e:
        logging.error(f"Error processing complaint: {e}")
        return jsonify({"success": False, "message": f"Server Error: {str(e)}"}), 500


@app.route('/api/official/login', methods=['POST'])
def official_login():
    """Authenticates the official using Username/Password + Unique Govt ID."""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    govt_id = data.get('govt_id')
    
    if not username or not password or not govt_id:
        return jsonify({
            "success": False, 
            "message": "Missing required fields (Username, Password, Govt ID)."
        }), 400

    official_record = OFFICIALS_DB.get(username)
    
    if not official_record:
        return jsonify({
            "success": False, 
            "message": "Authentication failed: Invalid credentials."
        }), 401

    if official_record['password_hash'] != f"hashed_password_{username.split('@')[0].split('.')[-1]}":
        return jsonify({
            "success": False, 
            "message": "Authentication failed: Invalid credentials."
        }), 401
    
    if official_record['govt_id'] != govt_id:
        logging.warning(f"Failed Govt ID validation attempt for user: {username}")
        return jsonify({
            "success": False, 
            "message": "Authentication failed: Unique Government ID mismatch."
        }), 401

    session_token = f"JWT.{official_record['department']}.{hash(username)}"
    
    logging.info(f"Official {official_record['name']} ({official_record['department']}) logged in successfully.")

    return jsonify({
        "success": True, 
        "message": "Login successful.",
        "token": session_token,
        "department": official_record['department'],
        "official_name": official_record['name']
    }), 200


if __name__ == '__main__':
    # Ensure you run 'pip install Flask flask-cors'
    app.run(debug=True, port=5000)