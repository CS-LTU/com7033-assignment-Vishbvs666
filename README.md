# com7033-assignment-Vishbvs666
### **Student ID: 2415083**

# **StrokeCare — Secure Stroke Prediction & Patient Management System**
*A complete secure Flask web application developed for COM7033 — Secure Software Development.*

---

## **1. About the Project**

**StrokeCare** is a secure web application built using **Python Flask** to help hospitals manage patient information related to stroke prediction and prevention. It enables healthcare professionals to securely store, update, analyse, and predict stroke risk based on patient data.

The project follows the **COM7033 Assessment 1 Brief** requirements, including:
- Secure coding practices
- CRUD functionality
- Multi-database architecture using SQLite + MongoDB
- Ethical programming standards
- Intuitive and professional UI
- Testing and version control through GitHub

Stroke is currently the **second leading cause of death globally**, making early detection and prevention essential. This application provides a modern, secure, and predictive tool to help doctors identify high-risk patients before a medical emergency occurs.

---

## **2. Problem the Application Aims to Solve**

Hospitals often face several challenges with traditional or outdated stroke-risk tracking systems:

### **2.1 Outdated or Fragmented Systems**
Many hospitals use general-purpose EMRs that do not specialise in stroke prediction.

### **2.2 Manual, Error-Prone Data Handling**
Paper forms or Excel sheets:
- Can get lost or damaged
- Are easily misread
- Cannot automatically predict stroke risk

### **2.3 No Built-in Predictive Capability**
Clinicians must interpret multiple variables manually, which may delay identification of high-risk cases.

### **2.4 Security Risks**
Without secure authentication, encryption, role-based control, and input validation, patient data becomes vulnerable.

### **How StrokeCare Solves These Problems**
- Provides a **centralised, secure platform** for patient data
- Uses a **machine learning model** to automatically predict stroke risk
- Implements **strict authentication and role-based access**
- Separates databases to increase security
- Offers a **clean, modern, clinical-grade interface**

---

# **3. Key Features Breakdown (Detailed)**

## **3.1 Secure Authentication System (SQLite)**

The authentication module ensures only authorised hospital staff can access sensitive medical information.

### ✔ **Registration with Password Hashing**
- Passwords are hashed using **Werkzeug PBKDF2**, making the database secure even if compromised.
- Usernames and emails are validated before storage.

### ✔ **Login with Role Verification**
Three user roles:
- **Admin** — full access
- **Doctor** — patient CRUD + predictions
- **HCP** — basic access (optional)

Only permitted users can access protected routes.

### ✔ **Session Security**
- Secure cookies
- Expiry-based logout
- Prevents session hijacking or fixation

### ✔ **CSRF Protection**
All forms include CSRF tokens to block cross-site request forgery attacks.

---

## **3.2 Admin Dashboard — User Management (CRUD)**

Admins can manage all hospital staff accounts.

### ✔ **Create Users**
Add new doctors, admins, or HCPs securely. Validates inputs and stores hashed passwords.

### ✔ **View Users**
Displays a clean table with all registered staff.

### ✔ **Update Users**
Modify user roles or email details.

### ✔ **Delete Users**
Secure deletion with confirmation to prevent accidents.

This system demonstrates full CRUD functionality and professional access control.

---

## **3.3 Doctor Dashboard — Patient Management (CRUD with MongoDB)**

Doctors have full control over patient data.

### ✔ **Add New Patients**
Includes demographics, lifestyle, and medical history:
- Gender
- Age
- BMI
- Work type
- Hypertension
- Glucose levels
- Smoking status
- Marital status

### ✔ **View Patients**
List view shows:
- Patient details
- Stroke risk badge
- Update/delete buttons

### ✔ **Edit Patients**
Update any field with full validation. Model prediction recalculates automatically.

### ✔ **Delete Patients**
Secure record deletion with confirmation dialogue.

This module is essential for everyday hospital operations.

---

## **3.4 Integrated Machine Learning Stroke Prediction**

An ML model helps doctors identify high-risk patients instantly.

### **Dataset:**
Kaggle Stroke Prediction Dataset (public, anonymised).

### **Model Training Process:**
1. Clean missing values
2. One-hot encode categories
3. Normalize numeric data
4. Handle class imbalance
5. Train **RandomForestClassifier**
6. Export using joblib
7. Load model inside Flask

### **Prediction Output:**
Probability score → converted to:
- **Low risk**
- **Medium risk**
- **High risk**

Displayed clearly in the UI with colour-coded badges.

---

## **3.5 Dual Database Architecture (SQLite + MongoDB)**

### ✔ **SQLite for Authentication**
Stores:
- Usernames
- Emails
- Hashed passwords
- Roles

Lightweight and secure for identity management.

### ✔ **MongoDB for Patient Data**
Stores:
- Complete patient profiles
- Medical and lifestyle details
- Prediction results

### **Why separate databases?**
- Enhances security
- Prevents cross-contamination of sensitive data
- Supports scalability
- Follows industry best practices

---

## **3.6 Security Features Implemented**

StrokeCare emphasises security from top to bottom.

### 🔒 Password Hashing
Prevents plain-text credentials.

### 🔒 Input Validation
Blocks malicious or malformed input.

### 🔒 CSRF Protection
Ensures all POST requests are trustworthy.

### 🔒 Secure Sessions
Cookies are HttpOnly and expire automatically.

### 🔒 Error Handling
No sensitive information revealed to users.

### 🔒 No Sensitive Data in URLs
Prevents attacks via query strings.

### 🔒 Access Control Enforcement
Each route checks user role before executing.

---

## **3.7 Professional User Interface (Violet Theme)**

The UI is designed with:
- Modern violet theme
- Clean spacing and typography
- Responsive Bootstrap layout
- Intuitive navigation for clinicians
- Clear buttons and action labels
- Confirmation modals to prevent accidental actions

The design aesthetic is calm, professional, and suitable for healthcare environments.

---

## **3.8 Testing**

Tests ensure functional reliability and security.

### ✔ Authentication Tests
- Registration
- Login
- Invalid credentials

### ✔ Patient CRUD Tests
- Insert
- Update
- Delete

### ✔ ML Model Tests
- Model loading
- Feature processing
- Prediction response

Run using:

---

## **3.9 Ethical Considerations**

StrokeCare respects medical ethics and data privacy.

### ✔ Public dataset only
No real patient data used.

### ✔ No logs containing sensitive data
Error logs omit patient information.

### ✔ Proper access control
Only authorised users can view or edit patient information.

### ✔ Professional and secure coding
Follows secure design principles outlined in the COM7033 brief.

---

# **4. Installation & Running the Application**

python3 -m venv venv
source venv/bin/activate


pip install -r requirements.txt


instance/config.py


python run.py

http://127.0.0.1:5000


### **1. Clone the Repository**
```bash
git clone https://github.com/CS-LTU/com7033-assignment-Vishbvs666
cd StrokeCare

**Generative AI Declaration:**
I used generative AI (ChatGPT) for debugging assistance and for preparing project documentation, including explanations, planning, and editing.
