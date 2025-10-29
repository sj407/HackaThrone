import RPi.GPIO as GPIO
import time
import matplotlib.pyplot as plt

TRIG = 23
ECHO = 24
GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

def get_distance():
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    start = time.time()
    stop = time.time()

    while GPIO.input(ECHO) == 0:
        start = time.time()
    while GPIO.input(ECHO) == 1:
        stop = time.time()

    distance = (stop - start) * 17150  # cm
    return round(distance, 2) if 2 < distance < 200 else None

readings = []
baseline = None
in_pothole = False
pothole_start = None
pothole_end = None
max_depth = 0
stable_buffer = []
start_time = time.time()

print("Scanning started... move sensor over surface.")

try:
    while True:
        # Safety timeout (25 s)
        if time.time() - start_time > 25:
            print("⏹ Timeout reached — stopping scan.")
            break

        dist = get_distance()
        if dist is None:
            continue
        readings.append(dist)
        print(f"Distance: {dist} cm")

        # Set baseline
        if baseline is None and len(readings) >= 5:
            baseline = sum(readings[-5:]) / 5
            print(f"Baseline set to {baseline:.2f} cm")
            continue
        if baseline is None:
            continue

        prev = readings[-2] if len(readings) > 1 else dist
        diff_base = abs(dist - baseline)
        diff_prev = abs(dist - prev)

        # Detect pothole start
        if not in_pothole and diff_base > 5 and diff_prev > 5:
            in_pothole = True
            pothole_start = len(readings) - 1
            print("⚠ Pothole detected!")

        # Inside pothole
        if in_pothole:
            if diff_base > max_depth:
                max_depth = diff_base

            # Track stability near baseline
            stable_buffer.append(diff_base <= 3)
            if len(stable_buffer) > 6:
                stable_buffer.pop(0)

            # Stop if 4 of last 6 readings are stable
            if sum(stable_buffer) >= 4:
                pothole_end = len(readings) - 1
                print("✅ Road stable again — pothole end.")
                break

        time.sleep(0.15)  # 6–7 readings/sec

except KeyboardInterrupt:
    print("Stopped manually.")
finally:
    GPIO.cleanup()

# ---------- Results + Visualization ----------
if pothole_start and pothole_end:
    pothole_length = (pothole_end - pothole_start) * 1.5
    print("\n========= RESULTS =========")
    print(f"Pothole Depth: {max_depth:.2f} cm")
    print(f"Pothole Length: {pothole_length:.2f} cm")

    if max_depth > 10:
        safety = "❌ Dangerous — avoid!"
    elif max_depth > 5:
        safety = "⚠ Caution — slow down!"
    else:
        safety = "✅ Safe to pass."
    print(f"Safety: {safety}")

    plt.figure(figsize=(8,3))
    colors = ['red' if pothole_start <= i <= pothole_end else 'green'
              for i in range(len(readings))]
    plt.bar(range(len(readings)), readings, color=colors)
    plt.axhline(y=baseline, color='blue', linestyle='--', label='Baseline')
    plt.title("2D Pothole Map")
    plt.xlabel("Reading Index")
    plt.ylabel("Distance (cm)")
    plt.legend()
    plt.show()
else:
    print("\nNo pothole detected or insufficient data.")
