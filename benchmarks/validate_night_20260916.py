"""Validate external repair scorers against known-good and seeded-bug code."""
import inspect
import pathlib
import tempfile
import night_tasks_20260916 as tasks

with tempfile.TemporaryDirectory(prefix='night_scorer_validation_') as directory:
    path=pathlib.Path(directory)/'solution.py'
    for kind,fixture in tasks.TASKS.items():
        path.write_text(fixture['code'])
        baseline=tasks.evaluate(kind,path)
        assert baseline['passed']<baseline['total'], (kind,baseline)
        reference=tasks.reference_graph if kind=='graph' else tasks.reference_intervals
        function_name='plan' if kind=='graph' else 'merge'
        path.write_text(inspect.getsource(reference)+f'\n{function_name}={reference.__name__}\n')
        correct=tasks.evaluate(kind,path)
        assert correct['passed']==correct['total'], (kind,correct)
        print(kind, 'seeded bug', baseline['passed'], '/', baseline['total'], 'reference',correct['passed'],'/',correct['total'])
