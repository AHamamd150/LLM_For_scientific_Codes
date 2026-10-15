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

def scalar_pt_sum(particles):
    """Compute scalar sum of pT for a list of particles."""
    return sum(p['pt'] for p in particles)

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
        "Lepton Selection": 0,
        "Jet Selection": 0,
        "BJet Selection": 0,
        "MET Selection": 0,
        "Transverse Mass Selection": 0,
        "Hadronic W Selection": 0,
        "Hadronic W Mass Selection": 0,
        "Top Candidate Selection": 0,
        "Final": 0
    }

    mt_list = []
    met_list = []
    leading_bjet_pt_list = []
    subleading_bjet_pt_list = []
    w_hadronic_mass_list = []
    top_mass_list = []
    dr_lepton_bjet_list = []
    ht_list = []
    njet_list = []
    leading_bjet_eta_list = []

    for event in events:
        # Step 1: Select electrons and muons
        leptons = get_leptons(event)
        electrons = get_electrons(event)
        muons = get_muons(event)

        # Apply pT and |eta| cuts
        selected_electrons = [e for e in electrons if e['pt'] > 25 and abs(e['eta']) < 2.5]
        selected_muons = [m for m in muons if m['pt'] > 25 and abs(m['eta']) < 2.4]
        selected_leptons = selected_electrons + selected_muons

        if len(selected_leptons) != 1:
            continue
        cutflow["Lepton Selection"] += 1

        # Step 2: Select jets
        jets = get_jets(event)
        selected_jets = [j for j in jets if j['pt'] > 30 and abs(j['eta']) < 2.5]
        if len(selected_jets) < 4:
            continue
        cutflow["Jet Selection"] += 1

        # Step 3: Select b-jets
        bjets = get_bjets(event)
        selected_bjets = [b for b in bjets if b['pt'] > 30 and abs(b['eta']) < 2.5]
        if len(selected_bjets) < 2:
            continue
        cutflow["BJet Selection"] += 1

        # Step 4: Select MET
        met = helper_get_met(event)
        if met is None or met['pt'] < 20:
            continue
        cutflow["MET Selection"] += 1

        # Step 5: Transverse mass of lepton + MET
        lepton = selected_leptons[0]
        mt = helper_transverse_mass(lepton, met)
        if mt < 30 or mt > 150:
            continue
        cutflow["Transverse Mass Selection"] += 1

        mt_list.append(mt)
        met_list.append(met['pt'])

        # Step 6: Build hadronic W from two leading non-b-tagged jets
        light_jets = get_light_jets(event)
        selected_light_jets = [j for j in light_jets if j['pt'] > 30 and abs(j['eta']) < 2.5]
        if len(selected_light_jets) < 2:
            continue
        cutflow["Hadronic W Selection"] += 1

        # Sort light jets by pT
        sorted_light_jets = sort_by_pt(selected_light_jets)
        jet1 = sorted_light_jets[0]
        jet2 = sorted_light_jets[1]
        w_hadronic = sum_objects(jet1, jet2)
        w_mass = helper_invariant_mass(jet1, jet2)

        if w_mass < 40 or w_mass > 120:
            continue
        cutflow["Hadronic W Mass Selection"] += 1

        w_hadronic_mass_list.append(w_mass)

        # Step 7: Build hadronic top from leading b-jet and hadronic W
        sorted_bjets = sort_by_pt(selected_bjets)
        bjet1 = sorted_bjets[0]
        bjet2 = sorted_bjets[1]
        top_hadronic = sum_objects(bjet1, w_hadronic)
        top_mass = helper_invariant_mass(bjet1, w_hadronic)

        leading_bjet_pt_list.append(bjet1['pt'])
        subleading_bjet_pt_list.append(bjet2['pt'])
        leading_bjet_eta_list.append(bjet1['eta'])

        # Step 8: Delta R between lepton and closest b-jet
        min_dr = float('inf')
        for bjet in selected_bjets:
            dr = helper_delta_r(lepton, bjet)
            if dr < min_dr:
                min_dr = dr
        dr_lepton_bjet_list.append(min_dr)

        # Step 9: HT (scalar sum of jet pT)
        ht = scalar_pt_sum(selected_jets)
        ht_list.append(ht)

        # Step 10: Number of jets
        njet_list.append(len(selected_jets))

        cutflow["Top Candidate Selection"] += 1

    cutflow["Final"] = cutflow["Top Candidate Selection"]

    # Print cutflow
    for key, value in cutflow.items():
        print(f"{key}: {value}")

    # Plotting
    plt.figure()
    plt.hist(mt_list, bins=40, density=True)
    plt.xlabel("MT (GeV)")
    plt.ylabel("density")
    plt.savefig("mt_hist.png")
    plt.close()

    plt.figure()
    plt.hist(met_list, bins=40, density=True)
    plt.xlabel("MET (GeV)")
    plt.ylabel("density")
    plt.savefig("met_hist.png")
    plt.close()

    plt.figure()
    plt.hist(leading_bjet_pt_list, bins=40, density=True)
    plt.xlabel("Leading b-jet pT (GeV)")
    plt.ylabel("density")
    plt.savefig("leading_bjet_pt_hist.png")
    plt.close()

    plt.figure()
    plt.hist(subleading_bjet_pt_list, bins=40, density=True)
    plt.xlabel("Subleading b-jet pT (GeV)")
    plt.ylabel("density")
    plt.savefig("subleading_bjet_pt_hist.png")
    plt.close()

    plt.figure()
    plt.hist(w_hadronic_mass_list, bins=40, density=True)
    plt.xlabel("W hadronic mass (GeV)")
    plt.ylabel("density")
    plt.savefig("w_hadronic_mass_hist.png")
    plt.close()

    plt.figure()
    plt.hist(top_mass_list, bins=40, density=True)
    plt.xlabel("Top hadronic mass (GeV)")
    plt.ylabel("density")
    plt.savefig("top_mass_hist.png")
    plt.close()

    plt.figure()
    plt.hist(dr_lepton_bjet_list, bins=40, density=True)
    plt.xlabel("ΔR(lepton, b-jet)")
    plt.ylabel("density")
    plt.savefig("dr_lepton_bjet_hist.png")
    plt.close()

    plt.figure()
    plt.hist(ht_list, bins=40, density=True)
    plt.xlabel("HT (GeV)")
    plt.ylabel("density")
    plt.savefig("ht_hist.png")
    plt.close()

    plt.figure()
    plt.hist(njet_list, bins=40, density=True)
    plt.xlabel("Number of jets")
    plt.ylabel("density")
    plt.savefig("njet_hist.png")
    plt.close()

    plt.figure()
    plt.hist(leading_bjet_eta_list, bins=40, density=True)
    plt.xlabel("Leading b-jet η")
    plt.ylabel("density")
    plt.savefig("leading_bjet_eta_hist.png")
    plt.close()

if __name__ == "__main__":
    main()
