"""ICL Kubernetes runtime implementation."""
from typing import Union, Dict, Any, List, Optional

from kubernetes import client

import infractl.base
import infractl.kubernetes as kube


class KubernetesRuntimeImplementation(
    infractl.base.RuntimeImplementation, registration_name='kubernetes'
):
    """Kubernetes runtime implementation."""

    namespace = 'default'
    image: str = 'python:3.9'

    async def deploy(
        self, program: infractl.base.program.Program, **kwargs
    ) -> infractl.base.DeployedProgram:
        """Deploys a program."""
        kube.api().batch_v1().create_namespaced_job(
            namespace=self.namespace,
            body=self.get_job_manifest('test')
        )
        return infractl.base.DeployedProgram(program=program, runner=KubernetesRunner())

    def get_job_manifest(self, name: str) -> client.V1Job:
        """Returns Kubernetes Job manifest."""
        return client.V1Job(
            api_version='batch/v1',
            kind='Job',
            metadata=client.V1ObjectMeta(name=name),
            spec=client.V1JobSpec(
                backoff_limit=1,
                completion_mode='NonIndexed',
                completions=1,
                parallelism=1,
                ttl_seconds_after_finished=600,
                template=client.V1JobTemplateSpec(
                    spec=client.V1PodSpec(
                        containers=[
                            client.V1Container(
                                name='program',
                                image=self.image,
                                image_pull_policy='IfNotPresent',
                                command=['python', '-c', 'print("hello")'],
                            ),
                        ],
                        restart_policy='Never',
                    ),
                ),
            ),
        )


class KubernetesRunner(infractl.base.Runnable):
    """Kubernetes runner."""

    async def run(
            self,
            parameters: Union[Dict[str, Any], List[str], None] = None,
            timeout: Optional[float] = None,
            detach: bool = False,
    ) -> infractl.base.ProgramRun:
        """Runs this runnable.

        Args:
            parameters: a dictionary of named arguments if a program's entry point is a function,
                a list of arguments otherwise.
            timeout: timeout in seconds to wait for a program completion, `None` (default) to wait
                forever.
            detach: `False` (default) to wait for a program completion, `True` to start the program
                and detach from it.
        """
        raise NotImplementedError()
