from datetime import datetime
from . import db


class Medicion(db.Model):
    __tablename__ = "mediciones"
    id = db.Column(db.Integer, primary_key=True)
    fecha_hora = db.Column(db.DateTime, default=datetime.now, nullable=False, index=True)
    temperatura = db.Column(db.Float, nullable=False)
    aceleracion_x = db.Column(db.Float, nullable=False)
    aceleracion_y = db.Column(db.Float, nullable=False)
    aceleracion_z = db.Column(db.Float, nullable=False)
    vibracion = db.Column(db.Float, nullable=False)
    corriente = db.Column(db.Float, nullable=False)
    tension = db.Column(db.Float, nullable=False)
    desviacion_tension = db.Column(db.Float, nullable=False)
    estado = db.Column(db.String(12), nullable=False)            # umbrales fijos
    indice_salud = db.Column(db.Float, nullable=True)            # NULL mientras no hay línea base
    semaforo_inteligente = db.Column(db.String(20), nullable=True)

    def to_dict(self):
        d = {}
        for c in self.__table__.columns:
            v = getattr(self, c.name)
            d[c.name] = v.isoformat(timespec="seconds") if isinstance(v, datetime) else v
        return d


class LineaBase(db.Model):
    __tablename__ = "linea_base"
    variable = db.Column(db.String(40), primary_key=True)
    promedio = db.Column(db.Float, nullable=False)
    desviacion_estandar = db.Column(db.Float, nullable=False)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.now, nullable=False)

    def to_dict(self):
        return {
            "variable": self.variable,
            "promedio": round(self.promedio, 4),
            "desviacion_estandar": round(self.desviacion_estandar, 4),
            "fecha_actualizacion": self.fecha_actualizacion.isoformat(timespec="seconds"),
        }
