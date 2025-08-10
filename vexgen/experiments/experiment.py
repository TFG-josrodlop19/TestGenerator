from os import makedirs, system
from os.path import exists

from requests import post

# First, open the file with the info of each sbom file
with open("repos_sbom.txt") as txt_file:
    system("rm -rf tests/")
    if not exists("tests/"):
        makedirs("tests/")
    for line in txt_file.read().split("\n"):
        owner_name, sbom_path = line.split(":")
        owner, name = owner_name.split("/")

        # Change the variable statements_group for any value like [no_clustering, cwe_type, attack_vector_av, attack_vector_ac,
        # attack_vector_au, attack_vector_c, attack_vector_i, attack_vector_a, reachable_code] to creare clusters
        statements_group = "no_grouping"

        # Change the user id if you want all VEXs to be associated with your user, if you want to use the frontend
        GenerateVEXRequest = {
            "owner": owner,
            "name": name,
            "sbom_path": sbom_path,
            "statements_group": statements_group,
            "user_id": "66c8ad4f9d81a71dc2a9de39"
        }

        # Second, generate the VEX and extended VEX file for each sbom file
        response = post(
            "http://localhost:8000/vex/generate",
            json=GenerateVEXRequest
        )
        s_path = sbom_path.replace("/", "*")
        with open(f"tests/{owner}*{name}:{s_path}.zip", "wb") as file:
            file.write(response.content)
