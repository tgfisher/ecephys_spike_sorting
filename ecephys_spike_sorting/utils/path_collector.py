import os
from pathlib import Path

from contextlib import contextmanager

import yaml

DEFAULT_ATTRIBUTE_FILENAME = "ece_attributes.yaml"

attributes_yaml_home = os.path.abspath(
    os.environ.get("ECE_ATTRIBUTES_DIR", "")
) # returns 'current' working dir if ECE_ATTRIBUTES_DIR is empty

attributes_file_name = os.environ.get(
    "ECE_ATTRIBUTES_FILENAME",
    DEFAULT_ATTRIBUTE_FILENAME
)

class AttributeFileNotFound(FileNotFoundError):
    def __str__(self):
        return (
            f"""Neither ECE_ATTRIBUTES_DIR, or ECE_ATTRIBUTES_FILENAME point to an attributes file.

            No 'ece_attributes.yaml' found in the current directory:
                    {Path(self.args[0]).parent}.

            Use environment variables ECE_ATTRIBUTES_DIR or ECE_ATTRIBUTES_FILENAME
              to set a parent directory or direct path to an attributes file.

            (see `ece_attributes_template.yaml` in the ecephys_spike_sorting repo for more info.)
            """
        )

def build_attributes_dict(attributes_path):
    try:
        with open(attributes_path, "r") as yamlstream:
            _attr_dict = yaml.full_load(yamlstream)
    except FileNotFoundError as e:
        default_path = os.path.join(
            os.path.abspath(""),
            DEFAULT_ATTRIBUTE_FILENAME
        )

        raise AttributeFileNotFound(default_path) from e

    return {
        'ece_path': _attr_dict["ecephys_path"],
        'npy_matlab_path': _attr_dict["npy_matlab_path"],
        'sglx_tools_pdict': _attr_dict["sglx_tools_path_dict"],
        'ks': {
            'versions': _attr_dict["ks_vers_path_dict"],
            'out_tmp': _attr_dict["ks_output_tmp"]
        },
    }

attributes_dict = build_attributes_dict(
    os.path.join(
        attributes_yaml_home,
        attributes_file_name,
    )
)


def main():

    def printdict(d, tabbed=0):
        TAB = "  "
        CR = "\n"
        leader = "" if tabbed else "\n"
        for key, value in d.items():
            key_str = leader + TAB * tabbed + f"{key}:"
            if isinstance(value, dict):
                print(key_str, sep="")
                pdict(value, tabbed = tabbed + 1)
            else:
                value_str = TAB * (tabbed + 1) + f"{value}"
                print(key_str, "\n", value_str, sep = "")

    att = build_attributes_dict(
        os.path.join(
            attributes_yaml_home,
            attributes_file_name,
        )
    )

    printdict(attributes_dict)

if __name__ == "__main__":

    main()
