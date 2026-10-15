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
        "Initial events": len(events),
        "Electrons (pT > 15, |eta| < 2.5)": 0,
        "Muons (pT > 10, |eta| < 2.4)": 0,
        "Exactly 2 electrons and 1 muon": 0,
        "Opposite sign electrons": 0,
        "Z mass (76 < m < 106 GeV)": 0,
        "MET > 30 GeV": 0,
        "W muon pT > 20 GeV": 0,
        "W transverse mass > 30 GeV": 0,
        "Final selected events": 0
    }

    z_mass_list = []
    w_trans_mass_list = []
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
        cutflow["Electrons (pT > 15, |eta| < 2.5)"] += 1

        # Step 2: Select muons with pT > 10 GeV and |eta| < 2.4
        muons = [m for m in get_muons(event) if m['pt'] > 10 and abs(m['eta']) < 2.4]
        if len(muons) < 1:
            continue
        cutflow["Muons (pT > 10, |eta| < 2.4)"] += 1

        # Step 3: Require exactly 2 electrons and 1 muon
        if len(electrons) != 2 or len(muons) != 1:
            continue
        cutflow["Exactly 2 electrons and 1 muon"] += 1

        # Step 4: Opposite sign electrons
        e1, e2 = electrons
        if not opposite_sign(e1, e2):
            continue
        cutflow["Opposite sign electrons"] += 1

        # Step 5: Build Z object from electrons
        z_obj = sum_objects(e1, e2)
        if z_obj is None:
            continue
        z_mass = helper_invariant_mass(e1, e2)
        if not (76 < z_mass < 106):
            continue
        cutflow["Z mass (76 < m < 106 GeV)"] += 1

        # Step 6: MET > 30 GeV
        met = helper_get_met(event)
        if met is None or met['pt'] < 30:
            continue
        cutflow["MET > 30 GeV"] += 1

        # Step 7: W muon pT > 20 GeV
        w_muon = muons[0]
        if w_muon['pt'] < 20:
            continue
        cutflow["W muon pT > 20 GeV"] += 1

        # Step 8: W transverse mass > 30 GeV
        w_trans_mass = helper_transverse_mass(w_muon, met)
        if w_trans_mass < 30:
            continue
        cutflow["W transverse mass > 30 GeV"] += 1

        # Collect data for plots
        cutflow["Final selected events"] += 1

        z_mass_list.append(z_mass)
        w_trans_mass_list.append(w_trans_mass)
        met_list.append(met['pt'])

        # Three-lepton system
        three_lepton = sum_objects(e1, e2, w_muon)
        three_lepton_pt = three_lepton['pt'] if three_lepton else 0.0
        three_lepton_pt_list.append(three_lepton_pt)
        three_lepton_mass = helper_invariant_mass(e1, e2, w_muon)
        three_lepton_mass_list.append(three_lepton_mass)

        z_pt_list.append(z_obj['pt'])
        w_muon_pt_list.append(w_muon['pt'])
        delta_phi_z_met = helper_delta_phi(z_obj['phi'], met['phi'])
        delta_phi_z_met_list.append(delta_phi_z_met)
        delta_r_electrons = helper_delta_r(e1, e2)
        delta_r_electrons_list.append(delta_r_electrons)
        w_muon_eta_list.append(w_muon['eta'])

    # Plotting
    plt.figure()
    plt.hist(z_mass_list, bins=40, range=(60, 120), density=True)
    plt.xlabel("Z mass (GeV)")
    plt.ylabel("density")
    plt.savefig("z_mass.png")
    plt.close()

    plt.figure()
    plt.hist(w_trans_mass_list, bins=40, density=True)
    plt.xlabel("W transverse mass (GeV)")
    plt.ylabel("density")
    plt.savefig("w_trans_mass.png")
    plt.close()

    plt.figure()
    plt.hist(met_list, bins=40, density=True)
    plt.xlabel("MET (GeV)")
    plt.ylabel("density")
    plt.savefig("met.png")
    plt.close()

    plt.figure()
    plt.hist(three_lepton_pt_list, bins=40, density=True)
    plt.xlabel("Three-lepton pT (GeV)")
    plt.ylabel("density")
    plt.savefig("three_lepton_pt.png")
    plt.close()

    plt.figure()
    plt.hist(z_pt_list, bins=40, density=True)
    plt.xlabel("Z pT (GeV)")
    plt.ylabel("density")
    plt.savefig("z_pt.png")
    plt.close()

    plt.figure()
    plt.hist(w_muon_pt_list, bins=40, density=True)
    plt.xlabel("W muon pT (GeV)")
    plt.ylabel("density")
    plt.savefig("w_muon_pt.png")
    plt.close()

    plt.figure()
    plt.hist(delta_phi_z_met_list, bins=40, range=(-3.14, 3.14), density=True)
    plt.xlabel("Delta phi (Z, MET)")
    plt.ylabel("density")
    plt.savefig("delta_phi_z_met.png")
    plt.close()

    plt.figure()
    plt.hist(three_lepton_mass_list, bins=40, density=True)
    plt.xlabel("Three-lepton mass (GeV)")
    plt.ylabel("density")
    plt.savefig("three_lepton_mass.png")
    plt.close()

    plt.figure()
    plt.hist(delta_r_electrons_list, bins=40, density=True)
    plt.xlabel("Delta R (electrons)")
    plt.ylabel("density")
    plt.savefig("delta_r_electrons.png")
    plt.close()

    plt.figure()
    plt.hist(w_muon_eta_list, bins=40, density=True)
    plt.xlabel("W muon eta")
    plt.ylabel("density")
    plt.savefig("w_muon_eta.png")
    plt.close()

    # Print cutflow
    for key, value in cutflow.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    main()
