#!/usr/bin/env python3
import sys
import math
import numpy as np
import matplotlib.pyplot as plt

def get_particle_mass(obj):
    """Return appropriate mass based on particle type."""
    if 'type' not in obj:
        return obj.get('mass', obj.get('jmass', 0.0))

    ptype = obj['type']
    if ptype == 0:    # photon
        return 0.0
    elif ptype == 1:  # electron
        return 0.0
    elif ptype == 2:  # muon
        return 0.0
    elif ptype == 3:  # tau
        return 1.777
    elif ptype == 4:  # jet
        return obj['jmass']
    else:
        return obj.get('mass', 0.0)

def four_momentum(obj):
    """Return (E, px, py, pz) from an object dict."""
    pt  = obj['pt']
    eta = obj['eta']
    phi = obj['phi']
    m   = get_particle_mass(obj)

    px = pt * math.cos(phi)
    py = pt * math.sin(phi)
    pz = pt * math.sinh(eta)
    E  = math.sqrt(px**2 + py**2 + pz**2 + m**2)
    return E, px, py, pz

def obj_from_four_momentum(E, px, py, pz):
    """
    Reconstruct a composite object dict from four-momentum (E, px, py, pz).
    Returns a dict with pt, eta, phi, and mass.
    """
    pt = math.sqrt(px**2 + py**2)
    phi = math.atan2(py, px)

    if pt > 0.0:
        eta = math.asinh(pz / pt)
    elif pz != 0.0:
        eta = math.copysign(float("inf"), pz)
    else:
        eta = 0.0

    p2 = px**2 + py**2 + pz**2
    m2 = E**2 - p2
    mass = math.sqrt(m2) if m2 > 0.0 else 0.0

    return {
        "pt": pt,
        "eta": eta,
        "phi": phi,
        "mass": mass
    }

def sum_objects(*args):
    """Return composite object from any combination of particles/lists."""
    particles = []
    for arg in args:
        if arg is None:
            continue
        if isinstance(arg, dict):
            particles.append(arg)
        elif isinstance(arg, list):
            particles.extend(p for p in arg if p is not None)

    if not particles:
        return None

    E_tot, px_tot, py_tot, pz_tot = 0.0, 0.0, 0.0, 0.0
    for p in particles:
        E, px, py, pz = four_momentum(p)
        E_tot += E
        px_tot += px
        py_tot += py
        pz_tot += pz

    return obj_from_four_momentum(E_tot, px_tot, py_tot, pz_tot)

def helper_invariant_mass(*args):
    """Return invariant mass from any combination of particles/lists."""
    obj = sum_objects(*args)
    return obj['mass'] if obj is not None else 0.0

def helper_delta_phi(phi1, phi2):
    """Compute Δφ normalized to [-π, π]."""
    dphi = phi1 - phi2
    while dphi > math.pi:
        dphi -= 2 * math.pi
    while dphi < -math.pi:
        dphi += 2 * math.pi
    return dphi

def helper_delta_r(obj1, obj2):
    """Compute ΔR between two objects."""
    deta = obj1['eta'] - obj2['eta']
    dphi = helper_delta_phi(obj1['phi'], obj2['phi'])
    return math.sqrt(deta**2 + dphi**2)

def helper_transverse_mass(visible, met):
    """Compute transverse mass of visible particle + MET."""
    dphi = helper_delta_phi(visible['phi'], met['phi'])
    return math.sqrt(2 * visible['pt'] * met['pt'] * (1 - math.cos(dphi)))

def read_lhco(filename):
    """Parse LHCO file and return list of events."""
    events = []
    current = None

    with open(filename) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = line.split()
            if not parts:
                continue

            # New event header (index = 0)
            if parts[0] == '0':
                if len(parts) < 2:
                    continue
                try:
                    event_id = int(parts[1])
                except ValueError:
                    continue
                if current is not None:
                    events.append(current)
                current = {'id': event_id, 'objects': []}

            # Object line
            elif current is not None:
                if len(parts) < 7:
                    continue
                try:
                    obj = {
                        'type':   int(parts[1]),
                        'eta':    float(parts[2]),
                        'phi':    float(parts[3]),
                        'pt':     float(parts[4]),
                        'jmass':  float(parts[5]),
                        'ntrk':   float(parts[6]),
                        'btag':   float(parts[7]) if len(parts) > 7 else 0.0,
                        'had_em': float(parts[8]) if len(parts) > 8 else 0.0
                    }
                except ValueError:
                    continue

                obj['charge'] = 1 if obj['ntrk'] > 0 else (-1 if obj['ntrk'] < 0 else 0)
                current['objects'].append(obj)

    if current is not None:
        events.append(current)

    return events

def get_electrons(event):
    """Return all electrons."""
    return [o for o in event['objects'] if o['type'] == 1]

def get_muons(event):
    """Return all muons."""
    return [o for o in event['objects'] if o['type'] == 2]

def opposite_sign(obj1, obj2):
    """Check if two objects have opposite charge."""
    return obj1['charge'] * obj2['charge'] < 0

def helper_get_met(event):
    """Return MET object or None."""
    for o in event['objects']:
        if o['type'] == 6:
            return o
    return None

def abs_eta(obj):
    """Return |η| of a particle."""
    return abs(obj['eta'])

def helper_get_leading(particles):
    """Return leading (highest pT) particle or None."""
    if not particles:
        return None
    return max(particles, key=lambda p: p['pt'])

def n_electrons(event, pt_cut=0.0, eta_cut=float('inf')):
    """Count electrons passing pT and |η| cuts."""
    electrons = get_electrons(event)
    return sum(1 for e in electrons if e['pt'] > pt_cut and abs(e['eta']) < eta_cut)

def n_muons(event, pt_cut=0.0, eta_cut=float('inf')):
    """Count muons passing pT and |η| cuts."""
    muons = get_muons(event)
    return sum(1 for m in muons if m['pt'] > pt_cut and abs(m['eta']) < eta_cut)

def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py <lhco_file1> [lhco_file2] ...")
        return

    files = sys.argv[1:]
    events = []
    for f in files:
        events.extend(read_lhco(f))

    cutflow = {
        "Initial": len(events),
        "Electron Selection": 0,
        "Muon Selection": 0,
        "Exactly 2 Electrons and 1 Muon": 0,
        "Opposite Charge Electrons": 0,
        "Z Mass Cut": 0,
        "MET Cut": 0,
        "W Muon pT Cut": 0,
        "W Transverse Mass Cut": 0,
        "Final": 0
    }

    z_mass_list = []
    w_transverse_mass_list = []
    met_list = []
    three_lepton_pt_list = []
    z_pt_list = []
    w_muon_pt_list = []
    delta_phi_z_met_list = []
    three_lepton_mass_list = []
    delta_r_electrons_list = []
    w_muon_eta_list = []

    for event in events:
        # Step 1: Select electrons with pT > 15 GeV and |eta| < 2.5
        electrons = [e for e in get_electrons(event) if e['pt'] > 15 and abs(e['eta']) < 2.5]
        if len(electrons) < 2:
            continue
        cutflow["Electron Selection"] += 1

        # Step 2: Select muons with pT > 10 GeV and |eta| < 2.4
        muons = [m for m in get_muons(event) if m['pt'] > 10 and abs(m['eta']) < 2.4]
        if len(muons) < 1:
            continue
        cutflow["Muon Selection"] += 1

        # Step 3: Require exactly 2 selected electrons and exactly 1 selected muon
        if len(electrons) != 2 or len(muons) != 1:
            continue
        cutflow["Exactly 2 Electrons and 1 Muon"] += 1

        # Step 4: Require the two selected electrons to have opposite charge
        e1, e2 = electrons
        if not opposite_sign(e1, e2):
            continue
        cutflow["Opposite Charge Electrons"] += 1

        # Step 5: Build z_obj from the two selected electrons
        z_obj = sum_objects(e1, e2)

        # Step 6: Select invariant mass of z_obj between 76 and 106 GeV
        z_mass = helper_invariant_mass(e1, e2)
        if not (76 < z_mass < 106):
            continue
        cutflow["Z Mass Cut"] += 1

        # Step 7: Define the selected muon as the W candidate lepton
        w_muon = muons[0]

        # Step 8: Require MET > 30 GeV
        met = helper_get_met(event)
        if met is None or met['pt'] < 30:
            continue
        cutflow["MET Cut"] += 1

        # Step 9: W candidate muon must have pT > 20 GeV
        if w_muon['pt'] < 20:
            continue
        cutflow["W Muon pT Cut"] += 1

        # Step 10: Select transverse mass of W candidate muon + MET > 30 GeV
        w_transverse_mass = helper_transverse_mass(w_muon, met)
        if w_transverse_mass < 30:
            continue
        cutflow["W Transverse Mass Cut"] += 1

        # Collect data for plots
        cutflow["Final"] += 1

        # Invariant mass of z_obj
        z_mass_list.append(z_mass)

        # Transverse mass of W candidate + MET
        w_transverse_mass_list.append(w_transverse_mass)

        # MET distribution
        met_list.append(met['pt'])

        # pT of three-lepton system (e1, e2, w_muon)
        three_lepton = sum_objects(e1, e2, w_muon)
        three_lepton_pt_list.append(three_lepton['pt'])

        # pT of z_obj
        z_pt_list.append(z_obj['pt'])

        # pT of W candidate muon
        w_muon_pt_list.append(w_muon['pt'])

        # Delta phi between z_obj and MET
        delta_phi_z_met = helper_delta_phi(z_obj['phi'], met['phi'])
        delta_phi_z_met_list.append(delta_phi_z_met)

        # Invariant mass of three-lepton system
        three_lepton_mass = helper_invariant_mass(e1, e2, w_muon)
        three_lepton_mass_list.append(three_lepton_mass)

        # Delta R between the two electrons forming z_obj
        delta_r_electrons = helper_delta_r(e1, e2)
        delta_r_electrons_list.append(delta_r_electrons)

        # Eta of the W candidate muon
        w_muon_eta_list.append(w_muon['eta'])

    # Print cutflow
    for key, value in cutflow.items():
        print(f"{key}: {value}")

    # Plotting
    def plot_histogram(data, title, xlabel, filename):
        plt.figure()
        plt.hist(data, bins=40, density=True)
        plt.xlabel(xlabel)
        plt.ylabel("density")
        plt.title(title)
        plt.savefig(filename)
        plt.close()

    plot_histogram(z_mass_list, "Z Mass", "Mass (GeV)", "z_mass.png")
    plot_histogram(w_transverse_mass_list, "W Transverse Mass", "Mass (GeV)", "w_transverse_mass.png")
    plot_histogram(met_list, "MET", "MET (GeV)", "met.png")
    plot_histogram(three_lepton_pt_list, "Three-Lepton pT", "pT (GeV)", "three_lepton_pt.png")
    plot_histogram(z_pt_list, "Z pT", "pT (GeV)", "z_pt.png")
    plot_histogram(w_muon_pt_list, "W Muon pT", "pT (GeV)", "w_muon_pt.png")
    plot_histogram(delta_phi_z_met_list, "Delta Phi (Z, MET)", "Delta Phi", "delta_phi_z_met.png")
    plot_histogram(three_lepton_mass_list, "Three-Lepton Mass", "Mass (GeV)", "three_lepton_mass.png")
    plot_histogram(delta_r_electrons_list, "Delta R (Electrons)", "Delta R", "delta_r_electrons.png")
    plot_histogram(w_muon_eta_list, "W Muon Eta", "Eta", "w_muon_eta.png")

if __name__ == "__main__":
    main()
