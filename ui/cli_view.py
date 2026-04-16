def render(state: dict) -> None:
    hdg = state.get('heading_deg', 0.0)
    pitch = state.get('pitch_deg', 0.0)
    roll = state.get('roll_deg', 0.0)
    calibrated = state.get('confidence_state', 'POOR') == 'GOOD'
    print(f"[Compass] HDG: {hdg:.1f}° | Tilt: {pitch:.1f}/{roll:.1f} | Cal: {calibrated}")
