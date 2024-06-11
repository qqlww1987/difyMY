from textwrap import dedent

import pytest

<<<<<<< HEAD
from core.utils.position_helper import get_position_map
=======
from core.helper.position_helper import get_position_map
>>>>>>> da5f2e168aa3491fff453f84b3393f4a4467be68


@pytest.fixture
def prepare_example_positions_yaml(tmp_path, monkeypatch) -> str:
    monkeypatch.chdir(tmp_path)
    tmp_path.joinpath("example_positions.yaml").write_text(dedent(
        """\
        - first
        - second
        # - commented
        - third
        
        - 9999999999999
        - forth
        """))
    return str(tmp_path)


def test_position_helper(prepare_example_positions_yaml):
    position_map = get_position_map(
        folder_path=prepare_example_positions_yaml,
        file_name='example_positions.yaml')
    assert len(position_map) == 4
    assert position_map == {
        'first': 0,
        'second': 1,
        'third': 2,
        'forth': 3,
    }
