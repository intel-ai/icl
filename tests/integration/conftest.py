import re
import time

import pytest
import requests
from kubernetes import client, config, stream


def pytest_addoption(parser):
    parser.addoption(
        '--address',
        action='store',
        default='localtest.me',
        type=str,
        help='ICL infrastructure address, default: localtest.me',
    )
    parser.addoption(
        '--jupyterhub-namespace',
        action='store',
        default='jupyterhub',
        type=str,
        help='ICL infrastructure address, default: jupyterhub',
    )


@pytest.fixture(scope='session')
def address(pytestconfig):
    yield pytestconfig.getoption('--address')


@pytest.fixture(scope='session')
def jupyterhub_namespace(pytestconfig):
    yield pytestconfig.getoption('--jupyterhub-namespace')


@pytest.fixture(scope="session")
def jupyterhub_session_pod_name(jupyterhub_namespace, address):
    """Creates a new JupyterHub session and returns a pod name for this session."""
    username = 'test'
    jupyterhub_address = f"jupyter.{address}"
    jupyterhub_url = f"http://{jupyterhub_address}/hub"
    jupyterhub_login_page = f"{jupyterhub_url}/login"
    jupyterhub_api_url = f"{jupyterhub_url}/api"

    http_session = requests.session()
    r = http_session.get(jupyterhub_login_page)
    assert r.status_code == 200
    xsrf_token = http_session.cookies['_xsrf']

    payload = {'_xsrf': xsrf_token, 'username': username, 'password': ""}
    r = http_session.post(jupyterhub_login_page, data=payload)
    assert r.status_code == 200

    config.load_kube_config()
    core_v1 = client.CoreV1Api()

    hub_all_pods = core_v1.list_namespaced_pod(
        namespace=jupyterhub_namespace, label_selector='component=hub'
    )
    assert len(hub_all_pods.items) == 1

    hub_pod = hub_all_pods.items[0]

    command = ['/bin/sh', '-c', f'jupyterhub token {username}']
    jupyterhub_token = stream.stream(
        core_v1.connect_get_namespaced_pod_exec,
        hub_pod.metadata.name,
        jupyterhub_namespace,
        command=command,
        stderr=False,
        stdin=False,
        stdout=True,
        tty=False,
    ).strip()

    assert len(jupyterhub_token) == 32

    for _ in range(30):
        r = requests.post(
            jupyterhub_api_url + f'/users/{username}/server',
            headers={'Authorization': f'token {jupyterhub_token}'},
            json={'name': username},
        )
        try:
            response_json = r.json()
            # Wait for "session is already started" code
            if response_json['status'] == 400:
                break
        except requests.exceptions.JSONDecodeError:
            pass
        time.sleep(5)

    assert (
        r.status_code == 400
    ), f'Request to {r.url}: got {r.status_code}, expected: 400. Response: {r.text}'

    jupyter_all_test_user_pods = core_v1.list_namespaced_pod(
        namespace=jupyterhub_namespace, label_selector=f'hub.jupyter.org/username={username}'
    ).items
    assert len(jupyter_all_test_user_pods) == 1

    return jupyter_all_test_user_pods[0].metadata.name


def exec_in_pod(api, pod_name, namespace, command):
    return stream.stream(
        api.connect_get_namespaced_pod_exec,
        pod_name,
        namespace,
        command=command,
        stderr=True,
        stdin=False,
        stdout=True,
        tty=False,
    )


# https://github.com/kubernetes-client/python/issues/476#issuecomment-375056804
def copy_file_to_pod(api, pod_name, namespace, source_file, destination_file):
    exec_command = ['/bin/sh']
    resp = stream.stream(
        api.connect_get_namespaced_pod_exec,
        pod_name,
        namespace,
        command=exec_command,
        stderr=True,
        stdin=True,
        stdout=True,
        tty=False,
        _preload_content=False,
    )
    buffer = b''
    with open(source_file, "rb") as file:
        buffer += file.read()

    commands = [
        bytes(f"cat <<'EOF' >{destination_file}\n", 'utf-8'),
        buffer,
        bytes("EOF\n", 'utf-8'),
    ]

    while resp.is_open():
        resp.update(timeout=1)
        if commands:
            cmd = commands.pop(0)
            resp.write_stdin(cmd)
        else:
            break
    assert len(commands) == 0
    resp.close()

    # TODO: "cat <<EOF" the test notebook file into the container
    # TODO: run the notebook and evaluate results


@pytest.fixture(scope="session")
def jupyterhub_enable_ssh(jupyterhub_namespace, jupyterhub_session_pod_name):
    """Enables ssh in the JupyterHub session."""
    config.load_kube_config()
    core_v1 = client.CoreV1Api()

    username, password = "jovyan", "insecure"

    _ = exec_in_pod(
        core_v1,
        jupyterhub_session_pod_name,
        jupyterhub_namespace,
        [
            '/bin/bash',
            '-c',
            'echo "jovyan:insecure" | sudo chpasswd',
        ],
    )

    output = exec_in_pod(
        core_v1,
        jupyterhub_session_pod_name,
        jupyterhub_namespace,
        [
            '/bin/bash',
            # Specify -l (login) option to execute ~/.profile and set conda environment
            '-lc',
            'infractl ssh enable',
        ],
    )

    # output is "Use the following command to log in to your session: ssh jovyan@localtest.me -p 32001"
    matcher = re.search(r'.+: ssh jovyan@([^ ]+) -p (\d+)', output)
    assert matcher, f'output "{output}" matches regex'

    host = matcher.group(1)
    port = int(matcher.group(2))

    yield username, password, host, port
