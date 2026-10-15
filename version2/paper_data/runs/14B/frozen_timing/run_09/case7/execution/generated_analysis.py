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

def opposite_sign(obj1, obj2):
    """Check if two objects have opposite charge."""
    return obj1['charge'] * obj2['charge'] < 0

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

def helper_delta_eta(obj1, obj2):
    """Compute Δη between two objects."""
    return obj1['eta'] - obj2['eta']

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

def n_jets(event, pt_cut=0.0, eta_cut=float('inf')):
    """Count jets passing pT and |η| cuts."""
    jets = get_jets(event)
    return sum(1 for j in jets if j['pt'] > pt_cut and abs(j['eta']) < eta_cut)

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
        "Tau selection": 0,
        "Jet selection": 0,
        "At least 2 taus": 0,
        "At least 2 jets": 0,
        "Opposite-sign taus": 0,
        "m_jj > 400 GeV": 0,
        "delta_eta_jj > 2.5": 0,
        "m_tt between 60-150 GeV": 0,
        "No b-jets in jets": 0,
        "Final selected events": 0
    }

    ditau_masses = []
    dijet_masses = []
    delta_eta_jj = []
    leading_tau_pt = []
    subleading_tau_pt = []
    leading_jet_pt = []
    subleading_jet_pt = []
    delta_r_tt = []
    delta_phi_tt_dijet = []
    centrality_tt_jj = []

    for event in events:
        # Cut 1: Tau selection
        taus = [t for t in get_taus(event) if t['pt'] > 20 and abs(t['eta']) < 2.3]
        if len(taus) < 2:
            continue
        cutflow["Tau selection"] += 1

        # Cut 2: Jet selection
        jets = [j for j in get_jets(event) if j['pt'] > 30 and abs(j['eta']) < 4.7]
        if len(jets) < 2:
            continue
        cutflow["Jet selection"] += 1

        # Cut 3: At least 2 taus
        if len(taus) < 2:
            continue
        cutflow["At least 2 taus"] += 1

        # Cut 4: At least 2 jets
        if len(jets) < 2:
            continue
        cutflow["At least 2 jets"] += 1

        # Cut 5: Opposite-sign taus
        leading_tau = helper_get_leading(taus)
        subleading_tau = helper_get_subleading(taus)
        if not opposite_sign(leading_tau, subleading_tau):
            continue
        cutflow["Opposite-sign taus"] += 1

        # Cut 6: m_jj > 400 GeV
        leading_jet = helper_get_leading(jets)
        subleading_jet = helper_get_subleading(jets)
        dijet_obj = sum_objects(leading_jet, subleading_jet)
        m_jj = dijet_obj['mass'] if dijet_obj else 0.0
        if m_jj < 400:
            continue
        cutflow["m_jj > 400 GeV"] += 1

        # Cut 7: delta_eta_jj > 2.5
        delta_eta = helper_delta_eta(leading_jet, subleading_jet)
        if abs(delta_eta) < 2.5:
            continue
        cutflow["delta_eta_jj > 2.5"] += 1

        # Cut 8: m_tt between 60-150 GeV
        ditau_obj = sum_objects(leading_tau, subleading_tau)
        m_tt = ditau_obj['mass'] if ditau_obj else 0.0
        if not (60 < m_tt < 150):
            continue
        cutflow["m_tt between 60-150 GeV"] += 1

        # Cut 9: No b-jets in jets
        if n_bjets(event, pt_cut=30, eta_cut=4.7) > 0:
            continue
        cutflow["No b-jets in jets"] += 1

        # Final selection
        cutflow["Final selected events"] += 1

        # Fill histograms
        ditau_masses.append(m_tt)
        dijet_masses.append(m_jj)
        delta_eta_jj.append(abs(delta_eta))
        leading_tau_pt.append(leading_tau['pt'])
        subleading_tau_pt.append(subleading_tau['pt'])
        leading_jet_pt.append(leading_jet['pt'])
        subleading_jet_pt.append(subleading_jet['pt'])
        delta_r_tt.append(helper_delta_r(leading_tau, subleading_tau))
        delta_phi_tt_dijet.append(helper_delta_phi(ditau_obj['phi'], dijet_obj['phi']))
        centrality_tt_jj.append(centrality_between_jets(ditau_obj, leading_jet, subleading_jet))

    # Print cutflow
    for key, value in cutflow.items():
        print(f"{key}: {value}")

    # Plot histograms
    plt.figure()
    plt.hist(ditau_masses, bins=40, range=(50, 160), density=True)
    plt.xlabel("m_tt (GeV)")
    plt.ylabel("density")
    plt.savefig("m_tt.png")
    plt.close()

    plt.figure()
    plt.hist(dijet_masses, bins=40, range=(400, 2000), density=True)
    plt.xlabel("m_jj (GeV)")
    plt.ylabel("density")
    plt.savefig("m_jj.png")
    plt.close()

    plt.figure()
    plt.hist(delta_eta_jj, bins=40, density=True)
    plt.xlabel("delta_eta_jj")
    plt.ylabel("density")
    plt.savefig("delta_eta_jj.png")
    plt.close()

    plt.figure()
    plt.hist(leading_tau_pt, bins=40, density=True)
    plt.xlabel("leading_tau_pt (GeV)")
    plt.ylabel("density")
    plt.savefig("leading_tau_pt.png")
    plt.close()

    plt.figure()
    plt.hist(subleading_tau_pt, bins=40, density=True)
    plt.xlabel("subleading_tau_pt (GeV)")
    plt.ylabel("density")
    plt.savefig("subleading_tau_pt.png")
    plt.close()

    plt.figure()
    plt.hist(leading_jet_pt, bins=40, density=True)
    plt.xlabel("leading_jet_pt (GeV)")
    plt.ylabel("density")
    plt.savefig("leading_jet_pt.png")
    plt.close()

    plt.figure()
    plt.hist(subleading_jet_pt, bins=40, density=True)
    plt.xlabel("subleading_jet_pt (GeV)")
    plt.ylabel("density")
    plt.savefig("subleading_jet_pt.png")
    plt.close()

    plt.figure()
    plt.hist(delta_r_tt, bins=40, density=True)
    plt.xlabel("delta_r_tt")
    plt.ylabel("density")
    plt.savefig("delta_r_tt.png")
    plt.close()

    plt.figure()
    plt.hist(delta_phi_tt_dijet, bins=40, density=True)
    plt.xlabel("delta_phi_tt_dijet")
    plt.ylabel("density")
    plt.savefig("delta_phi_tt_dijet.png")
    plt.close()

    plt.figure()
    plt.hist(centrality_tt_jj, bins=40, density=True)
    plt.xlabel("centrality_tt_jj")
    plt.ylabel("density")
    plt.savefig("centrality_tt_jj.png")
    plt.close()

if __name__ == "__main__":
    main()
