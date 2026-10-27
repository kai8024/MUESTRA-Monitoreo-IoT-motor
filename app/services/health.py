"""Línea base, desviaciones (z-score), índice de salud y semáforo inteligente (sección 15.3)."""
import statistics
from datetime import datetime

from flask import current_app

from .. import db
from ..models import LineaBase, Medicion

VARIABLES = ["temperatura", "vibracion", "desequilibrio_corriente", "desequilibrio_tension"]


def obtener_linea_base():
    return {lb.variable: lb for lb in LineaBase.query.all()}


def recalcular_linea_base(n=None):
    """Construye la línea base con las últimas n mediciones clasificadas NORMAL."""
    n = n or current_app.config["BASELINE_MIN_MUESTRAS"]
    filas = (Medicion.query.filter_by(estado="NORMAL")
             .order_by(Medicion.id.desc()).limit(n).all())
    if len(filas) < n:
        return False
    for var in VARIABLES:
        datos = [getattr(f, var) for f in filas]
        lb = db.session.get(LineaBase, var) or LineaBase(variable=var)
        lb.promedio = statistics.fmean(datos)
        lb.desviacion_estandar = statistics.pstdev(datos)
        lb.fecha_actualizacion = datetime.now()
        db.session.add(lb)
    db.session.commit()
    return True


def calcular_desviaciones(valores, linea_base, std_minima):
    z = {}
    for var in VARIABLES:
        lb = linea_base[var]
        std = max(lb.desviacion_estandar, std_minima[var])
        z[var] = (valores[var] - lb.promedio) / std
    return z


def calcular_indice(desviaciones, pesos, factor):
    penalizacion = factor * sum(pesos[v] * abs(desviaciones[v]) for v in VARIABLES)
    return max(0.0, min(100.0, 100.0 - penalizacion))


def clasificar_semaforo(indices_recientes, umbral_adv, umbral_crit):
    """Usa el promedio de los últimos índices (tendencia sostenida, no un pico aislado)."""
    suavizado = sum(indices_recientes) / len(indices_recientes)
    if suavizado < umbral_crit:
        return "CRITICO"
    if suavizado < umbral_adv:
        return "ADVERTENCIA"
    return "NORMAL"


def evaluar(medicion):
    """Asigna indice_salud y semaforo_inteligente a una medición ya persistida (flush)."""
    cfg = current_app.config
    if not obtener_linea_base():
        if Medicion.query.filter_by(estado="NORMAL").count() >= cfg["BASELINE_MIN_MUESTRAS"]:
            recalcular_linea_base()
    lb = obtener_linea_base()
    if not lb:
        medicion.indice_salud = None
        medicion.semaforo_inteligente = "CALIBRANDO"
        return {}
    valores = {v: getattr(medicion, v) for v in VARIABLES}
    z = calcular_desviaciones(valores, lb, cfg["STD_MINIMA"])
    medicion.indice_salud = round(calcular_indice(z, cfg["PESOS"], cfg["FACTOR_ESCALA"]), 2)
    previos = (Medicion.query.filter(Medicion.id < medicion.id, Medicion.indice_salud.isnot(None))
               .order_by(Medicion.id.desc()).limit(cfg["VENTANA_SUAVIZADO"] - 1).all())
    serie = [medicion.indice_salud] + [m.indice_salud for m in previos]
    medicion.semaforo_inteligente = clasificar_semaforo(
        serie, cfg["SEMAFORO_ADVERTENCIA"], cfg["SEMAFORO_CRITICO"])
    return {k: round(v, 2) for k, v in z.items()}
