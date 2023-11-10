"""
Tests to verify that ICL Kubernetes runtime and ICL cluster work together.

To run the tests you need a local ICL cluster available at `localtest.me`,
see [docs/kind.md](../../docs/kind.md) for the details.
These tests are intended to be executed outside the cluster.

When using HTTP/HTTPS proxy make sure `localtest.me` is added to "no proxy" lists, such as
`NO_PROXY` and `no_proxy`.
"""

import pytest

import infractl


@pytest.mark.asyncio
async def test_python_program(address):
    infrastructure = infractl.infrastructure(address=address)
    runtime = infractl.runtime(kind='kubernetes')
    program_run = await infractl.run(
        infractl.program('flows/program1.py'), runtime=runtime, infrastructure=infrastructure
    )
    assert program_run.is_completed()
