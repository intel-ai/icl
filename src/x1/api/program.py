"""X1 creating program functionality."""

import x1.base


def program(*args, kind: str = 'prefect', **kwargs) -> x1.base.Program:
    """Create a program.

    Args:
        args:
            Any positional arguments for `kind` program.
        kind:
            Kind of program, default is "prefect".
        kwargs:
            Any keywords arguments for `kind` program.

    Examples:
        1. Python file with Prefect flow:
            program('my_flow.py')
        2. Imported Prefect flow:
            from my_flow import flow1
            program(flow1)
    """
    if kind == 'prefect':
        # pylint: disable=import-outside-toplevel
        from x1.plugins import prefect_runtime

        return prefect_runtime.load_program(*args, **kwargs)

    raise NotImplementedError(f'Program kind f{kind} is not supported')
