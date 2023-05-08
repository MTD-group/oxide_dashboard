
db_files = ['/home/mjwaters/Dropbox/NW/MURI8/dev_software/oxide_dashboard_data/mp/mp_oxides.db',
            '/home/mjwaters/Dropbox/NW/MURI8/dev_software/oxide_dashboard_data/oqmd/oqmd_oxides.db']

from oxide_dashboard import OxideEngine
from oxide_dashboard import write_dashboard_html
from oxide_dashboard.utils import equiatomic
myengine = OxideEngine(db_files)
######################
E_HULL = 0.050
STRUCTURE = "FCC"

#############
METALS = [ 'Al',  ]
COMPS  = [ 1,  ]

#METALS = ['Fe', 'Co', 'Ni', 'Cr', 'Al' ]
#COMPS  = [ 28 ,   28,   28,   10, 6 ]

#METALS = ['Nb', 'Ti', 'Zr']
#COMPS = equiatomic(METALS)
##############
# df is a pandas data frame
df, lattice_param = myengine.query(METALS, COMPS, STRUCTURE, e_above_hull_lim = E_HULL)
print(df) 

write_dashboard_html(
    df, 
    lattice_param=lattice_param, 
    METALS=METALS, COMPS=COMPS, 
    STRUCTURE=STRUCTURE, E_HULL=E_HULL,
    add_plots = True,
    filename = None,
    #filename = 'stuff.html',
    )

################## if you just want to look at the table in IPython
from oxide_dashboard.utils import display_data 
new = display_data(df, top_unique = 5)
#display(new) # for IPython



