from fastapi import FastAPI
import json

app = FastAPI()

def load_data():
    with open("patients.json", "r") as f:
        data = json.load(f)

    return data

@app.get("/")
def hello():
    return {"message": "Patient Management System API"}

@app.get('/about')
def about():
    return {"message": "A fully functional API to manage your patient data"}

@app.get("/view")
def view():
    data = load_data()
    return data

@app.get("/patient/{patient_id}")
def view_patient(patient_id: int):
    data = load_data()
    for patient in data:
        if patient["id"] == patient_id:
            return patient
    return {"message": "Patient not found"}