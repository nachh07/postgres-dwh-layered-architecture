"""
Modelos de dominio — Value Objects del pipeline.

Define los tipos de datos inmutables que viajan entre las capas
del pipeline, evitando acoplamiento directo con primitivos.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict


@dataclass(frozen=True)
class StepResult:
    """
    Resultado de un paso individual del pipeline.

    Attributes:
        name:        Nombre descriptivo del paso (ej. "CSV → Landing").
        success:     True si el paso se completó sin errores.
        message:     Mensaje informativo adicional.
        started_at:  Timestamp de inicio.
        finished_at: Timestamp de fin (None si aún corre).
    """

    name: str
    success: bool
    message: str = ""
    started_at: datetime = field(default_factory=datetime.now)
    finished_at: datetime | None = None

    @property
    def elapsed_seconds(self) -> float | None:
        """Segundos transcurridos o None si el paso no finalizó."""
        if self.finished_at is None:
            return None
        return (self.finished_at - self.started_at).total_seconds()


@dataclass(frozen=True)
class PipelineResult:
    """
    Resultado agregado de la ejecución del pipeline completo.

    Attributes:
        success:    True si TODOS los pasos se completaron sin errores.
        steps:      Diccionario {nombre_paso: StepResult} con el detalle.
        started_at: Timestamp de inicio del pipeline.
        finished_at: Timestamp de finalización.
    """

    success: bool
    steps: Dict[str, StepResult] = field(default_factory=dict)
    started_at: datetime = field(default_factory=datetime.now)
    finished_at: datetime | None = None

    @property
    def elapsed_seconds(self) -> float | None:
        """Duración total en segundos."""
        if self.finished_at is None:
            return None
        return (self.finished_at - self.started_at).total_seconds()

    @property
    def failed_steps(self) -> list[str]:
        """Lista de nombres de pasos que fallaron."""
        return [name for name, step in self.steps.items() if not step.success]
