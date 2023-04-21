
from operator import itemgetter
import itertools
import numpy as np
from tqdm import tqdm

import os
import pandas as pd
from .old_sa import SubstrateAnalyzer

import pymatgen.core as mg

from pymatgen.symmetry.analyzer import SpacegroupAnalyzer
from pymatgen.core.lattice import Lattice
from pymatgen.core.composition import Composition
from pymatgen.io.ase import AseAtomsAdaptor

from ase.db import connect
from ase.data import chemical_symbols, atomic_numbers

from .lattice_data.fcc import lattice_parameters as all_FCC
from .lattice_data.bcc import lattice_parameters as all_BCC





def make_query_string_from_elements(query_elements):

    symbol_mask = [False for symbol in chemical_symbols]

    for symbol in query_elements: # marks the ones we want
        symbol_mask[atomic_numbers[symbol]] = True

    query_string = ''
    for z, sb in enumerate(symbol_mask):
        if sb:
            query_string += chemical_symbols[z] +'>=0,'
        else:
            query_string += chemical_symbols[z] +'=0,'

    return query_string


def make_alloy_string_from_elements(query_elements):
    qes = sorted(query_elements, key=lambda el: atomic_numbers[el])

    alloy_name = ''
    for el in qes:
        alloy_name+=el

    return alloy_name
    
    
###################

def make_spec_query_string_from_elements(query_elements, amounts):
    
    if len(query_elements) != len(amounts):
        print("Invalid inputs!")

    symbol_mask = [False for symbol in chemical_symbols]

    for symbol in query_elements: # marks the ones we want
        symbol_mask[atomic_numbers[symbol]] = True

    query_string = ''
    i = 0
    for z, sb in enumerate(symbol_mask):
        if sb:
            query_string += chemical_symbols[z] +'='+ str(amounts[i]) + ','
            i += 1
        else:
            query_string += chemical_symbols[z] +'=0,'

    return query_string
    
#############

def groupby_itemkey(iterable, item):
    """groupby keyed on (and pre-sorted by) itemgetter(item)."""
    itemkey = itemgetter(item)
    return itertools.groupby(sorted(iterable, key=itemkey), itemkey)
    
    
############

def MCIA(f, s, conventional = False):
    all_matches = []
    sa = SubstrateAnalyzer()

    if conventional:
        film = SpacegroupAnalyzer(f).get_conventional_standard_structure()
        substrate = SpacegroupAnalyzer(s).get_conventional_standard_structure()
    else:
        film = f
        substrate = s

    # Calculate all matches and group by substrate orientation
    matches_by_orient = groupby_itemkey(
        sa.calculate(film, substrate, lowest = True),
        "sub_miller")

    # Find the lowest area match for each substrate orientation
    lowest_matches = [min(g, key=itemgetter("match_area"))
                      for k, g in matches_by_orient]

    for match in lowest_matches:
        print(match)
        db_entry = {
            "sub_form": substrate.composition.reduced_formula,
            "orient": " ".join(map(str, match["sub_miller"])),
            "film_form": film.composition.reduced_formula,
            "film_orient": " ".join(map(str, match["film_miller"])),
            "area": match["match_area"],
        }
        all_matches.append(db_entry)

    df = pd.DataFrame(all_matches)
    #df.set_index("sub_id", inplace=True)
    return df.sort_values("area")
    
##############


def get_equiv_alloy_volume(atoms):
    symbols = atoms.get_chemical_symbols()

    volume = 0

    for sym in symbols:
        if sym != 'O':
            volume+=metallic_atomic_volumes[sym]
    return volume
    


#####
def equiv_alloy_volume(atoms, per_cell_volume):
    symbols = atoms.get_chemical_symbols()
    volume = 0
    for sym in symbols:
        if sym != 'O':
            volume+=per_cell_volume
    return volume
    

########
def get_substrate(lattice_param, structure):
    if structure == "BCC":
        return mg.Structure(Lattice.cubic(lattice_param), ["Cu", "Cu"], [[0, 0, 0], [0.5, 0.5, 0.5]])
    elif structure == "FCC":
        return mg.Structure(Lattice.cubic(lattice_param), ["Cu", "Cu", "Cu", "Cu"], [[0, 0, 0], [0.5, 0.5, 0], [0.5, 0, 0.5], [0, 0.5, 0.5]])
        
##########


    
##################
from itertools import compress
def sort_through_dupes(films):
    want = np.ones(len(films), dtype = bool)
    for i in range(len(films)):
        for j in range(i+1, len(films)):
            if (films[i]["formula"] == films[j]["formula"]) and (films[i]["natoms"] == films[j]["natoms"]) and (films[i]["spg_num"] == films[j]["spg_num"]):
                if films[i]["e_above_hull"] < films[j]["e_above_hull"]:
                    want[j] = False
                else:
                    want[i] = False
    return list(compress(films, want))


######

def print_mat_ids(films):
    for i in range(len(films)):
        print(films[i]["source"])

###########
def process_ICSD(ICSDs):
    def format_int_list(ilist):
        if len(ilist) > 0:
            out_string = '{'
            for iint in ilist[0:-1]:
                out_string+='%i, ' %iint
            out_string+= '%i}'% ilist[-1]
        else:
            out_string = ''
        return out_string

    return format_int_list(sorted(ICSDs))

#########

from pymatgen.analysis.elasticity.strain import Deformation
from pymatgen.core.surface import (SlabGenerator,
                                   get_symmetrically_distinct_miller_indices)
def misfit_strain(film, match, norm = True):
    def fast_norm(a):
        return np.sqrt(np.dot(a, a))
    # need film to be conventional standard structure
    struc = SlabGenerator(film, match['film_miller'], 20, 15,
                              primitive=True).get_slab().oriented_unit_cell

    # Generate 3D lattice vectors for film super lattice
    film_matrix = list(match['film_sl_vecs'])
    film_matrix.append(np.cross(film_matrix[0], film_matrix[1]))

    # Generate 3D lattice vectors for substrate super lattice
    # Out of plane substrate super lattice has to be same length as
    # Film out of plane vector to ensure no extra deformation in that
    # direction
    substrate_matrix = list(match['sub_sl_vecs'])
    temp_sub = np.cross(substrate_matrix[0], substrate_matrix[1])
    temp_sub = temp_sub * fast_norm(film_matrix[2]) / fast_norm(temp_sub)
    substrate_matrix.append(temp_sub)

    transform_matrix = np.transpose(np.linalg.solve(film_matrix,
                                                    substrate_matrix))
    dfm = Deformation(transform_matrix)

    strain = dfm.green_lagrange_strain.convert_to_ieee(struc, initial_fit=False)

    if norm:
        return (np.sum(np.power(np.array(strain), 2))) ** 0.5
    else:
        return strain.von_mises_strain

###################

class OxideEngine:
    def __init__(self, db_files: list):
    
        self.dbs = [connect(os.path.abspath(db_file ))  for db_file in db_files]


    def get_films(self, metals, per_cell_volume, e_above_hull_lim):
        howmany = 0
        my_qs = make_query_string_from_elements(['O'] + metals) + "e_above_hull<=" + str(e_above_hull_lim)
        substrates = []
        for db in self.dbs:
            for row in db.select(my_qs):
                atoms = row.toatoms()
                if len(set(atoms.get_chemical_symbols())) == 1:
                    continue
                v_mox_ratio = atoms.cell.volume / equiv_alloy_volume(atoms, per_cell_volume)
                try:
                    substrates.append({"structure": AseAtomsAdaptor.get_structure(atoms), 
                                       "atoms": atoms,
                                       "source": row['material_id'],
                                       "natoms": row['natoms'],
                                       "spg_num": row['spg_number'],
                                       "formula": row['pretty_formula'],
                                       "ox_at_%": 100*Composition(row['pretty_formula']).get_atomic_fraction("O"),
                                       "e_above_hull": row['e_above_hull'],
                                       "formation_energy_per_atom": row["formation_energy_per_atom"],
                                       "space group": row["spg_symbol"],
                                       "v_mox_ratio": v_mox_ratio,
                                       "ICSD IDs": process_ICSD(row.data.icsd_ids),
                                       "band gap": row["band_gap"]})
                except:
                    print('Tabulation failed for:', row)
                howmany +=1
        return substrates


    #add option for passing lattice parameter?
    def query(self, metals, composition, structure, e_above_hull_lim = 0.015, no_dupes = True):
        # deal with inputs
        if len(metals) != len(composition):
            print("Inputs do not match!")
            return None
        #if round(sum(composition), 6) != 1:
        #    print("Composition does not add to 1!")
        #    return None
        comp =  np.array(composition)
        composition_fractions = comp/comp.sum()
        
        parameter = 0
        if structure == "BCC":
            using = all_BCC
            factor = 2
        elif structure == "FCC":
            using = all_FCC
            factor = 4
        for i, metal in enumerate(metals):
            if using.get(metal) is None:
                print("Do not have lattice parameter for:", metal)
                return None
            parameter += using[metal]["val"] * composition_fractions[i]
        substrate = SpacegroupAnalyzer(get_substrate(parameter, structure)).get_conventional_standard_structure()
        per_cell_volume = substrate.volume / factor
        films = self.get_films(metals, per_cell_volume, e_above_hull_lim)
        if no_dupes:
            films = sort_through_dupes(films)
        # !!! actual analyzer part !!!
        all_matches = []
        sa = SubstrateAnalyzer()
        # Calculate all matches and group by substrate orientation
        for f in tqdm(films):
            film = f["structure"]
            matches_by_orient = groupby_itemkey(
                sa.calculate(film, substrate, lowest = True),
                "sub_miller")

            # Find the lowest area match for each substrate orientation
            lowest_matches = [min(g, key=itemgetter("match_area"))
                              for k, g in matches_by_orient]

            for match in lowest_matches:
                try:
                    db_entry = {
                        "material ID": f["source"],
                        "oxide": film.composition.reduced_formula,
                        "e_above_hull (eV)": f['e_above_hull'],
                        "form. energy per atom (eV/atom)": f["formation_energy_per_atom"],
                        "space-group": f["space group"],
                        "v_mox_ratio": f["v_mox_ratio"],
                        "atomic % of O in oxide": round(f["ox_at_%"], 2),
                        "band gap": f["band gap"],
                        "alloy orientation": " ".join(map(str, match["sub_miller"])),
                        "oxide orientation": " ".join(map(str, match["film_miller"])),
                        "misfit strain (norm)": misfit_strain(film, match, norm = True),
                        "min. coincident area": match["match_area"],
                        "similar ICSD structure IDs": f["ICSD IDs"],
                    }
                    all_matches.append(db_entry)
                except:
                    print(f["source"], "with composition", film.composition.reduced_formula, "failed")
        df = pd.DataFrame(all_matches)
        df = df.sort_values("min. coincident area")
        print("Calculated parameter is:", parameter)
        print("Found", len(films), "film candidates.")
        return  df, parameter
    
    
    

