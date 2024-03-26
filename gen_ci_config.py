import glob
import json
import os.path
import re

result = {}

for dockerfile in glob.iglob("./**/Dockerfile", recursive=True):
    context = os.path.dirname(dockerfile)
    name = os.path.basename(context)
    assert re.fullmatch(r"[\w-]+", name), f"unsafe name {name!r}"
    with open(dockerfile) as f:
        dependencies = [m.group(1) for m in re.finditer(r"^\s*FROM\s+attemptthisonline/(\S+).*$", f.read(), re.M)]
    build_tag = "attemptthisonline/" + name
    push_tags = [
        tag_base + name + ":" + version
        for tag_base in (
            "registry.gitlab.pxeger.com/attempt-this-online/languages/",
            # "docker.io/attemptthisonline/",  # TODO: login to Docker Hub
        )
        for version in ("$now", "latest")
    ]
    result[f"build {name}"] = {
        "extends": ".base",  # `.build` template is defined in main YAML file
        "needs": [f"build {dep}" for dep in dependencies] or ["init"],
        "script": [
            "now=$(echo $CI_PIPELINE_CREATED_AT | tr T: - | head -c 19)",
            f"podman build --no-cache {context} -t {build_tag}",
            *[f"podman push {build_tag} {push_tag}" for push_tag in push_tags],
        ],
    }

# note YAML 1.2 is backwards-compatible with JSON (but allows comments)
with open(".images.gitlab-ci.yml", "w") as f:
    f.write("# this file is generated by gen_ci_config.py - DO NOT EDIT\n")
    json.dump(result, f)
    f.write("\n")
