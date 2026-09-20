import csv
import os
import numpy as np
import matplotlib.pyplot as plt

# --------------------------------------------------
# SETTINGS
# --------------------------------------------------

DATA_FILE = "data/sensor_data.csv"
OUTPUT_DIR = "frequency_analysis"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Dataset is sampled once per day
SAMPLING_INTERVAL_SECONDS = 24 * 60 * 60
FS = 1 / SAMPLING_INTERVAL_SECONDS


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

timestamps = []
vibration = []
status = []

with open(DATA_FILE, "r", newline="") as file:
    reader = csv.DictReader(file)

    for row in reader:
        try:
            timestamps.append(row["Timestamp"])
            vibration.append(float(row["Vibration"]))
            status.append(row["Machine_Status"])
        except (ValueError, KeyError):
            continue

vibration = np.array(vibration)
status = np.array(status)

print("Total records:", len(vibration))
print("Sampling frequency:", FS, "Hz")


# --------------------------------------------------
# SEPARATE NORMAL AND ANOMALY DATA
# --------------------------------------------------

normal_signal = vibration[status == "Healthy"]
anomaly_signal = vibration[status == "Failure"]

print("Normal records:", len(normal_signal))
print("Failure records:", len(anomaly_signal))


# --------------------------------------------------
# FFT FUNCTION
# --------------------------------------------------

def calculate_fft(signal):

    # Remove DC component
    signal = signal - np.mean(signal)

    n = len(signal)

    fft_values = np.fft.rfft(signal)

    frequencies = np.fft.rfftfreq(n, d=1 / FS)

    magnitude = np.abs(fft_values) / n

    power = magnitude ** 2

    spectral_energy = np.sum(power)

    # Ignore 0 Hz when finding dominant frequency
    if len(magnitude) > 1:
        dominant_index = np.argmax(magnitude[1:]) + 1
        dominant_frequency = frequencies[dominant_index]
    else:
        dominant_frequency = 0

    return (
        frequencies,
        magnitude,
        power,
        spectral_energy,
        dominant_frequency
    )


# --------------------------------------------------
# CALCULATE FFT
# --------------------------------------------------

normal_freq, normal_mag, normal_power, normal_energy, normal_dominant = \
    calculate_fft(normal_signal)

anomaly_freq, anomaly_mag, anomaly_power, anomaly_energy, anomaly_dominant = \
    calculate_fft(anomaly_signal)


# --------------------------------------------------
# SPECTRAL PEAKS
# --------------------------------------------------

def find_spectral_peaks(frequencies, magnitude, number_of_peaks=5):

    if len(magnitude) <= 1:
        return []

    # Ignore DC component
    indices = np.argsort(magnitude[1:])[-number_of_peaks:] + 1

    indices = indices[np.argsort(magnitude[indices])[::-1]]

    peaks = []

    for index in indices:
        peaks.append(
            (frequencies[index], magnitude[index])
        )

    return peaks


normal_peaks = find_spectral_peaks(
    normal_freq,
    normal_mag
)

anomaly_peaks = find_spectral_peaks(
    anomaly_freq,
    anomaly_mag
)


# --------------------------------------------------
# PRINT RESULTS
# --------------------------------------------------

print("\n========== NORMAL SIGNAL ==========")
print("Dominant frequency:",
      normal_dominant,
      "Hz")

print("Spectral energy:",
      normal_energy)

print("Top spectral peaks:")

for frequency, magnitude in normal_peaks:
    print(
        "Frequency:",
        frequency,
        "Hz | Magnitude:",
        magnitude
    )


print("\n========== ANOMALY SIGNAL ==========")
print("Dominant frequency:",
      anomaly_dominant,
      "Hz")

print("Spectral energy:",
      anomaly_energy)

print("Top spectral peaks:")

for frequency, magnitude in anomaly_peaks:
    print(
        "Frequency:",
        frequency,
        "Hz | Magnitude:",
        magnitude
    )


# --------------------------------------------------
# SAVE FREQUENCY FEATURES
# --------------------------------------------------

features_file = os.path.join(
    OUTPUT_DIR,
    "frequency_features.csv"
)

with open(features_file, "w", newline="") as file:

    writer = csv.writer(file)

    writer.writerow([
        "Condition",
        "Number_of_Samples",
        "Dominant_Frequency_Hz",
        "Spectral_Energy"
    ])

    writer.writerow([
        "Normal",
        len(normal_signal),
        normal_dominant,
        normal_energy
    ])

    writer.writerow([
        "Anomaly",
        len(anomaly_signal),
        anomaly_dominant,
        anomaly_energy
    ])

print("\nFrequency features saved to:")
print(features_file)


# --------------------------------------------------
# PLOT 1 - NORMAL SIGNAL
# --------------------------------------------------

plt.figure(figsize=(10, 5))

plt.plot(normal_signal)

plt.title("Normal Vibration Signal - Time Domain")
plt.xlabel("Sample")
plt.ylabel("Vibration")

plt.tight_layout()

plt.savefig(
    os.path.join(
        OUTPUT_DIR,
        "normal_signal.png"
    )
)

plt.close()


# --------------------------------------------------
# PLOT 2 - ANOMALY SIGNAL
# --------------------------------------------------

plt.figure(figsize=(10, 5))

plt.plot(anomaly_signal)

plt.title("Anomaly Vibration Signal - Time Domain")
plt.xlabel("Sample")
plt.ylabel("Vibration")

plt.tight_layout()

plt.savefig(
    os.path.join(
        OUTPUT_DIR,
        "anomaly_signal.png"
    )
)

plt.close()


# --------------------------------------------------
# PLOT 3 - NORMAL FFT
# --------------------------------------------------

plt.figure(figsize=(10, 5))

plt.plot(normal_freq, normal_mag)

plt.title("Normal Vibration - FFT Magnitude")
plt.xlabel("Frequency (Hz)")
plt.ylabel("Magnitude")

plt.tight_layout()

plt.savefig(
    os.path.join(
        OUTPUT_DIR,
        "normal_fft.png"
    )
)

plt.close()


# --------------------------------------------------
# PLOT 4 - ANOMALY FFT
# --------------------------------------------------

plt.figure(figsize=(10, 5))

plt.plot(anomaly_freq, anomaly_mag)

plt.title("Anomaly Vibration - FFT Magnitude")
plt.xlabel("Frequency (Hz)")
plt.ylabel("Magnitude")

plt.tight_layout()

plt.savefig(
    os.path.join(
        OUTPUT_DIR,
        "anomaly_fft.png"
    )
)

plt.close()


# --------------------------------------------------
# PLOT 5 - NORMAL POWER SPECTRUM
# --------------------------------------------------

plt.figure(figsize=(10, 5))

plt.plot(normal_freq, normal_power)

plt.title("Normal Vibration - Power Spectrum")
plt.xlabel("Frequency (Hz)")
plt.ylabel("Power")

plt.tight_layout()

plt.savefig(
    os.path.join(
        OUTPUT_DIR,
        "normal_power_spectrum.png"
    )
)

plt.close()


# --------------------------------------------------
# PLOT 6 - ANOMALY POWER SPECTRUM
# --------------------------------------------------

plt.figure(figsize=(10, 5))

plt.plot(anomaly_freq, anomaly_power)

plt.title("Anomaly Vibration - Power Spectrum")
plt.xlabel("Frequency (Hz)")
plt.ylabel("Power")

plt.tight_layout()

plt.savefig(
    os.path.join(
        OUTPUT_DIR,
        "anomaly_power_spectrum.png"
    )
)

plt.close()


print("\n========== FFT ANALYSIS COMPLETE ==========")
print("Plots saved in:", OUTPUT_DIR)