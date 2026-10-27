# Monitoreo IoT de motor trifásico — software

## Arranque rápido
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python run.py                       # backend + dashboard en http://localhost:5000
python simulator/esp32_simulator.py --escenario normal --n 60 --intervalo 0.2   # construye la línea base
python simulator/esp32_simulator.py --escenario degradacion --n 80 --intervalo 0.5
pytest
```
## Contrato JSON del ESP32 (POST /api/mediciones, header `X-API-Key`)
`temperatura, aceleracion_x/y/z, corriente_l1/l2/l3, tension_l1/l2/l3`
El backend calcula vibración, desequilibrios, estado, índice de salud y semáforo.

## Estructura
- `app/services/classifier.py` umbrales fijos e indicadores (funciones puras)
- `app/services/health.py` línea base, z-score, índice de salud, semáforo inteligente
- `app/routes/api.py` endpoints REST · `app/templates/index.html` dashboard
- `simulator/` ESP32 simulado · `tests/` pruebas
