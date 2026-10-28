"""Simula el ESP32 enviando mediciones de un motor monofásico al backend.
Uso:
  python simulator/esp32_simulator.py --escenario normal --n 60 --intervalo 0.2
  python simulator/esp32_simulator.py --escenario degradacion --n 80 --intervalo 0.5
Escenarios: normal | calor | vibracion | sobrecarga | subtension | degradacion
"""
import argparse
import random
import time

import requests


def lectura(escenario, i):
    g = random.gauss
    temp, vib_extra, i_factor, v_offset = g(42, 0.4), 0.0, 1.0, 0.0
    if escenario == "calor":
        temp += 0.35 * i
    elif escenario == "vibracion":
        vib_extra = min(0.02 * i, 0.9)
    elif escenario == "sobrecarga":
        i_factor = 1 + min(0.008 * i, 0.45)
    elif escenario == "subtension":
        v_offset = -min(0.6 * i, 28)
    elif escenario == "degradacion":
        # Deriva lenta: el índice de salud debe advertir antes que los umbrales fijos.
        temp += 0.08 * i
        vib_extra = 0.004 * i
        i_factor = 1 + 0.002 * i
        v_offset = -0.08 * i
    return {
        "temperatura": round(temp, 2),
        "aceleracion_x": round(g(0, 0.03) + g(0, vib_extra), 4),
        "aceleracion_y": round(g(0, 0.03) + g(0, vib_extra), 4),
        "aceleracion_z": round(g(1.0, 0.03) + g(0, vib_extra), 4),
        "corriente": round(g(3.2, 0.04) * i_factor, 3),
        "tension": round(g(220, 0.8) + v_offset, 2),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--url", default="http://localhost:5000/api/mediciones")
    p.add_argument("--key", default="cambia-esta-clave")
    p.add_argument("--escenario", default="normal",
                   choices=["normal", "calor", "vibracion", "sobrecarga", "subtension", "degradacion"])
    p.add_argument("--n", type=int, default=60)
    p.add_argument("--intervalo", type=float, default=1.0)
    a = p.parse_args()
    for i in range(a.n):
        r = requests.post(a.url, json=lectura(a.escenario, i), headers={"X-API-Key": a.key}, timeout=5)
        m = r.json().get("medicion", {})
        print(f"[{i:03d}] {r.status_code} estado={m.get('estado')} "
              f"salud={m.get('indice_salud')} semaforo={m.get('semaforo_inteligente')}")
        time.sleep(a.intervalo)


if __name__ == "__main__":
    main()
