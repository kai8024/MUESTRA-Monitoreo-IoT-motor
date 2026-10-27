import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///motor.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    API_KEY = os.getenv("API_KEY", "cambia-esta-clave")

    # Umbrales fijos experimentales (secciones 15.1 y 15.2): (advertencia, crítico)
    UMBRALES = {
        "temperatura": (50.0, 65.0),
        "vibracion": (1.2, 2.0),
        "desequilibrio_corriente": (5.0, 10.0),
        "desequilibrio_tension": (2.0, 4.0),
    }

    # Línea base e índice de salud (sección 15.3) -> calibrar en pruebas
    BASELINE_MIN_MUESTRAS = 50
    PESOS = {
        "temperatura": 0.35,
        "vibracion": 0.35,
        "desequilibrio_corriente": 0.20,
        "desequilibrio_tension": 0.10,
    }
    FACTOR_ESCALA = 10.0       # penalización = FACTOR * sum(peso * |z|)
    STD_MINIMA = {             # evita dividir por ~0 si la línea base fue muy estable
        "temperatura": 0.5,
        "vibracion": 0.02,
        "desequilibrio_corriente": 0.5,
        "desequilibrio_tension": 0.2,
    }
    SEMAFORO_ADVERTENCIA = 80.0   # índice suavizado < 80 -> ADVERTENCIA
    SEMAFORO_CRITICO = 60.0       # índice suavizado < 60 -> CRÍTICO
    VENTANA_SUAVIZADO = 5         # nº de índices recientes que se promedian
