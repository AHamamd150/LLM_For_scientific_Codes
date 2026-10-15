#!/usr/bin/env python3
import sys
import math
import numpy as np
import matplotlib.pyplot as plt
import csv

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

def get_leptons(event):
    """Return all electrons and muons."""
    return [o for o in event['objects'] if o['type'] in (1, 2)]

def get_electrons(event):
    """Return all electrons."""
    return [o for o in event['objects'] if o['type'] == 1]

def get_muons(event):
    """Return all muons."""
    return [o for o in event['objects'] if o['type'] == 2]

def get_taus(event):
    """Return all taus."""
    return [o for o in event['objects'] if o['type'] == 3]

def get_jets(event):
    """Return all jets."""
    return [o for o in event['objects'] if o['type'] == 4]

def get_bjets(event):
    """Return all b-tagged jets."""
    return [o for o in event['objects'] if o['type'] == 4 and int(o['btag']) == 1]

def get_light_jets(event):
    """Return all non-b-tagged jets."""
    return [o for o in event['objects'] if o['type'] == 4 and int(o['btag']) == 0]

def get_photons(event):
    """Return all photons."""
    return [o for o in event['objects'] if o['type'] == 0]

def helper_get_met(event):
    """Return MET object or None."""
    for o in event['objects']:
        if o['type'] == 6:
            return o
    return None

def helper_get_leading(particles):
    """Return leading (highest pT) particle or None."""
    if not particles:
        return None
    return max(particles, key=lambda p: p['pt'])

def helper_get_subleading(particles):
    """Return subleading (second highest pT) particle or None."""
    if len(particles) < 2:
        return None
    sorted_p = sorted(particles, key=lambda p: p['pt'], reverse=True)
    return sorted_p[1]

def sort_by_pt(particles):
    """Return particles sorted by pT (descending)."""
    return sorted(particles, key=lambda p: p['pt'], reverse=True)

def n_jets(event, pt_cut=0.0, eta_cut=float('inf')):
    """Count jets passing pT and |η| cuts."""
    jets = get_jets(event)
    return sum(1 for j in jets if j['pt'] > pt_cut and abs(j['eta']) < eta_cut)

def n_bjets(event, pt_cut=0.0, eta_cut=float('inf')):
    """Count b-jets passing pT and |η| cuts."""
    bjets = get_bjets(event)
    return sum(1 for b in bjets if b['pt'] > pt_cut and abs(b['eta']) < eta_cut)

def n_leptons(event, pt_cut=0.0, eta_cut=float('inf')):
    """Count leptons passing pT and |η| cuts."""
    leptons = get_leptons(event)
    return sum(1 for l in leptons if l['pt'] > pt_cut and abs(l['eta']) < eta_cut)

def compute_phi(obj):
    """Compute azimuthal angle phi from momentum components."""
    _, px, py, _ = four_momentum(obj)
    return math.atan2(py, px)

def vector_pt_components(particles):
    """Return (px_total, py_total) for vector pT sum."""
    px_tot = sum(p['pt'] * math.cos(p['phi']) for p in particles)
    py_tot = sum(p['pt'] * math.sin(p['phi']) for p in particles)
    return px_tot, py_tot

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
        "Electron and muon selection": 0,
        "Exactly 1 lepton": 0,
        "At least 2 jets": 0,
        "No b-jets": 0,
        "MET > 30 GeV": 0,
        "Transverse mass 40-120 GeV": 0,
        "Dijet mass 60-100 GeV": 0,
        "Delta R < 3.0": 0,
        "Final": 0
    }

    mt_list = []
    mjj_list = []
    met_list = []
    lepton_pt_list = []
    jet1_pt_list = []
    jet2_pt_list = []
    dr_list = []
    dphi_list = []
    lepton_eta_list = []
    dphi_lepton_jets_list = []

    csv_data = []

    for event in events:
        # Step 1: Select electrons and muons
        electrons = get_electrons(event)
        muons = get_muons(event)
        leptons = []
        for l in electrons:
            if l['pt'] > 25 and abs(l['eta']) < 2.5:
                leptons.append(l)
        for l in muons:
            if l['pt'] > 20 and abs(l['eta']) < 2.4:
                leptons.append(l)
        if len(leptons) != 1:
            continue
        cutflow["Electron and muon selection"] += 1

        # Step 2: Exactly 1 lepton
        if len(leptons) != 1:
            continue
        cutflow["Exactly 1 lepton"] += 1

        # Step 3: At least 2 jets
        jets = get_jets(event)
        jets = [j for j in jets if j['pt'] > 30 and abs(j['eta']) < 2.5]
        if len(jets) < 2:
            continue
        cutflow["At least 2 jets"] += 1

        # Step 4: No b-jets
        bjets = get_bjets(event)
        if any(b['pt'] > 30 and abs(b['eta']) < 2.5 for b in bjets):
            continue
        cutflow["No b-jets"] += 1

        # Step 5: MET > 30 GeV
        met = helper_get_met(event)
        if met is None or met['pt'] < 30:
            continue
        cutflow["MET > 30 GeV"] += 1

        # Step 6: Transverse mass of lepton + MET between 40 and 120 GeV
        lepton = leptons[0]
        mt = helper_transverse_mass(lepton, met)
        if not (40 < mt < 120):
            continue
        cutflow["Transverse mass 40-120 GeV"] += 1

        # Step 7: Invariant mass of two leading jets between 60 and 100 GeV
        jet1 = helper_get_leading(jets)
        jet2 = helper_get_subleading(jets)
        if jet1 is None or jet2 is None:
            continue
        mjj = helper_invariant_mass(jet1, jet2)
        if not (60 < mjj < 100):
            continue
        cutflow["Dijet mass 60-100 GeV"] += 1

        # Step 8: Delta R between two leading jets < 3.0
        dr = helper_delta_r(jet1, jet2)
        if dr >= 3.0:
            continue
        cutflow["Delta R < 3.0"] += 1

        # Save for plots and CSV
        mt_list.append(mt)
        mjj_list.append(mjj)
        met_list.append(met['pt'])
        lepton_pt_list.append(lepton['pt'])
        jet1_pt_list.append(jet1['pt'])
        jet2_pt_list.append(jet2['pt'])
        dr_list.append(dr)

        # Delta phi between lepton and MET
        dphi = helper_delta_phi(lepton['phi'], met['phi'])
        dphi_list.append(dphi)

        # Lepton eta
        lepton_eta_list.append(lepton['eta'])

        # Delta phi between lepton and two-jet system
        jet_system = sum_objects(jet1, jet2)
        if jet_system is not None:
            dphi_lepton_jets = helper_delta_phi(lepton['phi'], jet_system['phi'])
        else:
            dphi_lepton_jets = 0.0
        dphi_lepton_jets_list.append(dphi_lepton_jets)

        # CSV data
        csv_data.append([
            mt,
            mjj,
            met['pt'],
            lepton['pt'],
            dr,
            dphi_lepton_jets
        ])

        cutflow["Final"] += 1

    # Print cutflow
    for key, value in cutflow.items():
        print(f"{key}: {value}")

    # Plotting
    plt.figure()
    plt.hist(mt_list, bins=40, range=(30, 150), density=True)
    plt.xlabel("Transverse mass (GeV)")
    plt.ylabel("density")
    plt.savefig("mt_hist.png")
    plt.close()

    plt.figure()
    plt.hist(mjj_list, bins=40, range=(40, 120), density=True)
    plt.xlabel("Dijet mass (GeV)")
    plt.ylabel("density")
    plt.savefig("mjj_hist.png")
    plt.close()

    plt.figure()
    plt.hist(met_list, bins=40, range=(0, 200), density=True)
    plt.xlabel("MET (GeV)")
    plt.ylabel("density")
    plt.savefig("met_hist.png")
    plt.close()

    plt.figure()
    plt.hist(lepton_pt_list, bins=40, range=(0, 200), density=True)
    plt.xlabel("Lepton pT (GeV)")
    plt.ylabel("density")
    plt.savefig("lepton_pt_hist.png")
    plt.close()

    plt.figure()
    plt.hist(jet1_pt_list, bins=40, range=(0, 200), density=True)
    plt.xlabel("Leading jet pT (GeV)")
    plt.ylabel("density")
    plt.savefig("jet1_pt_hist.png")
    plt.close()

    plt.figure()
    plt.hist(jet2_pt_list, bins=40, range=(0, 200), density=True)
    plt.xlabel("Subleading jet pT (GeV)")
    plt.ylabel("density")
    plt.savefig("jet2_pt_hist.png")
    plt.close()

    plt.figure()
    plt.hist(dr_list, bins=40, range=(0, 5), density=True)
    plt.xlabel("Delta R between jets")
    plt.ylabel("density")
    plt.savefig("dr_hist.png")
    plt.close()

    plt.figure()
    plt.hist(dphi_list, bins=40, range=(-3.14, 3.14), density=True)
    plt.xlabel("Delta phi between lepton and MET")
    plt.ylabel("density")
    plt.savefig("dphi_lepton_met_hist.png")
    plt.close()

    plt.figure()
    plt.hist(lepton_eta_list, bins=40, range=(-2.5, 2.5), density=True)
    plt.xlabel("Lepton eta")
    plt.ylabel("density")
    plt.savefig("lepton_eta_hist.png")
    plt.close()

    plt.figure()
    plt.hist(dphi_lepton_jets_list, bins=40, range=(-3.14, 3.14), density=True)
    plt.xlabel("Delta phi between lepton and two-jet system")
    plt.ylabel("density")
    plt.savefig("dphi_lepton_jets_hist.png")
    plt.close()

    # Save CSV
    with open("mlp_data.csv", "w", newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(["mt", "mjj", "met", "lepton_pt", "dr", "dphi_lepton_jets"])
        csvwriter.writerows(csv_data)

if __name__ == "__main__":
    main()
