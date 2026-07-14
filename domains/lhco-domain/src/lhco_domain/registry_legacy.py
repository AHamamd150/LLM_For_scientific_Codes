from helper_selector import HelperSpec


HELPER_REGISTRY: list[HelperSpec] = [
    # =========================================================================
    # parser / core momentum
    # =========================================================================
    HelperSpec(
        name="four_momentum",
        section="parser_core",
        summary="Convert an object dict into (E, px, py, pz).",
        keywords=("four momentum", "px", "py", "pz", "energy", "invariant mass"),
        aliases=("4-momentum", "lorentz components"),
        dependencies=("get_particle_mass",),
    ),
    HelperSpec(
        name="sum_objects",
        section="parser_core",
        summary="Combine particles or particle lists into one composite object by summing four-momenta.",
        keywords=("sum objects", "composite system", "combine particles", "system"),
        aliases=("combine objects", "build composite system", "candidate from constituents"),
        dependencies=("four_momentum", "obj_from_four_momentum"),
    ),

    HelperSpec(
        name="helper_invariant_mass",
        section="parser_core",
        summary="Compute invariant mass from one or more objects or lists of objects.",
        keywords=("invariant mass", "mass", "dijet mass", "dilepton mass", "visible mass"),
        aliases=("mjj", "mll", "visible invariant mass", "candidate mass"),
        dependencies=("sum_objects",),
    ),

    HelperSpec(
        name="helper_delta_r",
        section="parser_core",
        summary="Compute delta R between two objects.",
        keywords=("delta r", "dr", "angular separation"),
        aliases=("ΔR", "cone distance", "angular distance"),
        dependencies=("helper_delta_phi",),
    ),
    HelperSpec(
        name="helper_transverse_mass",
        section="parser_core",
        summary="Compute transverse mass",
        keywords=("transverse mass", "mt", "w leptonic"),
        aliases=("MT", "mT", "leptonic W transverse mass"),
        dependencies=("helper_delta_phi",),
    ),
    HelperSpec(
        name="get_particle_mass",
        section="parser_core",
        summary="Return particle mass using LHCO type convention or embedded mass fields.",
        keywords=("mass", "particle mass", "jet mass", "lhco type"),
        aliases=("mass lookup", "object mass"),
    ),

    HelperSpec(
        name="obj_from_four_momentum",
        section="parser_core",
        summary="Build a composite object dict from (E, px, py, pz).",
        keywords=("composite object", "four momentum", "reconstruct object", "system"),
        aliases=("build system object", "composite candidate"),
    ),
    
    HelperSpec(
        name="helper_delta_phi",
        section="parser_core",
        summary="Compute azimuthal angle difference normalized to [-pi, pi].",
        keywords=("delta phi", "dphi", "azimuthal angle"),
        aliases=("Δφ", "delta-phi", "phi separation"),
    ),
    HelperSpec(
        name="read_lhco",
        section="parser_core",
        summary="Parse an LHCO file into a list of events with reconstructed objects.",
        keywords=("lhco", "parser", "read file", "events"),
        aliases=("input parser", "event reader"),
    ),

    # =========================================================================
    # common selections / object access
    # =========================================================================

    HelperSpec(
        name="get_leptons",
        section="selection",
        summary="Return all electrons and muons in an event without applying any cuts.",
        keywords=(
            "raw lepton collection",
            "combined electron and muon collection",
            "uncut electrons and muons",
            "electron+muon collection",
            ),
        aliases=("l", "electron+muon", "charged light leptons"),
    ),
    HelperSpec(
        name="get_electrons",
        section="selection",
        summary="Return all electrons in an event. Use when electron-specific cuts differ from muon cuts.",
        keywords=("electrons", "electron", "electron cuts"),
        aliases=("e", "electron channel", "electron-specific selection"),
    ),
    HelperSpec(
        name="get_muons",
        section="selection",
        summary="Return all muons in an event. Use when muon-specific cuts differ from electron cuts.",
        keywords=("muons", "muon", "muon cuts" ),
        aliases=("mu", "muon channel", "muon-specific selection"),
    ),
    HelperSpec(
        name="get_taus",
        section="selection",
        summary="Return all taus in an event.",
        keywords=("taus", "tau"),
        aliases=("τ", "tau leptons", "hadronic tau"),
    ),
    HelperSpec(
        name="get_jets",
        section="selection",
        summary="Return all jets in an event.",
        keywords=("jets", "jet", "leading jet", "subleading jet"),
        aliases=("j", "hadronic objects", "jet collection"),
    ),
    HelperSpec(
        name="get_bjets",
        section="selection",
        summary="Return all b-tagged jets in an event.",
        keywords=("b-tagged jets", "b jets", "b-jet veto", "bjet"),
        aliases=("b jets", "b-tagged collection", "heavy-flavor jets"),
    ),
    HelperSpec(
        name="get_light_jets",
        section="selection",
        summary="Return all non-b-tagged jets in an event.",
        keywords=("light jets", "non-b-tagged jets"),
        aliases=("light-flavor jets", "non-b jets"),
    ),
    HelperSpec(
        name="get_photons",
        section="selection",
        summary="Return all photons in an event.",
        keywords=("photons", "photon"),
        aliases=("gamma", "γ", "diphoton inputs"),
    ),
    HelperSpec(
        name="helper_get_met",
        section="selection",
        summary="Return the LHCO MET object; Necessary in using MET",
        keywords=("MET", "MET direction", "MET pt", "missing transverse energy"),
        aliases=("MET", "missing ET"),
    ),
    HelperSpec(
        name="helper_get_leading",
        section="selection",
        summary="Return the highest-pT object from a particle list.",
        keywords=("leading", "highest pt", "leading object"),
        aliases=("leading object", "highest-pT object"),
    ),
    HelperSpec(
        name="helper_get_subleading",
        section="selection",
        summary="Return the second-highest-pT object from a particle list.",
        keywords=("subleading", "second highest pt", "subleading object"),
        aliases=("second-leading object", "second-highest-pT object"),
    ),
    HelperSpec(
        name="sort_by_pt",
        section="selection",
        summary="Return a particle list sorted by descending pT.",
        keywords=("sort by pt", "leading jets", "subleading jet", "ordering"),
        aliases=("pt ordering", "rank by pt", "sorted objects"),
    ),

    # =========================================================================
    # pseudorapidity / rapidity
    # =========================================================================
    HelperSpec(
        name="helper_delta_eta",
        section="eta_rapidity",
        summary="Compute delta eta between two objects.",
        keywords=("delta eta", "deta", "eta difference"),
        aliases=("Δη", "eta separation"),
    ),
    HelperSpec(
        name="abs_delta_eta",
        section="eta_rapidity",
        summary="Compute absolute delta eta between two objects.",
        keywords=("absolute delta eta", "abs delta eta", "|deta|"),
        aliases=("abs Δη", "|Δη|"),
    ),
    HelperSpec(
        name="rapidity",
        section="eta_rapidity",
        summary="Compute true rapidity from the four-momentum of an object.",
        keywords=("rapidity", "true rapidity", "y"),
        aliases=("y", "lorentz rapidity"),
    ),
    HelperSpec(
        name="abs_eta",
        section="eta_rapidity",
        summary="Return absolute pseudorapidity of an object.",
        keywords=("absolute eta", "|eta|"),
        aliases=("abs eta", "|η|"),
    ),

    # =========================================================================
    # transverse / vector sums / HT
    # =========================================================================
    HelperSpec(
        name="transverse_energy",
        section="transverse",
        summary="Compute transverse energy ET = E / cosh(eta).",
        keywords=("transverse energy", "et"),
        aliases=("ET", "E_T"),
    ),
    HelperSpec(
        name="scalar_pt_sum",
        section="transverse",
        summary="Compute scalar sum of pT over a particle list; use only for HT/ST-like scalar activity, not for the pT of a composite object.",
        keywords=(
            "scalar pt sum",
            "sum of transverse momenta",
            "HT",
            "ST",
            "scalar activity",
            "scalar sum pT",
        ),
        aliases=(
            "scalar HT-like sum",
            "ST",
            "H_T-like scalar sum",
        ),
    ),
    HelperSpec(
        name="vector_pt_sum",
        section="transverse",
        summary="Compute magnitude of the vector pT sum over a particle list.",
        keywords=("vector pt sum", "missing momentum", "recoil"),
        aliases=("vector recoil", "transverse recoil magnitude"),
    ),
    HelperSpec(
        name="vector_pt_components",
        section="transverse",
        summary="Return total px and py from a particle list.",
        keywords=("px total", "py total", "vector pt components"),
        aliases=("transverse momentum components", "sum px py"),
    ),
    HelperSpec(
        name="compute_ht",
        section="transverse",
        summary="Compute HT as scalar sum of all jet pT in an event.",
        keywords=("ht", "scalar jet pt sum"),
        aliases=("H_T", "jet HT"),
    ),

    # =========================================================================
    # angular distributions
    # =========================================================================
    HelperSpec(
        name="compute_phi",
        section="angular",
        summary="Compute phi from momentum components of an object.",
        keywords=("phi", "azimuthal angle"),
        aliases=("azimuth", "φ"),
    ),
    HelperSpec(
    name="min_delta_r",
    section="angular",
    summary="Compute the minimum delta R among all pairs in the same particle list.",
    keywords=(
        "minimum delta R among all pairs in the same particle list",
        "minimum pairwise delta R in the same particle list",
        "min pairwise delta R in one particle list",
        "minimum delta R within a particle list",
    ),
    aliases=("min ΔR",),
    ),
    HelperSpec(
    name="max_delta_r",
    section="angular",
    summary="Compute the maximum delta R among all pairs in the same particle list.",
    keywords=(
        "maximum delta R among all pairs in the same particle list",
        "maximum pairwise delta R in the same particle list",
        "max pairwise delta R in one particle list",
        "maximum delta R within a particle list",
    ),
    aliases=("max ΔR",),
    ),
    HelperSpec(
        name="helper_delta_phi_ll",
        section="angular",
        summary="Compute delta phi between the two leading leptons in an event.",
        keywords=("delta phi ll", "dilepton delta phi", "leading leptons"),
        aliases=("Δφ(ll)", "dilepton azimuthal separation"),
        dependencies=("get_leptons", "sort_by_pt", "helper_delta_phi")  
    ),
    HelperSpec(
        name="helper_delta_phi_met",
        section="angular",
        summary="Compute delta phi between an object and MET in an event.",
        keywords=("delta phi met", "object met", "dphi met"),
        aliases=("Δφ(object, MET)", "object-MET angular separation"),
        dependencies=("helper_get_met", "helper_delta_phi"),
    ),

    HelperSpec(
        name="helper_delta_phi_l_twojet",
        section="angular",
        summary="Compute delta phi between the leading lepton and the two-jet system built from the two leading jets.",
        keywords=(
           "delta phi between lepton and two-jet system",
           "delta phi between lepton and twojet system",
           "delta phi lepton two-jet system",
           "delta phi lepton twojet",
           "lepton and two-jet system",
           "leading lepton and two-jet system",
           "delta phi between lepton and hadronic w candidate",
           "delta phi between w candidates",
        ),
        aliases=(
            "Δφ(lepton, two-jet system)",
            "delta_phi_lepton_twojet",
            "delta phi lepton twojet",
            "lepton-twojet delta phi",
            "Δφ(lepton, Whad)",
        ),
        dependencies=("get_leptons", "get_jets", "sort_by_pt", "helper_get_leading", "sum_objects", "helper_delta_phi"),
     ),
    HelperSpec(
        name="helper_delta_eta_ll",
        section="angular",
        summary="Compute delta eta between the two leading leptons in an event.",
        keywords=("delta eta ll", "dilepton delta eta"),
        aliases=("Δη(ll)", "dilepton eta separation"),
    ),
    HelperSpec(
        name="helper_delta_r_ll",
        section="angular",
        summary="Compute delta R between the two leading leptons in an event.",
        keywords=("delta r ll", "dilepton delta r"),
        aliases=("ΔR(ll)", "dilepton angular distance"),
        dependencies=("get_leptons", "sort_by_pt", "helper_delta_r")
    ),
    HelperSpec(
        name="cos_theta_star_collins_soper",
        section="angular",
        summary="Compute signed cos(theta*) in the Collins-Soper frame for a two-object system.",
        keywords=(
            "cos theta star in Collins-Soper frame",
            "cos theta star Collins-Soper",
            "cos(theta*) of the diphoton system in Collins-Soper frame",
            "Collins-Soper frame angle",
            "two-object Collins-Soper angle",
            "diphoton Collins-Soper cos theta",
            "H to gamma gamma cos theta star",
        ),
        aliases=(
            "cos(theta*)",
            "cos theta star",
            "cos_theta_star",
            "cos_theta_star_collins_soper",
            "Collins-Soper theta star",
            "diphoton Collins-Soper angle",
        ),
        dependencies=(
            "four_momentum",
            "sum_objects",
        ),
    ),
    HelperSpec(
        name="centrality_between_jets",
        section="angular",
        summary="Compute eta centrality of an object relative to two jets as |eta_obj - eta_center_jj| / |delta_eta_jj|.",
        keywords=(
            "centrality of system relative to two jets",
            "eta centrality between jets",
            "VBF centrality",
            "object centrality in dijet eta gap",
        ),
        aliases=(
            "centrality",
            "eta centrality",
            "VBF centrality",
    ),
        dependencies=(),
    ),
    # =========================================================================
    # mass distributions
    # =========================================================================
    HelperSpec(
        name="dilepton_mass",
        section="mass",
        summary="Compute invariant mass of the two leading leptons.",
        keywords=("dilepton mass", "ll mass"),
        aliases=("mll", "m(ll)"),
        dependencies=("get_leptons", "sort_by_pt", "helper_invariant_mass"),
    ),
    HelperSpec(
        name="dijet_mass",
        section="mass",
        summary="Compute invariant mass of the two leading jets. Useful for a hadronic W candidate reconstructed from jj.",
        keywords=("dijet mass", "jj mass", "w hadronic candidate", "two leading jets"),
        aliases=("mjj", "m(jj)", "hadronic W mass", "W->jj candidate mass"),
        dependencies=("get_jets", "sort_by_pt", "helper_invariant_mass"),
    ),
    HelperSpec(
        name="dielectron_mass",
        section="mass",
        summary="Compute invariant mass of the two leading electrons.",
        keywords=("dielectron mass", "ee mass"),
        aliases=("mee", "m(ee)"),
    ),
    HelperSpec(
        name="dimuon_mass",
        section="mass",
        summary="Compute invariant mass of the two leading muons.",
        keywords=("dimuon mass", "mumu mass"),
        aliases=("mμμ", "m(mu mu)"),
    ),
    HelperSpec(
        name="four_lepton_mass",
        section="mass",
        summary="Compute invariant mass of the four leading leptons.",
        keywords=("four lepton mass", "4l mass"),
        aliases=("m4l", "m(4l)"),
    ),
    HelperSpec(
        name="visible_mass",
        section="mass",
        summary="Compute invariant mass of all visible objects in an event.",
        keywords=("visible mass", "all visible objects"),
        aliases=("total visible mass", "event visible invariant mass"),
    ),
    # =========================================================================
    # transverse mass / ratios
    # =========================================================================
    HelperSpec(
        name="mt_lepton_met",
        section="mt_ratios",
        summary="Compute transverse mass of the leading lepton and MET.",
        keywords=("mt lepton met", "transverse mass lepton met", "w leptonic candidate"),
        aliases=("mT(l,MET)", "leptonic W transverse mass"),
        dependencies=("get_leptons", "helper_get_met", "helper_get_leading", "helper_transverse_mass"),
    ),
    HelperSpec(
        name="pt_ratio",
        section="mt_ratios",
        summary="Compute pT ratio of two objects.",
        keywords=("pt ratio", "momentum ratio"),
        aliases=("transverse momentum ratio", "pT balance"),
    ),
    HelperSpec(
        name="met_over_sqrt_ht",
        section="mt_ratios",
        summary="Compute MET divided by sqrt(HT).",
        keywords=("met over sqrt ht", "met significance proxy"),
        aliases=("MET significance proxy", "MET/sqrt(HT)"),
    ),
    HelperSpec(
        name="met_over_ht",
        section="mt_ratios",
        summary="Compute MET over HT ratio.",
        keywords=("met over ht", "met ht ratio"),
        aliases=("MET/HT", "missing energy fraction"),
    ),

    # =========================================================================
    # multiplicities
    # =========================================================================
    HelperSpec(
    name="n_jets",
    section="multiplicity",
    summary="Count jets passing pT and eta cuts.",
    keywords=("number of jets", "jet multiplicity", "at least 2 jets"),
    aliases=("Njets", "jet count"),
    dependencies=("get_jets",),
),

HelperSpec(
    name="n_bjets",
    section="multiplicity",
    summary="Count b-jets passing pT and eta cuts.",
    keywords=("number of b jets", "bjet multiplicity", "b-tag veto"),
    aliases=("Nbjets", "b-jet count"),
    dependencies=("get_bjets",),
),

HelperSpec(
    name="n_electrons",
    section="multiplicity",
    summary="Count electrons passing pT and eta cuts.",
    keywords=("number of electrons", "electron multiplicity"),
    aliases=("Nelectrons", "electron count"),
    dependencies=("get_electrons",),
),

HelperSpec(
    name="n_muons",
    section="multiplicity",
    summary="Count muons passing pT and eta cuts.",
    keywords=("number of muons", "muon multiplicity"),
    aliases=("Nmuons", "muon count"),
    dependencies=("get_muons",),
),

    HelperSpec(
        name="n_taus",
        section="multiplicity",
        summary="Count taus passing pT and eta cuts.",
        keywords=("number of taus", "tau multiplicity"),
        aliases=("Ntaus", "tau count"),
    ),
    HelperSpec(
        name="n_photons",
        section="multiplicity",
        summary="Count photons passing pT and eta cuts.",
        keywords=("number of photons", "photon multiplicity"),
        aliases=("Nphotons", "photon count"),
    ),
    HelperSpec(
        name="n_leptons",
        section="multiplicity",
        summary="Count electrons and muons passing the same pT and eta cuts.",
        keywords=(
            "common lepton cut",
            "same cut for electrons and muons",
            "combined lepton multiplicity",
            "count merged leptons",
    ),
    aliases=("Nleptons", "lepton count"),
    dependencies=("get_leptons",),
),
    # =========================================================================
    # charge-related
    # =========================================================================
    HelperSpec(
        name="opposite_sign",
        section="charge",
        summary="Check whether two charged objects have opposite sign.",
        keywords=("opposite sign", "os pair"),
        aliases=("OS", "opposite-charge pair"),
    ),
    HelperSpec(
        name="same_sign",
        section="charge",
        summary="Check whether two charged objects have the same sign.",
        keywords=("same sign", "ss pair"),
        aliases=("SS", "same-charge pair"),
    ),
    HelperSpec(
        name="total_charge",
        section="charge",
        summary="Compute total charge of a particle list.",
        keywords=("total charge", "charge sum"),
        aliases=("net charge", "sum of charges"),
    ),
    HelperSpec(
        name="get_os_pairs",
        section="charge",
        summary="Return all opposite-sign pairs from a particle list.",
        keywords=("os pairs", "opposite-sign pairs"),
        aliases=("OS pairs", "opposite-charge combinations"),
    ),
    HelperSpec(
        name="get_ss_pairs",
        section="charge",
        summary="Return all same-sign pairs from a particle list.",
        keywords=("ss pairs", "same-sign pairs"),
        aliases=("SS pairs", "same-charge combinations"),
    ),

    # =========================================================================
    # domain-specific reconstruction
    # =========================================================================
    HelperSpec(
        name="find_z_candidate",
        section="reconstruction",
        summary="Find an opposite-sign lepton pair closest to the Z mass within a mass window.",
        keywords=("z candidate", "z boson", "os dilepton"),
        aliases=("reconstruct Z", "on-Z dilepton candidate"),
    ),
    HelperSpec(
        name="find_w_candidate_leptonic",
        section="reconstruction",
        summary="Compute leptonic W candidate transverse mass from lepton and MET.",
        keywords=("w leptonic candidate", "leptonic w", "transverse mass lepton met"),
        aliases=("reconstruct leptonic W", "W->lν candidate", "W leptonic proxy"),
    ),
    HelperSpec(
        name="find_higgs_candidate_4l",
        section="reconstruction",
        summary="Compute four-lepton Higgs candidate mass.",
        keywords=("higgs 4l", "four-lepton higgs", "h→4l"),
        aliases=("H->4l", "four-lepton Higgs"),
    ),
    HelperSpec(
        name="find_higgs_candidate_2b",
        section="reconstruction",
        summary="Compute di-b-jet Higgs candidate mass.",
        keywords=("higgs 2b", "di-b-jet higgs", "h→bb"),
        aliases=("H->bb", "bb Higgs candidate"),
    ),
    HelperSpec(
        name="find_higgs_candidate_gammagamma",
        section="reconstruction",
        summary="Compute diphoton Higgs candidate mass.",
        keywords=("higgs gammagamma", "diphoton higgs", "h→γγ"),
        aliases=("H->γγ", "diphoton Higgs"),
    ),

    # =========================================================================
    # tau-specific reconstruction
    # =========================================================================
    HelperSpec(
        name="find_ditau_os_pair",
        section="tau_reconstruction",
        summary="Find the best opposite-sign tau pair, optionally within a mass window.",
        keywords=("ditau os", "opposite-sign tau pair", "tau tau"),
        aliases=("OS tau pair", "ττ OS candidate"),
    ),
    HelperSpec(
        name="find_ditau_ss_pair",
        section="tau_reconstruction",
        summary="Find the best same-sign tau pair.",
        keywords=("ditau ss", "same-sign tau pair", "tau tau"),
        aliases=("SS tau pair", "ττ SS candidate"),
    ),
]
