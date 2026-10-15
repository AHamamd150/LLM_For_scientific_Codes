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


def get_jets(event):
    """Return all jets."""
    return [o for o in event['objects'] if o['type'] == 4]


def get_bjets(event):
    """Return all b-tagged jets."""
    return [o for o in event['objects'] if o['type'] == 4 and int(o['btag']) == 1]


def get_light_jets(event):
    """Return all non-b-tagged jets."""
    return [o for o in event['objects'] if o['type'] == 4 and int(o['btag']) == 0]


def get_leptons(event):
    """Return all electrons and muons."""
    return [o for o in event['objects'] if o['type'] in (1, 2)]


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


def abs_eta(obj):
    """Return |η| of a particle."""
    return abs(obj['eta'])


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


def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py <lhco_file1> [lhco_file2 ...]")
        sys.exit(1)

    all_events = []
    for filename in sys.argv[1:]:
        all_events.extend(read_lhco(filename))

    cutflow = {
        "initial": len(all_events),
        "lepton": 0,
        "jets": 0,
        "bjets": 0,
        "met": 0,
        "mt": 0,
        "w_hadronic": 0,
        "top_hadronic": 0
    }

    mt_values = []
    met_values = []
    leading_bjet_pt = []
    subleading_bjet_pt = []
    w_hadronic_mass = []
    top_hadronic_mass = []
    delta_r_lepton_bjet = []
    ht_values = []
    njets_values = []
    leading_bjet_eta = []

    for event in all_events:
        # Step 1: Select electrons and muons
        electrons = [e for e in get_electrons(event) if e['pt'] > 25 and abs(e['eta']) < 2.5]
        muons = [m for m in get_muons(event) if m['pt'] > 25 and abs(m['eta']) < 2.4]
        leptons = electrons + muons

        if len(leptons) != 1:
            continue
        cutflow["lepton"] += 1

        lepton = leptons[0]

        # Step 2: Select jets
        jets = [j for j in get_jets(event) if j['pt'] > 30 and abs(j['eta']) < 2.5]
        if len(jets) < 4:
            continue
        cutflow["jets"] += 1

        # Step 3: Select b-jets
        bjets = [b for b in get_bjets(event) if b['pt'] > 30 and abs(b['eta']) < 2.5]
        if len(bjets) < 2:
            continue
        cutflow["bjets"] += 1

        # Step 4: Select MET
        met = helper_get_met(event)
        if met is None or met['pt'] < 20:
            continue
        cutflow["met"] += 1

        # Step 5: Select transverse mass of lepton + MET
        mt = helper_transverse_mass(lepton, met)
        if not (30 < mt < 150):
            continue
        cutflow["mt"] += 1
        mt_values.append(mt)
        met_values.append(met['pt'])

        # Step 6: Build hadronic W from two leading non-b-tagged jets
        light_jets = [j for j in jets if j not in bjets]
        if len(light_jets) < 2:
            continue
        light_jets_sorted = sort_by_pt(light_jets)
        w_hadronic = sum_objects(light_jets_sorted[0], light_jets_sorted[1])
        if w_hadronic is None or not (40 < w_hadronic['mass'] < 120):
            continue
        cutflow["w_hadronic"] += 1
        w_hadronic_mass.append(w_hadronic['mass'])

        # Step 7: Build hadronic top from leading b-jet and hadronic W
        bjets_sorted = sort_by_pt(bjets)
        if len(bjets_sorted) < 1:
            continue
        top_hadronic = sum_objects(bjets_sorted[0], w_hadronic)
        if top_hadronic is None or not (100 < top_hadronic['mass'] < 250):
            continue
        cutflow["top_hadronic"] += 1

        # Fill histograms
        leading_bjet = bjets_sorted[0]
        subleading_bjet = bjets_sorted[1] if len(bjets_sorted) > 1 else None

        leading_bjet_pt.append(leading_bjet['pt'])
        if subleading_bjet:
            subleading_bjet_pt.append(subleading_bjet['pt'])

        delta_r_lepton_bjet.append(helper_delta_r(lepton, leading_bjet))

        ht_values.append(scalar_pt_sum(jets))
        njets_values.append(len(jets))
        leading_bjet_eta.append(leading_bjet['eta'])

    # Plotting
    plt.figure()
    plt.hist(mt_values, bins=40, density=True)
    plt.xlabel("Transverse mass (GeV)")
    plt.ylabel("Density")
    plt.savefig("mt.png")
    plt.close()

    plt.figure()
    plt.hist(met_values, bins=40, density=True)
    plt.xlabel("MET (GeV)")
    plt.ylabel("Density")
    plt.savefig("met.png")
    plt.close()

    plt.figure()
    plt.hist(leading_bjet_pt, bins=40, density=True)
    plt.xlabel("Leading b-jet pT (GeV)")
    plt.ylabel("Density")
    plt.savefig("bjet1_pt.png")
    plt.close()

    plt.figure()
    plt.hist(subleading_bjet_pt, bins=40, density=True)
    plt.xlabel("Subleading b-jet pT (GeV)")
    plt.ylabel("Density")
    plt.savefig("bjet2_pt.png")
    plt.close()

    plt.figure()
    plt.hist(w_hadronic_mass, bins=40, density=True)
    plt.xlabel("Hadronic W mass (GeV)")
    plt.ylabel("Density")
    plt.savefig("w_hadronic_mass.png")
    plt.close()

    plt.figure()
    plt.hist(top_hadronic_mass, bins=40, density=True)
    plt.xlabel("Hadronic top mass (GeV)")
    plt.ylabel("Density")
    plt.savefig("top_hadronic_mass.png")
    plt.close()

    plt.figure()
    plt.hist(delta_r_lepton_bjet, bins=40, density=True)
    plt.xlabel("ΔR(lepton, b-jet)")
    plt.ylabel("Density")
    plt.savefig("delta_r_lepton_bjet.png")
    plt.close()

    plt.figure()
    plt.hist(ht_values, bins=40, density=True)
    plt.xlabel("HT (GeV)")
    plt.ylabel("Density")
    plt.savefig("ht.png")
    plt.close()

    plt.figure()
    plt.hist(njets_values, bins=40, density=True)
    plt.xlabel("Number of jets")
    plt.ylabel("Density")
    plt.savefig("njets.png")
    plt.close()

    plt.figure()
    plt.hist(leading_bjet_eta, bins=40, density=True)
    plt.xlabel("Leading b-jet η")
    plt.ylabel("Density")
    plt.savefig("bjet1_eta.png")
    plt.close()

    # Cutflow summary
    print("Cutflow:")
    print(f"Initial events: {cutflow['initial']}")
    print(f"Events with 1 lepton: {cutflow['lepton']}")
    print(f"Events with ≥4 jets: {cutflow['jets']}")
    print(f"Events with ≥2 b-jets: {cutflow['bjets']}")
    print(f"Events with MET > 20 GeV: {cutflow['met']}")
    print(f"Events with 30 < MT < 150 GeV: {cutflow['mt']}")
    print(f"Events with 40 < W_hadronic < 120 GeV: {cutflow['w_hadronic']}")
    print(f"Events with 100 < top_hadronic < 250 GeV: {cutflow['top_hadronic']}")


if __name__ == "__main__":
    main()
