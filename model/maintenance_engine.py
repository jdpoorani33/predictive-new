import math
import numpy as np

STATUS_HIERARCHY = ["Healthy", "Slight Wear", "Moderate Wear", "Warning", "Critical"]

# Global configurable cost & energy parameters
DEFAULT_COST_CONFIG = {
    "labour_cost": 3000.0,
    "spare_parts_cost": 3500.0,
    "inspection_cost": 1000.0,
    "service_cost": 500.0,
    "other_cost": 0.0,
    "repair_replacement_cost": 12000.0,
    "downtime_cost": 8000.0,
    "production_loss": 4000.0,
    "emergency_labour_cost": 6000.0,
    "electricity_rate": 8.0,  # ₹/kWh
    "voltage": 415.0,         # 3-Phase AC Volts
    "power_factor": 0.85,
    "operating_hours": 24.0,  # Hours/day
    "rul_thresholds": {
        "monitor_normally": 30,
        "plan_maintenance": 15,
        "schedule_soon": 7,
        "inspect_urgently": 3
    }
}

def get_machine_condition(health_pct, rul_days, is_anomaly=False, is_severe=False):
    """
    Classifies high-level machine condition:
      - Healthy
      - Warning
      - Critical
    """
    h = float(health_pct)
    r = float(rul_days)
    if h <= 25.0 or r <= 25.0 or (h <= 35.0 and (is_anomaly or is_severe)):
        return "Critical"
    elif h < 75.0 or r < 120.0 or is_anomaly or is_severe:
        return "Warning"
    else:
        return "Healthy"

def calculate_failure_risk(health_pct, rul_days, lifespan_days=250.0, is_anomaly=False, is_severe=False):
    """
    Dynamically computes failure risk percentage (0.0% to 100.0%) based on:
      1. Health index degradation (100 - health)
      2. RUL decay ratio (1 - RUL / Lifespan)
      3. Anomaly detection & active fault penalty
    """
    h = float(health_pct)
    r = float(rul_days)
    l = max(1.0, float(lifespan_days))
    
    health_factor = max(0.0, 100.0 - h)
    rul_factor = max(0.0, (1.0 - (r / l)) * 100.0)
    
    base_risk = 0.60 * health_factor + 0.40 * rul_factor
    
    if is_anomaly:
        base_risk += 12.5
    if is_severe:
        base_risk += 20.0
        
    clamped_risk = round(max(0.0, min(100.0, base_risk)), 1)
    return clamped_risk

def derive_probable_issue(temp, vib, curr, press, noise, health, is_anomaly=False, active_event="None", fft_info=None):
    """
    Derives dynamic human-readable component problem and concise diagnostic summary
    strictly based on real-time sensor, frequency-domain, and anomaly telemetry.
    """
    active_str = str(active_event) if active_event else "None"
    
    # Check FFT info if present
    fft_vib_anomaly = False
    fft_curr_anomaly = False
    if fft_info and isinstance(fft_info, dict):
        fft_vib_anomaly = fft_info.get("vibration_anomaly", False)
        fft_curr_anomaly = fft_info.get("current_anomaly", False)

    # Sensor thresholds & deviations
    high_vib = vib >= 0.35 or fft_vib_anomaly or "Vibration" in active_str
    high_curr = curr >= 8.8 or fft_curr_anomaly or "Current" in active_str
    high_temp = temp >= 68.0 or "Thermal" in active_str or "Temp" in active_str
    press_anomaly = press <= 4.2 or press >= 6.5 or "Pressure" in active_str
    high_noise = noise >= 48.0 or "Noise" in active_str

    if high_vib and high_curr and high_temp:
        main_issue = "Bearing degradation & motor overload"
        short_desc = "High vibration, current, and thermal stress detected."
    elif high_vib:
        if vib >= 0.50:
            main_issue = "Excessive vibration detected / Possible bearing imbalance"
            short_desc = "Excessive vibration pattern detected. Possible bearing imbalance or mechanical wear."
        else:
            main_issue = "Bearing likely wearing out"
            short_desc = "Vibration amplitude is elevated above baseline. Bearing likely wearing out."
    elif high_curr and high_temp:
        main_issue = "Motor overload & elevated thermal stress"
        short_desc = "Motor current and operating temperature are increasing abnormally."
    elif high_curr:
        main_issue = "Motor current increasing abnormally"
        short_desc = "Motor current is increasing abnormally. Possible electrical overload or winding friction."
    elif high_temp:
        main_issue = "Elevated motor temperature"
        short_desc = "Motor operating temperature is above normal thermal threshold."
    elif press_anomaly:
        main_issue = "Pressure abnormality detected"
        short_desc = "Pressure abnormality detected. Possible hydraulic leakage or pipe blockage."
    elif high_noise:
        main_issue = "Acoustic noise anomaly"
        short_desc = "Acoustic noise level elevated. Mechanical alignment inspection recommended."
    elif is_anomaly or health < 75.0:
        main_issue = "Abnormal vibration/sensor pattern detected"
        short_desc = "Abnormal vibration pattern detected. Further inspection recommended."
    else:
        main_issue = "Normal Operation"
        short_desc = "System operating within healthy parameters."

    return main_issue, short_desc

def get_maintenance_recommendation(
    predicted_rul,
    machine_health=100.0,
    active_event="None",
    max_lifespan_days=250,
    prev_status_level=0,
    sensor_anomaly_score=0.0,
    is_anomaly=False,
    sensor_telemetry=None,
    cost_config=None,
    plc_id="PLC_01"
):
    """
    Comprehensive Multi-Factor Maintenance + Energy + Cost Decision Engine.
    Combines:
      - RUL & Machine Health
      - Anomaly & FFT/Frequency-Domain telemetry
      - Preventive Servicing Cost vs Expected Failure Cost
      - 3-Phase Energy Consumption, Inefficiency %, & Daily Energy Cost
      - Human-Readable Alerts & Explanation Evidence
    """
    rul = float(predicted_rul)
    health = float(machine_health)
    lifespan = max(1.0, float(max_lifespan_days))
    anomaly_score = float(sensor_anomaly_score)

    # Resolve sensor telemetry defaults if not passed
    telemetry = sensor_telemetry or {}
    temp = float(telemetry.get("temperature", telemetry.get("Motor_Temp", 62.0)))
    vib = float(telemetry.get("vibration", telemetry.get("Vibration_X", 0.2)))
    curr = float(telemetry.get("motor_current", telemetry.get("Motor_Current", 8.0)))
    press = float(telemetry.get("pressure", telemetry.get("Pressure_Inlet", 5.0)))
    noise = float(telemetry.get("noise", telemetry.get("Noise", 42.0)))

    # Resolve cost configuration
    cfg = dict(DEFAULT_COST_CONFIG)
    if cost_config and isinstance(cost_config, dict):
        cfg.update(cost_config)

    # RUL thresholds
    rul_cfg = cfg.get("rul_thresholds", DEFAULT_COST_CONFIG["rul_thresholds"])
    monitor_norm = float(rul_cfg.get("monitor_normally", 30))
    plan_maint = float(rul_cfg.get("plan_maintenance", 15))
    sched_soon = float(rul_cfg.get("schedule_soon", 7))
    inspect_urg = float(rul_cfg.get("inspect_urgently", 3))

    # Standard status evaluation
    rul_crit = 0.10 * lifespan   # ~25 days
    rul_warn = 0.25 * lifespan   # ~62 days
    rul_mod = 0.50 * lifespan    # ~125 days
    rul_slight = 0.75 * lifespan # ~187 days
    
    is_severe_fault = active_event not in ["None", "", None] and ("Burst" in active_event or "Peak" in active_event)
    is_any_anomaly = is_anomaly or anomaly_score > 1.0 or is_severe_fault

    if health <= 15.0 or rul <= inspect_urg or (health <= 25.0 and is_severe_fault):
        calculated_level = 4  # Critical
    elif health < 40.0 or rul < sched_soon or anomaly_score > 1.5 or is_severe_fault:
        calculated_level = 3  # Warning
    elif health < 60.0 or rul < plan_maint or anomaly_score > 0.8 or is_anomaly:
        calculated_level = 2  # Moderate Wear
    elif health < 80.0 or rul <= monitor_norm or anomaly_score > 0.3:
        calculated_level = 1  # Slight Wear
    else:
        calculated_level = 0  # Healthy

    current_level = max(prev_status_level, calculated_level)
    status = STATUS_HIERARCHY[current_level]

    # Dynamic RUL-Based Action & Window Recommendation
    if rul > monitor_norm and current_level <= 1:
        recommendation = "Continue Normal Operation"
        priority = "Low"
        priority_level = "Low"
        priority_symbol = "🟢"
        window = "Routine inspection within 90–120 days"
        inspection_deadline_days = min(60, int(rul / 2))
    elif rul > plan_maint:
        recommendation = "Plan maintenance"
        priority = "Moderate"
        priority_level = "Medium"
        priority_symbol = "🟡"
        inspection_deadline_days = max(7, int(rul / 2))
        window = f"Plan maintenance and inspect within {inspection_deadline_days} days"
    elif rul > sched_soon:
        recommendation = "Schedule maintenance soon"
        priority = "High"
        priority_level = "High"
        priority_symbol = "🟠"
        inspection_deadline_days = max(3, int(rul / 2))
        window = f"Schedule maintenance within {inspection_deadline_days} days"
    elif rul > inspect_urg:
        recommendation = "Inspect urgently"
        priority = "Urgent"
        priority_level = "High"
        priority_symbol = "🟠"
        inspection_deadline_days = 2
        window = "Inspect urgently within 48 hours"
    else:
        recommendation = "Maintain immediately"
        priority = "Critical"
        priority_level = "Critical"
        priority_symbol = "🔴"
        inspection_deadline_days = 1
        window = "Critical — immediate maintenance recommended"

    if active_event not in ["None", "", None] and priority in ["Low", "Moderate"]:
        priority = "High"
        priority_level = "High"
        priority_symbol = "🟠"
        recommendation = f"Active anomaly ({active_event}): Inspect component immediately"
        window = "Inspect within 24-48 hours"

    machine_cond = get_machine_condition(health, rul, is_anomaly=is_any_anomaly, is_severe=is_severe_fault)
    failure_risk = calculate_failure_risk(health, rul, lifespan_days=lifespan, is_anomaly=is_any_anomaly, is_severe=is_severe_fault)
    fail_prob = round(failure_risk / 100.0, 4)

    # Main Issue Problem Diagnosis
    main_issue, short_problem_desc = derive_probable_issue(temp, vib, curr, press, noise, health, is_anomaly=is_any_anomaly, active_event=active_event)

    # 1. Preventive Maintenance Cost Calculation
    labour_cost = float(cfg.get("labour_cost", 3000.0))
    spare_parts_cost = float(cfg.get("spare_parts_cost", 3500.0))
    inspection_cost = float(cfg.get("inspection_cost", 1000.0))
    service_cost = float(cfg.get("service_cost", 500.0))
    other_cost = float(cfg.get("other_cost", 0.0))
    preventive_cost = round(labour_cost + spare_parts_cost + inspection_cost + service_cost + other_cost, 2)

    # 2. Failure Cost & Expected Failure Cost Calculation
    repair_replacement_cost = float(cfg.get("repair_replacement_cost", 12000.0))
    downtime_cost = float(cfg.get("downtime_cost", 8000.0))
    production_loss = float(cfg.get("production_loss", 4000.0))
    emergency_labour_cost = float(cfg.get("emergency_labour_cost", 6000.0))
    total_failure_impact = round(repair_replacement_cost + downtime_cost + production_loss + emergency_labour_cost, 2)
    expected_failure_cost = round(fail_prob * total_failure_impact, 2)

    # 3. Potential Savings & Cost Decision
    potential_savings = round(expected_failure_cost - preventive_cost, 2)
    
    if priority_level == "Critical" or rul <= 7.0:
        cost_decision_msg = f"CRITICAL — Safety and operational risk override cost optimization. Maintain immediately."
        is_cost_effective = True
    elif potential_savings > 0:
        cost_decision_msg = f"Preventive maintenance recommended — estimated saving ₹{potential_savings:,.0f}."
        is_cost_effective = True
    else:
        cost_decision_msg = f"Continue monitoring — immediate preventive maintenance is not currently cost-effective."
        is_cost_effective = False

    # 4. Energy-Aware Calculations (3-Phase Electrical Motor Model)
    voltage = float(cfg.get("voltage", 415.0))
    power_factor = float(cfg.get("power_factor", 0.85))
    operating_hours = float(cfg.get("operating_hours", 24.0))
    electricity_rate = float(cfg.get("electricity_rate", 8.0))

    # Power (kW) = sqrt(3) * V * I * PF / 1000
    current_power_kw = round((math.sqrt(3) * voltage * curr * power_factor) / 1000.0, 2)
    
    # Dynamic baseline current based on PLC number or nominal load (7.5A baseline)
    plc_num = int(''.join(filter(str.isdigit, str(plc_id)))) if any(c.isdigit() for c in str(plc_id)) else 1
    baseline_current = round(7.5 + (plc_num * 0.2), 1)
    baseline_power_kw = round((math.sqrt(3) * voltage * baseline_current * power_factor) / 1000.0, 2)

    current_energy_kwh = round(current_power_kw * operating_hours, 1)
    baseline_energy_kwh = round(baseline_power_kw * operating_hours, 1)
    excess_energy_kwh = round(max(0.0, current_energy_kwh - baseline_energy_kwh), 1)
    
    energy_inefficiency_pct = round(max(0.0, ((current_energy_kwh - baseline_energy_kwh) / max(1.0, baseline_energy_kwh)) * 100.0), 1)
    additional_energy_cost_per_day = round(excess_energy_kwh * electricity_rate, 2)

    # Energy Anomaly Classification
    if energy_inefficiency_pct >= 25.0 and (vib > 0.4 or is_any_anomaly):
        energy_status = "Critical Energy Inefficiency"
        energy_anomaly_msg = f"{plc_id}: High energy consumption (+{energy_inefficiency_pct}%) and abnormal vibration detected. Possible motor/bearing issue. Inspect immediately."
    elif energy_inefficiency_pct >= 12.0 and vib > 0.3:
        energy_status = "Maintenance-Related Energy Anomaly"
        energy_anomaly_msg = f"{plc_id}: Energy consumption is +{energy_inefficiency_pct}% above baseline with increasing vibration. Possible mechanical degradation. Maintenance recommended."
    elif energy_inefficiency_pct >= 8.0:
        energy_status = "Warning"
        energy_anomaly_msg = f"{plc_id}: Energy consumption is approximately {energy_inefficiency_pct}% above its normal baseline. Monitor motor efficiency."
    else:
        energy_status = "Normal"
        energy_anomaly_msg = f"{plc_id}: Energy consumption is within the normal operating range."

    # Human-Readable Concise Alert Format (Requirement 2 & 18)
    rul_weeks = round(rul / 7.0, 1)
    if rul_weeks < 1.0:
        rul_time_str = f"~{int(rul)} days"
    else:
        rul_time_str = f"~{rul_weeks} weeks" if rul_weeks != 1.0 else "~1 week"

    human_readable_alert = f"{priority_symbol} {plc_id} — {main_issue}.\nAbout {rul_time_str} left before failure. Recommended: inspect within {inspection_deadline_days} days."

    # Combined Intelligent Decision (Requirement 8 & 10)
    energy_part = f"Energy consumption: +{energy_inefficiency_pct}% above baseline (₹{additional_energy_cost_per_day:,.0f}/day excess cost)" if excess_energy_kwh > 0 else "Energy consumption: within normal range"
    saving_part = f"Estimated potential saving: ₹{potential_savings:,.0f} + future energy savings" if potential_savings > 0 else "Servicing cost exceeds immediate breakdown risk"
    
    total_recommendation_summary = (
        f"{priority_symbol} {plc_id} — Maintenance Recommendation\n\n"
        f"Issue: {main_issue}\n"
        f"Remaining Useful Life: Approximately {rul_time_str} left before predicted failure.\n"
        f"Action Window: Please inspect within {inspection_deadline_days} days.\n"
        f"{energy_part}\n"
        f"Preventive maintenance cost: ₹{preventive_cost:,.0f}\n"
        f"Expected failure cost: ₹{expected_failure_cost:,.0f} (Failure Risk: {failure_risk:.1f}%)\n"
        f"{saving_part}\n"
        f"Recommended Action: {recommendation} within {inspection_deadline_days} days."
    )

    # Model / Calculation Transparency Evidence List ("Why this recommendation?")
    vib_baseline = 0.20 + (plc_num * 0.08)
    curr_baseline = 7.5 + (plc_num * 0.4)
    vib_pct_change = round(max(0.0, ((vib - vib_baseline) / max(0.01, vib_baseline)) * 100.0), 1)
    curr_pct_change = round(max(0.0, ((curr - curr_baseline) / max(0.01, curr_baseline)) * 100.0), 1)

    why_recommendation = []
    if vib_pct_change > 0:
        why_recommendation.append(f"Vibration increased by {vib_pct_change}% (measured {vib:.2f} mm/s vs baseline {vib_baseline:.2f} mm/s)")
    if curr_pct_change > 0:
        why_recommendation.append(f"Motor current increased by {curr_pct_change}% (measured {curr:.1f} A vs baseline {curr_baseline:.1f} A)")
    if energy_inefficiency_pct > 0:
        why_recommendation.append(f"Energy consumption is {energy_inefficiency_pct}% above baseline (adding ₹{additional_energy_cost_per_day:,.0f}/day in energy loss)")
    why_recommendation.append(f"Failure probability is {fail_prob*100:.1f}% with Machine Health at {health:.1f}%")
    why_recommendation.append(f"Random Forest predicted RUL is approximately {int(rul)} days (~{rul_time_str})")
    if expected_failure_cost > preventive_cost:
        why_recommendation.append(f"Expected failure cost (₹{expected_failure_cost:,.0f}) is higher than preventive maintenance cost (₹{preventive_cost:,.0f}), yielding estimated savings of ₹{potential_savings:,.0f}")

    return {
        "plc_id": plc_id,
        "maintenance_status": status,
        "machine_condition": machine_cond,
        "failure_risk_pct": failure_risk,
        "failure_probability": fail_prob,
        "recommended_action": recommendation,
        "inspection_priority": priority,
        "priority_level": priority_level,
        "priority_symbol": priority_symbol,
        "next_inspection_window": window,
        "inspection_deadline_days": inspection_deadline_days,
        "status_level": current_level,
        
        # New Maintenance Cost Optimization fields
        "main_issue": main_issue,
        "short_problem_desc": short_problem_desc,
        "human_readable_alert": human_readable_alert,
        "preventive_cost": preventive_cost,
        "preventive_cost_breakdown": {
            "labour": labour_cost,
            "spare_parts": spare_parts_cost,
            "inspection": inspection_cost,
            "service": service_cost,
            "other": other_cost
        },
        "total_failure_impact": total_failure_impact,
        "failure_impact_breakdown": {
            "repair_replacement": repair_replacement_cost,
            "downtime": downtime_cost,
            "production_loss": production_loss,
            "emergency_labour": emergency_labour_cost
        },
        "expected_failure_cost": expected_failure_cost,
        "potential_savings": potential_savings,
        "is_cost_effective": is_cost_effective,
        "cost_decision_msg": cost_decision_msg,
        
        # New Energy-Aware Predictive Maintenance fields
        "voltage": voltage,
        "current_power_kw": current_power_kw,
        "baseline_power_kw": baseline_power_kw,
        "current_energy_kwh": current_energy_kwh,
        "baseline_energy_kwh": baseline_energy_kwh,
        "excess_energy_kwh": excess_energy_kwh,
        "energy_inefficiency_pct": energy_inefficiency_pct,
        "energy_status": energy_status,
        "energy_anomaly_msg": energy_anomaly_msg,
        "additional_energy_cost_per_day": additional_energy_cost_per_day,
        "electricity_rate": electricity_rate,
        
        # Combined Intelligent Summaries & Transparency Evidence
        "total_recommendation_summary": total_recommendation_summary,
        "why_recommendation": why_recommendation
    }
