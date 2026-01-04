#!/usr/bin/env python3
"""
Golf club physics calibration script with Magnus effect.
Validates ball flight distances and helps tune parameters.
"""

import math

# Physics constants
GRAVITY = 9.81  # m/s²
YARDS_PER_METER = 1.094
AIR_DENSITY = 1.225  # kg/m³
BALL_MASS = 0.0459  # kg
BALL_DIAMETER = 0.0427  # m
BALL_AREA = math.pi * (BALL_DIAMETER / 2) ** 2

# Club definitions
clubs = {
    'driver': {'loft': 10.5, 'type': 'driver'},
    'wood3': {'loft': 15, 'type': 'wood'},
    'wood5': {'loft': 19, 'type': 'wood'},
    'hybrid5': {'loft': 27, 'type': 'hybrid'},
    'iron6': {'loft': 31, 'type': 'iron'},
    'iron7': {'loft': 34, 'type': 'iron'},
    'iron8': {'loft': 37, 'type': 'iron'},
    'iron9': {'loft': 41, 'type': 'iron'},
    'pw': {'loft': 46, 'type': 'wedge'},
    'sw': {'loft': 56, 'type': 'wedge'}
}

# Swing speeds by club type (m/s) - calibrated for Magnus effect
swing_speeds = {
    'driver': 62,   # ~139 mph
    'wood': 56,     # ~125 mph
    'hybrid': 48,   # ~107 mph
    'iron': 44,     # ~98 mph
    'wedge': 33     # ~74 mph
}

# Target distances for average golfer (yards)
target_distances = {
    'driver': 220,
    'wood3': 200,
    'wood5': 180,
    'hybrid5': 165,
    'iron6': 150,
    'iron7': 140,
    'iron8': 130,
    'iron9': 120,
    'pw': 110,
    'sw': 80
}

def get_smash_factor(loft, club_type):
    """Calculate smash factor based on loft and club type."""
    # Driver/woods: higher smash factors (1.40-1.48)
    # Irons/wedges: lower smash factors (1.20-1.40)
    if club_type in ['driver', 'wood']:
        return 1.48 - (loft * 0.003)
    elif club_type == 'hybrid':
        return 1.40 - (loft * 0.004)
    elif club_type == 'iron':
        return 1.43 - (loft * 0.0055)  # More aggressive drop for irons
    else:  # wedges
        return 1.42 - (loft * 0.005)

def get_launch_angle(loft, club_type):
    """Calculate launch angle - varies by club type."""
    # Driver/woods: launch angle is higher than loft (due to dynamic loft)
    # Irons: launch angle closer to loft
    # Wedges: launch angle is ~75% of loft
    if club_type == 'driver':
        return loft + 2  # Driver launches 2-4° above static loft
    elif club_type == 'wood':
        return loft + 1  # Woods launch slightly above loft
    elif club_type == 'hybrid':
        return loft * 0.9
    elif club_type == 'iron':
        return loft * 0.85
    else:  # wedges
        return loft * 0.75

def get_ball_speed(loft, club_type):
    """Calculate ball speed from swing speed and smash factor."""
    swing_speed = swing_speeds[club_type]
    # 5 wood gets slightly lower swing speed due to shaft length/control tradeoff
    if loft == 19:  # 5 wood
        swing_speed *= 0.95
    return swing_speed * get_smash_factor(loft, club_type)

def get_backspin(loft, club_type, ball_speed):
    """Calculate backspin rate based on club type and loft."""
    # Calibrated spin rates for realistic distances with Magnus effect
    if club_type == 'driver':
        return 2200 + loft * 30  # ~2500 rpm
    elif club_type == 'wood':
        return 3000 + loft * 50  # ~3750-3950 rpm
    elif club_type == 'hybrid':
        return 3500 + loft * 60  # ~5120 rpm
    elif club_type == 'iron':
        return 4000 + loft * 80  # ~6480-7280 rpm
    else:  # wedges
        return 6000 + loft * 70  # ~9220-9920 rpm (reduced from 100x)

def get_drag_coefficient(speed):
    """Calculate drag coefficient based on ball speed (Reynolds number)."""
    Re = (speed * BALL_DIAMETER) / 0.000015

    if Re < 100000:
        return 0.5
    elif Re > 200000:
        return 0.23
    else:
        t = (Re - 100000) / 100000
        return 0.5 - (0.27 * t)

def get_lift_coefficient(spin_rpm, speed):
    """Calculate lift coefficient from Magnus effect."""
    omega = spin_rpm * 2 * math.pi / 60
    spin_parameter = (BALL_DIAMETER / 2) * omega / max(speed, 0.1)
    Cl = min(0.25 * spin_parameter, 0.35)
    return Cl

def calculate_distance(ball_speed, launch_angle_deg, loft, club_type):
    """Calculate carry distance using force-based simulation with Magnus effect."""
    launch_angle = math.radians(launch_angle_deg)

    # Get backspin rate
    backspin_rpm = get_backspin(loft, club_type, ball_speed)

    # Initial conditions
    pos = {'x': 0, 'y': 0.02, 'z': 0}
    vel = {
        'x': ball_speed * math.cos(launch_angle),
        'y': ball_speed * math.sin(launch_angle),
        'z': 0
    }

    # Simulation parameters
    dt = 0.001  # Small timestep for accuracy
    max_time = 15  # Maximum flight time
    t = 0
    max_height = 0

    # Simulate trajectory using forces
    while t < max_time and pos['y'] >= 0.02:
        # Current speed
        speed = math.sqrt(vel['x']**2 + vel['y']**2 + vel['z']**2)

        if speed < 0.1:
            break

        # Unit velocity
        vx = vel['x'] / speed
        vy = vel['y'] / speed
        vz = vel['z'] / speed

        # Aerodynamic coefficients
        Cd = get_drag_coefficient(speed)
        Cl = get_lift_coefficient(backspin_rpm, speed)

        # Dynamic pressure
        q = 0.5 * AIR_DENSITY * speed * speed * BALL_AREA

        # Forces
        # 1. Gravity
        F_gravity_y = -BALL_MASS * GRAVITY

        # 2. Drag (opposite to velocity)
        F_drag = q * Cd
        F_drag_x = -F_drag * vx
        F_drag_y = -F_drag * vy
        F_drag_z = -F_drag * vz

        # 3. Magnus lift (from backspin, perpendicular to velocity)
        F_lift = q * Cl
        horizontal_speed = math.sqrt(vel['x']**2 + vel['z']**2)

        # Lift components (perpendicular to velocity in vertical plane)
        lift_x = F_lift * (-vel['x'] * vel['y']) / (speed * max(horizontal_speed, 0.1))
        lift_y = F_lift * horizontal_speed / speed
        lift_z = F_lift * (-vel['z'] * vel['y']) / (speed * max(horizontal_speed, 0.1))

        # Total forces
        F_x = F_drag_x + lift_x
        F_y = F_gravity_y + F_drag_y + lift_y
        F_z = F_drag_z + lift_z

        # Acceleration
        ax = F_x / BALL_MASS
        ay = F_y / BALL_MASS
        az = F_z / BALL_MASS

        # Update velocity and position (Euler integration)
        vel['x'] += ax * dt
        vel['y'] += ay * dt
        vel['z'] += az * dt

        pos['x'] += vel['x'] * dt
        pos['y'] += vel['y'] * dt
        pos['z'] += vel['z'] * dt

        if pos['y'] > max_height:
            max_height = pos['y']

        t += dt

    # Calculate total horizontal distance
    distance_meters = math.sqrt(pos['x']**2 + pos['z']**2)
    distance_yards = distance_meters * YARDS_PER_METER

    return distance_yards

def analyze_clubs():
    """Analyze all clubs and print results."""
    print("=" * 80)
    print("GOLF CLUB PHYSICS CALIBRATION")
    print("=" * 80)
    print()

    results = []

    for club_id, club_data in clubs.items():
        loft = club_data['loft']
        club_type = club_data['type']

        # Calculate physics
        smash_factor = get_smash_factor(loft, club_type)
        swing_speed = swing_speeds[club_type]
        ball_speed = get_ball_speed(loft, club_type)
        launch_angle = get_launch_angle(loft, club_type)
        distance = calculate_distance(ball_speed, launch_angle, loft, club_type)
        target = target_distances[club_id]
        error = distance - target
        error_pct = (error / target) * 100

        results.append({
            'id': club_id,
            'loft': loft,
            'swing': swing_speed,
            'smash': smash_factor,
            'ball_speed': ball_speed,
            'launch_angle': launch_angle,
            'distance': distance,
            'target': target,
            'error': error,
            'error_pct': error_pct
        })

    # Print table
    print(f"{'Club':<10} {'Loft':<6} {'Swing':<7} {'Smash':<7} {'Ball':<7} {'Launch':<8} {'Dist':<7} {'Target':<8} {'Error':<10}")
    print(f"{'':10} {'(°)':<6} {'(m/s)':<7} {'Factor':<7} {'(m/s)':<7} {'(°)':<8} {'(yds)':<7} {'(yds)':<8} {'(yds/%)':<10}")
    print("-" * 80)

    for r in results:
        print(f"{r['id']:<10} {r['loft']:<6.1f} {r['swing']:<7.1f} {r['smash']:<7.2f} "
              f"{r['ball_speed']:<7.1f} {r['launch_angle']:<8.1f} {r['distance']:<7.0f} "
              f"{r['target']:<8.0f} {r['error']:>+6.0f}/{r['error_pct']:>+5.1f}%")

    print()
    print("=" * 80)
    print("ANALYSIS")
    print("=" * 80)

    # Check for issues
    avg_error_pct = sum(abs(r['error_pct']) for r in results) / len(results)
    print(f"Average error: {avg_error_pct:.1f}%")
    print()

    # Check ordering
    print("Distance ordering check:")
    for i in range(len(results) - 1):
        if results[i]['distance'] < results[i+1]['distance']:
            print(f"  ⚠️  {results[i]['id']} ({results[i]['distance']:.0f} yds) < "
                  f"{results[i+1]['id']} ({results[i+1]['distance']:.0f} yds)")

    print()
    return results

if __name__ == '__main__':
    results = analyze_clubs()

    print()
    print("RECOMMENDATIONS:")
    print("1. Adjust smash factor formula to reduce with loft more appropriately")
    print("2. Consider different launch angle ratios for different club types")
    print("3. Driver typically has lower launch angle than woods (10-13° vs 15-18°)")
    print("4. Woods/hybrids may need different physics than irons/wedges")
