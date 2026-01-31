from typing import TypedDict, Literal, Dict, List, Any, TypeVar
from runnables import my_runnable, addition_runnable, subtraction_runnable, multiplication_runnable, division_runnable, deferrable_runnable
from collections.abc import Mapping
import json, asyncio

class Atom(TypedDict):
    id: int
    kind: Literal["tool", "final"]
    name: str
    input: Dict[str, Any]
    dependsOn: List[int]

class AtomPlan(TypedDict):
    atoms: List[Atom]


OutputT = TypeVar("OutputT", float, int)
ConfigT = TypeVar("ConfigT", bound=Mapping)

## ========================================//===========//========================================
## Execution of linear or non-linear plans.
## ========================================//===========//========================================
class CalculatorRunnable(my_runnable.Runnable[str, OutputT, ConfigT]):
    """
    A class that executes a series of operations defined in an atom plan, resolving dependencies 
    and applying the corresponding operations in a topologically sorted order.

    The `CalculatorRunnable` class is designed to handle a series of computational tasks, each represented 
    as an "atom" in the atom plan. It performs plan validation, resolves dependencies, and executes the 
    operations defined in the atom plan.

    Atoms in the plan are either "tool" (intermediate operations) or "final" (the last operation, 
    whose result is returned). The class manages input resolution, execution order, and error handling 
    during the pipeline execution.

    Example for (15 + 7) * 3 - 10:
    {
        "atoms": [
            {"id": 1, "kind": "tool", "name": "add", "input": {"a": 15, "b": 7}, "dependsOn": []},
            {"id": 2, "kind": "tool", "name": "multiply", "input": {"a": "<result_of_1>", "b": 3}, "dependsOn": [1]},
            {"id": 3, "kind": "tool", "name": "subtract", "input": {"a": "<result_of_2>", "b": 10}, "dependsOn": [2]},
            {"id": 4, "kind": "final", "name": "report", "dependsOn": [3]}
        ]
    }
    """
    def __init__(self, config: ConfigT | None = None) -> None:
        super().__init__(config=config)
        self.name = self.__class__.__name__

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
    
    def _get_factory(self, name: str) -> my_runnable.Runnable:
        match name:
            case "add":
                return lambda b: addition_runnable.AdditionRunnable(b)
            case "subtract":
                return lambda b: subtraction_runnable.SubtractionRunnable(b)
            case "multiply":
                return lambda b: multiplication_runnable.MultiplicationRunnable(b)
            case "divide":
                return lambda b: division_runnable.DivisionRunnable(b)
        raise ValueError(f"Unknown runnable name received: {name}")
    
    def _resolve_inputs(self, raw_inputs: Dict[str, Any], results: Dict[int, Any]) -> Dict[str, Any]:
        resolved = {}
        for key, value in raw_inputs.items():
            if isinstance(value, str) and value.startswith("<result_of_"):
                atom_id = int(value[len("<result_of_"):-1])
                resolved[key] = results[atom_id]
            else:
                resolved[key] = value
        return resolved
    
    def _topological_sort(self) -> AtomPlan:
        atoms = {atom["id"]: atom for atom in self.atom_plan["atoms"]}
        visited = set()
        sorted_atoms: AtomPlan = []

        def visit(atom_id):
            if atom_id in visited:
                return
            for dep_id in atoms[atom_id].get("dependsOn", []):
                visit(dep_id)
            visited.add(atom_id)
            sorted_atoms.append(atoms[atom_id])

        for atom_id in atoms:
            visit(atom_id)

        return sorted_atoms
    
    def _build_execution_plan(self) -> my_runnable.Runnable:
        pipeline: my_runnable.Runnable = []
        self.sorted_atoms = self._topological_sort()

        for atom in self.sorted_atoms:
            if atom["kind"] == "final":
                continue
            
            raw_inputs = atom["input"]

            def make_get_a(raw_inputs):
                def get_a(results):
                    resolved = self._resolve_inputs(raw_inputs, results)
                    return resolved["a"]
                return get_a

            def make_get_b(raw_inputs):
                def get_b(results):
                    resolved = self._resolve_inputs(raw_inputs, results)
                    return resolved["b"]
                return get_b

            factory = self._get_factory(atom["name"])

            runnable = deferrable_runnable.DeferredRunnable(
                factory = factory,
                get_constructor_arg = make_get_b(raw_inputs),
                get_invoke_arg = make_get_a(raw_inputs),
                config = { "signature": atom["id"] }
            )

            pipeline = pipeline | runnable if pipeline else runnable

        return pipeline
    
    async def _call(self, atom_plan: str | dict, config: ConfigT | None = None) -> OutputT:
        """
        Executes the provided atom plan, resolving dependencies and running the corresponding operations in the correct order.

        This method takes an atom plan (either as a JSON string or a dictionary) and performs the following steps:
        
        1. **Parsing and Validation**: The atom plan is parsed from JSON (if given as a string) and validated.
           This ensures that all required keys and structures are present and correct.
        
        2. **Building Execution Plan**: A topological sort of the atoms is performed to determine the correct
           order of execution, resolving dependencies as needed.
        
        3. **Running Operations**: For each atom (excluding the final one), the appropriate runnable 
           operation is created based on its name, and inputs are resolved. The operations are then 
           executed sequentially.

        4. **Returning the Result**: The result of the final atom (the last operation in the pipeline) 
           is returned as the output of the method.

        Args:
            atom_plan (str | dict): The atom plan, either as a JSON string or a Python dictionary.
            config (ConfigT | None, optional): Optional configuration to pass to the execution pipeline.

        Returns:
            OutputT: The result of executing the atom plan, which can be an integer or float.
        
        Raises:
            RuntimeError: If parsing or validating the atom plan fails, or if any execution error occurs.

        Example:
            atom_plan = '{"atoms": [{"id": 1, "kind": "tool", "name": "add", "input": {"a": 2, "b": 3}, "dependsOn": []}, {"id": 2, "kind": "final", "name": "result", "input": {}, "dependsOn": [1]}]}'
            result = await calculator._call(atom_plan)
            print(result)  # Should output 5 if the atom plan performs an addition.
        """
        try:
            atom_plan_json = json.loads(atom_plan) if isinstance(atom_plan, str) else atom_plan
            self.atom_plan: AtomPlan = self._validate_atom_plan(atom_plan_json)
        except Exception as e:
            raise RuntimeError(f"Failed to parse atom plan to json with error {e}")

        pipeline = self._build_execution_plan()
        output = await pipeline.invoke(1, {})

        return output



def testing():
    print('Testing Calculator:\n')

    try:
        atom_plan: AtomPlan = {
            "atoms": [
                {"id": 1, "kind": "tool", "name": "add", "input": {"a": 15, "b": 7}, "dependsOn": []},
                {"id": 2, "kind": "tool", "name": "multiply", "input": {"a": "<result_of_1>", "b": 3}, "dependsOn": [1]},
                {"id": 3, "kind": "tool", "name": "subtract", "input": {"a": "<result_of_2>", "b": 10}, "dependsOn": [2]},
                {"id": 4, "kind": "final", "name": "report", "dependsOn": [3]}
            ]
        }

        non_linear_atom_plan: AtomPlan = {
            "atoms": [
                { "id": 1, "kind": "tool", "name": "add", "input": {"a": 2, "b": 10}, "dependsOn": [] },
                { "id": 2, "kind": "tool", "name": "add", "input": {"a": "<result_of_1>", "b": 4}, "dependsOn": [1] },
                { "id": 3, "kind": "tool", "name": "add", "input": {"a": "<result_of_2>", "b": 2}, "dependsOn": [2] },
                { "id": 4, "kind": "tool", "name": "divide", "input": {"a": 4, "b": 5}, "dependsOn": [] },
                { "id": 5, "kind": "tool", "name": "subtract", "input": {"a": 8, "b": "<result_of_4>"}, "dependsOn": [4] },
                { "id": 6, "kind": "tool", "name": "multiply", "input": {"a": "<result_of_3>", "b": "<result_of_5>"}, "dependsOn": [3, 5] },
                { "id": 7, "kind": "final", "name": "report", "dependsOn": [6] }
            ]
        }

        scrambled_non_linear_atom_plan: AtomPlan = {
            "atoms": [
                { "id": 1, "kind": "tool", "name": "add", "input": {"a": 2, "b": 10}, "dependsOn": [] },
                { "id": 2, "kind": "tool", "name": "add", "input": {"a": "<result_of_1>", "b": 4}, "dependsOn": [1] },
                { "id": 3, "kind": "tool", "name": "add", "input": {"a": "<result_of_2>", "b": 2}, "dependsOn": [2] },
                { "id": 4, "kind": "tool", "name": "multiply", "input": {"a": "<result_of_3>", "b": "<result_of_6>"}, "dependsOn": [3, 6] },
                { "id": 5, "kind": "tool", "name": "divide", "input": {"a": 4, "b": 5}, "dependsOn": [] },
                { "id": 6, "kind": "tool", "name": "subtract", "input": {"a": 8, "b": "<result_of_5>"}, "dependsOn": [5] },
                { "id": 7, "kind": "final", "name": "report", "dependsOn": [4] }
            ]
        }

        calc = CalculatorRunnable()

        print('Test 1: Linear plan.')
        end_result = asyncio.run(calc.invoke(json.dumps(atom_plan)))
        assert end_result == 56, f"Expected 56, got {end_result}."
        print(f'Test 1 passed. Passed (15 + 7) * 3 - 10, expected 56, and received {end_result}.\n')

        print('Test 2: Non-linear, but ordered plan.')
        end_result = asyncio.run(calc.invoke(json.dumps(non_linear_atom_plan)))
        assert end_result == 129.6, f"Expected 129.6, got {end_result}."
        print(f'Test 2 passed. Passed (2 + 10 + 4 + 2) * (8 - 4 / 5), expected 129.6, received {end_result}.\n')

        print('Test 3: Non-linear, unordered plan.')
        end_result = asyncio.run(calc.invoke(json.dumps(scrambled_non_linear_atom_plan)))
        assert end_result == 129.6, f"Expected 129.6, got {end_result}."
        print(f'Test 3 passed. Passed (2 + 10 + 4 + 2) * (8 - 4 / 5), expected 129.6, received {end_result}.\n')

        print('Yeap, pretty much all Calculator tests passed.')

    except AssertionError as e:
        raise RuntimeError(f'Test failed with error: {e}')
    except Exception as e:
        raise RuntimeError(f'Calculator tests failed with error: {e}')

if __name__ == "__main__":
    testing()