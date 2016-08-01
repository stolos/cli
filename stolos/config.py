import yaml


class Config(object):
    def __init__(self, **kwargs):
        self._data = kwargs

    def write(self):
        with open('.stolos/config.yaml', 'w+') as fout:
            yaml.safe_dump(self._data, fout, default_flow_style=False)
