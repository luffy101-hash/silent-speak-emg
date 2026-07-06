# Wiring

## Grove EMG → ESP32-S3 DevKitC-1

| Grove EMG | Wire | ESP32-S3 |
|-----------|------|----------|
| VCC (red) | 3.3V | 3V3 |
| GND (black) | GND | GND |
| SIG (yellow) | analog | GPIO 1 to 4 |

Use separate Grove boards for channels 1 to 4 on GPIO 1, 2, 3, 4.

## Electrodes

- **Masseter:** lower-rear inside each earmuff (jaw clench)
- **Temporalis:** upper inside each earmuff (temple)
- **Reference:** earlobe clip, shared across all boards

## Bench test without headphones

Tape electrodes to jaw/cheek, reference on earlobe, run USB serial to laptop.
