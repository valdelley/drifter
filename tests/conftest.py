import os
import shutil
import string
import subprocess

import pytest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
TESTS_DIR = os.path.abspath(os.path.dirname(__file__))


class Box:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self._create_environment()

    def _run(self, cmd, read=True):
        env = os.environ.copy()
        env['VAGRANT_CWD'] = self.base_dir
        env['VIRTUALIZATION_PARAMETERS_FILE'] = os.path.join(self.base_dir, 'parameters.yml')
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        proc.wait()

        if read:
            return proc.stdout.read().decode('utf-8')

    def _template(self, src, dest, mapping):
        with open(src) as f:
            raw_file = f.read()

        raw_file_template = string.Template(raw_file)
        templated_file = raw_file_template.substitute(**mapping)

        with open(dest, 'w') as f:
            f.write(templated_file)

    def _create_environment(self):
        self._template(
            os.path.join(TESTS_DIR, 'data/ansible.cfg'),
            os.path.join(self.base_dir, 'ansible.cfg'),
            {'roles_path': os.path.join(BASE_DIR, 'provisioning', 'roles')}
        )

        self._template(
            os.path.join(TESTS_DIR, 'data/parameters.yml'),
            os.path.join(self.base_dir, 'parameters.yml'),
            {'playbook_path': os.path.join(self.base_dir, 'playbook.yml')}
        )

        shutil.copy(
            os.path.join(BASE_DIR, 'provisioning', 'playbook.yml.dist'),
            os.path.join(self.base_dir, 'playbook.yml')
        )

        shutil.copytree(
            os.path.join(BASE_DIR, 'provisioning', 'roles'),
            os.path.join(self.base_dir, 'roles')
        )

        with open(os.path.join(BASE_DIR, 'Vagrantfile.dist')) as f:
            lines = f.readlines()
            lines[-1] = "load '{}'".format(os.path.join(BASE_DIR, 'Vagrantfile'))

        with open(os.path.join(self.base_dir, 'Vagrantfile'), 'w') as f:
            f.write('\n'.join(lines))

    def up(self):
        self._run(['vagrant', 'up', '--provision'], read=False)

    def destroy(self):
        self._run(['vagrant', 'halt'], read=False)
        self._run(['vagrant', 'destroy', '-f'], read=False)

    def execute(self, cmd):
        return self._run(['vagrant', 'ssh', '-c', cmd])


@pytest.fixture(scope='module')
def box(tmpdir_factory):
    vagrant_box = Box(str(tmpdir_factory.mktemp('drifter')))
    vagrant_box.up()
    yield vagrant_box
    vagrant_box.destroy()
