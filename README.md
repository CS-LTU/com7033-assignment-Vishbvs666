# StrokeCare — Secure Stroke Prediction & Patient Management System  
**Module:** COM7033 – Secure Software Development  
**Student ID:** 2415083  

---

## 1. About the Project

**StrokeCare** is a secure web-based application developed using **Python Flask** to support hospitals and healthcare professionals in managing patient data related to **stroke risk assessment and prevention**.

The system enables authorised users to securely:
- Record and manage patient demographic, lifestyle, and medical information
- Predict stroke risk using a machine learning model
- Maintain ethical, secure, and professional handling of sensitive healthcare data

Stroke is recognised by the **World Health Organization (WHO)** as the second leading cause of death globally. Early identification of high-risk patients is critical for preventative healthcare. StrokeCare addresses this challenge by integrating **secure software design**, **data-driven prediction**, and **role-based access control** into a single platform.

The application has been developed in alignment with the **COM7033 Assessment 1 Brief**, demonstrating:
- Secure programming practices
- CRUD functionality
- Multi-database architecture (SQLite + MongoDB)
- Ethical and professional software development
- Testing and version control using GitHub

---

## 2. Problems the Application Aims to Solve

### 2.1 Fragmented Clinical Data Systems
Many healthcare environments rely on general-purpose record systems that are not specialised for stroke risk assessment. This can lead to:
- Disconnected data sources
- Increased cognitive load on clinicians
- Delayed identification of high-risk patients

### 2.2 Manual and Error-Prone Processes
Traditional approaches such as paper forms or spreadsheets:
- Are vulnerable to data loss and human error
- Do not validate inputs consistently
- Cannot provide automated clinical decision support

### 2.3 Lack of Predictive Support
Stroke risk assessment often requires clinicians to manually interpret multiple variables (e.g. age, BMI, glucose levels, hypertension), which can be time-consuming and inconsistent.

### 2.4 Security and Privacy Risks
Without strong authentication, access control, and secure data handling, patient information is vulnerable to:
- Unauthorised access
- Data leakage
- Compliance failures

StrokeCare addresses these issues by providing a **centralised, secure, and predictive system** designed specifically for stroke-related healthcare workflows.

---

## 3. Stakeholders and Intended Users

StrokeCare has been designed for the following stakeholders:

### 3.1 Patients
- Indirect beneficiaries of the system
- Benefit from improved accuracy, early risk detection, and secure handling of their medical data
- No direct access to the application

### 3.2 Healthcare Professionals (HCPs)
- View patient records relevant to their role
- Support clinical workflows without unnecessary access to sensitive administrative controls

### 3.3 Doctors
- Perform full CRUD operations on patient data
- View machine learning–based stroke risk predictions
- Update patient records and reassess risk dynamically

### 3.4 Administrators
- Manage user accounts and roles
- Enforce role-based access control
- Maintain system integrity and security

---

## 4. Installation and Setup

### 4.1 Prerequisites
- Python 3.10+
- MongoDB (local or cloud instance)
- Git

### 4.2 Installation Steps

```bash
# Clone the repository
git clone https://github.com/CS-LTU/com7033-assignment-Vishbvs666
cd StrokeCare

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate   # macOS/Linux
# venv\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt

## 4.3 Configuration

Application configuration is stored securely in the following file:

- `instance/config.py`

Sensitive information such as:
- database connection details
- secret keys
- environment-specific settings  

is **separated from the main source code**, reducing the risk of accidental exposure and supporting secure software development practices.

---

## 4.4 Running the Application

To start the Flask application, run the following command:

```bash
python run.py

Once the server is up and running

http://127.0.0.1:5000
