#! /usr/bin/env python3

"""
Routines for Writing Vertical Profiles from UKMO NIMROD Files
"""

vp_script="/gws/smf/j04/ncas_radar/rrniii/BioDAR/VP_Extraction/vp_extraction.py"
#log output location
log_output="/gws/smf/j04/ncas_radar/rrniii/BioDAR/VP_Extraction/Output/"

data_input = "/gws/smf/j07/ncas_radar/data/ukmo-nimrod/raw_h5_data/single-site/"
data_output = "/gws/smf/j07/ncas_radar/data/ukmo-nimrod/"

from datetime import timedelta
from dateutil.parser import parse as dateparse
from os import path, system
from sys import argv
from re import sub
from vp_params import cvp_sites, qvp_sites

#function for getting list of dates
def date_range(start, end):
    delta = end - start  # as timedelta
    start_list = [start + timedelta(days=i) for i in range(delta.days + 1)]
    end_list   = [start + timedelta(days=j, hours=23, minutes=59, seconds=59) for j in range(delta.days + 1)]
    return start_list, end_list

#Define Start and End
mode = argv[1]
index = int(argv[2])
start_date = dateparse(argv[3])
end_date = dateparse(argv[4])
site_len = int(argv[5])
verbose = (argv[6].lower() == 'true')

if mode == 'CVP':
    sites = cvp_sites
    data_output = path.join(data_output,"raw_cvp_data")
elif mode == 'QVP':
    sites = qvp_sites
    data_output = path.join(data_output,"raw_qvp_data")
else:
    print ('VP mode not recognised. Exitting')
    raise

if site_len > len(sites):
    print ("Expected number of sites is greater than size of site dictonary")
    raise

[start_list, end_list] = date_range(start_date, end_date)

print("Overall start date is: ", start_list[0].strftime("%Y%m%d"+"T"+"%H%M%S"))
print("Overall end date is:   ", end_list[-1].strftime("%Y%m%d"+"T"+"%H%M%S"))

d = index//site_len
s = index%site_len

year=str(start_list[d].year)
start = start_list[d].strftime("%Y%m%d"+"T"+"%H%M%S")
end = end_list[d].strftime("%Y%m%d"+"T"+"%H%M%S")

radar = sites[s]['radar']

input_data_dir=path.join(data_input,radar,year)

args=""
if verbose:
    args += " -v"
if 'ukmo-nimrod' in input_data_dir:
    args += " -m"
args += f" -s {start}"
args += f" -e {end}"
if mode == 'CVP':
    args += f" -a {sites[s]['col_lat']}"
    args += f" -o {sites[s]['col_long']}"
    args += f" -p {sites[s]['col_pos_name']}"
    loop_key = 'col_radius'
elif mode == 'QVP':
    if not sites[s]['azimuth_exclude'] == None:
        args += f" -b {sites[s]['azimuth_exclude']}"
    args += f" -c {sites[s]['count_threshold']}"
    loop_key = "elevation"

for itt in range(0, len(sites[s][loop_key])):

    el = sites[s][loop_key][itt]

    if mode == "CVP":
        out_data_dir=path.join(data_output,radar,sites[s]['col_pos_name'],str(el).replace(".","_"),year)
        file_check="{}_{:.1f}km_{}.nc".format(sites[s]['col_pos_name'],el,start_list[d].strftime("%Y%m%d"))
        if not itt == 0:
            pattern = " \-r.*"
            args = sub(pattern,'',args)
        args += f" -r {el}"

    elif mode == "QVP":
        out_data_dir=path.join(data_output,radar,year)
        file_check="{}_QVP_{:.1f}deg.nc".format(start_list[d].strftime("%Y%m%d"), el)
        if not itt == 0:
            pattern = " \-l.*"
            args = sub(pattern,'',args)
        args += f" -l {el}"
    if path.exists(path.join(out_data_dir,file_check)):
        with open(path.join(log_output,mode+'_Done.txt'), 'a') as log:
            log.write("Done Already: "+file_check+ '\n')
    else:
        with open(path.join(log_output,mode+'_To_do.txt'), 'a') as log:
            log.write("Sent to Lotus: "+file_check+ '\n')
        python_run_cmd='python {} {} {} {}{}'.format(vp_script, mode, input_data_dir, out_data_dir, args)

        #print (python_run_cmd)
        system(python_run_cmd)
