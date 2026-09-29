"""
Fixtures para testear los DAGs SIN instalar Airflow.

- Agrega dags/ al sys.path (igual que hace Airflow) para poder importar `dwh_common`.
- `fake_airflow` reemplaza los módulos de Airflow que usan los DAGs por dobles
  mínimos que registran tasks y dependencias, con la misma semántica de `>>`
  que Airflow para tasks, listas y TaskGroups (raíces/hojas del grupo).

Por qué no instalar Airflow en el CI: sus constraints fijan versiones que
chocan con config/requirements.txt y la instalación tarda varios minutos.
La importación real de los DAGs se verifica en Docker con
`airflow dags list-import-errors`.
"""

import runpy
import sys
import types
from itertools import pairwise
from pathlib import Path

import pytest

DAGS_DIR = Path(__file__).resolve().parents[2] / "dags"

if str(DAGS_DIR) not in sys.path:
    sys.path.insert(0, str(DAGS_DIR))


# ---------------------------------------------------------------------------
# Dobles de Airflow
# ---------------------------------------------------------------------------


class FakeDAG:
    """DAG mínimo: guarda sus argumentos y sus tasks por task_id."""

    current: "FakeDAG | None" = None

    def __init__(self, dag_id: str, **kwargs):
        self.dag_id = dag_id
        self.kwargs = kwargs
        self.tasks: dict[str, FakeOperator] = {}

    def __enter__(self):
        FakeDAG.current = self
        return self

    def __exit__(self, *exc):
        FakeDAG.current = None


def _as_downstream(obj) -> list:
    """Tasks que quedan aguas abajo al hacer `x >> obj`."""
    if isinstance(obj, FakeTaskGroup):
        return obj.roots
    if isinstance(obj, list):
        return [t for item in obj for t in _as_downstream(item)]
    return [obj]


def _as_upstream(obj) -> list:
    """Tasks que quedan aguas arriba al hacer `obj >> x`."""
    if isinstance(obj, FakeTaskGroup):
        return obj.leaves
    if isinstance(obj, list):
        return [t for item in obj for t in _as_upstream(item)]
    return [obj]


def _link(upstream, downstream) -> None:
    for up in _as_upstream(upstream):
        for down in _as_downstream(downstream):
            up.downstream.add(down.task_id)
            down.upstream.add(up.task_id)


class _Dependable:
    def __rshift__(self, other):
        _link(self, other)
        return other

    def __rrshift__(self, other):
        _link(other, self)
        return self


class FakeTaskGroup(_Dependable):
    """TaskGroup mínimo: prefija task_ids y expone raíces/hojas del grupo."""

    stack: list["FakeTaskGroup"] = []

    def __init__(self, group_id: str, **kwargs):
        self.group_id = group_id
        self.kwargs = kwargs
        self.children: list[FakeOperator] = []

    def __enter__(self):
        FakeTaskGroup.stack.append(self)
        return self

    def __exit__(self, *exc):
        FakeTaskGroup.stack.pop()

    @property
    def _ids(self) -> set[str]:
        return {t.task_id for t in self.children}

    @property
    def roots(self) -> list:
        return [t for t in self.children if not t.upstream & self._ids]

    @property
    def leaves(self) -> list:
        return [t for t in self.children if not t.downstream & self._ids]


class FakeOperator(_Dependable):
    """PythonOperator mínimo."""

    def __init__(self, task_id: str, python_callable, op_kwargs=None, **kwargs):
        prefix = "".join(f"{g.group_id}." for g in FakeTaskGroup.stack)
        self.task_id = prefix + task_id
        self.python_callable = python_callable
        self.op_kwargs = op_kwargs or {}
        self.kwargs = kwargs
        self.upstream: set[str] = set()
        self.downstream: set[str] = set()
        for group in FakeTaskGroup.stack:
            group.children.append(self)
        FakeDAG.current.tasks[self.task_id] = self


def fake_chain(*tasks) -> None:
    for up, down in pairwise(tasks):
        _link(up, down)


def _module(name: str, **attrs) -> types.ModuleType:
    mod = types.ModuleType(name)
    mod.__dict__.update(attrs)
    return mod


@pytest.fixture
def fake_airflow(monkeypatch):
    """Instala los módulos falsos de Airflow en sys.modules."""
    modules = {
        "airflow": {"DAG": FakeDAG},
        "airflow.models": {},
        "airflow.models.baseoperator": {"chain": fake_chain},
        "airflow.operators": {},
        "airflow.operators.python": {"PythonOperator": FakeOperator},
        "airflow.utils": {},
        "airflow.utils.task_group": {"TaskGroup": FakeTaskGroup},
    }
    for name, attrs in modules.items():
        monkeypatch.setitem(sys.modules, name, _module(name, **attrs))


@pytest.fixture
def load_dag(fake_airflow):
    """Ejecuta un archivo de dags/ y devuelve el objeto `dag` que define."""

    def _load(filename: str) -> FakeDAG:
        namespace = runpy.run_path(str(DAGS_DIR / filename))
        return namespace["dag"]

    return _load
