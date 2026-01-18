"""
Garmin Connect API REST wrapper
Provides REST endpoints for python-garminconnect library
"""

import os
from datetime import date, datetime
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, Body
from pydantic import BaseModel
from garminconnect import Garmin

# Global Garmin client
garmin_client: Optional[Garmin] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class HydrationData(BaseModel):
    value_in_ml: float


class BloodPressureData(BaseModel):
    systolic: int
    diastolic: int
    pulse: int
    notes: Optional[str] = None


class BodyCompositionData(BaseModel):
    weight: Optional[float] = None
    percent_fat: Optional[float] = None
    percent_hydration: Optional[float] = None
    visceral_fat_mass: Optional[float] = None
    bone_mass: Optional[float] = None
    muscle_mass: Optional[float] = None
    basal_met: Optional[float] = None
    active_met: Optional[float] = None
    physique_rating: Optional[float] = None
    metabolic_age: Optional[float] = None
    visceral_fat_rating: Optional[float] = None
    bmi: Optional[float] = None


class WeighInData(BaseModel):
    weight: float
    unit: str = "kg"


class GearDefaultData(BaseModel):
    gear_uuid: str
    activity_type_pk: int
    default: bool


class GearActivityData(BaseModel):
    activity_id: int
    gear_uuid: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Auto-login on startup if credentials are provided via environment variables."""
    global garmin_client
    email = os.getenv("GARMIN_EMAIL")
    password = os.getenv("GARMIN_PASSWORD")

    if email and password:
        try:
            garmin_client = Garmin(email, password)
            garmin_client.login()
            print("Auto-logged in successfully")
        except Exception as e:
            print(f"Auto-login failed: {e}")

    yield


app = FastAPI(
    title="Garmin Connect API",
    description="REST API wrapper for python-garminconnect library",
    version="1.0.0",
    lifespan=lifespan
)


def get_client() -> Garmin:
    """Get the Garmin client, raising an error if not logged in."""
    if garmin_client is None:
        raise HTTPException(status_code=401, detail="Not logged in. Call /auth/login first.")
    return garmin_client


def parse_date(date_str: str) -> date:
    """Parse a date string in YYYY-MM-DD format."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")


# ============== Authentication ==============

@app.post("/auth/login", tags=["Authentication"])
async def login(credentials: LoginRequest):
    """Login to Garmin Connect."""
    global garmin_client
    try:
        garmin_client = Garmin(credentials.email, credentials.password)
        garmin_client.login()
        return {"status": "success", "message": "Logged in successfully"}
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.post("/auth/logout", tags=["Authentication"])
async def logout():
    """Logout from Garmin Connect."""
    global garmin_client
    if garmin_client:
        garmin_client.logout()
        garmin_client = None
    return {"status": "success", "message": "Logged out"}


@app.get("/auth/status", tags=["Authentication"])
async def auth_status():
    """Check authentication status."""
    return {"logged_in": garmin_client is not None}


# ============== Hydration & Wellness ==============

@app.get("/wellness/hydration/{date_str}", tags=["Hydration & Wellness"])
async def get_hydration_data(date_str: str):
    """Get hydration data for a specific date."""
    client = get_client()
    return client.get_hydration_data(date_str)


@app.post("/wellness/hydration/{date_str}", tags=["Hydration & Wellness"])
async def add_hydration_data(date_str: str, data: HydrationData):
    """Add hydration data for a specific date."""
    client = get_client()
    return client.add_hydration_data(data.value_in_ml, date_str)


@app.post("/wellness/blood-pressure", tags=["Hydration & Wellness"])
async def set_blood_pressure(data: BloodPressureData):
    """Record blood pressure measurement."""
    client = get_client()
    return client.set_blood_pressure(
        systolic=data.systolic,
        diastolic=data.diastolic,
        pulse=data.pulse,
        notes=data.notes
    )


@app.delete("/wellness/blood-pressure/{bp_id}", tags=["Hydration & Wellness"])
async def delete_blood_pressure(bp_id: int):
    """Delete a blood pressure record."""
    client = get_client()
    return client.delete_blood_pressure(bp_id)


@app.get("/wellness/pregnancy", tags=["Hydration & Wellness"])
async def get_pregnancy_summary():
    """Get pregnancy tracking summary."""
    client = get_client()
    return client.get_pregnancy_summary()


@app.get("/wellness/menstrual/{date_str}", tags=["Hydration & Wellness"])
async def get_menstrual_data(date_str: str):
    """Get menstrual data for a specific date."""
    client = get_client()
    return client.get_menstrual_data_for_date(date_str)


@app.get("/wellness/menstrual-calendar", tags=["Hydration & Wellness"])
async def get_menstrual_calendar(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)")
):
    """Get menstrual calendar data for a date range."""
    client = get_client()
    return client.get_menstrual_calendar_data(start_date, end_date)


@app.get("/wellness/all-day-events/{date_str}", tags=["Hydration & Wellness"])
async def get_all_day_events(date_str: str):
    """Get all-day events for a specific date."""
    client = get_client()
    return client.get_all_day_events(date_str)


# ============== Fitness Metrics (HRV, VO2, Training Readiness) ==============

@app.get("/fitness/hrv/{date_str}", tags=["Fitness Metrics"])
async def get_hrv_data(date_str: str):
    """Get Heart Rate Variability (HRV) data for a specific date."""
    client = get_client()
    return client.get_hrv_data(date_str)


@app.get("/fitness/max-metrics/{date_str}", tags=["Fitness Metrics"])
async def get_max_metrics(date_str: str):
    """Get max metrics (VO2 max, etc.) for a specific date."""
    client = get_client()
    return client.get_max_metrics(date_str)


@app.get("/fitness/heart-rates/{date_str}", tags=["Fitness Metrics"])
async def get_heart_rates(date_str: str):
    """Get heart rate data for a specific date."""
    client = get_client()
    return client.get_heart_rates(date_str)


@app.get("/fitness/resting-heart-rate/{date_str}", tags=["Fitness Metrics"])
async def get_resting_heart_rate(date_str: str):
    """Get resting heart rate for a specific date."""
    client = get_client()
    return client.get_rhr_day(date_str)


@app.get("/fitness/training-readiness/{date_str}", tags=["Fitness Metrics"])
async def get_training_readiness(date_str: str):
    """Get training readiness for a specific date."""
    client = get_client()
    return client.get_training_readiness(date_str)


@app.get("/fitness/morning-training-readiness/{date_str}", tags=["Fitness Metrics"])
async def get_morning_training_readiness(date_str: str):
    """Get morning training readiness for a specific date."""
    client = get_client()
    return client.get_morning_training_readiness(date_str)


@app.get("/fitness/training-status/{date_str}", tags=["Fitness Metrics"])
async def get_training_status(date_str: str):
    """Get training status for a specific date."""
    client = get_client()
    return client.get_training_status(date_str)


@app.get("/fitness/stress/{date_str}", tags=["Fitness Metrics"])
async def get_stress_data(date_str: str):
    """Get stress data for a specific date."""
    client = get_client()
    return client.get_stress_data(date_str)


@app.get("/fitness/all-day-stress/{date_str}", tags=["Fitness Metrics"])
async def get_all_day_stress(date_str: str):
    """Get all-day stress data for a specific date."""
    client = get_client()
    return client.get_all_day_stress(date_str)


# ============== Daily Health & Activity ==============

@app.get("/health/stats/{date_str}", tags=["Daily Health & Activity"])
async def get_stats(date_str: str):
    """Get daily stats for a specific date."""
    client = get_client()
    return client.get_stats(date_str)


@app.get("/health/summary/{date_str}", tags=["Daily Health & Activity"])
async def get_user_summary(date_str: str):
    """Get user summary for a specific date."""
    client = get_client()
    return client.get_user_summary(date_str)


@app.get("/health/stats-and-body/{date_str}", tags=["Daily Health & Activity"])
async def get_stats_and_body(date_str: str):
    """Get combined stats and body data for a specific date."""
    client = get_client()
    return client.get_stats_and_body(date_str)


@app.get("/health/steps/{date_str}", tags=["Daily Health & Activity"])
async def get_steps_data(date_str: str):
    """Get steps data for a specific date."""
    client = get_client()
    return client.get_steps_data(date_str)


@app.get("/health/sleep/{date_str}", tags=["Daily Health & Activity"])
async def get_sleep_data(date_str: str):
    """Get sleep data for a specific date."""
    client = get_client()
    return client.get_sleep_data(date_str)


@app.get("/health/respiration/{date_str}", tags=["Daily Health & Activity"])
async def get_respiration_data(date_str: str):
    """Get respiration data for a specific date."""
    client = get_client()
    return client.get_respiration_data(date_str)


@app.get("/health/spo2/{date_str}", tags=["Daily Health & Activity"])
async def get_spo2_data(date_str: str):
    """Get SpO2 (blood oxygen) data for a specific date."""
    client = get_client()
    return client.get_spo2_data(date_str)


@app.get("/health/floors/{date_str}", tags=["Daily Health & Activity"])
async def get_floors_data(date_str: str):
    """Get floors climbed data for a specific date."""
    client = get_client()
    return client.get_floors(date_str)


# ============== Body Composition & Weight ==============

@app.get("/body/composition/{date_str}", tags=["Body Composition & Weight"])
async def get_body_composition(date_str: str):
    """Get body composition for a specific date."""
    client = get_client()
    return client.get_body_composition(date_str)


@app.put("/body/composition", tags=["Body Composition & Weight"])
async def set_body_composition(data: BodyCompositionData):
    """Set body composition data."""
    client = get_client()
    return client.set_body_composition(
        weight=data.weight,
        percent_fat=data.percent_fat,
        percent_hydration=data.percent_hydration,
        visceral_fat_mass=data.visceral_fat_mass,
        bone_mass=data.bone_mass,
        muscle_mass=data.muscle_mass,
        basal_met=data.basal_met,
        active_met=data.active_met,
        physique_rating=data.physique_rating,
        metabolic_age=data.metabolic_age,
        visceral_fat_rating=data.visceral_fat_rating,
        bmi=data.bmi
    )


@app.post("/body/composition", tags=["Body Composition & Weight"])
async def add_body_composition(data: BodyCompositionData):
    """Add body composition data."""
    client = get_client()
    return client.add_body_composition(
        weight=data.weight,
        percent_fat=data.percent_fat,
        percent_hydration=data.percent_hydration,
        visceral_fat_mass=data.visceral_fat_mass,
        bone_mass=data.bone_mass,
        muscle_mass=data.muscle_mass,
        basal_met=data.basal_met,
        active_met=data.active_met,
        physique_rating=data.physique_rating,
        metabolic_age=data.metabolic_age,
        visceral_fat_rating=data.visceral_fat_rating,
        bmi=data.bmi
    )


@app.get("/body/weigh-ins", tags=["Body Composition & Weight"])
async def get_weigh_ins(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)")
):
    """Get weigh-ins for a date range."""
    client = get_client()
    return client.get_weigh_ins(start_date, end_date)


@app.get("/body/weigh-ins/{date_str}", tags=["Body Composition & Weight"])
async def get_daily_weigh_ins(date_str: str):
    """Get weigh-ins for a specific date."""
    client = get_client()
    return client.get_daily_weigh_ins(date_str)


@app.post("/body/weigh-in", tags=["Body Composition & Weight"])
async def add_weigh_in(data: WeighInData):
    """Add a weigh-in entry."""
    client = get_client()
    return client.add_weigh_in(weight=data.weight, unitKey=data.unit)


@app.delete("/body/weigh-ins", tags=["Body Composition & Weight"])
async def delete_weigh_ins(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)")
):
    """Delete weigh-ins for a date range."""
    client = get_client()
    return client.delete_weigh_ins(start_date, end_date)


@app.delete("/body/weigh-in/{weigh_in_id}", tags=["Body Composition & Weight"])
async def delete_weigh_in(weigh_in_id: int):
    """Delete a specific weigh-in entry."""
    client = get_client()
    return client.delete_weigh_in(weigh_in_id)


# ============== Gear & Equipment ==============

@app.get("/gear", tags=["Gear & Equipment"])
async def get_gear(user_profile_number: int):
    """Get all gear for a user."""
    client = get_client()
    return client.get_gear(user_profile_number)


@app.get("/gear/defaults", tags=["Gear & Equipment"])
async def get_gear_defaults(user_profile_number: int):
    """Get gear defaults for a user."""
    client = get_client()
    return client.get_gear_defaults(user_profile_number)


@app.get("/gear/{gear_uuid}/stats", tags=["Gear & Equipment"])
async def get_gear_stats(gear_uuid: str):
    """Get statistics for a specific gear item."""
    client = get_client()
    return client.get_gear_stats(gear_uuid)


@app.get("/gear/{gear_uuid}/activities", tags=["Gear & Equipment"])
async def get_gear_activities(
    gear_uuid: str,
    start: int = Query(0, description="Start index"),
    limit: int = Query(20, description="Number of activities to return")
):
    """Get activities associated with a gear item."""
    client = get_client()
    return client.get_gear_activities(gear_uuid, start, limit)


@app.put("/gear/default", tags=["Gear & Equipment"])
async def set_gear_default(data: GearDefaultData):
    """Set gear as default for an activity type."""
    client = get_client()
    return client.set_gear_default(
        gear_uuid=data.gear_uuid,
        activity_type_pk=data.activity_type_pk,
        default=data.default
    )


@app.post("/gear/activity", tags=["Gear & Equipment"])
async def add_gear_to_activity(data: GearActivityData):
    """Associate gear with an activity."""
    client = get_client()
    return client.add_gear_to_activity(
        activity_id=data.activity_id,
        gear_uuid=data.gear_uuid
    )


@app.delete("/gear/activity", tags=["Gear & Equipment"])
async def remove_gear_from_activity(data: GearActivityData):
    """Remove gear association from an activity."""
    client = get_client()
    return client.remove_gear_from_activity(
        activity_id=data.activity_id,
        gear_uuid=data.gear_uuid
    )


# ============== User Info ==============

@app.get("/user/profile", tags=["User"])
async def get_user_profile():
    """Get user profile information."""
    client = get_client()
    return {
        "full_name": client.get_full_name(),
        "unit_system": client.get_unit_system()
    }


@app.get("/user/device", tags=["User"])
async def get_device_last_used():
    """Get last used device information."""
    client = get_client()
    return client.get_device_last_used()


# ============== Health Check ==============

@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "logged_in": garmin_client is not None}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
