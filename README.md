# Prototipo académico IoT — motor eléctrico monofásico

El sistema monitorea la condición de un **motor eléctrico monofásico** con un **ESP32** (temperatura, vibración, corriente y tensión). Los datos llegan por Wi-Fi al servidor, que calcula un **índice de salud adaptativo** y lo muestra en un panel web con **semáforo inteligente**, para anticipar fallas incipientes.

## Arranque rápido
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env                              # Linux/macOS: cp .env.example .env
python run.py                       # backend + dashboard en http://localhost:5000
python simulator/esp32_simulator.py --escenario normal --n 60 --intervalo 0.2
python simulator/esp32_simulator.py --escenario degradacion --n 80 --intervalo 0.5
pytest
```

Si cambias el esquema de la base, borra `instance/motor.db` y vuelve a arrancar.

## Contrato JSON del ESP32 (`POST /api/mediciones`, header `X-API-Key`)
`temperatura, aceleracion_x, aceleracion_y, aceleracion_z, corriente, tension`

El backend calcula la magnitud de vibración, la desviación porcentual de tensión respecto a 220 V, el estado por umbrales fijos, el índice de salud (z-score frente a la línea base) y el semáforo.

Firmware de referencia: `firmware/esp32_motor_monitor/esp32_motor_monitor.ino`.

## Estructura
- `app/services/classifier.py` umbrales fijos e indicadores
- `app/services/health.py` línea base, índice de salud, semáforo inteligente
- `app/routes/api.py` endpoints REST · `app/templates/index.html` dashboard
- `simulator/` ESP32 simulado · `firmware/` sketch para el hardware · `tests/` pruebas
