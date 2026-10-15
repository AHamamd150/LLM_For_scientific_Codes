#!/usr/bin/env python3
import sys
import math
import matplotlib.pyplot as plt
import numpy as np


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


def abs_delta_eta(obj1, obj2):
    """Compute |Δη| between two objects."""
    return abs(obj1['eta'] - obj2['eta'])


def get_taus(event):
    """Return all taus."""
    return [o for o in event['objects'] if o['type'] == 3]


def get_jets(event):
    """Return all jets."""
    return [o for o in event['objects'] if o['type'] == 4]


def get_bjets(event):
    """Return all b-tagged jets."""
    return [o for o in event['objects'] if o['type'] == 4 and int(o['btag']) == 1]


def opposite_sign(obj1, obj2):
    """Check if two objects have opposite charge."""
    return obj1['charge'] * obj2['charge'] < 0


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


def n_bjets(event, pt_cut=0.0, eta_cut=float('inf')):
    """Count b-jets passing pT and |η| cuts."""
    bjets = get_bjets(event)
    return sum(1 for b in bjets if b['pt'] > pt_cut and abs(b['eta']) < eta_cut)


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


def abs_eta(obj):
    """Return |η| of a particle."""
    return abs(obj['eta'])


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


def main():
    import sys
    import os

    if len(sys.argv) < 2:
        print("Usage: python3 script.py <lhco_file1> [lhco_file2 ...]")
        sys.exit(1)

    all_events = []
    for filename in sys.argv[1:]:
        if not os.path.exists(filename):
            print(f"File not found: {filename}")
            continue
        all_events.extend(read_lhco(filename))

    cutflow = {
        "initial": len(all_events),
        "2_taus": 0,
        "2_jets": 0,
        "opposite_sign": 0,
        "m_jj > 400": 0,
        "delta_eta_jj > 2.5": 0,
        "m_tautau 60-150": 0,
        "no_bjets": 0
    }

    # Histogram data
    m_tautau_hist = []
    m_jj_hist = []
    delta_eta_jj_hist = []
    pt_tau1_hist = []
    pt_tau2_hist = []
    pt_jet1_hist = []
    pt_jet2_hist = []
    delta_r_tautau_hist = []
    delta_phi_tautau_dijet_hist = []
    centrality_hist = []

    for event in all_events:
        # Initial cutflow
        cutflow["initial"] += 1

        # 1. Select taus with pT > 20 GeV and |eta| < 2.3
        taus = [t for t in get_taus(event) if t['pt'] > 20 and abs(t['eta']) < 2.3]
        if len(taus) < 2:
            continue
        cutflow["2_taus"] += 1

        # 2. Define leading and subleading tau
        tau1 = helper_get_leading(taus)
        tau2 = helper_get_subleading(taus)
        if tau1 is None or tau2 is None:
            continue

        # 3. Select jets with pT > 30 GeV and |eta| < 4.7
        jets = [j for j in get_jets(event) if j['pt'] > 30 and abs(j['eta']) < 4.7]
        if len(jets) < 2:
            continue
        cutflow["2_jets"] += 1

        # 4. Define leading and subleading jet
        jet1 = helper_get_leading(jets)
        jet2 = helper_get_subleading(jets)
        if jet1 is None or jet2 is None:
            continue

        # 5. Require opposite-sign tau pair
        if not opposite_sign(tau1, tau2):
            continue
        cutflow["opposite_sign"] += 1

        # 6. m_jj > 400 GeV
        dijet_obj = sum_objects(jet1, jet2)
        if dijet_obj is None or dijet_obj['mass'] < 400:
            continue
        cutflow["m_jj > 400"] += 1

        # 7. |delta_eta_jj| > 2.5
        if abs_delta_eta(jet1, jet2) < 2.5:
            continue
        cutflow["delta_eta_jj > 2.5"] += 1

        # 8. m_tautau between 60 and 150 GeV
        ditau_obj = sum_objects(tau1, tau2)
        if ditau_obj is None or not (60 < ditau_obj['mass'] < 150):
            continue
        cutflow["m_tautau 60-150"] += 1

        # 9. Veto events with b-tagged jets
        if n_bjets(event, pt_cut=30, eta_cut=4.7) > 0:
            continue
        cutflow["no_bjets"] += 1

        # Fill histograms
        m_tautau_hist.append(ditau_obj['mass'])
        m_jj_hist.append(dijet_obj['mass'])
        delta_eta_jj_hist.append(abs_delta_eta(jet1, jet2))
        pt_tau1_hist.append(tau1['pt'])
        pt_tau2_hist.append(tau2['pt'])
        pt_jet1_hist.append(jet1['pt'])
        pt_jet2_hist.append(jet2['pt'])
        delta_r_tautau_hist.append(helper_delta_r(tau1, tau2))
        delta_phi_tautau_dijet_hist.append(helper_delta_phi(ditau_obj['phi'], dijet_obj['phi']))
        centrality_hist.append(centrality_between_jets(ditau_obj, jet1, jet2))

    # Plot histograms
    def save_hist(values, bins, title, xlabel, filename):
        plt.figure()
        plt.hist(values, bins=bins, density=True)
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel("density")
        plt.savefig(filename)
        plt.close()

    save_hist(m_tautau_hist, 40, "Ditau invariant mass", "m_ττ (GeV)", "m_tautau.png")
    save_hist(m_jj_hist, 40, "Dijet invariant mass", "m_jj (GeV)", "m_jj.png")
    save_hist(delta_eta_jj_hist, 40, "Delta eta between jets", "Δη_jj", "delta_eta_jj.png")
    save_hist(pt_tau1_hist, 40, "Leading tau pT", "pT (GeV)", "pt_tau1.png")
    save_hist(pt_tau2_hist, 40, "Subleading tau pT", "pT (GeV)", "pt_tau2.png")
    save_hist(pt_jet1_hist, 40, "Leading jet pT", "pT (GeV)", "pt_jet1.png")
    save_hist(pt_jet2_hist, 40, "Subleading jet pT", "pT (GeV)", "pt_jet2.png")
    save_hist(delta_r_tautau_hist, 40, "Delta R between taus", "ΔR_ττ", "delta_r_tautau.png")
    save_hist(delta_phi_tautau_dijet_hist, 40, "Delta phi between ditau and dijet", "Δφ_ττ-jj", "delta_phi_tautau_dijet.png")
    save_hist(centrality_hist, 40, "Centrality of ditau relative to jets", "Centrality", "centrality.png")

    # Print cutflow
    print("Cutflow:")
    for key in cutflow:
        print(f"{key}: {cutflow[key]}")


if __name__ == "__main__":
    main()
