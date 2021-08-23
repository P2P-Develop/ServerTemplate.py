import os
import pathlib
import yaml
from importlib import import_module
import re
import json

_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>%%NAME%%</title>
    <link href="https://fonts.googleapis.com/css?family=Open+Sans:400,700|Source+Code+Pro:300,600|Titillium+Web:400,600,700" rel="stylesheet">
    <link rel="stylesheet" type="text/css" href="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/3.43.0/swagger-ui.css" >
    <style>
        [class~=swagger-ui] [class~=info] p,[class~=swagger-ui] [class~=tab] li,[class~=swagger-ui] [class~=info] li,[class~=swagger-ui] a[class~=nostyle]{color:#ccc !important;}html{box-sizing:border-box;}html{overflow:-moz-scrollbars-vertical;}html{overflow-y:scroll;}[class~=swagger-ui] select,.swagger-ui .scheme-container,[class~=swagger-ui] [class~=info] [class~=title]{background-color:#222;}*:before,*,*:after{box-sizing:inherit;}body{margin-left:0;}[class~=swagger-ui] [class~=info] [class~=title],body,[class~=swagger-ui] select,.swagger-ui .scheme-container{color:#ccc;}body{margin-bottom:0;}[class~=swagger-ui] [class~=opblock] [class~=opblock-section-header] label,[class~=swagger-ui] [class~=opblock-description-wrapper] p,[class~=swagger-ui] [class~=parameter__deprecated],[class~=swagger-ui],[class~=swagger-ui] [class~=responses-inner] h4,[class~=swagger-ui] [class~=opblock-title_normal] p,[class~=swagger-ui] [class~=opblock] [class~=opblock-section-header] h4,[class~=swagger-ui] textarea,[class~=swagger-ui] [class~=info] [class~=base-url],[class~=swagger-ui] [class~=btn],[class~=swagger-ui] label,[class~=swagger-ui] [class~=parameter__name],[class~=swagger-ui] [class~=parameter__type],[class~=swagger-ui] [class~=parameter__in],[class~=swagger-ui] [class~=response-col_status],.swagger-ui .opblock .opblock-summary-description,[class~=swagger-ui] [class~=info] table,[class~=swagger-ui] [class~=info] [class~=title],.swagger-ui .responses-inner h5,[class~=swagger-ui] table thead tr th,[class~=swagger-ui] [class~=opblock-external-docs-wrapper] p,[class~=swagger-ui] table thead tr td{color:#ccc !important;}[class~=swagger-ui] [class~=opblock] [class~=opblock-section-header]{background-color:transparent;}body{margin-right:0;}body{margin-top:0;}body{background:#fafafa;}body{background-color:#222;}
    </style>
</head>
<body>
<div id="swagger-ui"></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/3.43.0/swagger-ui-bundle.js"> </script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/3.43.0/swagger-ui-standalone-preset.js"> </script>
<script>
    window.onload = function() {
        window.ui = SwaggerUIBundle({
            spec: "",
            dom_id: '#swagger-ui',
            deepLinking: true,
            presets: [
                SwaggerUIBundle.presets.apis,
                SwaggerUIStandalonePreset
            ],
            plugins: [
                SwaggerUIBundle.plugins.DownloadUrl
            ]
        })
    }
</script>
</body>
</html>
"""

_SWAGGER_TEMPLATE = """
swagger: "2.0"
info:
  description: "API Docs"
  title: "API Document"
  version: "latest"
host: "127.0.0.1"
basePath: "/"
schemes:
- http

"""


def printf(str):
    print(str, end="")


def processStep(target):
    c = 0
    obj = target
    for step in steps:
        c = c + 1
        print(f"\n------------Processing step {c} of {len(steps)}------------")
        obj = step(obj)


global swagger


def whatsTypeOfThisObj(obj):
    typ3 = type(obj)
    if typ3 is dict or typ3 is tuple:
        return "object"
    elif typ3 is bool:
        return "boolean"
    elif typ3 is str:
        return "string"
    elif typ3 is int:
        return "integer"
    elif typ3 is list:
        return "array"
    return None


def clean(obj: dict):
    print("Cleaning...")
    os.remove("docs/swagger.yml")
    print("Minimizing...")
    with open("docs.html", "r", encoding="utf-8") as r:
        abss = r.read()
    with open("docs.html", "w", encoding="utf-8") as w:
        w.write(abss.replace("\n", "").replace("    ", ""))


def genHTML(obj: dict):
    print("Generating docs html...")
    rz = json.dumps(obj)
    with open("docs.html", "w", encoding="utf-8") as w:
        w.write(_HTML_TEMPLATE.replace("\"\"", rz).replace("%%NAME%%", obj["info"]["title"]))


def save(obj: dict):
    print("Exporting swagger settings...")
    if not os.path.exists("docs/"):
        os.mkdir("docs")
    with open("docs/swagger.yml", "w", encoding="utf-8") as w:
        w.write(yaml.dump(obj))
    return obj


def buildSwagger(obj: dict):
    print("Building swagger file...")
    print("Initializing swagger...")
    swagger["paths"] = {}
    for o in obj.items():
        swagger["paths"][o[0]] = o[1]
        print(f"{o[0]} was built successfully.")
    return swagger


def normalizeParams(obj: dict):
    for gz in obj.items():
        for method in list(gz[1].items()):
            print(f"Normalizing parameters of '{gz[0]} - {method[0]}'...")
            if "params" not in gz[1][method[0]]:
                print(f"No parameters was found in '{gz[0]} - {method[0]}'.")
                continue
            for param in list(gz[1][method[0]]["params"]):
                param["description"] = param["about"]
                del param["about"]
                if "required" in param:
                    if param["in"] == "path":
                        param["required"] = True
                elif param["in"] == "path":
                    param["required"] = True
                else:
                    param["required"] = False
            method[1]["parameters"] = method[1]["params"]
            del method[1]["params"]
    return obj


def b(ex):
    properties = {}
    for zz in ex.items():
        tz = whatsTypeOfThisObj(zz[1])
        if tz is "array":

            atField = ""
            for at in zz[1]:
                fa = whatsTypeOfThisObj(at)
                if atField != "" and atField != fa:
                    atField = "object"
                    break
                atField = fa

            if atField == "":
                atField = "object"

            properties[zz[0]] = {
                "type": tz,
                "items": {
                    "type": atField
                }
            }

            if atField == "object":
                i = 0
                properties[zz[0]]["items"]["properties"] = {}
                for hb in zz[1][0].items():
                    ahx = whatsTypeOfThisObj(hb)
                    bz = {
                        "type": ahx,
                        "example": hb[0]
                    }
                    if ahx == "object":
                        bz["example"] = hb[1]
                        properties[zz[0]]["items"]["properties"][hb[0]] = bz
                    else:
                        properties[zz[0]]["items"]["properties"][hb[1]] = bz
                    i = i + 1
                    pass
            elif atField is not None:
                properties[zz[0]]["example"] = zz[1]

        elif tz is not None:
            properties[zz[0]] = {
                "type": tz,
                "example": zz[1]
            }
        else:
            properties[zz[0]] = {
                "type": "string",
                "example": str(zz[1])
            }
    return properties


def buildExample(obj: dict):
    for bb in obj.items():
        for ep in bb[1].items():
            print(f"Building response schema of '{bb[0]}'...")
            if "responses" not in ep[1]:
                print(f"No response schema was found in '{bb[0]}'.")
                continue
            for response in list(ep[1]["responses"].items()):
                a = response[1]
                if "example" not in a:
                    print("No example was found in response.")
                    continue
                ex = a["example"]
                schema = {}
                typ3 = whatsTypeOfThisObj(ex)
                schema["type"] = typ3
                if typ3 == "object":
                    schema["properties"] = b(ex)
                elif typ3 is not None:
                    schema["example"] = ex
                else:
                    schema["type"] = "string"
                    schema["example"] = str(ex)
                response[1]["schema"] = schema
                del response[1]["example"]
    return obj


def normalizeResponses(obj: dict):
    normalized = {}

    for docs in obj.items():
        print(f"Normalizing responses of '{docs[0]}'...")

        doc = docs[1]["responses"]

        for methods in doc.items():
            staging = methods[1]

            staging["summary"] = staging["about"]
            del staging["about"]

            staging["produces"] = [staging["returns"]]
            del staging["returns"]
            staging["responses"] = {}
            for code in list(staging.items()):
                if not str.isdecimal(str(code[0])):
                    continue

                coode = code[1]
                coode["description"] = coode["about"]
                del coode["about"]

                staging["responses"][code[0]] = code[1]
                del staging[code[0]]

            if "params" in docs[1]:
                staging["params"] = docs[1]["params"]
            normalized[docs[0]] = {methods[0]: staging}

    return normalized


def loadAsSwagger(obj):
    swaggers = {}
    for fName in obj:
        if fName.endswith(".py"):
            moduleName = fName[4:-3].replace("/", ".")
            module = import_module(moduleName)
            if "genDoc" not in dir(module):
                print(f"No docs were found in '{moduleName}'.")
                continue
            print(f"Importing docs from endpoint module '{moduleName}'...")

            moduleName = moduleName.replace("server.handler_root", "").replace(".", "/")
            if re.match("^(.+?/|/)?_$", moduleName):
                moduleName = moduleName[:-1]

            swaggers[moduleName] = {
                "responses": module.docs()
            }
            if "params" in dir(module):
                swaggers[moduleName]["params"] = module.params()
        elif fName.endswith(".json"):
            with open(fName, "r", encoding="utf-8") as j:
                doc = json.JSONDecoder().decode(j.read())
                if "docs" not in doc:
                    print(f"No docs were found in '{doc}'.")
                    continue
                print(f"Importing docs from endpoint json '{fName}'...")
                path = fName[:-5].replace("resources/handle", "")
                if re.match("^(.+?/|/)?_$", path):
                    path = path[:-1]
                swaggers[path] = {
                    "responses": doc["docs"]["responses"]
                }

                if "params" in doc["docs"]:
                    swaggers[path]["params"] = doc["docs"]["params"]

    std = sorted(swaggers)
    tmp = {}
    for swg in std:
        tmp[swg] = swaggers[swg]
    return tmp


def loadYaml(obj):
    global swagger
    printf("Loading template...")
    swagger = yaml.load(_SWAGGER_TEMPLATE, Loader=yaml.FullLoader)
    print("Done")
    return obj


def find(obj):
    print("Searching modules...")
    docs = []
    for file in pathlib.Path("src/server/handler_root/").glob("**/*.py"):
        f = "/".join(file.parts)
        print("Found: " + f[:-3])
        if f in docs:
            print(f"ERROR: A conflict has occurred in {f[:3]}.")
        docs.append(f)
    print("Searching files...")
    for file in pathlib.Path("resources/handle/").glob("**/*"):
        f = "/".join(file.parts)
        print("Found: " + f)
        if f in docs:
            print(f"ERROR: A conflict has found in {f}.")
        docs.append(f)
    print(f"Found {len(docs)} endpoint(s).")
    print("Sorting...")
    return docs


steps = [
    find,
    loadYaml,
    loadAsSwagger,
    normalizeResponses,
    buildExample,
    normalizeParams,
    buildSwagger,
    save,
    genHTML,
    clean
]

if __name__ == "__main__":
    print("Generating documents...")
    processStep(steps)
    docPath = os.path.abspath("docs.html")
    print(f"\n\nDocument generated successfully: {docPath}")

def gen():
    processStep(steps)
