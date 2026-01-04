#!/usr/bin/env python3
"""
Golf club physics calibration script.
Validates ball flight distances and helps tune parameters.
"""

import math

# Physics constants
GRAVITY = 9.81  # m/s²
YARDS_PER_METER = 1.094

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

# Swing speeds by club type (m/s)
swing_speeds = {
    'driver': 48,   # ~107 mph
    'wood': 42.5,   # ~95 mph
    'hybrid': 38,   # ~85 mph
    'iron': 36,     # ~80 mph
    'wedge': 32     # ~72 mph
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
    else:  # irons and wedges
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

def calculate_distance(ball_speed, launch_angle_deg, loft, club_type):
    """Calculate carry distance using projectile motion with drag approximation."""
    launch_angle = math.radians(launch_angle_deg)

    # Time of flight (ideal)
    flight_time = (2 * ball_speed * math.sin(launch_angle)) / GRAVITY

    # Horizontal distance (ideal)
    distance_meters = ball_speed * math.cos(launch_angle) * flight_time

    # Apply drag factor based on loft and club type
    # This approximates air resistance and spin effects
    # Use different coefficients for different club types
    if club_type == 'driver':
        drag_efficiency = 1.0 - (loft * 0.0076)
    elif club_type == 'wood':
        # Woods need more aggressive drag, especially 5W which has optimal launch angle
        # 5W gets extra penalty due to being close to optimal projectile angle
        if loft == 19:  # 5 wood
            drag_efficiency = 1.0 - (loft * 0.0105)
        else:
            drag_efficiency = 1.0 - (loft * 0.0092)
    elif club_type == 'hybrid':
        drag_efficiency = 1.0 - (loft * 0.0082)
    else:  # irons and wedges
        drag_efficiency = 1.0 - (loft * 0.0078)

    distance_meters *= drag_efficiency

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
