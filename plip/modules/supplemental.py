"""
Protein-Ligand Interaction Profiler - Analyze and visualize protein-ligand interactions in PDB files.
supplemental.py - Supplemental functions for PLIP analysis.
Copyright 2014 Sebastian Salentin

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

# Compatibility
from __future__ import print_function

# Python standard library
import re
from collections import namedtuple
import os
from multiprocessing import Process
if os.name != 'nt':  # Resource module not available for Windows
    import resource
import subprocess
import math  # Reimport for Windows

# External libraries
import pybel
from pybel import *
from openbabel import *
import numpy as np
from pymol import cmd
from pymol import finish_launching


def is_biolip_artifact(hetid):
    """Checks for the HET ID in the BioLip artifact list. Contains non-biological compounds often used appearing
    as artifacts in PDB structures."""
    # List from http://zhanglab.ccmb.med.umich.edu/BioLiP/ligand_list (2014-07-10)
    excluded = ['ACE', 'HEX', 'TMA', 'SOH', 'P25', 'CCN', 'PR', 'PTN', 'NO3', 'TCN', 'BU1', 'BCN', 'CB3', 'HCS', 'NBN',
                'SO2', 'MO6', 'MOH', 'CAC', 'MLT', 'KR', '6PH', 'MOS', 'UNL', 'MO3', 'SR', 'CD3', 'PB', 'ACM', 'LUT',
                'PMS', 'OF3', 'SCN', 'DHB', 'E4N', '13P', '3PG', 'CYC', 'NC', 'BEN', 'NAO', 'PHQ', 'EPE', 'BME', 'TB',
                'ETE', 'EU', 'OES', 'EAP', 'ETX', 'BEZ', '5AD', 'OC2', 'OLA', 'GD3', 'CIT', 'DVT', 'OC6', 'MW1', 'OC3',
                'SRT', 'LCO', 'BNZ', 'PPV', 'STE', 'PEG', 'RU', 'PGE', 'MPO', 'B3P', 'OGA', 'IPA', 'LU', 'EDO', 'MAC',
                '9PE', 'IPH', 'MBN', 'C1O', '1PE', 'YF3', 'PEF', 'GD', '8PE', 'DKA', 'RB', 'YB', 'GGD', 'SE4', 'LHG',
                'SMO', 'DGD', 'CMO', 'MLI', 'MW2', 'DTT', 'DOD', '7PH', 'PBM', 'AU', 'FOR', 'PSC', 'TG1', 'KAI', '1PG',
                'DGA', 'IR', 'PE4', 'VO4', 'ACN', 'AG', 'MO4', 'OCL', '6UL', 'CHT', 'RHD', 'CPS', 'IR3', 'OC4', 'MTE',
                'HGC', 'CR', 'PC1', 'HC4', 'TEA', 'BOG', 'PEO', 'PE5', '144', 'IUM', 'LMG', 'SQU', 'MMC', 'GOL', 'NVP',
                'AU3', '3PH', 'PT4', 'PGO', 'ICT', 'OCM', 'BCR', 'PG4', 'L4P', 'OPC', 'OXM', 'SQD', 'PQ9', 'BAM', 'PI',
                'PL9', 'P6G', 'IRI', '15P', 'MAE', 'MBO', 'FMT', 'L1P', 'DUD', 'PGV', 'CD1', 'P33', 'DTU', 'XAT', 'CD',
                'THE', 'U1', 'NA', 'MW3', 'BHG', 'Y1', 'OCT', 'BET', 'MPD', 'HTO', 'IBM', 'D01', 'HAI', 'HED', 'CAD',
                'CUZ', 'TLA', 'SO4', 'OC5', 'ETF', 'MRD', 'PT', 'PHB', 'URE', 'MLA', 'TGL', 'PLM', 'NET', 'LAC', 'AUC',
                'UNX', 'GA', 'DMS', 'MO2', 'LA', 'NI', 'TE', 'THJ', 'NHE', 'HAE', 'MO1', 'DAO', '3PE', 'LMU', 'DHJ',
                'FLC', 'SAL', 'GAI', 'ORO', 'HEZ', 'TAM', 'TRA', 'NEX', 'CXS', 'LCP', 'HOH', 'OCN', 'PER', 'ACY', 'MH2',
                'ARS', '12P', 'L3P', 'PUT', 'IN', 'CS', 'NAW', 'SB', 'GUN', 'SX', 'CON', 'C2O', 'EMC', 'BO4', 'BNG',
                'MN5', '__O', 'K', 'CYN', 'H2S', 'MH3', 'YT3', 'P22', 'KO4', '1AG', 'CE', 'IPL', 'PG6', 'MO5', 'F09',
                'HO', 'AL', 'TRS', 'EOH', 'GCP', 'MSE', 'AKR', 'NCO', 'PO4', 'L2P', 'LDA', 'SIN', 'DMI', 'SM', 'DTD',
                'SGM', 'DIO', 'PPI', 'DDQ', 'DPO', 'HCA', 'CO5', 'PD', 'OS', 'OH', 'NA6', 'NAG', 'W', 'ENC', 'NA5',
                'LI1', 'P4C', 'GLV', 'DMF', 'ACT', 'BTB', '6PL', 'BGL', 'OF1', 'N8E', 'LMT', 'THM', 'EU3', 'PGR', 'NA2',
                'FOL', '543', '_CP', 'PEK', 'NSP', 'PEE', 'OCO', 'CHD', 'CO2', 'TBU', 'UMQ', 'MES', 'NH4', 'CD5', 'HTG',
                'DEP', 'OC1', 'KDO', '2PE', 'PE3', 'IOD', 'NDG', 'CL', 'HG', 'F', 'XE', 'TL', 'BA', 'LI', 'BR', 'TAU',
                'TCA', 'SPD', 'SPM', 'SAR', 'SUC', 'PAM', 'SPH', 'BE7', 'P4G', 'OLC', 'OLB', 'LFA', 'D10', 'D12', 'DD9',
                'HP6', 'R16', 'PX4', 'TRD', 'UND', 'FTT', 'MYR', 'RG1', 'IMD', 'DMN', 'KEN', 'C14', 'UPL', 'CMJ', 'ULI',
                'MYS', 'TWT', 'M2M', 'P15', 'PG0', 'PEU', 'AE3', 'TOE', 'ME2', 'PE8', '6JZ', '7PE', 'P3G', '7PG', 'PG5',
                '16P', 'XPE', 'PGF', 'AE4', '7E8', '7E9', 'MVC', 'TAR', 'DMR', 'LMR', 'NER', '02U', 'NGZ', 'LXB', 'A2G',
                'BM3', 'NAA', 'NGA', 'LXZ', 'PX6', 'PA8', 'LPP', 'PX2', 'MYY', 'PX8', 'PD7', 'XP4', 'XPA', 'PEV', '6PE',
                'PEX', 'PEH', 'PTY', 'YB2', 'PGT', 'CN3', 'AGA', 'DGG', 'CD4', 'CN6', 'CDL', 'PG8', 'MGE', 'DTV', 'L44',
                'L2C', '4AG', 'B3H', '1EM', 'DDR', 'I42', 'CNS', 'PC7', 'HGP', 'PC8', 'HGX', 'LIO', 'PLD', 'PC2', 'PCF',
                'MC3', 'P1O', 'PLC', 'PC6', 'HSH', 'BXC', 'HSG', 'DPG', '2DP', 'POV', 'PCW', 'GVT', 'CE9', 'CXE', 'C10',
                'CE1', 'SPJ', 'SPZ', 'SPK', 'SPW', 'HT3', 'HTH', '2OP', '3NI', 'BO3', 'DET', 'D1D', 'SWE', 'SOG']
    return hetid.upper() in excluded


def is_metalion(hetid):
    # #@todo Use OpenBabel instead
    """Checks if a PDB ligand is a metal ion"""
    # Based on het IDs of metal ions in PDB files (from http://metalweb.cerm.unifi.it/search/metal/), Apr 2014
    metals = ['LI', 'BE', 'NA', 'MG', 'K', 'CA', 'RB', 'SR', 'CS', 'BA', 'V', 'CR', 'MN', 'CO', 'NI', 'FE',
              'FE1', 'FE2', 'FE3', 'FE4', 'CO', 'NI', 'CU', 'ZN', 'Y', 'ZR1', 'ZR2', 'ZR3', 'MO', 'RU', 'RU1', 'RH',
              'RH1', 'PD', 'AG', 'CD', 'LA', 'HFA', 'HFB', 'HFC', 'HFD', 'HFE', 'TA1', 'TA2', 'TA3', 'TA4', 'TA5',
              'TA6', 'W', 'W1', 'RE', 'OS', 'IR', 'PT', 'PT1', 'AU', 'HG', 'CE', 'PR', 'SM', 'EU', 'GD', 'TB', 'HO',
              'ER', 'YB', 'LU', 'PA', 'U', 'AL', 'GA', 'GE', 'IN', 'SN1', 'SB', 'TL', 'PB']
    return hetid.upper() in metals


def is_other_ion(hetid):
    """Checks if a PDB ligand is an ion"""
    ions = ['CL', 'IOD', 'BR']
    return hetid.upper() in ions


def is_dna(hetid):
    """Check if a PDB ligand is a DNA/RNA base"""
    dna = ['A', 'C', 'T', 'G', 'U', 'DA', 'DC', 'DT', 'DG', 'DU']
    return hetid.upper() in dna


def is_artifact(hetid):
    """Returns if the ligand is most likely and artifact or other stuff not meaningful (i.e. common solvents)"""
    # NH2 is amidated N-terminus
    # ACE is acetylated C-terminus
    artifacts = ['GOL', 'EDO', 'DOD', 'DMS', 'FMT', 'UNL', 'UPL', '1PE', 'UNX', 'EOH']
    return hetid.upper() in artifacts


def is_mod_aa(hetid):
    # #@todo Get rid of that list
    """Returns if the 'ligand' is just a modified amino acid"""
    # Adapted from ASTRAL RAF (Rapid Access Format) Sequence Maps (Biopython), added other cases.
    mod_aa_dict = {
        '2AS': 'D', '3AH': 'H', '5HP': 'E', 'ACL': 'R', 'AIB': 'A',
        'ALM': 'A', 'ALO': 'T', 'ALY': 'K', 'ARM': 'R', 'ASA': 'D',
        'ASB': 'D', 'ASK': 'D', 'ASL': 'D', 'ASQ': 'D', 'AYA': 'A',
        'BCS': 'C', 'BHD': 'D', 'BMT': 'T', 'BNN': 'A', 'BUC': 'C',
        'BUG': 'L', 'C5C': 'C', 'C6C': 'C', 'CCS': 'C', 'CEA': 'C',
        'CHG': 'A', 'CLE': 'L', 'CME': 'C', 'CSD': 'A', 'CSO': 'C',
        'CSP': 'C', 'CSS': 'C', 'CSW': 'C', 'CXM': 'M', 'CY1': 'C',
        'CY3': 'C', 'CYG': 'C', 'CYM': 'C', 'CYQ': 'C', 'DAH': 'F',
        'DAL': 'A', 'DAR': 'R', 'DAS': 'D', 'DCY': 'C', 'DGL': 'E',
        'DGN': 'Q', 'DHA': 'A', 'DHI': 'H', 'DIL': 'I', 'DIV': 'V',
        'DLE': 'L', 'DLY': 'K', 'DNP': 'A', 'DPN': 'F', 'DPR': 'P',
        'DSN': 'S', 'DSP': 'D', 'DTH': 'T', 'DTR': 'W', 'DTY': 'Y',
        'DVA': 'V', 'EFC': 'C', 'FLA': 'A', 'FME': 'M', 'GGL': 'E',
        'GLZ': 'G', 'GMA': 'E', 'GSC': 'G', 'HAC': 'A', 'HAR': 'R',
        'HIC': 'H', 'HIP': 'H', 'HMR': 'R', 'HPQ': 'F', 'HTR': 'W',
        'HYP': 'P', 'IIL': 'I', 'IYR': 'Y', 'KCX': 'K', 'LLP': 'K',
        'LLY': 'K', 'LTR': 'W', 'LYM': 'K', 'LYZ': 'K', 'MAA': 'A',
        'MEN': 'N', 'MHS': 'H', 'MIS': 'S', 'MLE': 'L', 'MPQ': 'G',
        'MSA': 'G', 'MSE': 'M', 'MVA': 'V', 'NEM': 'H', 'NEP': 'H',
        'NLE': 'L', 'NLN': 'L', 'NLP': 'L', 'NMC': 'G', 'OAS': 'S',
        'OCS': 'C', 'OMT': 'M', 'PAQ': 'Y', 'PCA': 'E', 'PEC': 'C',
        'PHI': 'F', 'PHL': 'F', 'PR3': 'C', 'PRR': 'A', 'PTR': 'Y',
        'SAC': 'S', 'SAR': 'G', 'SCH': 'C', 'SCS': 'C', 'SCY': 'C',
        'SEL': 'S', 'SEP': 'S', 'SET': 'S', 'SHC': 'C', 'SHR': 'K',
        'SOC': 'C', 'STY': 'Y', 'SVA': 'S', 'TIH': 'A', 'TPL': 'W',
        'TPO': 'T', 'TPQ': 'A', 'TRG': 'K', 'TRO': 'W', 'TYB': 'Y',
        'TYQ': 'Y', 'TYS': 'Y', 'TYY': 'Y', 'AGM': 'R', 'GL3': 'G',
        'SMC': 'C', 'ASX': 'B', 'CGU': 'E', 'CSX': 'C', 'GLX': 'Z',
        'MCS': 'C', 'UNK': None, 'MLY': None, 'B3M': None, 'BIL': None,
        'B3L': None, 'D3P': None, 'D4P': None, 'ACE': None, 'NH2': None,
        'B3T': None, 'XCP': None, 'XPC': None, 'B3E': 'E', 'GHP': None,
        '3MY': 'Y', '3FG': None, 'OMY': 'Y', 'MP8': 'P', 'FP9': 'P',
        'ORN': 'A', '4BF': 'Y', 'HAO': None
    }
    return hetid.upper() in mod_aa_dict


def is_lig(hetid):
    """Checks if a PDB compound can be excluded as a small molecule ligand"""
    h = hetid.upper()
    return not (h == 'HOH' or is_mod_aa(h) or is_dna(h) or is_metalion(h) or is_other_ion(h) or is_artifact(h))


def parse_pdb(fil):
    """Extracts additional information from PDB files.
    I. When reading in a PDB file, OpenBabel numbers ATOMS and HETATOMS continously.
    In PDB files, TER records are also counted, leading to a different numbering system.
    This functions reads in a PDB file and provides a mapping as a dictionary.
    II. Additionally, it returns a list of modified residues.
    III. Furthermore, covalent linkages between ligands and protein residues/other ligands are identified
    """
    # #@todo Also consider SSBOND entries here
    i, j = 0, 0  # idx and PDB numbering
    d = {}
    modres = set()
    covlinkage = namedtuple("covlinkage", "id1 chain1 pos1 conf1 id2 chain2 pos2 conf2")
    covalent = []
    previous_ter = False
    for line in fil:
        if line.startswith(("ATOM", "HETATM")):
            if not previous_ter:
                i += 1
                j += 1
            else:
                i += 1
                j += 2
            d[i] = j
            previous_ter = False
        # Numbering Changes at TER records
        if line.startswith("TER"):
            previous_ter = True
        # Get modified residues
        if line.startswith("MODRES"):
            modres.add(line[12:15].strip())
        # Get covalent linkages between ligands
        if line.startswith("LINK"):
            conf1, id1, chain1, pos1 = line[16].strip(), line[17:20].strip(), line[21].strip(), int(line[22:26])
            conf2, id2, chain2, pos2 = line[46].strip(), line[47:50].strip(), line[51].strip(), int(line[52:56])
            covalent.append(covlinkage(id1=id1, chain1=chain1, pos1=pos1, conf1=conf1,
                                       id2=id2, chain2=chain2, pos2=pos2, conf2=conf2))
    return d, modres, covalent


def get_altconf_atoms(f):
    """Return a list of PDB atom ids belonging to atoms with alternate conformations."""
    alt = []
    for line in f:
        if line.startswith(("ATOM", "HETATM")):
            atomid, location = int(line[6:11]), line[16]
            location = 'A' if location == ' ' else location
            if location != 'A':
                alt.append(atomid)
    return alt


def extract_pdbid(string):
    """Use regular expressions to get a PDB ID from a string"""
    p = re.compile("[0-9][0-9a-z]{3}")
    m = p.search(string.lower())
    try:
        return m.group()
    except AttributeError:
        return "UnknownProtein"


def whichrestype(atom):
    """Returns the residue name of an Pybel or OpenBabel atom."""
    if isinstance(atom, Atom):
        try:
            return atom.OBAtom.GetResidue().GetName()
        except AttributeError:
            return None
    elif isinstance(atom, OBAtom):
        return atom.GetResidue().GetName() if atom.GetResidue is not None else None
    else:
        return None


def whichresnumber(atom):
    """Returns the residue number of an Pybel or OpenBabel atom (numbering as in original PDB file)."""
    if isinstance(atom, Atom):
        return atom.OBAtom.GetResidue().GetNum()
    elif isinstance(atom, OBAtom):
        return atom.GetResidue().GetNum()
    else:
        return None


def whichchain(atom):
    """Returns the residue number of an PyBel or OpenBabel atom."""
    if isinstance(atom, Atom):
        return atom.OBAtom.GetResidue().GetChain()
    elif isinstance(atom, OBAtom):
        return atom.GetResidue().GetChain()
    else:
        return None

#########################
# Mathematical operations
#########################


def euclidean3d(v1, v2):
    """Faster implementation of euclidean distance for the 3D case."""
    if not len(v1) == 3 and len(v2) == 3:
        print("Vectors are not in 3D space. Returning None.")
        return None
    return math.sqrt((v1[0] - v2[0]) ** 2 + (v1[1] - v2[1]) ** 2 + (v1[2] - v2[2]) ** 2)


def vector(p1, p2):
    """Vector from p1 to p2.
    :param p1: coordinates of point p1
    :param p2: coordinates of point p2
    :returns : numpy array with vector coordinates
    """
    return None if len(p1) != len(p2) else np.array([p2[i]-p1[i] for i in xrange(len(p1))])


def vecangle(v1, v2, deg=True):
    """Calculate the angle between two vectors
    :param v1: coordinates of vector v1
    :param v2: coordinates of vector v2
    :returns : angle in degree or rad
    """
    if np.array_equal(v1, v2):
        return 0.0
    dm = np.dot(v1, v2)
    cm = np.linalg.norm(v1) * np.linalg.norm(v2)
    angle = np.arccos(round(dm/cm, 10))  # Round here to prevent floating point errors
    return math.degrees(angle) if deg else angle


def normalize_vector(v):
    """Take a vector and return the normalized vector
    :param v: a vector v
    :returns : normalized vector v
    """
    norm = np.linalg.norm(v)
    return v/norm if not norm == 0 else v


def centroid(coo):
    """Calculates the centroid from a 3D point cloud and returns the coordinates
    :param coo: Array of coordinate arrays
    :returns : centroid coordinates as list
    """
    return map(np.mean, (([c[0] for c in coo]), ([c[1] for c in coo]), ([c[2] for c in coo])))


def projection(pnormal1, ppoint, tpoint):
    """Calculates the centroid from a 3D point cloud and returns the coordinates
    :param pnormal1: normal of plane
    :param ppoint: coordinates of point in the plane
    :param tpoint: coordinates of point to be projected
    :returns : coordinates of point orthogonally projected on the plane
    """
    # Choose the plane normal pointing to the point to be projected
    pnormal2 = [coo*(-1) for coo in pnormal1]
    d1 = euclidean3d(tpoint, pnormal1 + ppoint)
    d2 = euclidean3d(tpoint, pnormal2 + ppoint)
    pnormal = pnormal1 if d1 < d2 else pnormal2
    # Calculate the projection of tpoint to the plane
    sn = -np.dot(pnormal, vector(ppoint, tpoint))
    sd = np.dot(pnormal, pnormal)
    sb = sn / sd
    return [c1 + c2 for c1, c2 in zip(tpoint, [sb*pn for pn in pnormal])]


def cluster_doubles(double_list):
    """Given a list of doubles, they are clustered if they share one element
    :param double_list: list of doubles
    :returns : list of clusters (tuples)
    """
    location = {}  # hashtable of which cluster each element is in
    clusters = []
    # Go through each double
    for t in double_list:
        a, b = t[0], t[1]
        # If they both are already in different clusters, merge the clusters
        if a in location and b in location:
            if location[a] != location[b]:
                clusters[location[a]] = clusters[location[a]].union(clusters[location[b]])  # Merge clusters
                clusters = clusters[:location[a]+1] + clusters[location[b]+1:]  # Delete other cluster
                # Rebuild index of locations for each element as they have changed now
                location = {}
                for i, cluster in enumerate(clusters):
                    for c in cluster:
                        location[c] = i
        else:
            # If a is already in a cluster, add b to that cluster
            if a in location:
                clusters[location[a]].add(b)
                location[b] = location[a]
            # If b is already in a cluster, add a to that cluster
            if b in location:
                clusters[location[b]].add(a)
                location[a] = location[b]
            # If neither a nor b is in any cluster, create a new one with a and b
            if not (b in location and a in location):
                clusters.append(set(t))
                location[a] = len(clusters) - 1
                location[b] = len(clusters) - 1
    return map(tuple, clusters)


#################
# File operations
#################

def tilde_expansion(folder_path):
    """Tilde expansion, i.e. converts '~' in paths into <value of $HOME>."""
    return os.path.expanduser(folder_path) if '~' in folder_path else folder_path


def folder_exists(folder_path):
    """Checks if a folder exists"""
    return os.path.exists(folder_path)


def create_folder_if_not_exists(folder_path):
    """Creates a folder if it does not exists."""
    folder_path = tilde_expansion(folder_path)
    folder_path = "".join([folder_path, '/']) if not folder_path[-1] == '/' else folder_path
    direc = os.path.dirname(folder_path)
    if not folder_exists(direc):
        os.makedirs(direc)


def cmd_exists(c):
    return subprocess.call("type " + c, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0

################
# PyMOL-specific
################


def object_exists(object_name):
    """Checks if an object exists in the open PyMOL session."""
    return object_name in cmd.get_names("objects")


def initialize_pymol(options):
    """Initializes PyMOL"""
    # Pass standard arguments of function to prevent PyMOL from printing out PDB headers (workaround)
    finish_launching(args=['pymol', options, '-K'])
    cmd.reinitialize()


def start_pymol(quiet=False, options='-p', run=False):
    """Starts up PyMOL and sets general options. Quiet mode suppresses all PyMOL output.
    Command line options can be passed as the second argument."""
    import pymol
    pymol.pymol_argv = ['pymol', '%s' % options] + sys.argv[1:]
    if run:
        initialize_pymol(options)
    if quiet:
        cmd.feedback('disable', 'all', 'everything')


def get_bs_coordinates(fil, dist, lig):
    """Load a structure file and get all coordinates from the binding site atoms within
    a defined distance around a specific ligand."""
    dist = int(dist)
    cmd.load(fil)
    cmd.select("tmp", "(all within %i of resn %s) and not resn %s" % (dist, lig, lig))
    cmd.select("tmp", "tmp and not hetatm")
    coordinates = cmd.get_model('tmp', 1).get_coord_list()
    return coordinates


def standard_settings():
    """Sets up standard settings for a nice visualization."""
    cmd.set('bg_rgb', [1.0, 1.0, 1.0])  # White background
    cmd.set('depth_cue', 0)  # Turn off depth cueing (no fog)
    cmd.set('cartoon_side_chain_helper', 1)  # Improve combined visualization of sticks and cartoon
    cmd.set('cartoon_fancy_helices', 1)  # Nicer visualization of helices (using tapered ends)
    cmd.set('transparency_mode', 1)  # Turn on multilayer transparency
    cmd.set('dash_radius', 0.05)
    set_custom_colorset()


def set_custom_colorset():
    """Defines a colorset with matching colors. Provided by Joachim."""
    cmd.set_color('myorange', '[253, 174, 97]')
    cmd.set_color('mygreen', '[171, 221, 164]')
    cmd.set_color('myred', '[215, 25, 28]')
    cmd.set_color('myblue', '[43, 131, 186]')
    cmd.set_color('mylightblue', '[158, 202, 225]')
    cmd.set_color('mylightgreen', '[229, 245, 224]')


#############################################
# Following code adapted from Joachim Haupt #
#############################################


def getligs(mol, altconf, idx_to_pdb, modres, covalent):
    """Get all ligands from a PDB file. Adapted from Joachim's structTools"""
    #############################
    # Read in file and get name #
    #############################

    data = namedtuple('ligand', 'mol mapping water members')
    ligands = []

    #########################
    # Filtering using lists #
    #########################

    all_res = [o for o in pybel.ob.OBResidueIter(mol.OBMol)
               if not (o.GetResidueProperty(9) or o.GetResidueProperty(0))]
    water = [o for o in pybel.ob.OBResidueIter(mol.OBMol) if o.GetResidueProperty(9)]
    all_res = [a for a in all_res if is_lig(a.GetName()) and a.GetName() not in modres]  # Filter out non-ligands

    ############################################
    # Filtering by counting and artifacts list #
    ############################################
    # #@todo Reduce the use of BioLiP lists
    artifacts = []
    unique_ligs = set(a.GetName() for a in all_res)
    for ulig in unique_ligs:
        # Discard if appearing 10 times or more and is possible artifact
        if is_biolip_artifact(ulig) and [a.GetName() for a in all_res].count(ulig) >= 10:
            artifacts.append(ulig)
    all_res = [a for a in all_res if a.GetName() not in artifacts]
    all_res_dict = {(a.GetName(), a.GetChain(), a.GetNum()): a for a in all_res}

    #########################
    # Identify kmer ligands #
    #########################

    lignames = list(set([a.GetName() for a in all_res]))
    # Remove all those not considered by ligands and pairings including alternate conformations

    ligdoubles = [[(link.id1, link.chain1, link.pos1),
                   (link.id2, link.chain2, link.pos2)] for link in
                  [c for c in covalent if c.id1 in lignames and c.id2 in lignames and
                   c.conf1 in ['A', ''] and c.conf2 in ['A', '']
                  and (c.id1, c.chain1, c.pos1) in all_res_dict and (c.id2, c.chain2, c.pos2) in all_res_dict]]
    kmers = cluster_doubles(ligdoubles)
    if not kmers:  # No ligand kmers, just normal independent ligands
        res_kmers = [[all_res_dict[res]] for res in all_res_dict]
    else:
        # res_kmers contains clusters of covalently bound ligand residues (kmer ligands)
        res_kmers = [[all_res_dict[res] for res in kmer] for kmer in kmers]

        # In this case, add other ligands which are not part of a kmer
        in_kmer = []
        for res_kmer in res_kmers:
            for res in res_kmer:
                in_kmer.append((res.GetName(), res.GetChain(), res.GetNum()))
        for res in all_res_dict:
            if res not in in_kmer:
                newres = [all_res_dict[res], ]
                res_kmers.append(newres)

    ###################
    # Extract ligands #
    ###################

    for kmer in res_kmers:  # iterate over all ligands
        members = [(res.GetName(), res.GetChain(), res.GetNum()) for res in kmer]
        rname, rchain, rnum = sorted(members)[0]  # representative name, chain, and number
        hetatoms = set()
        for obresidue in kmer:
            hetatoms_res = set([(obatom.GetIdx(), obatom) for obatom in pybel.ob.OBResidueAtomIter(obresidue)
                        if not obatom.IsHydrogen()])

            hetatoms_res = set([atm for atm in hetatoms_res if not idx_to_pdb[atm[0]] in altconf])  # Remove alt. conformations
            hetatoms.update(hetatoms_res)
        if len(hetatoms) == 0:
            continue
        hetatoms = dict(hetatoms)  # make it a dict with idx as key and OBAtom as value
        lig = pybel.ob.OBMol()  # new ligand mol
        neighbours = dict()
        for obatom in hetatoms.values():  # iterate over atom objects
            idx = obatom.GetIdx()
            lig.AddAtom(obatom)
            # ids of all neighbours of obatom
            neighbours[idx] = set([neighbour_atom.GetIdx() for neighbour_atom
                                   in pybel.ob.OBAtomAtomIter(obatom)]) & set(hetatoms.keys())

        ##############################################################
        # map the old atom idx of OBMol to the new idx of the ligand #
        ##############################################################

        newidx = dict(zip(hetatoms.keys(), [obatom.GetIdx() for obatom in pybel.ob.OBMolAtomIter(lig)]))
        mapold = dict(zip(newidx.values(), newidx))
        # copy the bonds
        for obatom in hetatoms:
            for neighbour_atom in neighbours[obatom]:
                bond = hetatoms[obatom].GetBond(hetatoms[neighbour_atom])
                lig.AddBond(newidx[obatom], newidx[neighbour_atom], bond.GetBondOrder())
        lig = pybel.Molecule(lig)
        # For kmers, the representative ids are chosen (first residue of kmer)
        lig.data.update({'Name': rname,
                         'Chain': rchain,
                         'ResNr': rnum})
        lig.title = '-'.join((rname, rchain, str(rnum)))
        ligands.append(data(mol=lig, mapping=mapold, water=water, members=members))
    return ligands


def read_pdb(pdbfname, safe=False):
    """Reads a given PDB file and returns a Pybel Molecule. If requested, do it
    safely to except Open Babel crashes. All bonds are read in as single bonds
    if requested, saving a lot of time at OpenBabel import."""
    global exitcode
    pybel.ob.obErrorLog.StopLogging()  # Suppress all OpenBabel warnings
    if os.name != 'nt':  # Resource module not available for Windows
        resource.setrlimit(resource.RLIMIT_STACK, (2**28, -1))  # set stack size to 256MB
    sys.setrecursionlimit(10**5)  # increase Python recoursion limit
    success = True
    if safe:  # read the file safely, since it can happen, that babel crashes on large files
        if os.path.exists(pdbfname):
            def f(fname):
                readmol('pdb', fname)
            p = Process(target=f, args=(pdbfname,))  # make the file reading a separate process
            p.start()
            p.join()
            exitcode = p.exitcode
            success = exitcode == 0
            del p
        else:
            print("  Error: PDB file not found!")
            success = False
            exitcode = 1
    if success:
        mol = readmol('pdb', pdbfname)  # only read the file iff it was successful before
    elif exitcode == 4:
        sys.stderr.write('Error: Input file could not be read by OpenBabel.')
        sys.exit(4)
    else:
        mol = pybel.Molecule(pybel.ob.OBMol())
        print("  Error: Failed to read '%s' with OpenBabel (exit code %d)!" % (pdbfname, exitcode))
    return mol


def readmol(fformat='mol', path=None):
    """Reads the given molecule file and returns the corresponding Pybel molecule.
    In contrast to the standard Pybel implementation, the file is closed properly."""
    obc = pybel.ob.OBConversion()
    obc.SetInFormat(fformat)
    mol = pybel.ob.OBMol()
    with open(path) as f:
        obc.ReadString(mol, str(f.read()))
        if mol.Empty():
            sys.exit(4)
    return pybel.Molecule(mol)