import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///motor.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    API_KEY = os.getenv("API_KEY", "cambia-esta-clave")

    # Placa del motor de laboratorio (prototipo académico).
    # Inducción monofásica 1/2 HP: encaja con ~3.2 A a 220 V / 60 Hz.
    MOTOR = {
        "id": "M1-LAB",
        "nombre": "Motor de pruebas de laboratorio",
        "tipo": "Inducción monofásica con capacitor de arranque",
        "potencia_hp": 0.5,
        "potencia_kw": 0.37,
        "tension_nominal_v": 220.0,
        "corriente_nominal_a": 3.2,
        "frecuencia_hz": 60,
        "velocidad_rpm": 1725,
        "polos": 4,
        "factor_servicio": 1.15,
        "clase_aislamiento": "B",
        "conexion": "Monofásica",
        "uso": "Banco de pruebas académico — monitoreo de condición IoT",
    }
    TENSION_NOMINAL = float(os.getenv("TENSION_NOMINAL", MOTOR["tension_nominal_v"]))

    # Umbrales fijos experimentales (advertencia, crítico).
    # Corriente: sobrecarga. Desviación de tensión: |V - Vnom| / Vnom * 100.
    UMBRALES = {
        "temperatura": (50.0, 65.0),
        "vibracion": (1.2, 2.0),
        "corriente": (4.0, 5.5),
        "desviacion_tension": (5.0, 10.0),
    }

    # Línea base e índice de salud adaptativo (z-score respecto al régimen normal).
    BASELINE_MIN_MUESTRAS = 50
    PESOS = {
        "temperatura": 0.30,
        "vibracion": 0.35,
        "corriente": 0.25,
        "desviacion_tension": 0.10,
    }
    FACTOR_ESCALA = 10.0       # penalización = FACTOR * sum(peso * |z|)
    STD_MINIMA = {             # evita dividir por ~0 si la línea base fue muy estable
        "temperatura": 0.5,
        "vibracion": 0.02,
        "corriente": 0.05,
        "desviacion_tension": 0.2,
    }
    SEMAFORO_ADVERTENCIA = 80.0   # índice suavizado < 80 -> ADVERTENCIA (falla incipiente)
    SEMAFORO_CRITICO = 60.0       # índice suavizado < 60 -> CRÍTICO
    VENTANA_SUAVIZADO = 5         # nº de índices recientes que se promedian
