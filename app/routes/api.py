from functools import wraps

from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import func

from .. import db
from ..models import LineaBase, Medicion
from ..services import classifier, health

api_bp = Blueprint("api", __name__)

CAMPOS = ["temperatura", "aceleracion_x", "aceleracion_y", "aceleracion_z",
          "corriente_l1", "corriente_l2", "corriente_l3",
          "tension_l1", "tension_l2", "tension_l3"]


def requiere_api_key(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if request.headers.get("X-API-Key") != current_app.config["API_KEY"]:
            return jsonify(error="API key inválida"), 401
        return f(*args, **kwargs)
    return wrapper


def validar(data):
    if not isinstance(data, dict):
        raise ValueError("El cuerpo debe ser un objeto JSON")
    faltan = [c for c in CAMPOS if c not in data]
    if faltan:
        raise ValueError(f"Campos faltantes: {', '.join(faltan)}")
    try:
        return {c: float(data[c]) for c in CAMPOS}
    except (TypeError, ValueError):
        raise ValueError("Todos los campos deben ser numéricos")


@api_bp.post("/mediciones")
@requiere_api_key
def crear_medicion():
    try:
        d = validar(request.get_json(silent=True))
    except ValueError as e:
        return jsonify(error=str(e)), 400

    # El backend recalcula los indicadores: no se confía en lo que calcule el ESP32.
    d["vibracion"] = classifier.calcular_vibracion(
        d["aceleracion_x"], d["aceleracion_y"], d["aceleracion_z"])
    d["desequilibrio_corriente"] = classifier.calcular_desequilibrio(
        [d["corriente_l1"], d["corriente_l2"], d["corriente_l3"]])
    d["desequilibrio_tension"] = classifier.calcular_desequilibrio(
        [d["tension_l1"], d["tension_l2"], d["tension_l3"]])

    d["estado"], detalle = classifier.clasificar(d, current_app.config["UMBRALES"])
    m = Medicion(**d)
    db.session.add(m)
    db.session.flush()                      # necesitamos m.id para evaluar el histórico
    desviaciones = health.evaluar(m)
    db.session.commit()
    return jsonify(medicion=m.to_dict(), detalle_umbrales=detalle,
                   desviaciones=desviaciones), 201


@api_bp.get("/mediciones")
def listar_mediciones():
    limit = min(request.args.get("limit", 100, type=int), 1000)
    q = Medicion.query.order_by(Medicion.id.desc())
    if desde := request.args.get("desde"):
        q = q.filter(Medicion.fecha_hora >= desde)
    filas = q.limit(limit).all()
    return jsonify([m.to_dict() for m in reversed(filas)])   # cronológico


@api_bp.get("/estado")
def estado():
    m = Medicion.query.order_by(Medicion.id.desc()).first()
    if not m:
        return jsonify(error="Sin mediciones"), 404
    return jsonify(m.to_dict())


@api_bp.get("/estadisticas")
def estadisticas():
    t = db.session.query(func.avg(Medicion.temperatura), func.max(Medicion.temperatura),
                         func.min(Medicion.temperatura), func.count(Medicion.id)).one()
    dist = dict(db.session.query(Medicion.estado, func.count()).group_by(Medicion.estado).all())
    return jsonify(temperatura={"promedio": t[0], "maxima": t[1], "minima": t[2]},
                   total=t[3], distribucion_estados=dist)


@api_bp.get("/salud")
def salud():
    m = Medicion.query.order_by(Medicion.id.desc()).first()
    if not m:
        return jsonify(error="Sin mediciones"), 404
    lb = health.obtener_linea_base()
    desv = (health.calcular_desviaciones(
        {v: getattr(m, v) for v in health.VARIABLES}, lb, current_app.config["STD_MINIMA"])
        if lb else {})
    return jsonify(indice_salud=m.indice_salud, semaforo_inteligente=m.semaforo_inteligente,
                   desviaciones={k: round(v, 2) for k, v in desv.items()})


@api_bp.get("/linea-base")
def linea_base():
    return jsonify([lb.to_dict() for lb in LineaBase.query.all()])


@api_bp.post("/linea-base/recalcular")
@requiere_api_key
def recalcular_linea_base():
    ok = health.recalcular_linea_base(request.args.get("n", type=int))
    if not ok:
        return jsonify(error="No hay suficientes mediciones NORMAL"), 409
    return jsonify(ok=True)


@api_bp.get("/alertas")
def alertas():
    limit = min(request.args.get("limit", 20, type=int), 200)
    filas = (Medicion.query
             .filter((Medicion.estado != "NORMAL") |
                     Medicion.semaforo_inteligente.in_(["ADVERTENCIA", "CRITICO"]))
             .order_by(Medicion.id.desc()).limit(limit).all())
    return jsonify([m.to_dict() for m in filas])
