import json
import subprocess
import yaml

def exportCleanFromHistory(outputFile="environment.yaml"):
    print("Exporting Conda packages from history...")
    
    # fetch conda explicit history export
    condaHistoryResult = subprocess.run(
        ["conda", "env", "export", "--from-history"],
        capture_output=True,
        text=True,
        shell=True
    )
    
    if condaHistoryResult.returncode != 0:
        print(f"Error running conda export: {condaHistoryResult.stderr}")
        return

    yamlData = yaml.safe_load(condaHistoryResult.stdout)

    # remove prefix line
    yamlData.pop("prefix", None)

    print("Identifying all Conda-managed packages...")
    
    # fetch full JSON list of packages known to Conda
    condaListResult = subprocess.run(
        ["conda", "list", "--json"],
        capture_output=True,
        text=True,
        shell=True
    )
    
    allCondaPackages = set()
    if condaListResult.returncode == 0:
        condaJsonData = json.loads(condaListResult.stdout)
        for package in condaJsonData:
            # If channel is NOT pypi, Conda manages it!
            if package.get("channel") != "pypi":
                normalizedName = package["name"].lower().replace("_", "-")
                allCondaPackages.add(normalizedName)

    print("Fetching explicit Pip-only packages...")
    
    # fetch Pip packages
    pipResult = subprocess.run(
        ["pip", "list", "--not-required", "--format=freeze"],
        capture_output=True,
        text=True,
        shell=True
    )

    # add any extra sub-dependencies or C-libraries here if pip miscategorizes them
    ignoredPackages = {"pip", "setuptools", "wheel", "brotli", "brotli-python"}

    pipPackages = []
    if pipResult.returncode == 0 and pipResult.stdout.strip():
        for rawLine in pipResult.stdout.strip().splitlines():
            if "==" in rawLine:
                packageName = rawLine.split("==")[0].strip().lower().replace("_", "-")
                
                # only add if not in ignored list and not managed by conda
                if packageName not in ignoredPackages and packageName not in allCondaPackages:
                    pipPackages.append(rawLine)

    # append deduplicated pip packages
    if pipPackages:
        yamlData["dependencies"] = [
            dep for dep in yamlData.get("dependencies", []) 
            if not (isinstance(dep, dict) and "pip" in dep)
        ]
        yamlData["dependencies"].append({"pip": pipPackages})

    # save final file
    with open(outputFile, "w") as targetFile:
        yaml.dump(yamlData, targetFile, sort_keys=False, default_flow_style=False)

    print(f"Done. Clean environment exported to '{outputFile}'")

if __name__ == "__main__":
    exportCleanFromHistory()