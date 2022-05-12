from src.app.model.serializer import read_json_file


def test_read_json_file(project_template_file_name):
    json = read_json_file(json_file_name=project_template_file_name)
    assert json
