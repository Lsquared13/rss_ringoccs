#!/bin/bash
rsr_file_list=../tables/rsr_1kHz_files_after_USO_failure_withuplink.txt
data_path=../data/

bash get_rsr_files.sh $rsr_file_list $data_path
