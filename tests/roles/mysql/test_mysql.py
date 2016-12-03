def test_mysql_role_installs_mysql(box):
    assert '2.1.4' in box.execute('git --version')


def test_other(box):
    assert '5.6' in box.execute('mysql --version')
