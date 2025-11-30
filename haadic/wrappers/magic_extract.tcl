gds read {gds_file}
#for r extraction
flatten {top_cell}
#/r
load {top_cell}
select top cell
set SUB 0
extract path {root_path}/extfile
extract all
#for r extraction
ext2sim labels on
ext2sim {root_path}/{top_cell}
extresist tolerance 10
extresist
#/r
ext2spice lvs
#set threshold for capacitance extraction (in fF)
#set to infinite to disable
ext2spice cthresh 0.1
ext2spice extresist on
ext2spice -p {root_path}/extfile -o {output_file}
quit -noprompt
