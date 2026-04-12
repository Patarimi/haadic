from haadic.main import template


def test_template(tmp_path):
    template(tmp_path, no_input=True)
