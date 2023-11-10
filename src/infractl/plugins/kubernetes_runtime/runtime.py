"""ICL Kubernetes runtime implementation."""

import infractl.base


class KubernetesRuntimeImplementation(
    infractl.base.RuntimeImplementation, registration_name='kubernetes'
):
    """Kubernetes runtime implementation."""

    async def deploy(
        self, program: infractl.base.program.Program, **kwargs
    ) -> infractl.base.DeployedProgram:
        raise NotImplementedError()
