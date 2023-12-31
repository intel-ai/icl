import dynaconf

import infractl
import infractl.base
import infractl.docker.remote


def test_manifest_filter():
    settings = dynaconf.Dynaconf()
    settings.update(
        {
            'localtest.me': {
                'registry_internal_endpoint': 'http://internal.endpoint',
            }
        }
    )
    infractl.base.SETTINGS = settings
    builder = infractl.docker.remote.Builder(
        infrastructure=infractl.infrastructure(address='localtest.me')
    )
    manifest = builder.manifest_filter(
        {
            'apiVersion': 'batch/v1',
            'kind': 'Job',
            'metadata': {'labels': {}},
            'spec': {
                'template': {
                    'spec': {
                        'parallelism': 1,
                        'completions': 1,
                        'restartPolicy': 'Never',
                        'containers': [
                            {
                                'name': 'prefect-job',
                                'env': [],
                            }
                        ],
                    }
                }
            },
        }
    )

    job = manifest['spec']
    pod = job['template']['spec']

    assert len(pod['containers']) == 2, 'pod has 2 containers'

    prefect_container = pod['containers'][0]
    dind_container = pod['containers'][1]

    assert prefect_container['name'] == 'prefect-job'
    assert dind_container['name'] == 'dind'
    print(manifest)
