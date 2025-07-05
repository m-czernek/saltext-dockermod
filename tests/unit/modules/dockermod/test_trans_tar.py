import logging
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

#  pylint: disable-next=import-error,no-name-in-module
import saltext.dockermod.modules.dockermod as docker_mod

log = logging.getLogger(__name__)


@pytest.fixture
def configure_loader_modules():
    return {
        docker_mod: {
            "__utils__": {
                "state.get_sls_opts": MagicMock(
                    return_value={
                        "pillarenv": MagicMock(),
                        "pillar": {},
                        "grains": {},
                    }
                ),
                "args.clean_kwargs": lambda **x: x,
            },
            "__salt__": {
                "config.option": MagicMock(return_value=None),
                "cmd.run": fake_run,
            },
            "__opts__": {
                "id": "dockermod-unit-test",
                "lock_saltenv": False,
                "pillarenv": "base",
                "grains": {},
                "pillar": {},
            },
        },
    }


setattr(configure_loader_modules, "_pytestfixturefunction", True)


def fake_run(*args, **kwargs):
    log.debug("Fake run call args: %s, kwargs: %s", args, kwargs)
    return "{}"


def test_trans_tar_should_have_grains_in_sls_opts_including_pillar_override():
    container_name = "fnord"
    expected_grains = {
        "roscivs": "bottia",
        "fnord": "dronf",
        "salt": "NaCl",
    }
    expected_pillars = {
        "this": {"is": {"my": {"pillar": "data"}}},
    }
    extra_pillar_data = {"some": "extras"}
    fake_trans_tar = MagicMock(return_value=b"hi")
    patch_trans_tar = patch(
        "saltext.dockermod.modules.dockermod._prepare_trans_tar",
        fake_trans_tar,
    )
    patch_call = patch(
        "saltext.dockermod.modules.dockermod.call",
        MagicMock(return_value=expected_grains),
    )
    fake_get_pillar = MagicMock()
    fake_get_pillar.compile_pillar.return_value = expected_pillars
    patch_pillar = patch(
        "saltext.dockermod.modules.dockermod.salt.pillar.get_pillar",
        MagicMock(return_value=fake_get_pillar),
    )
    patch_run_all = patch(
        "saltext.dockermod.modules.dockermod.run_all",
        MagicMock(return_value={"retcode": 1, "stderr": "early exit test"}),
    )
    with patch_trans_tar, patch_call, patch_pillar, patch_run_all:
        docker_mod.sls(container_name, pillar=extra_pillar_data)
        # TODO: It would be fine if we could make this test require less magic numbers -W. Werner, 2019-08-27
        actual_sls_opts = fake_trans_tar.call_args[0][1]
        for (
            key,
            value,
        ) in expected_grains.items():
            assert key in actual_sls_opts["grains"]
            assert value == actual_sls_opts["grains"][key]
        expected_pillars.update(extra_pillar_data)
        for (
            key,
            value,
        ) in expected_pillars.items():
            assert key in actual_sls_opts["pillar"]
            assert value == actual_sls_opts["pillar"][key]
