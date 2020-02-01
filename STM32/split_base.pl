# importing csv module
import csv
import argparse
import sys


parser = argparse.ArgumentParser(description='create a symbol from csv file')
parser.add_argument("--design")
parser.add_argument("--variant")
parser.add_argument("--group")
parser.add_argument("--directory")
parser.add_argument("--part")

args = parser.parse_args()
design_name = args.design
variant_name = args.variant
group_name = args.group
directory_name = args.directory
part_name = args.part

# initializing
boilerplate_raw_data = []

"""
"""
from os import makedirs, path
    
if __name__ == '__main__':
    def _make(dirpath: str) -> None:
        if not (path.exists(dirpath) and path.isdir(dirpath)):
            makedirs(dirpath)
    _make('topsrc')
    _make('pinsrc')

base_cvs_file = 'Base.csv'

with open(base_cvs_file, 'r') as CSVBfile:

    CSVbreader = csv.reader(CSVBfile)
    for brow in CSVbreader:
        boilerplate_raw_data.append(brow)
    num_of_brows = CSVbreader.line_num


script = open("script.txt", "w")
run_generate = open("run_generate", "w")
script.write("rm -r out\n")
    
line_number = 1
for brow in boilerplate_raw_data[:num_of_brows]:
    # parsing each column of a row
    if line_number > 4:
        if brow[2] == "Active":
            design = brow[1]
            footprint = brow[5]
            script.write("load  {}\n".format(design))
            script.write("csv pinout pinsrc/{}.csv\n".format(design))
            run_generate.write("python3.7 ../generate_stm.py  --group stm32   --directory  ./topsrc/    --design {}\n".format(design))
            filename = "topsrc/{}.csv".format(design)
            file = open(filename, "w")
            file.write("DEF,{}\n".format(design))
            file.write("FOOT,{}\n".format(footprint))
            file.write("PINFILE,{}.csv\n".format(design))
            file.close()

    line_number = line_number + 1

script.write("exit\n")
script.close()
run_generate.close()	     
