import importlib
import inspect
import os
import pkgutil
from typing import Dict

from core.base_skill import BaseSkill
from core.debug.events import EventLevel
from core.debug.tracer import Tracer, ensure_tracer

class SkillDiscovery:
    def __init__(self, skills_pkg_path: str = "skills", tracer: Tracer | None = None):
        self.skills_pkg_path = skills_pkg_path
        self.skills: Dict[str, BaseSkill] = {}
        self.tracer = ensure_tracer(tracer)

    def discover(self) -> Dict[str, BaseSkill]:
        """
        Varre a pasta de skills e carrega instâncias de classes que herdam de BaseSkill.
        """
        self.skills = {}
        self.tracer.trace(
            "skills.discovery.started",
            level=EventLevel.DEBUG,
            component="core.discovery",
            payload={"skills_package": self.skills_pkg_path},
        )
        
        # Encontra o caminho absoluto do pacote de skills
        pkg = importlib.import_module(self.skills_pkg_path)
        pkg_path = os.path.dirname(pkg.__file__)

        for _, name, is_pkg in pkgutil.iter_modules([pkg_path]):
            if is_pkg:
                continue
            
            full_module_name = f"{self.skills_pkg_path}.{name}"
            try:
                module = importlib.import_module(full_module_name)
                
                # Recarrega o módulo para garantir que pegamos alterações recentes (útil para dev)
                importlib.reload(module)
            except Exception as exc:
                self.tracer.trace(
                    "skill_discovery_failed",
                    level=EventLevel.ERROR,
                    component="core.discovery",
                    message=f"Falha ao importar módulo de skill: {full_module_name}",
                    payload={
                        "module_name": full_module_name,
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    },
                )
                continue

            for _, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, BaseSkill) and 
                    obj is not BaseSkill):
                    try:
                        skill_instance = obj()
                        if hasattr(skill_instance, "set_tracer"):
                            skill_instance.set_tracer(self.tracer)
                        self.skills[skill_instance.name] = skill_instance
                        self.tracer.trace(
                            "skill_discovered",
                            level=EventLevel.INFO,
                            component="core.discovery",
                            message=f"Skill descoberta: {skill_instance.name}",
                            payload={
                                "skill_name": skill_instance.name,
                                "module_name": full_module_name,
                                "class_name": obj.__name__,
                            },
                        )
                    except Exception as exc:
                        self.tracer.trace(
                            "skill_discovery_failed",
                            level=EventLevel.ERROR,
                            component="core.discovery",
                            message=f"Falha ao instanciar skill: {obj.__name__}",
                            payload={
                                "module_name": full_module_name,
                                "class_name": obj.__name__,
                                "error_type": type(exc).__name__,
                                "error": str(exc),
                            },
                        )

        self.tracer.trace(
            "skills.discovery.completed",
            level=EventLevel.DEBUG,
            component="core.discovery",
            payload={"skills_count": len(self.skills)},
        )
        
        return self.skills
