#!/bin/bash

set -euo pipefail

### SETUP DATA FOLDER TO LOOP OVER
data_dir="/data/gpfs/projects/punim2121/Atherosclerosis/xenium_data/"

# Drop scratch folders that start with "._"
panel_dir_list=($(find "$data_dir" -maxdepth 1 -type d -name '*Panel*' -a ! -name '._*' | sort))


### SEGMENTATION PARAMETERS
# Size of cell expansion after cell segmentation (um) => has to be converted to pixels!
segment_expansion_sizes_um=('4' '6' '10') 

# Segmentation methods
segment_methods=('cellpose')

## Cellpose model types
cellpose_model_types=('cyto' 'nuclei')


### BAYSOR PARAMETERS
# Values for 'scale' parameter in Baysor => ~ expected RADIUS of cells in um-s
baysor_scale_arr_um=('3' '5' '8') 


start=$(date +%s)

for panel in "${panel_dir_list[@]}"; do
    sample_name_list=($(find "$panel" -maxdepth 1 -type d -printf '%f\n' | sort))
   
    # Loop over all samples in a batch
    for sample_name in "${sample_name_list[@]}"; do
        sample_dir="$panel/$sample_name"
  	
	if [[ -d "$sample_dir" ]] && [[ "$sample_dir" == *"P3_H"* ]]; then
	       		
        ## Input filename of DAPI image
	    input_fn="$sample_dir/morphology_mip.ome.tif"
	    
	    ## Extract PanelX + PX_X -> i.e. Panel1_P3_D as sample dirname + later as output directory	     
	    panel_suffix=$(echo "$panel" | rev | cut -d'_' -f 1 | rev)
        sample_suffix=$(awk -F__ '{print $3}' <<< "$sample_name")

	    sample_dirname="${panel_suffix}_${sample_suffix}"
	    output_dir="${data_dir}processed_data/cell_segmentation/$sample_dirname"

        #### BAYSOR inputs
        baysor_molecules="$sample_dir/transcripts.csv.gz"
	    
        echo 'test'
 	    echo $input_fn
	    echo $output_dir
        fi
    done
done

end=$(date +%s)
#echo "Execution time: $((end - start)) seconds"
