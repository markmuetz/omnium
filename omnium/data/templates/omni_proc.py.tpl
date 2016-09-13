import importlib

from omnium.processes import {{ baseclass }}

class {{ process_name_capitalized }}({{ baseclass }}):
    name = '{{ process_name }}'
    out_ext = '{{ out_ext }}'

    def load_modules(self):
        {% if module_names -%}
        {% for module_name in module_names -%}
        self.{{ module_name }} = importlib.import_module('{{ module_name }}')
        {% endfor -%}
        {% else -%}
        pass
        {% endif %}
    def load_upstream(self):
        super({{ process_name_capitalized }}, self).load_upstream()
        # self.data = data 
        # return self.data

    def run(self):
        super({{ process_name_capitalized }}, self).run()
        # self.process_data = self.data
        # return self.process_data

    def save(self):
        super({{ process_name_capitalized }}, self).save()

