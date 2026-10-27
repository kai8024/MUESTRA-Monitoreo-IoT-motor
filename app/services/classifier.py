"""Cálculo de indicadores y clasificación por umbrales fijos (secciones 15.1 y 15.2).
Funciones puras: no dependen de Flask ni de la BD, así son fáciles de testear."""
import math

NIVELES = {"NORMAL": 0, "ADVERTENCIA": 1, "CRITICO": 2}


def calcular_vibracion(ax, ay, az):
    """Indicador experimental A = sqrt(X²+Y²+Z²) (incluye la gravedad, ~1 g en reposo)."""
    return math.sqrt(ax ** 2 + ay ** 2 + az ** 2)


def calcular_desequilibrio(valores):
    """% = máxima desviación de una fase respecto al promedio / promedio * 100."""
    promedio = sum(valores) / len(valores)
    if promedio < 1e-6:          # motor apagado / sin lectura
        return 0.0
    return max(abs(v - promedio) for v in valores) / promedio * 100.0


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
