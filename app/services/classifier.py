"""Indicadores y clasificación por umbrales fijos para motor monofásico.
Funciones puras: no dependen de Flask ni de la BD."""
import math

NIVELES = {"NORMAL": 0, "ADVERTENCIA": 1, "CRITICO": 2}


def calcular_vibracion(ax, ay, az):
    """Magnitud de aceleración A = sqrt(X²+Y²+Z²) (incluye gravedad, ~1 g en reposo)."""
    return math.sqrt(ax ** 2 + ay ** 2 + az ** 2)


def calcular_desviacion_porcentual(valor, nominal):
    """|valor - nominal| / nominal * 100. Usado para tensión de red del motor monofásico."""
    if abs(nominal) < 1e-6:
        return 0.0
    return abs(valor - nominal) / abs(nominal) * 100.0


def nivel_variable(valor, advertencia, critico):
    if valor > critico:
        return "CRITICO"
    if valor >= advertencia:
        return "ADVERTENCIA"
    return "NORMAL"


def clasificar(valores, umbrales):
    """Devuelve (estado_global, detalle_por_variable). El global es el peor caso."""
    detalle = {v: nivel_variable(valores[v], *umbrales[v]) for v in umbrales}
    peor = max(detalle.values(), key=lambda n: NIVELES[n])
    return peor, detalle
