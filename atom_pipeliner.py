from typing import TypedDict, Literal, Dict, List, Any
from runnables import json_parser_runnable
import json

class Atom(TypedDict):
    id: int
    kind: Literal["tool", "final"]
    name: str
    input: Dict[str, Any]
    dependsOn: List[int]

class AtomPlan(TypedDict):
    atoms: List[Atom]

class calculator():
    def __init__(self, atom_plan_str: str) -> None:
        self.atom_plan_str = atom_plan_str
        try:
            self.atom_plan: AtomPlan = self._validate_atom_plan(json.loads(self.atom_plan_str))
        except Exception as e:
            raise RuntimeError(f"Failed to parse atom plan to json with error {e}")

    def _validate_atom(self, atom: Dict[str, Any]) -> Atom:
        if not isinstance(atom, dict):
            raise TypeError("Atom must be a dict")
        
        required_keys = ["id", "kind", "name", "dependsOn"]
        for key in required_keys:
            if key not in atom:
                raise KeyError(f"Missing key '{key}' in atom")
            
        if atom["kind"] not in {"tool", "final"}:
            raise ValueError(f"Invalid kind: {atom['kind']}")
        if not isinstance(atom["id"], int):
            raise TypeError("id must be int")
        if not isinstance(atom["dependsOn"], list) or not all(isinstance(i, int) for i in atom["dependsOn"]):
            raise TypeError("dependsOn must be a list of ints")
        
        if atom["kind"] == "tool":
            if "input" not in atom:
                raise KeyError(f"Missing input key in atom '{atom['id']}'")
            if not isinstance(atom["input"], dict):
                raise TypeError("input must be a dict")

            required_input_keys = ["a", "b"]
            for key in required_input_keys:
                if key not in atom["input"]:
                    raise KeyError(f"Missing key '{key}' in  input id '{atom['id']}'")

        return atom 

    def _validate_atom_plan(self, data: Dict[str, Any]) -> AtomPlan:
        if not isinstance(data, dict):
            raise TypeError("AtomPlan must be a dict")
        if "atoms" not in data:
            raise KeyError("Missing 'atoms' key")
        if not isinstance(data["atoms"], list):
            raise TypeError("'atoms' must be a list")
        validated_atoms = [self._validate_atom(a) for a in data["atoms"]]
        return {"atoms": validated_atoms}

    def __str__(self) -> str:
        return self.atom_plan_str

def testing():
    atom_plan: AtomPlan = {
        "atoms": [
            {"id": 1, "kind": "tool", "name": "add", "input": {"a": 15, "b": 7}, "dependsOn": []},
            {"id": 2, "kind": "tool", "name": "multiply", "input": {"a": "<result_of_1>", "b": 3}, "dependsOn": [1]},
            {"id": 3, "kind": "tool", "name": "subtract", "input": {"a": "<result_of_2>", "b": 10}, "dependsOn": [2]},
            {"id": 4, "kind": "final", "name": "report", "dependsOn": [3]}
        ]
    }

    calc = calculator(json.dumps(atom_plan))

    print(calc)
    print(type(calc.atom_plan))
    print(calc.atom_plan)

if __name__ == "__main__":
    testing()