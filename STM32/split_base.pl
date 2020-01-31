# importing csv module
import csv
import argparse


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


boilerplate_cvs_file = 'Base.csv'

with open(boilerplate_cvs_file, 'r') as CSVBfile:

    CSVbreader = csv.reader(CSVBfile)
    for brow in CSVbreader:
        boilerplate_raw_data.append(brow)
    num_of_brows = CSVbreader.line_num

line_number = 1
for brow in boilerplate_raw_data[:num_of_brows]:
    # parsing each column of a row
    if line_number > 4:
        if brow[2] == "Active":
            design = brow[1]
            footprint = brow[5]
            print("load  {}".format(design))
            print("csv pinout pinsrc/{}.csv".format(design))
            filename = "topsrc/{}.csv".format(design)
            file = open(filename, "w")
            file.write("DEF,{}\n".format(design))
            file.write("FOOT,{}\n".format(footprint))
            file.write("PINFILE,{}.csv\n".format(design))
            file.close()

    line_number = line_number + 1

print("exit")
