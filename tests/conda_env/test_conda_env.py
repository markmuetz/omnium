import os


def test_in_conda_env():
    conda_default_env = os.environ.get('CONDA_DEFAULT_ENV')
    print(conda_default_env)
    assert conda_default_env, 'Not in a conda env'
    assert conda_default_env == 'omnium_testing', 'In the wrong conda env: {}'\
                                                  .format(conda_default_env)
