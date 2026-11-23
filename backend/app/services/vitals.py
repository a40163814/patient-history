def compute_bmi(height_cm: float, weight_kg: float) -> tuple[float, str]:
    """
    Computes BMI strictly in code using the formula: weight_kg / (height_m ^ 2)
    Classifies according to revised consensus guidelines for India / Asian populations.
    Always designated as 'self-reported'.
    """
    if height_cm <= 0 or weight_kg <= 0:
        raise ValueError("Height and weight must be positive numbers")
    
    height_m = height_cm / 100.0
    bmi = round(weight_kg / (height_m ** 2), 1)
    
    # Revised Indian / Asian guidelines:
    # < 18.5: Underweight
    # 18.5 - 22.9: Normal
    # 23.0 - 24.9: Overweight
    # >= 25.0: Obese
    if bmi < 18.5:
        category = "Underweight"
    elif bmi <= 22.9:
        category = "Normal"
    elif bmi <= 24.9:
        category = "Overweight"
    else:
        category = "Obese"
        
    return bmi, category
