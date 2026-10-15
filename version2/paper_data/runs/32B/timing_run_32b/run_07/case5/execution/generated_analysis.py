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


def abs_eta(obj):
    """Return |η| of a particle."""
    return abs(obj['eta'])


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


def centrality_between_jets(ditau_obj, jet1, jet2):
    """Compute centrality between jets and ditau."""
    jet1_phi = jet1['phi']
    jet2_phi = jet2['phi']
    ditau_phi = ditau_obj['phi']
    dphi1 = helper_delta_phi(jet1_phi, ditau_phi)
    dphi2 = helper_delta_phi(jet2_phi, ditau_phi)
    return min(abs(dphi1), abs(dphi2)) / math.pi


def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py <lhco_file1> [lhco_file2 ...]")
        sys.exit(1)

    all_events = []
    for filename in sys.argv[1:]:
        all_events.extend(read_lhco(filename))

    cutflow = {
        "initial": len(all_events),
        "2_taus": 0,
        "2_jets": 0,
        "opposite_sign": 0,
        "m_jj": 0,
        "delta_eta_jj": 0,
        "m_tautau": 0,
        "no_bjets": 0
    }

    # Histogram data
    m_tautau = []
    m_jj = []
    delta_eta_jj = []
    pt_tau1 = []
    pt_tau2 = []
    pt_jet1 = []
    pt_jet2 = []
    delta_r_tautau = []
    delta_phi_tautau_dijet = []
    centrality = []

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

        # 6. Invariant mass of leading and subleading jets (m_jj) > 400 GeV
        dijet_obj = sum_objects(jet1, jet2)
        if dijet_obj is None or dijet_obj['mass'] < 400:
            continue
        cutflow["m_jj"] += 1

        # 7. |delta eta| between the two leading jets > 2.5
        if abs_delta_eta(jet1, jet2) < 2.5:
            continue
        cutflow["delta_eta_jj"] += 1

        # 8. Invariant mass of ditau between 60 and 150 GeV
        ditau_obj = sum_objects(tau1, tau2)
        if ditau_obj is None or not (60 < ditau_obj['mass'] < 150):
            continue
        cutflow["m_tautau"] += 1

        # 9. Veto events with b-tagged jets
        if get_bjets(event):
            continue
        cutflow["no_bjets"] += 1

        # Fill histograms
        m_tautau.append(ditau_obj['mass'])
        m_jj.append(dijet_obj['mass'])
        delta_eta_jj.append(abs_delta_eta(jet1, jet2))
        pt_tau1.append(tau1['pt'])
        pt_tau2.append(tau2['pt'])
        pt_jet1.append(jet1['pt'])
        pt_jet2.append(jet2['pt'])
        delta_r_tautau.append(helper_delta_r(tau1, tau2))
        delta_phi_tautau_dijet.append(helper_delta_phi(ditau_obj['phi'], dijet_obj['phi']))
        centrality.append(centrality_between_jets(ditau_obj, jet1, jet2))

    # Plotting
    plt.figure()
    plt.hist(m_tautau, bins=40, range=(50, 160), density=True)
    plt.xlabel("m_tautau (GeV)")
    plt.ylabel("density")
    plt.savefig("m_tautau.png")
    plt.close()

    plt.figure()
    plt.hist(m_jj, bins=40, range=(200, 2000), density=True)
    plt.xlabel("m_jj (GeV)")
    plt.ylabel("density")
    plt.savefig("m_jj.png")
    plt.close()

    plt.figure()
    plt.hist(delta_eta_jj, bins=40, range=(0, 10), density=True)
    plt.xlabel("delta_eta_jj")
    plt.ylabel("density")
    plt.savefig("delta_eta_jj.png")
    plt.close()

    plt.figure()
    plt.hist(pt_tau1, bins=40, range=(0, 200), density=True)
    plt.xlabel("pt_tau1 (GeV)")
    plt.ylabel("density")
    plt.savefig("pt_tau1.png")
    plt.close()

    plt.figure()
    plt.hist(pt_tau2, bins=40, range=(0, 200), density=True)
    plt.xlabel("pt_tau2 (GeV)")
    plt.ylabel("density")
    plt.savefig("pt_tau2.png")
    plt.close()

    plt.figure()
    plt.hist(pt_jet1, bins=40, range=(0, 1000), density=True)
    plt.xlabel("pt_jet1 (GeV)")
    plt.ylabel("density")
    plt.savefig("pt_jet1.png")
    plt.close()

    plt.figure()
    plt.hist(pt_jet2, bins=40, range=(0, 1000), density=True)
    plt.xlabel("pt_jet2 (GeV)")
    plt.ylabel("density")
    plt.savefig("pt_jet2.png")
    plt.close()

    plt.figure()
    plt.hist(delta_r_tautau, bins=40, range=(0, 5), density=True)
    plt.xlabel("delta_r_tautau")
    plt.ylabel("density")
    plt.savefig("delta_r_tautau.png")
    plt.close()

    plt.figure()
    plt.hist(delta_phi_tautau_dijet, bins=40, range=(-math.pi, math.pi), density=True)
    plt.xlabel("delta_phi_tautau_dijet")
    plt.ylabel("density")
    plt.savefig("delta_phi_tautau_dijet.png")
    plt.close()

    plt.figure()
    plt.hist(centrality, bins=40, range=(0, 1), density=True)
    plt.xlabel("centrality")
    plt.ylabel("density")
    plt.savefig("centrality.png")
    plt.close()

    # Print cutflow
    print("Cutflow:")
    for key, value in cutflow.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
