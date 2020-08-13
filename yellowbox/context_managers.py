from contextlib import contextmanager, nullcontext, AbstractContextManager
from typing import Generator, TypeVar, Callable

from docker.models.containers import Container as DockerContainer
from docker.models.networks import Network as DockerNetwork
from yaspin import yaspin

_T = TypeVar("_T")
_CT = TypeVar("_CT", bound=DockerContainer)
_NT = TypeVar("_NT", bound=DockerNetwork)
_Gen = Generator[_T, None, None]

_DEFAULT_TIMEOUT = 10


@contextmanager
def killing(container: _CT, *, timeout: float = _DEFAULT_TIMEOUT, signal: str = 'SIGKILL') -> _Gen[_CT]:
    """A context manager that kills a docker container upon completion.

    Example:
        container = DockerContainer(...)
        with killing(container):
            ...
        # Container is now killed with SIGKILL

    Args:
        container: Container to kill upon completion
        timeout: Time to wait for container to be killed after sending a signal.
        Defaults to 10 seconds.
        signal: The signal to send to the container

    Returns:
        A context manager to be used in a 'with' statement.
    """
    try:
        yield container
    finally:
        if container.status.lower() not in ('exited', 'stopped'):
            container.kill(signal)
            container.wait(timeout=timeout)


@contextmanager
def disconnecting(network: _NT) -> _Gen[_NT]:
    """A context manager that disconnects a docker network upon completion.

    Example:
        network = DockerNetwork(...)
        with disconnecting(network):
            ...
        # Network is now disconnected from all containers and is removed
        # from docker.

    Args:
        network: Network to disconnect upon completion.

    Returns:
        A context manager to be used in a 'with' statement.
    """
    try:
        yield network
    finally:
        for container in network.containers:
            network.disconnect(container)
        network.remove()


@contextmanager
def spinner(text):
    with yaspin(text=text) as spinner:
        try:
            yield
        except Exception:
            spinner.fail("💥 ")
            raise
        spinner.ok("✅ ")


def get_spinner(s) -> Callable[[str], AbstractContextManager]:
    if s:
        return spinner
    return nullcontext
