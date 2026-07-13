import json
from jinja2 import Template

with open("reports/drift.json", "r") as f:
    data = json.load(f)

template = """
<html>
<head>
<title>Terraform Drift Report</title>
<style>
table {
    border-collapse: collapse;
    width:100%;
}
th, td {
    border:1px solid black;
    padding:8px;
}
th{
    background:#efefef;
}
</style>
</head>

<body>

<h2>Terraform Drift Report</h2>

<table>

<tr>
<th>Resource</th>
<th>Action</th>
<th>Changed By</th>
<th>Time</th>
</tr>

{% for item in data %}
<tr>
<td>{{ item.resource }}</td>
<td>{{ item.action }}</td>
<td>{{ item.changed_by }}</td>
<td>{{ item.time }}</td>
</tr>
{% endfor %}

</table>

</body>
</html>
"""

html = Template(template).render(data=data)

with open("reports/report.html", "w") as f:
    f.write(html)

print("HTML Report Generated")
