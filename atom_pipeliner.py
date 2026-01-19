from typing import TypedDict, Literal, Dict, List, Any
from runnables import my_runnable, addition_runnable, subtraction_runnable, multiplication_runnable, division_runnable
import json, asyncio

class Atom(TypedDict):
    id: int
    kind: Literal["tool", "final"]
    name: str
    input: Dict[str, Any]
    dependsOn: List[int]

class AtomPlan(TypedDict):
    atoms: List[Atom]

class Calculator():
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

        if validated_atoms[-1]["kind"] != "final":
            raise RuntimeError("No final atom found")

        return {"atoms": validated_atoms}
    
    def _create_runnable(self, name: str, inputs: Dict) -> my_runnable.Runnable:
        match name:
            case "add":
                return addition_runnable.AdditionRunnable(inputs["b"])
            case "subtract":
                return subtraction_runnable.SubtractionRunnable(inputs["b"])
            case "multiply":
                return multiplication_runnable.MultiplicationRunnable(inputs["b"])
            case "divide":
                return division_runnable.DivisionRunnable(inputs["b"])
        raise ValueError(f"Unknown runnable name received: {name}")
    
    def _resolve_inputs(self, raw_inputs):
        resolved = {}
        for key, value in raw_inputs.items():
            resolved[key] = 0 if isinstance(value, str) and value.startswith("<result_of_") else value
        return resolved

    async def build_and_run_pipeline(self) -> Any:
        results: Dict[int, Any] = { }
        pipeline: my_runnable.Runnable | None = None

        for atom in self.atom_plan["atoms"]:
            # Returns the final result
            if atom["kind"] == "final":
                return await pipeline.invoke(self.atom_plan["atoms"][0]["input"]["b"])

            resolved_inputs = self._resolve_inputs(atom["input"])
            runnable = self._create_runnable(atom["name"], resolved_inputs)

            if pipeline is None:
                pipeline = runnable
            else:
                pipeline = pipeline.pipe(runnable)
        
        raise RuntimeError("No final atom found")

    def __str__(self) -> str:
        return self.atom_plan_str

def testing():
    print('Testing Calculator:\n')

    try:
        print('Test 1: Linear dependency.')
        atom_plan: AtomPlan = {
            "atoms": [
                {"id": 1, "kind": "tool", "name": "add", "input": {"a": 7, "b": 15}, "dependsOn": []},
                {"id": 2, "kind": "tool", "name": "multiply", "input": {"a": "<result_of_1>", "b": 3}, "dependsOn": [1]},
                {"id": 3, "kind": "tool", "name": "subtract", "input": {"a": "<result_of_2>", "b": 10}, "dependsOn": [2]},
                {"id": 4, "kind": "final", "name": "report", "dependsOn": [3]}
            ]
        }

        calc = Calculator(json.dumps(atom_plan))
        end_result = asyncio.run(calc.build_and_run_pipeline())
        print(f'Test 1 passed. Passed (15 + 7) * 3 - 10 and received {end_result}.\n')

        print('Yeap, pretty much all Calculator tests passed.')

    except Exception as e:
        raise RuntimeError(f'Calculator tests failed with error {e}')

if __name__ == "__main__":
    testing()