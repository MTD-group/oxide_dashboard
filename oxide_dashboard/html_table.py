
import pandas as pd
from .utils import display_data, alloy_composition_to_string

from .MCIAheading import MCIAheading
from .MCIAscript import MCIAscript

def make_sortable(name_of_file):
    with open(name_of_file, 'r') as file:
        # read a list of lines into data
        data = file.readlines()


    if False: # replaces the heading lines with ones with onclick sorting
        with open("MCIAheading.txt", 'r') as headingfile:
            # read a list of lines into data
            headingdata = headingfile.readlines()

        for i in range(len(headingdata)):
            data[i] = headingdata[i]
        with open(name_of_file, 'w') as file:
            file.writelines(data)

    headinglines = MCIAheading.split('\n')
    for i in range(len(headinglines)):
        data[i] = headinglines[i]+'\n'


    f1 = open(name_of_file, 'w')
    f1.writelines(data)
    
    #f2 = open("MCIAscript.txt", 'r')
    #f1.write(f2.read())
    #f2.close()
    f1.write(MCIAscript)

    f1.close()



def formatting(x):
    if "mp" in x: 
        return '<a href="https://materialsproject.org/materials/{0}" target="_blank">{0}</a>'.format(x)
    else: 
        return '<a href="http://oqmd.org/materials/entry/{0}" target="_blank">{1}</a>'.format(x[5:], x)



def write_dashboard_html(df, lattice_param=None, add_plots = True,
    filename = None, 
    METALS=None, COMPS=None, STRUCTURE=None, E_HULL=None):

    #########
    compformat = alloy_composition_to_string(METALS,COMPS)

    if filename is not None:
        name_of_file = filename
    else:
        prefix = STRUCTURE + "-" + compformat + "-e_lim=" + str(E_HULL) 
        name_of_file =  prefix + '.html'
        
    #name_of_pfile = prefix + '.plot.html'

    ######
    if lattice_param is not None:
        lattice_param_string = STRUCTURE + "-" +compformat + ": a = " + str(round(lattice_param, 4)) + " Å"
        ## TODO catch case where STRUCTURE, METALS, and COMPS are not passed
        
    ###############
    dfcopy = display_data(df, top_unique = 5)
    #dfcopy2 = display_data(df, top_unique = 5)

    pd.set_option("display.max_rows", None, "display.max_columns", None)


    ####################################
    # create html out of the df
    dfcopy['material ID'] = dfcopy['material ID'].apply(formatting)


    dfcopy.to_html(open(name_of_file, 'w'), 
                        justify = "center", 
                        table_id = "myTable2",
                        render_links=True, 
                        escape = False)
    make_sortable(name_of_file)

    if add_plots:
        from .html_plots import prepend_plots
        # to add to a new file
        #prepend_plots(name_of_pfile, name_of_file, dfcopy2,
        #    append_string=lattice_param_string)
        # to add to the existing one
        prepend_plots(name_of_file, name_of_file, dfcopy,
            append_string=lattice_param_string)
