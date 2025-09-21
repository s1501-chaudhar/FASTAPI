from fastapi import FastAPI, Path, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, computed_field
from typing import Annotated, Literal, Optional
import json

app = FastAPI()


# -------------------------------
# Models
# -------------------------------

class Patient(BaseModel):
    id: Annotated[int, Field(..., gt=0, example=1)]
    name: Annotated[str, Field(..., example="John Doe")]
    age: Annotated[int, Field(..., gt=0, example=30)]
    city: Annotated[str, Field(..., example="New York")]
    height: Annotated[float, Field(..., gt=0, example=175.5)]  # in cm
    weight: Annotated[float, Field(..., gt=0, example=70.5)]   # in kg
    gender: Annotated[Literal["male", "female", "others"], Field(..., example="male")]

    @computed_field
    @property
    def bmi(self) -> float:
        return round(self.weight / ((self.height / 100) ** 2), 2)

    @computed_field
    @property
    def verified(self) -> str:
        bmi = self.bmi
        if bmi < 18.5:
            return "Underweight"
        elif bmi < 25:
            return "Healthy"
        elif bmi < 30:
            return "Overweight"
        else:
            return "Obese"


class PatientUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = Field(None, gt=0)
    city: Optional[str] = None
    height: Optional[float] = Field(None, gt=0)
    weight: Optional[float] = Field(None, gt=0)
    gender: Optional[Literal["male", "female", "others"]] = None


# -------------------------------
# Helpers for File Storage
# -------------------------------

def load_data():
    try:
        with open("patients.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_data(data):
    with open("patients.json", "w") as f:
        json.dump(data, f, indent=2)


# -------------------------------
# Routes
# -------------------------------

@app.get("/")
def hello():
    return {"message": "Patient Management System API"}


@app.get("/about")
def about():
    return {"message": "A fully functional API to manage your patient data"}


@app.get("/view")
def view_all_patients():
    data = load_data()
    return data


@app.get("/patient/{patient_id}")
def view_patient(patient_id: int = Path(..., description="ID of the patient", example=1)):
    data = load_data()
    for patient in data:
        if patient["id"] == patient_id:
            return patient
    raise HTTPException(status_code=404, detail="Patient not found")


@app.get("/sort")
def sort_patients(
    sort_by: str = Query(..., description='Sort by "height", "weight", "age", or "bmi"'),
    order: str = Query("asc", description='Order: "asc" or "desc"')
):
    valid_fields = ['height', 'weight', 'age', 'bmi']
    if sort_by not in valid_fields:
        raise HTTPException(status_code=400, detail=f"Invalid sort field. Choose from {valid_fields}")
    if order not in ['asc', 'desc']:
        raise HTTPException(status_code=400, detail='Order must be "asc" or "desc"')

    data = load_data()

    # Convert to Patient models to access computed BMI
    patients = [Patient(**p) for p in data]

    # Sort using attribute
    reverse = order == "desc"
    sorted_patients = sorted(patients, key=lambda p: getattr(p, sort_by), reverse=reverse)

    return [p.model_dump() for p in sorted_patients]


@app.post("/create")
def create_patient(patient: Patient):
    data = load_data()

    # Check if ID already exists
    if any(p["id"] == patient.id for p in data):
        raise HTTPException(status_code=400, detail="Patient with this ID already exists")

    data.append(patient.model_dump())
    save_data(data)

    return JSONResponse(status_code=201, content={
        "message": "Patient created successfully",
        "patient": patient.model_dump()
    })


@app.put("/edit/{patient_id}")
def update_patient(patient_id: int, patient_update: PatientUpdate):
    data = load_data()

    for idx, patient in enumerate(data):
        if patient["id"] == patient_id:
            # Merge updates
            updated_data = patient.copy()
            updates = patient_update.model_dump(exclude_unset=True)
            updated_data.update(updates)

            # Validate and re-serialize
            updated_patient = Patient(**updated_data)
            data[idx] = updated_patient.model_dump()

            save_data(data)

            return JSONResponse(status_code=200, content={
                "message": "Patient updated successfully",
                "patient": data[idx]
            })

    raise HTTPException(status_code=404, detail="Patient not found")

@app.delete("/delete/{patient_id}")
def delete_patient(patient_id: int):
    data = load_data()

    for idx, patient in enumerate(data):
        if patient["id"] == patient_id:
            del data[idx]
            save_data(data)
            return JSONResponse(status_code=200, content={"message": "Patient deleted successfully"})

    raise HTTPException(status_code=404, detail="Patient not found")
