


from bokeh.layouts import gridplot,  row
from bokeh.models import BooleanFilter, CDSView, ColumnDataSource,  Label, LabelSet, Range1d, HoverTool
from bokeh.plotting import figure, output_file, show, save
#from bokeh.models.tools import *
from bokeh.models.tools import (BoxZoomTool, PanTool, SaveTool,
    ResetTool, HoverTool )

def prepend_plots(name_of_pfile, name_of_file, df, append_string='', show_results = False):

    f2 = open(name_of_file, 'r')
    file_contents = f2.read()
    f2.close()


    hover = HoverTool(tooltips=[
        ("mat_id", "@mp_ids"),
        ("oxide orientation", "@ox_orients"),
        ('mcia', '@mcia'),
        ('misfit strain', '@strain'),
        ('formation energy', '@form'),
        ])
    TOOLS = [BoxZoomTool(), PanTool(), SaveTool(), ResetTool(), hover]

    output_file(name_of_pfile)

    data_dict = dict(
        form=list(df["Formation energy (eV/atom)"]),
        mcia=list(df["Min. coincident area"]),
        strain=list(df["Misfit strain (norm)"]),
        names=list(df["Oxide"]),
        mp_ids=list(df["Material ID"]),
        v_mox_ratio=list(df["Vmox/Vm ratio"]),
        ox_orients=list(df["Oxide orientation"]),
        ox_chem_pot=list(df['Oxygen chemical potential (eV/atom)']),
        ox_atom_percent=list(df["Oxide O at.%"]),
        )
    if False: # shows data for debuging
        for key in data_dict:
            print(key, 'len():', len(data_dict[key]) )
            for thing in data_dict[key]:
                print(thing)
    source = ColumnDataSource(data=data_dict)

    bottom_left= None
    bottom_right = None
    right=None
    left=None

    kwrds= dict(x_offset=3, y_offset=3,
        source=source, text_font_size="12pt",
        #render_mode='canvas',
        )

    # create a view of the source for one plot to use
    #view = CDSView()#source=source) # source is depricated

    # create a new plot and add a renderer
    left = figure(tools=TOOLS, title='MCIA vs Formation Energy Per Atom')
    left.circle(x='form', y='mcia', size=8, hover_color="deeppink", source=source)
    left.xaxis[0].axis_label = 'Formation energy per atom (eV/atom)'
    left.yaxis[0].axis_label = 'MCIA'
    labels = LabelSet(x='form', y='mcia', text='names',
                  **kwrds)
    left.add_layout(labels)

    # create another new plot, add a renderer that uses the view of the data source
    if True:
        right = figure(tools=TOOLS, title='Misfit Strain vs Formation Energy Per Atom')
        right.circle(x='form', y='strain', size=8, hover_color="deeppink", source=source)#, view=view)
        right.xaxis[0].axis_label = 'Formation energy per atom (eV/atom)'
        right.yaxis[0].axis_label = 'Misfit Strain'
        labels = LabelSet(x='form', y='strain', text='names',
                      **kwrds)
        right.add_layout(labels)

    ##########
    if True:
        bottom_left = figure(tools=TOOLS, title='Misfit Strain vs Vm/ox Ratio ')
        bottom_left.circle(x='v_mox_ratio', y='strain', size=8, hover_color="deeppink", source=source)
        bottom_left.xaxis[0].axis_label = 'Vmox/Vm Ratio'
        bottom_left.yaxis[0].axis_label = 'Misfit Strain'
        labels = LabelSet(x='v_mox_ratio', y='strain', text='names',
                      **kwrds)
        bottom_left.add_layout(labels)
    
    ##########
    if True:
        bottom_right = figure(tools=TOOLS, title='Oxygen Chemical Potential vs Oxygen Fraction')
        bottom_right.circle(x='ox_atom_percent', y='ox_chem_pot', size=8, hover_color="deeppink", source=source)
        bottom_right.xaxis[0].axis_label = 'Oxide Ox at.%'
        bottom_right.yaxis[0].axis_label = 'Oxygen Chemical Potential (eV/atom)'
        labels = LabelSet(x='ox_atom_percent', y='ox_chem_pot', text='names',
                      **kwrds)
        bottom_right.add_layout(labels)
    
    ####
    p = gridplot([[left, right],[bottom_left,bottom_right],[None,None]]) # Nones are placeholders

    save(p)
    if show_results:
        show(p)

    f1 = open(name_of_pfile, 'a+')
    f1.write("<br>")
    f1.write(append_string)
    f1.write("<br><br>")
    f1.write(file_contents)
    f1.close()
