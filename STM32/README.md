Run ST's config tool

<path-to_STM32CubeMX/STM32CubeMX

select access to select MCU ,
export page as Base excel file
convert to Base.csv
mkdir topsrc
mkdir pinsrc
run python3.7 split_base.pl > script.txt
run java -jar <path-to_STM32CubeMX>/STM32CubeMX -q script.txt