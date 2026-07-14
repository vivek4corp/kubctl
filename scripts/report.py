import json
import os
from jinja2 import Template


DRIFT_FILE = "reports/drift.json"
REPORT_FILE = "reports/report.html"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)



def normalize_drift(data):

    result = []

    for item in data:

        # If drift entry is string
        if isinstance(item, str):

            result.append({
                "resource": item,
                "action": "UNKNOWN",
                "changed_by": "UNKNOWN",
                "time": "UNKNOWN"
            })


        # If drift entry is object
        elif isinstance(item, dict):

            result.append({
                "resource": item.get("resource", "UNKNOWN"),
                "action": item.get("action", "UNKNOWN"),
                "changed_by": item.get("changed_by", "UNKNOWN"),
                "time": item.get("time", "UNKNOWN")
            })

    return result



if not os.path.exists(DRIFT_FILE):
    raise FileNotFoundError(
        f"{DRIFT_FILE} not found"
    )


data = load_json(DRIFT_FILE)

data = normalize_drift(data)


os.makedirs(
    "reports",
    exist_ok=True
)



template = """
<html>

<head>

<title>Terraform Drift Report</title>

<style>

body {
    font-family: Arial, sans-serif;
}

table {
    border-collapse: collapse;
    width:100%;
}

th, td {
    border:1px solid black;
    padding:8px;
}

th {
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



html = Template(template).render(
    data=data
)



with open(
    REPORT_FILE,
    "w",
    encoding="utf-8"
) as f:

    f.write(html)



print("HTML Report Generated:", REPORT_FILE)
