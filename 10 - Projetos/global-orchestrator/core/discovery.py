import importlib
import inspect
import os
import pkgutil
from typing import Dict, Type
from core.base_skill import BaseSkill

class SkillDiscovery:
    def __init__(self, skills_pkg_path: str = "skills"):
        self.skills_pkg_path = skills_pkg_path
        self.skills: Dict[str, BaseSkill] = {}

    def discover(self) -> Dict[str, BaseSkill]:
        """
        Varre a pasta de skills e carrega instâncias de classes que herdam de BaseSkill.
        """
        self.skills = {}
        
        # Encontra o caminho absoluto do pacote de skills
        pkg = importlib.import_module(self.skills_pkg_path)
        pkg_path = os.path.dirname(pkg.__file__)

        for _, name, is_pkg in pkgutil.iter_modules([pkg_path]):
            if is_pkg:
                continue
            
            full_module_name = f"{self.skills_pkg_path}.{name}"
            module = importlib.import_module(full_module_name)
            
            # Recarrega o módulo para garantir que pegamos alterações recentes (útil para dev)
            importlib.reload(module)

            for _, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, BaseSkill) and 
                    obj is not BaseSkill):
                    
                    skill_instance = obj()
                    self.skills[skill_instance.name] = skill_instance
                    print(f"✅ Skill descoberta: {skill_instance.name}")
        
        return self.skills
