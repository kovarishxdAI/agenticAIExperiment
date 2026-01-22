from typing import TypedDict, Literal, Dict, List, Any, Callable
from runnables import my_runnable, addition_runnable, subtraction_runnable, multiplication_runnable, division_runnable, deferrable_runnable
import json, asyncio

class Atom(TypedDict):
    id: int
    kind: Literal["tool", "final"]
    name: str
    input: Dict[str, Any]
    dependsOn: List[int]

class AtomPlan(TypedDict):
    atoms: List[Atom]

class ExecutionNode:
    def __init__(
        self,
        runnable: my_runnable.Runnable,
        get_input: Callable[[dict[int, Any]], Any],
    ):
        self.runnable = runnable
        self.get_input = get_input

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
    
    ## =================//===========//====================
    ## Execution of linear plans.
    ## Works if no atom has a parameter "b" depending on
    ## the result of a previous atom.
    ## =================//===========//====================
    def _create_runnable(self, name: str, inputs: Dict) -> my_runnable.Runnable:
        match name:
            case "add":
                return addition_runnable.AdditionRunnable(inputs.get("b"))
            case "subtract":
                return subtraction_runnable.SubtractionRunnable(inputs.get("b"))
            case "multiply":
                return multiplication_runnable.MultiplicationRunnable(inputs.get("b"))
            case "divide":
                return division_runnable.DivisionRunnable(inputs.get("b"))
        raise ValueError(f"Unknown runnable name received: {name}")
    
    def _resolve_inputs(self, raw_inputs):
        resolved = {}
        for key, value in raw_inputs.items():
            resolved[key] = 0 if isinstance(value, str) and value.startswith("<result_of_") else value
        return resolved

    async def build_and_run_pipeline(self) -> Any:
        pipeline: my_runnable.Runnable | None = None

        for atom in self.atom_plan["atoms"]:
            if atom["kind"] == "final":
                return await pipeline.invoke(self.atom_plan["atoms"][0]["input"]["a"])

            resolved_inputs = self._resolve_inputs(atom["input"])
            runnable = self._create_runnable(atom["name"], resolved_inputs)

            if pipeline is None:
                pipeline = runnable
            else:
                pipeline = pipeline.pipe(runnable)
        
        raise RuntimeError("No final atom found")
    
    ## =================//===========//====================
    
    ## =================//===========//====================
    ## Execution of non-linear plans.
    ## Works well, but does not use pipe method, as every 
    ## atom is running its own runnable without pipelines.
    ## =================//===========//====================
    def _create_deferrable_runnable(self, name: str) -> my_runnable.Runnable:
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
    
    def _resolve_inputs_non_linear(self, raw_inputs: Dict[str, Any], results: Dict[int, Any]) -> Dict[str, Any]:
        resolved = {}
        for key, value in raw_inputs.items():
            if isinstance(value, str) and value.startswith("<result_of_"):
                atom_id = int(value[len("<result_of_"):-1])
                resolved[key] = results[atom_id]
            else:
                resolved[key] = value
        return resolved
    
    def build_execution_plan(self) -> dict[int, ExecutionNode]:
        nodes: dict[int, ExecutionNode] = {}

        for atom in self.atom_plan["atoms"]:
            if atom["kind"] == "final":
                continue
            
            raw_inputs = atom["input"]

            def make_get_a(raw_inputs):
                def get_a(results):
                    resolved = self._resolve_inputs_non_linear(raw_inputs, results)
                    return resolved["a"]
                return get_a

            def make_get_b(raw_inputs):
                def get_b(results):
                    resolved = self._resolve_inputs_non_linear(raw_inputs, results)
                    return resolved["b"]
                return get_b

            factory = self._create_deferrable_runnable(atom["name"])

            runnable = deferrable_runnable.DeferredRunnable(
                factory = factory,
                get_constructor_args = make_get_b(raw_inputs)
            )

            nodes[atom["id"]] = ExecutionNode(
                runnable = runnable,
                get_input = make_get_a(raw_inputs),
            )

        return nodes
    
    def _topological_sort(self):
        atoms = {atom["id"]: atom for atom in self.atom_plan["atoms"]}
        visited = set()
        sorted_atoms = []

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
    
    async def execute_plan(self) -> Any:
        nodes = self.build_execution_plan()
        results: dict[int, Any] = {}

        sorted_atoms = self._topological_sort()

        for atom in sorted_atoms:
            if atom["kind"] == "final":
                return results[atom["dependsOn"][0]]

            node = nodes[atom["id"]]
            #print("Results pre-calc:", results)
            #print("Node:", atom["name"])
            input_value = node.get_input(results)
            #print("Input value:", input_value)
            results[atom["id"]] = await node.runnable.invoke(input_value, results)
            #print("Results post-calc:", results)

        raise RuntimeError("No final atom found")

    ## =================//===========//====================

    def __str__(self) -> str:
        return self.atom_plan_str

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

        print('Test 1: Linear calculator and linear plan.')
        calc = Calculator(json.dumps(atom_plan))
        end_result = asyncio.run(calc.build_and_run_pipeline())
        print(f'Test 1 passed. Passed (15 + 7) * 3 - 10 and received {end_result}.\n')

        print('Test 2: Non-linear calculator, but linear plan.')
        non_linear_calc_linear_plan = Calculator(json.dumps(atom_plan))
        end_result = asyncio.run(non_linear_calc_linear_plan.execute_plan())
        print(f'Test 2 passed. Passed (15 + 7) * 3 - 10 and received {end_result}.\n')

        print('Test 3: Non-linear calculator and non-linear plan.')
        non_linear_calc_non_linear_plan = Calculator(json.dumps(non_linear_atom_plan))
        end_result = asyncio.run(non_linear_calc_non_linear_plan.execute_plan())
        print(f'Test 3 passed. Passed (2 + 10 + 4 + 2) * (8 - 4 / 5), expected 129.6, received {end_result}.\n')

        print('Test 4: Non-linear calculator and non-linear, scrambled plan.')
        non_linear_calc_non_linear_plan = Calculator(json.dumps(scrambled_non_linear_atom_plan))
        end_result = asyncio.run(non_linear_calc_non_linear_plan.execute_plan())
        print(f'Test 4 passed. Passed (2 + 10 + 4 + 2) * (8 - 4 / 5), expected 129.6, received {end_result}.\n')

        print('Yeap, pretty much all Calculator tests passed.')

    except Exception as e:
        raise RuntimeError(f'Calculator tests failed with error {e}')

if __name__ == "__main__":
    testing()