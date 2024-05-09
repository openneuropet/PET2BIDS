from pathlib import Path
import os
import json
import pprint
import argparse


class Style:
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    UNDERLINE = "\033[4m"
    RESET = "\033[0m"


def fetch_pairs_of_jsons(path_one: Path, path_two: Path):

    path_one, path_two = Path(path_one), Path(path_two)

    paths = {path_one: {}, path_two: {}}
    for path in paths.keys():
        for root, folders, files in os.walk(path):
            for f in files:
                if Path(f).suffix == ".json":
                    paths[path][f] = os.path.join(root, f)

    paths = {path_one.name: paths[path_one], path_two.name: paths[path_two]}

    pairs = []
    for sidecar in paths[next(iter(paths))]:
        if (
            sidecar in paths[path_one.name].keys()
            and sidecar in paths[path_two.name].keys()
        ):
            pairs.append(sidecar)

    to_compare = {}
    for pair in pairs:
        to_compare[pair] = (paths[path_one.name][pair], paths[path_two.name][pair])

    return to_compare


def compare_jsons(json_paths, show_matches=True):
    for json_name, json_files in json_paths.items():
        # load keys from each json to be compared into sets
        with open(json_files[0]) as left_file:
            left = json.load(left_file)
        with open(json_files[1]) as right_file:
            right = json.load(right_file)

        left_set, right_set = set(left.keys()), set(right.keys())
        # find the intersection of the sets
        intersection = left_set.intersection(right_set)

        difference = left_set.difference(right_set)

        # (key, folder path 1 json, folder path 2 json)
        # <key name> <path 1 value> <path 2 value>
        # compare values between each entry/key
        name_element_length = len(list(intersection)[0])
        left_element_length = len(str(left[list(intersection)[0]]))
        for i in list(intersection):
            if len(i) > name_element_length:
                name_element_length = len(i)
            if len(str(left[i])) > left_element_length:
                left_element_length = len(str(left[i]))

        name_padding = name_element_length
        left_padding = left_element_length

        comparison_string = f"\nComparison between {json_files[0]} and {json_files[1]}"
        print(Style.RESET + comparison_string)
        # print out a header/column names
        header = (
            "   keyname".ljust(name_padding, " ")
            + "    \tleft".ljust(left_padding, " ")
            + "    \tright"
        )
        print(Style.RESET + header)
        for i in list(intersection):
            print(Style.RESET, end="")
            left_value, right_value = left[i], right[i]
            approximate = False
            if type(left_value) is str and type(right_value) is str:
                if left_value == right_value and show_matches:
                    print(
                        Style.GREEN
                        + f"== {i.ljust(name_padding, ' ')}\t{str(left_value).ljust(left_padding, ' ')}\t{right_value}"
                    )
                elif (
                    set(left_value.lower().split(" "))
                    == set(right_value.lower().split(" "))
                    and show_matches
                ):
                    print(
                        Style.YELLOW
                        + f"~= {i.ljust(name_padding, ' ')}\t{str(left_value).ljust(left_padding, ' ')}\t{right_value}"
                    )
                    approximate = True
            if left_value == right_value and show_matches:
                print(
                    Style.GREEN
                    + f"== {i.ljust(name_padding, ' ')}\t{str(left_value).ljust(left_padding, ' ')}\t{right_value}"
                )
            elif not approximate:
                print(
                    Style.RED
                    + f"!= {i.ljust(name_padding, ' ')}\t{str(left_value).ljust(left_padding, ' ')}\t{right_value}"
                )
            print(Style.RESET, end="")

        # record where sets differ

        # iterate through were sets don't intersect
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "leftpath", type=Path, help="The first path to examine json files in."
    )
    parser.add_argument(
        "right_path", type=Path, help="The second path to examine json files in."
    )

    args = parser.parse_args()

    x = fetch_pairs_of_jsons(args.leftpath, args.right_path)

    y = compare_jsons(x)
