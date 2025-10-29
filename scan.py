import RPi.GPIO as GPIO
import time
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# ------------------- GPIO Setup -------------------
TRIG = 23
ECHO = 24

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

# ------------------- Sensor Function -------------------
def get_distance():
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    start_time = time.time()
    stop_time = time.time()

    while GPIO.input(ECHO) == 0:
        start_time = time.time()

    while GPIO.input(ECHO) == 1:
        stop_time = time.time()

    time_elapsed = stop_time - start_time
    distance = (time_elapsed * 34300) / 2  # cm

    if distance < 2 or distance > 200:
        return None
    return round(distance, 2)

# ------------------- Data Lists -------------------
distances = []
x_vals = []
reference_depth = None
pothole_detected = False
index = 0
stop_flag = False

# ------------------- Matplotlib Setup -------------------
plt.style.use('dark_background')
fig, ax = plt.subplots()
line_normal, = ax.plot([], [], 'go-', label='Normal Surface')
line_pothole, = ax.plot([], [], 'ro-', label='Pothole Zone')
ax.set_xlim(0, 50)
ax.set_ylim(0, 100)
ax.set_xlabel('Scan Step')
ax.set_ylabel('Distance (cm)')
ax.set_title('?? Real-time Pothole Detection Map')
ax.legend()

# ------------------- Update Function -------------------
def update(frame):
    global index, reference_depth, pothole_detected, stop_flag

    if stop_flag:
        return line_normal, line_pothole

    distance = get_distance()
    if distance is None:
        return line_normal, line_pothole

    distances.append(distance)
    x_vals.append(index)
    index += 1
    print(f"Distance: {distance} cm")

    # Set reference surface
    if reference_depth is None and len(distances) > 5:
        reference_depth = sum(distances[-5:]) / 5
        print(f"? Reference surface set: {reference_depth:.2f} cm")

    # Detect pothole start
    if reference_depth and not pothole_detected and distance > reference_depth + 5:
        pothole_detected = True
        print("? Pothole detected! Measuring depth...")

    # Detect pothole end
    if reference_depth and pothole_detected and abs(distance - reference_depth) <= 2:
        print("\n? Road surface stabilized again.")
        pothole_depth = max(distances) - reference_depth
        print(f"?? Pothole depth: {pothole_depth:.2f} cm")
        print("Stopping scan...\n")
        stop_flag = True

    # Split points for visualization
    normal_x = [x_vals[i] for i, d in enumerate(distances)
                if reference_depth and abs(d - reference_depth) <= 5]
    normal_y = [distances[i] for i, d in enumerate(distances)
                if reference_depth and abs(d - reference_depth) <= 5]

    pothole_x = [x_vals[i] for i, d in enumerate(distances)
                 if reference_depth and d > reference_depth + 5]
    pothole_y = [distances[i] for i, d in enumerate(distances)
                 if reference_depth and d > reference_depth + 5]

    line_normal.set_data(normal_x, normal_y)
    line_pothole.set_data(pothole_x, pothole_y)

    ax.set_xlim(0, max(50, len(x_vals)))
    ax.set_ylim(0, max(100, max(distances) + 10))

    return line_normal, line_pothole

# ------------------- Run Animation -------------------
ani = FuncAnimation(fig, update, interval=300)
plt.show()

GPIO.cleanup()
