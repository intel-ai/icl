import asyncio
import pathlib
import tarfile
from unittest.mock import AsyncMock, Mock, patch

import dynaconf
import prefect
import pytest
from prefect import filesystems

import infractl
import infractl.base
from infractl.plugins.prefect_runtime import runtime

RuntimeFile = infractl.base.RuntimeFile

FLOW3 = """
import prefect

@prefect.flow
def my_flow_3():
    pass
"""

FLOW4 = """
import prefect

@prefect.flow(name='this-is-flow-4')
def my_flow_4():
    pass
"""


@pytest.mark.asyncio
async def test_deploy(tmp_path: pathlib.Path):
    flow_path = tmp_path / 'flows' / 'flow.py'
    flow_path.parent.mkdir(parents=True, exist_ok=True)
    flow_path.write_text(FLOW3)

    storage_path = tmp_path / 'storage'
    storage_path.mkdir(parents=True, exist_ok=True)
    # set basepath using "file" schema to use LocalFileSystem
    infractl.base.SETTINGS['local.prefect_storage_basepath'] = storage_path.as_uri()

    infrastructure = infractl.infrastructure(address='local')
    prefect_runtime = infractl.runtime()
    program = await infractl.deploy(
        infractl.program(flow_path.as_posix()),
        runtime=prefect_runtime,
        infrastructure=infrastructure,
    )

    # Get a Prefect deployment for this program
    prefect_deployment = program.runner.deployment
    # Note that Prefect changes function name 'my_flow_3' to flow name 'my-flow-3'
    assert prefect_deployment.flow_name == 'my-flow-3'


@pytest.mark.asyncio
async def test_flow_name_from_decorator(tmp_path: pathlib.Path):
    flow_path = tmp_path / 'flows' / 'flow.py'
    flow_path.parent.mkdir(parents=True, exist_ok=True)
    flow_path.write_text(FLOW4)

    storage_path = tmp_path / 'storage'
    storage_path.mkdir(parents=True, exist_ok=True)
    # set basepath using "file" schema to use LocalFileSystem
    infractl.base.SETTINGS['local.prefect_storage_basepath'] = storage_path.as_uri()

    infrastructure = infractl.infrastructure(address='local')
    prefect_runtime = infractl.runtime()
    program = await infractl.deploy(
        infractl.program(flow_path.as_posix()),
        runtime=prefect_runtime,
        infrastructure=infrastructure,
    )

    # Get a Prefect deployment for this program
    prefect_deployment = program.runner.deployment
    assert prefect_deployment.flow_name == 'this-is-flow-4'


@pytest.mark.asyncio
async def test_flow_name_from_argument(tmp_path: pathlib.Path):
    flow_path = tmp_path / 'flows' / 'flow.py'
    flow_path.parent.mkdir(parents=True, exist_ok=True)
    flow_path.write_text(FLOW4)

    storage_path = tmp_path / 'storage'
    storage_path.mkdir(parents=True, exist_ok=True)
    # set basepath using "file" schema to use LocalFileSystem
    infractl.base.SETTINGS['local.prefect_storage_basepath'] = storage_path.as_uri()

    infrastructure = infractl.infrastructure(address='local')
    prefect_runtime = infractl.runtime()
    program = await infractl.deploy(
        infractl.program(flow_path.as_posix()),
        name='my-flow-4-renamed',
        runtime=prefect_runtime,
        infrastructure=infrastructure,
    )

    # Get a Prefect deployment for this program
    prefect_deployment = program.runner.deployment
    assert prefect_deployment.flow_name == 'my-flow-4-renamed'


def test_prefect_runtime_implementation():
    gpu_count = 1
    infrastructure = infractl.infrastructure(address='local', gpus=gpu_count)
    infrastructure_implementation = infractl.base.get_infrastructure_implementation(infrastructure)

    runtime_implementation = runtime.PrefectRuntimeImplementation(
        infractl.runtime(), infrastructure_implementation
    )
    data = {
        'local': {
            'prefect_storage_fsspec': {
                'key': 'key',
                'secret': 'secret',
                'client_kwargs': {'endpoint_url': 'endpoint_url'},
            },
            'prefect_shared_volume_mount': '/data',
        }
    }
    settings = dynaconf.Dynaconf()
    settings.update(data)
    runtime_implementation._settings = settings

    assert runtime_implementation.remote_storage_settings == {
        'key': 'key',
        'secret': 'secret',
        'use_ssl': False,
        'client_kwargs': {
            'endpoint_url': 'endpoint_url',
        },
    }, 'Prefect storage settings are loaded from settings'

    kubernetes_job_block = runtime_implementation.kubernetes_job()
    kubernetes_job_block.name = 'foo'
    kubernetes_job = kubernetes_job_block.build_job()

    assert kubernetes_job['spec']['template']['spec']['containers'][0]['volumeMounts'] == [
        {
            'name': 'shared-volume',
            'mountPath': '/data',
        }
    ], 'Kubernetes Job contains volumeMounts'

    assert kubernetes_job['spec']['template']['spec']['containers'][0]['resources'] == {
        'limits': {"gpu": str(gpu_count)},
    }, 'Kubernetes Job contains resources'

    assert kubernetes_job['spec']['template']['spec']['volumes'] == [
        {
            'name': 'shared-volume',
            'persistentVolumeClaim': {
                'claimName': 'shared-volume',
            },
        }
    ], 'Kubernetes Job contains volumes'


def test_prefect_runtime_customizations():
    infrastructure_implementation = infractl.base.get_infrastructure_implementation(
        infractl.infrastructure()
    )
    runtime_implementation = runtime.PrefectRuntimeImplementation(
        runtime=infractl.runtime(),
        infrastructure_implementation=infrastructure_implementation,
    )

    customizations = [
        {
            'op': 'add',
            'path': '/spec/template/spec/containers/1',
            'value': {
                'name': 'second-container',
                'image': 'busybox',
            },
        },
    ]

    runtime_implementation._settings = dynaconf.Dynaconf()
    kubernetes_job_block = runtime_implementation.kubernetes_job(customizations=customizations)
    kubernetes_job_block.name = 'foo'
    kubernetes_job = kubernetes_job_block.build_job()
    print(kubernetes_job)

    assert kubernetes_job['spec']['template']['spec']['containers'][0]['name'] == 'prefect-job'
    assert kubernetes_job['spec']['template']['spec']['containers'][1]['name'] == 'second-container'


def test_prefect_runtime_implementation_environment():
    infrastructure = infractl.infrastructure(address='local')
    infrastructure_implementation = infractl.base.get_infrastructure_implementation(infrastructure)
    runtime_implementation = runtime.PrefectRuntimeImplementation(
        infractl.runtime(environment={'foo': 'bar'}), infrastructure_implementation
    )

    kubernetes_job_block = runtime_implementation.kubernetes_job()
    kubernetes_job_block.name = 'foo'
    kubernetes_job = kubernetes_job_block.build_job()
    kubernetes_job_env = kubernetes_job['spec']['template']['spec']['containers'][0]['env']

    assert {
        'name': 'foo',
        'value': 'bar',
    } in kubernetes_job_env, 'Kubernetes Job contains environment variable foo'


def test_prefect_runtime_implementation_dependencies():
    infrastructure = infractl.infrastructure(address='local')
    infrastructure_implementation = infractl.base.get_infrastructure_implementation(infrastructure)
    runtime_implementation = runtime.PrefectRuntimeImplementation(
        infractl.runtime(dependencies={'pip': ['boto', 'botocore']}), infrastructure_implementation
    )

    kubernetes_job_block = runtime_implementation.kubernetes_job()
    kubernetes_job_block.name = 'foo'
    kubernetes_job = kubernetes_job_block.build_job()
    kubernetes_job_env = kubernetes_job['spec']['template']['spec']['containers'][0]['env']

    assert {
        'name': 'EXTRA_PIP_PACKAGES',
        'value': 'boto botocore',
    } in kubernetes_job_env, 'Kubernetes Job contains environment variable EXTRA_PIP_PACKAGES'


@pytest.mark.asyncio
async def test_prefect_runtime_upload_files(tmp_path: pathlib.Path, set_cwd):
    storage_path = tmp_path / 'storage'
    working_path = tmp_path / 'working'

    file1_path = working_path / 'file1'

    storage_path.mkdir()
    working_path.mkdir()

    file1_path.write_text('This is file1')

    block = runtime.PrefectBlock(
        kind='local-file-system',
        name='test',
        block=filesystems.LocalFileSystem(basepath=storage_path),
    )

    infrastructure = infractl.infrastructure(address='local')
    infrastructure_implementation = infractl.base.get_infrastructure_implementation(infrastructure)
    runtime_implementation = runtime.PrefectRuntimeImplementation(
        infractl.runtime(files=['file1']),
        infrastructure_implementation,
    )

    with set_cwd(working_path):
        await runtime_implementation.upload_files(block)

    assert tarfile.is_tarfile(storage_path / 'cwd.tar')

    script_path = storage_path / runtime_implementation._script
    script = script_path.read_text().splitlines()

    assert script_path.exists(), 'The script exists'
    assert '#!/bin/bash' == script[0], 'The first line of the script is the shebang'


@pytest.mark.asyncio
async def test_infractl_deploy_timeout(tmp_path: pathlib.Path, set_cwd):
    from infractl.plugins.prefect_runtime.runtime import PrefectRuntimeImplementation

    flow_path = tmp_path / 'flow.py'
    flow_path.write_text(FLOW3)

    old_deploy = PrefectRuntimeImplementation.deploy

    async def deploy_and_sleep(*args, **kwargs):
        await asyncio.sleep(5)
        return await old_deploy(*args, **kwargs)

    with set_cwd(flow_path.parent):
        with patch.object(PrefectRuntimeImplementation, 'deploy', new=deploy_and_sleep):
            with pytest.raises(asyncio.exceptions.TimeoutError):
                await infractl.deploy(infractl.program('flow.py'), timeout=0.1)


@pytest.mark.asyncio
async def test_infractl_program_run_timeout(tmp_path: pathlib.Path, set_cwd):
    from infractl.plugins.prefect_runtime.runtime import PrefectProgramRunner

    flow_path = tmp_path / 'flow.py'
    flow_path.write_text(FLOW3)

    with set_cwd(flow_path.parent):
        program = infractl.base.DeployedProgram(
            program=infractl.program('flow.py'),
            runner=PrefectProgramRunner(Mock(), Mock()),
        )

    timeout = 2.5

    # test `prefect.deployments.run_deployment` called with timeout
    run_deployment_mock = AsyncMock(return_value=Mock())
    with patch.object(prefect.deployments, 'run_deployment', new=run_deployment_mock):
        await program.run(timeout=timeout)
    run_deployment_mock.assert_awaited_once()
    run_deployment_mock.await_args.kwargs["timeout"] == timeout

    # test throwing an exception if a flow run does not have time to
    # complete for the specified timeout
    flow_run = Mock()
    flow_run.state.is_final = Mock(return_value=False)

    run_deployment_mock = AsyncMock(return_value=flow_run)
    cancel_mock = AsyncMock()
    with patch.object(prefect.deployments, 'run_deployment', new=run_deployment_mock):
        with patch.object(PrefectProgramRunner, 'cancel', new=cancel_mock):
            with pytest.raises(asyncio.exceptions.TimeoutError):
                await program.run(timeout=timeout)
