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

def get_taus(event):
    """Return all taus."""
    return [o for o in event['objects'] if o['type'] == 3]

def get_jets(event):
    """Return all jets."""
    return [o for o in event['objects'] if o['type'] == 4]

def get_bjets(event):
    """Return all b-tagged jets."""
    return [o for o in event['objects'] if o['type'] == 4 and int(o['btag']) == 1]

def n_bjets(event, pt_cut=0.0, eta_cut=float('inf')):
    """Count b-jets passing pT and |η| cuts."""
    bjets = get_bjets(event)
    return sum(1 for b in bjets if b['pt'] > pt_cut and abs(b['eta']) < eta_cut)

def opposite_sign(obj1, obj2):
    """Check if two objects have opposite charge."""
    return obj1['charge'] * obj2['charge'] < 0

def centrality_between_jets(obj, jet1, jet2):
    """
    Compute eta centrality of obj relative to two jets.

    centrality = |eta_obj - eta_center_jj| / |delta_eta_jj|
    Smaller values mean obj is closer to the midpoint between the two jets.
    """
    eta_gap = abs(jet1["eta"] - jet2["eta"])
    if eta_gap <= 0.0:
        return 0.0

    eta_center = 0.5 * (jet1["eta"] + jet2["eta"])
    return abs(obj["eta"] - eta_center) / eta_gap

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
        "Taus selected (pT > 20, |eta| < 2.3)": 0,
        "At least 2 taus": 0,
        "Opposite-sign tau pair": 0,
        "Jets selected (pT > 30, |eta| < 4.7)": 0,
        "At least 2 jets": 0,
        "m_jj > 400 GeV": 0,
        "delta_eta_jj > 2.5": 0,
        "No b-jets": 0,
        "m_tt between 60 and 150 GeV": 0
    }

    ditau_mass_list = []
    dijet_mass_list = []
    delta_eta_jj_list = []
    leading_tau_pt_list = []
    subleading_tau_pt_list = []
    leading_jet_pt_list = []
    subleading_jet_pt_list = []
    delta_r_tt_list = []
    delta_phi_tt_jj_list = []
    centrality_tt_jj_list = []

    for event in events:
        # Step 1: Select taus with pT > 20 GeV and |eta| < 2.3
        taus = [t for t in get_taus(event) if t['pt'] > 20 and abs(t['eta']) < 2.3]
        if len(taus) < 2:
            continue
        cutflow["Taus selected (pT > 20, |eta| < 2.3)"] += 1

        # Step 2: Require at least 2 taus
        if len(taus) < 2:
            continue
        cutflow["At least 2 taus"] += 1

        # Step 3: Opposite-sign tau pair
        leading_tau = helper_get_leading(taus)
        subleading_tau = helper_get_subleading(taus)
        if not leading_tau or not subleading_tau or not opposite_sign(leading_tau, subleading_tau):
            continue
        cutflow["Opposite-sign tau pair"] += 1

        # Step 4: Select jets with pT > 30 GeV and |eta| < 4.7
        jets = [j for j in get_jets(event) if j['pt'] > 30 and abs(j['eta']) < 4.7]
        if len(jets) < 2:
            continue
        cutflow["Jets selected (pT > 30, |eta| < 4.7)"] += 1

        # Step 5: Require at least 2 jets
        if len(jets) < 2:
            continue
        cutflow["At least 2 jets"] += 1

        # Step 6: m_jj > 400 GeV
        leading_jet = helper_get_leading(jets)
        subleading_jet = helper_get_subleading(jets)
        dijet_mass = helper_invariant_mass(leading_jet, subleading_jet)
        if dijet_mass < 400:
            continue
        cutflow["m_jj > 400 GeV"] += 1

        # Step 7: delta_eta_jj > 2.5
        delta_eta_jj = abs(leading_jet['eta'] - subleading_jet['eta'])
        if delta_eta_jj < 2.5:
            continue
        cutflow["delta_eta_jj > 2.5"] += 1

        # Step 8: No b-jets
        if n_bjets(event, pt_cut=30, eta_cut=4.7) > 0:
            continue
        cutflow["No b-jets"] += 1

        # Step 9: m_tt between 60 and 150 GeV
        ditau_mass = helper_invariant_mass(leading_tau, subleading_tau)
        if not (60 < ditau_mass < 150):
            continue
        cutflow["m_tt between 60 and 150 GeV"] += 1

        # Collect data for plots
        ditau_mass_list.append(ditau_mass)
        dijet_mass_list.append(dijet_mass)
        delta_eta_jj_list.append(delta_eta_jj)
        leading_tau_pt_list.append(leading_tau['pt'])
        subleading_tau_pt_list.append(subleading_tau['pt'])
        leading_jet_pt_list.append(leading_jet['pt'])
        subleading_jet_pt_list.append(subleading_jet['pt'])
        delta_r_tt = helper_delta_r(leading_tau, subleading_tau)
        delta_r_tt_list.append(delta_r_tt)
        delta_phi_tt_jj = helper_delta_phi(leading_tau['phi'] + subleading_tau['phi'], leading_jet['phi'] + subleading_jet['phi'])
        delta_phi_tt_jj_list.append(delta_phi_tt_jj)
        centrality_tt_jj = centrality_between_jets(sum_objects(leading_tau, subleading_tau), leading_jet, subleading_jet)
        centrality_tt_jj_list.append(centrality_tt_jj)

    # Print cutflow
    for key, value in cutflow.items():
        print(f"{key}: {value}")

    # Plotting
    def plot_hist(data, title, xlabel, filename):
        plt.figure()
        plt.hist(data, bins=40, density=True)
        plt.xlabel(xlabel)
        plt.ylabel("density")
        plt.title(title)
        plt.savefig(filename)
        plt.close()

    plot_hist(ditau_mass_list, "Ditau invariant mass", "m_tt (GeV)", "ditau_mass.png")
    plot_hist(dijet_mass_list, "Dijet invariant mass", "m_jj (GeV)", "dijet_mass.png")
    plot_hist(delta_eta_jj_list, "Delta eta between jets", "$\\Delta\\eta_{jj}$", "delta_eta_jj.png")
    plot_hist(leading_tau_pt_list, "Leading tau pT", "pT (GeV)", "leading_tau_pt.png")
    plot_hist(subleading_tau_pt_list, "Subleading tau pT", "pT (GeV)", "subleading_tau_pt.png")
    plot_hist(leading_jet_pt_list, "Leading jet pT", "pT (GeV)", "leading_jet_pt.png")
    plot_hist(subleading_jet_pt_list, "Subleading jet pT", "pT (GeV)", "subleading_jet_pt.png")
    plot_hist(delta_r_tt_list, "Delta R between taus", "$\\Delta R_{\\tau\\tau}$", "delta_r_tt.png")
    plot_hist(delta_phi_tt_jj_list, "Delta phi between ditau and dijet", "$\\Delta\\phi_{\\text{tt},\\text{jj}}$", "delta_phi_tt_jj.png")
    plot_hist(centrality_tt_jj_list, "Centrality of ditau relative to jets", "Centrality", "centrality_tt_jj.png")

if __name__ == "__main__":
    main()
