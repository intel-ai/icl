"""Infrastructure for X1 cluster."""

import functools
from typing import Optional, Tuple

import dynaconf

import x1.base


class X1InfrastructureImplementation(x1.base.InfrastructureImplementation, registration_name='X1'):
    """X1 Infrastructure specification."""

    # Custom settings to use instead of global x1.base.SETTINGS
    _settings: Optional[dynaconf.Dynaconf] = None

    @functools.cached_property
    def address(self) -> str:
        """Gets infrastructure address."""
        target = self.infrastructure
        if target.address:
            return target.address
        current_settings = self._settings or x1.base.SETTINGS
        return current_settings.get('default_address', 'localtest.me')

    @functools.cached_property
    def gpus(self) -> Optional[Tuple[str, int]]:
        """Gets GPUs limits."""
        target = self.infrastructure
        if target.gpus:
            return target.gpus
        current_settings = self._settings or x1.base.SETTINGS
        return current_settings.get('default_gpus_limits', None)
