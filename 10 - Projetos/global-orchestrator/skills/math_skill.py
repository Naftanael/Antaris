from core.base_skill import BaseSkill
import ast
import operator as op
import statistics
from typing import Any, Dict

class MathSkill(BaseSkill):
    # Operadores permitidos para segurança
    operators = {
        ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
        ast.Div: op.truediv, ast.Pow: op.pow, ast.BitXor: op.xor,
        ast.USub: op.neg
    }

    @property
    def name(self) -> str:
        return "math_skill"

    @property
    def description(self) -> str:
        return "Realiza cálculos matemáticos e estatísticos (média, mediana). Ex: 'average([1,2,3])' ou '2+2'."

    def _safe_eval(self, node):
        if isinstance(node, ast.Num): return node.n
        if isinstance(node, ast.BinOp):
            return self.operators[type(node.op)](self._safe_eval(node.left), self._safe_eval(node.right))
        if isinstance(node, ast.UnaryOp):
            return self.operators[type(node.op)](self._safe_eval(node.operand))
        if isinstance(node, ast.Call):
            if node.func.id == 'average' or node.func.id == 'mean':
                return statistics.mean([self._safe_eval(arg) for arg in node.args[0].elts])
            if node.func.id == 'median':
                return statistics.median([self._safe_eval(arg) for arg in node.args[0].elts])
        raise TypeError(f"Operação não suportada: {type(node)}")

    def execute(self, arguments: Dict[str, Any]) -> Any:
        expression = arguments.get("expression", "").strip()
        if not expression: return "Nenhuma expressão fornecida."
        
        try:
            # Substitui termos comuns para o parser
            expression = expression.replace("average", "mean")
            node = ast.parse(expression, mode='eval').body
            result = self._safe_eval(node)
            return f"Resultado: {result}"
        except Exception as e:
            return f"Erro na execução rápida: {str(e)}"

