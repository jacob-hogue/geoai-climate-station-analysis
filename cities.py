# 20 cities across 5 Köppen climate zones used throughout the analysis.
# Each city was verified to have >85% data coverage from 1950-2023 via NOAA GHCN.
# Altitude in metres above sea level, required by the meteostat Point constructor.

CITIES_BY_ZONE = {
    "tropical": [
        {"name": "Miami",    "latitude": 25.77,  "longitude": -80.19,  "altitude": 2},
        {"name": "Honolulu", "latitude": 21.31,  "longitude": -157.82, "altitude": 5},
        {"name": "San Juan", "latitude": 18.47,  "longitude": -66.12,  "altitude": 19},
        {"name": "Darwin",   "latitude": -12.46, "longitude": 130.84,  "altitude": 30},
    ],
    "arid": [
        {"name": "Phoenix",  "latitude": 33.45,  "longitude": -112.07, "altitude": 331},
        {"name": "Cairo",    "latitude": 30.06,  "longitude": 31.25,   "altitude": 23},
        {"name": "Riyadh",   "latitude": 24.69,  "longitude": 46.72,   "altitude": 612},
        {"name": "Antofagasta","latitude": -23.65, "longitude": -70.40, "altitude": 94},
    ],
    "temperate": [
        {"name": "Tokyo",       "latitude": 35.68,  "longitude": 139.69,  "altitude": 40},
        {"name": "New York",    "latitude": 40.71,  "longitude": -74.01,  "altitude": 10},
        {"name": "Paris",       "latitude": 48.85,  "longitude": 2.35,    "altitude": 35},
        {"name": "Los Angeles", "latitude": 34.05,  "longitude": -118.25, "altitude": 71},
    ],
    "continental": [
        {"name": "Moscow",      "latitude": 55.75,  "longitude": 37.62,   "altitude": 156},
        {"name": "Beijing",     "latitude": 39.91,  "longitude": 116.39,  "altitude": 44},
        {"name": "Minneapolis", "latitude": 44.98,  "longitude": -93.27,  "altitude": 270},
        {"name": "Winnipeg",    "latitude": 49.88,  "longitude": -97.13,  "altitude": 239},
    ],
    "polar": [
        {"name": "Reykjavik",   "latitude": 64.13,  "longitude": -21.90,  "altitude": 52},
        {"name": "Barrow",      "latitude": 71.29,  "longitude": -156.79, "altitude": 11},
        {"name": "Murmansk",    "latitude": 68.97,  "longitude": 33.05,   "altitude": 51},
        {"name": "Churchill",   "latitude": 58.74,  "longitude": -94.07,  "altitude": 29},
    ],
}
