import pytest

from app import create_app, db
from app.services import classifier, health


class TestConfig:
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    API_KEY = "test"
    from app.config import Config as _C
    UMBRALES, PESOS, FACTOR_ESCALA, STD_MINIMA = _C.UMBRALES, _C.PESOS, _C.FACTOR_ESCALA, _C.STD_MINIMA
    SEMAFORO_ADVERTENCIA, SEMAFORO_CRITICO = _C.SEMAFORO_ADVERTENCIA, _C.SEMAFORO_CRITICO
    VENTANA_SUAVIZADO = 5
    BASELINE_MIN_MUESTRAS = 10


def test_vibracion_en_reposo_es_1g():
    assert classifier.calcular_vibracion(0, 0, 1) == pytest.approx(1.0)


def test_desequilibrio():
    assert classifier.calcular_desequilibrio([10, 10, 10]) == 0
    assert classifier.calcular_desequilibrio([9, 10, 11]) == pytest.approx(10.0)
    assert classifier.calcular_desequilibrio([0, 0, 0]) == 0   # motor apagado


def test_umbrales_peor_caso():
    from app.config import Config
    v = {"temperatura": 55, "vibracion": 1.0, "desequilibrio_corriente": 2, "desequilibrio_tension": 1}
    estado, det = classifier.clasificar(v, Config.UMBRALES)
    assert estado == "ADVERTENCIA" and det["temperatura"] == "ADVERTENCIA"


def test_semaforo():
    assert health.clasificar_semaforo([95, 90], 80, 60) == "NORMAL"
    assert health.clasificar_semaforo([75, 70], 80, 60) == "ADVERTENCIA"
    assert health.clasificar_semaforo([40, 50], 80, 60) == "CRITICO"


@pytest.fixture
def client():
    app = create_app(TestConfig)
    with app.app_context():
        yield app.test_client()
        db.drop_all()


PAYLOAD = dict(temperatura=42, aceleracion_x=0, aceleracion_y=0, aceleracion_z=1,
               corriente_l1=3.2, corriente_l2=3.2, corriente_l3=3.2,
               tension_l1=220, tension_l2=220, tension_l3=220)


def test_api_rechaza_sin_key(client):
    assert client.post("/api/mediciones", json=PAYLOAD).status_code == 401


def test_api_valida_campos(client):
    r = client.post("/api/mediciones", json={"temperatura": 1}, headers={"X-API-Key": "test"})
    assert r.status_code == 400


def test_flujo_completo_calibra_y_alerta(client):
    h = {"X-API-Key": "test"}
    for i in range(10):
        p = dict(PAYLOAD, temperatura=42 + (i % 3) * 0.2)
        r = client.post("/api/mediciones", json=p, headers=h)
        assert r.status_code == 201
    # tras 10 mediciones normales se construye la línea base
    assert len(client.get("/api/linea-base").get_json()) == 4
    r = client.post("/api/mediciones", json=dict(PAYLOAD, temperatura=48), headers=h).get_json()
    assert r["medicion"]["estado"] == "NORMAL"                 # aún bajo el umbral fijo (50 °C)
    assert r["medicion"]["indice_salud"] < 95                  # pero el índice ya se resiente
