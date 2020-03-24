#!/usr/bin/env python3

import sys
import os
import json
import numpy as np
import ROOT
import awkward
import uproot
import argparse
import importlib
from array import array
from root_numpy.tmva import evaluate_reader
import xml.etree.ElementTree as ET

parser = argparse.ArgumentParser()

parser.add_argument(
    "--dframes", type=str, default="df_step1.awkd",
    help="awkd file of datasets df prepared, default=%(default)s"
    )

parser.add_argument(
    "--lepton", type=str, default="m",
    help="muon or electron channel, default=%(default)s"
    )

parser.add_argument(
    "--boson", type=str, default="W",
    help="W or Z, default=%(default)s"
    )

parser.add_argument(
    "--region", type=str, default="signal_loose_W",
    help="region , default=%(default)s"
    )

parser.add_argument(
    "--output", type=str, default="",
    help="output filename, default='region'_'lepton'.root"
    )

args = parser.parse_args()

# samples dict
# ============
samples_dict = list(awkward.load(args.dframes))
samples_dict = dict.fromkeys([i.split("/")[0] for i in samples_dict])

# a class to book multiple hists
# ==============================
class book_hist_dict:
    def __init__(self, xbins, xlow=0, xup=1, titleX="",
                 ybins=None, ylow=None, yup=None, titleY="",
                 keys=[], keys_sub=[]):
        self.xbins = xbins
        self.xlow = xlow
        self.xup = xup
        self.titleX = titleX
        self.ybins = ybins
        self.ylow = ylow
        self.yup = yup
        self.titleY = titleY
        self.keys = keys
        self.keys_sub = keys_sub

    def hist_1D(self):
        if type(self.xbins) == int:
            variable = ROOT.TH1F("", "", self.xbins, self.xlow, self.xup)
            bw = variable.GetBinWidth(1)

        elif type(self.xbins) == np.ndarray:
            variable = ROOT.TH1F("", "", len(self.xbins) - 1, self.xbins.astype(np.float64))
            bw = None

        else:
            return None

        titleX = self.titleX
        if bw is not None:
            titleY = f"Events/{bw}"
        else:
            titleY = "Events"

        variable.SetTitle(f"{titleX};{titleX};{titleY}")
        variable.SetName(titleX)

        return variable

    def hist_2D(self):
        if type(self.xbins) == int:

            if type(self.ybins) == int:
                variable = ROOT.TH2F("", "", self.xbins, self.xlow, self.xup,
                                     self.ybins, self.ylow, self.yup)

            elif type(self.ybins) == np.ndarray:
                variable = ROOT.TH2F("", "", self.xbins, self.xlow, self.xup,
                                     len(self.ybins) - 1, self.ybins.astype(np.float64))

        elif type(self.xbins) == np.ndarray:
            if type(self.ybins) == int:
                variable = ROOT.TH2F("", "", len(self.xbins) - 1, self.xbins.astype(np.float64),
                                     self.ybins, self.ylow, self.yup)

            elif type(self.ybins) == np.ndarray:
                variable = ROOT.TH2F("", "", len(self.xbins) - 1, self.xbins.astype(np.float64),
                                     len(self.ybins) - 1, self.ybins.astype(np.float64))

        else:
            return None

        titleX = self.titleX
        titleY = self.titleY

        variable.SetTitle(f"{titleX}_{titleY};{titleX};{titleY}")
        variable.SetName(f"{titleX}_{titleY}")

        return variable

    def clone(self):

        if self.ybins is None:
            hist_ = self.hist_1D()
        else:
            hist_ = self.hist_2D()

        hist_dict = {}

        for key in self.keys:
            name_ = f"{key}_{hist_.GetName()}"
            hist_dict[key] = hist_.Clone()
            hist_dict[key].SetName(name_)

            for key_sub in self.keys_sub:
                name = f"{name_}_{key_sub}"
                hist_dict[f"{key}_{key_sub}"] = hist_.Clone()
                hist_dict[f"{key}_{key_sub}"].SetName(name)

        return hist_dict

# book histograms
# ===============

# xbins, xlow, xup, variable
hists_1D = [
    (40, 0, 2000, "lept1_pt"),
    #(30, 0, 300, "lept2_pt"),
    (26, -2.6, 2.6, "lept1_eta"),
    #(25, -2.5, 2.5, "lept2_eta"),
    (34, -3.4, 3.4, "lept1_phi"),
    #(32, -3.2, 3.2, "lept2_phi"),
    (20, 0, 1000, "pf_met_corr"),
    (34, -3.4, 3.4, "pf_met_corr_phi"),
    # ak8 jet
    (80, 0.0, 400.0, "fatjet_m"),
    (80, 200.0, 2000.0, "fatjet_pt"),
    (26, -2.6, 2.6, "fatjet_eta"),
    (34, -3.4, 3.4, "fatjet_phi"),
    (40, 0.0, 0.5, "fatjet_n2b1"),
    (40, 0.0, 0.4, "fatjet_n2b2"),
    (40, 0.0, 1.0, "fatjet_tau21"),
    # W
    (50, 0.0, 2000.0, "w_pt"),
    (51, -5.1, 5.1, "w_eta"),
    (40, 0.0, 2000.0, "w_mt"),
    # vbf jets
    (120, 0.0, 2000.0, "vbf_j1_pt"),
    (40, 0.0, 2000.0, "vbf_j2_pt"),
    (51, -5.1, 5.1, "vbf_j1_eta"),
    (51, -5.1, 5.1, "vbf_j2_eta"),
    (20, 0.0, 10.0, "vbf_jj_Deta"),
    (34, -3.4, 3.4, "vbf_j1_phi"),
    (34, -3.4, 3.4, "vbf_j2_phi"),
    (40, 500.0, 2500.0, "vbf_jj_m"),
    #
    (60, -6.0, 6.0, "boson_centrality"),
    (40, -4.0, 4.0, "zeppenfeld_w_Deta"),
    (40, -4.0, 4.0, "zeppenfeld_v_Deta"),
    # W V system
    (50, 0, 2500, "wv_m"),
    (np.array([600, 700, 800, 900,
               1000, 1200, 1500, 2000, 2500]), 0, 0, "wv_m_8bin"),
    (60, 0.0, 600.0, "wv_pt"),
    (20, -5.0, 5.0, "wv_eta"),
    (34, -3.4, 3.4, "wv_phi"),
    (40, -1.0, 1.0, "mva_score"),
]

hists_2D = [
    (40, 0.0, 0.5, "n2b1",
     40, 0.0, 1.0, "tau21"),
    (40, 0.0, 0.4, "n2b2",
     40, 0.0, 1.0, "tau21"),
]

hist_keys = list(samples_dict.keys())

ROOT.TH1.SetDefaultSumw2()

for histogram in hists_1D:
    make_hists = (
        f"h_{histogram[3]} = book_hist_dict("
        f"xbins=histogram[0], xlow=histogram[1],"
        f"xup=histogram[2], titleX=histogram[3],"
        f"keys=hist_keys)"
    )
    exec(f"{make_hists}.clone()")

for histogram in hists_2D:
    make_hists = (
        f"h2_{histogram[3]}_{histogram[7]} = book_hist_dict("
        f"xbins=histogram[0], xlow=histogram[1],"
        f"xup=histogram[2], titleX=histogram[3],"
        f"ybins=histogram[4], ylow=histogram[5],"
        f"yup=histogram[6], titleY=histogram[7],"
        f"keys=hist_keys)"
    )
    exec(f"{make_hists}.clone()")

# fill ROOT histogram with numpy array
# ===================================
def fill_hist_1d(hist, array, weight=1.0, overflow_in_last_bin=False):

    if len(array) == 0:
        return None

    if type(weight) == float:
        for v in array:
            hist.Fill(v, weight)

    else:
        for v, w in zip(array, weight):
            hist.Fill(v, w)

    if overflow_in_last_bin:
        last_bin = hist.GetNbinsX()
        last_content = hist.GetBinContent(last_bin)
        overflow_bin = last_bin + 1
        overflow_content = hist.GetBinContent(overflow_bin)

        hist.SetBinContent(last_bin, last_content + overflow_content)
        hist.SetBinContent(overflow_bin, 0.0)

    return None

def fill_hist_2d(hist, array1, array2, weight=1.0):

    if len(array1) == 0:
        return None

    if type(weight) == float:
        for v1, v2 in zip(array1, array2):
            hist.Fill(v1, v2, weight)

    else:
        for v1, v2, w in zip(array1, array2, weight):
            hist.Fill(v1, v2, w)

    return None

# total raw entries in data sets
total_entries = book_hist_dict(xbins=1, titleX="total_entries").hist_1D()
total_entries.SetCanExtend(ROOT.TH1.kAllAxes)

# selection code import
sel_code = importlib.import_module(f"selections.{args.region}")

lep_channel = {
    "e": sel_code.e_channel,
    "m": sel_code.m_channel
}

if args.boson == "Z":
    lep_channel2 = {
        "e": sel_code.e_channel2,
        "m": sel_code.m_channel2
    }

region_ = sel_code.region_
apply_btag0Wgt = sel_code.apply_btag0Wgt

# add selection code to root file
code_text = open(f"selections/{args.region}.py").read()
ttext = ROOT.TText(0.0, 0.0, "\n" + code_text)
ttext.SetName("selection_code")


# loop over samples, apply selections,
# and fill histograms.
# ===================================

dfs = awkward.load(args.dframes)

for i in dfs:

    xs_weight = dfs[i]["xs_weight"]

    df = dfs[i]["dframe"]

    key = i.split("/")[0]
    filename = i.split("/")[1]

    print(key, xs_weight, filename)

    lep_sel = lep_channel[args.lepton](df)
    region_sel = region_(df, args.lepton)

    if args.boson == "W":
        skim_df = df[lep_sel & region_sel]
        total_weight = xs_weight * skim_df["gen_weight"] * skim_df["trig_eff_weight"] \
                        * skim_df["id_eff_weight"] * skim_df["pu_weight"]

    if args.boson == "Z":
        lep_sel2 = lep_channel2[args.lepton](df)
        skim_df = df[lep_sel & lep_sel2 & region_sel]
        total_weight = xs_weight * skim_df["gen_weight"] * skim_df["trig_eff_weight"] * skim_df["trig_eff_weight2"] \
                        * skim_df["id_eff_weight"] * skim_df["id_eff_weight2"] * skim_df["pu_weight"]

    if apply_btag0Wgt:
        total_weight = total_weight * skim_df["btag0_weight"]

    print("filling hists .... ")

    if "data" in key:
        total_entries.Fill("data", len(skim_df))

    else:
        total_entries.Fill(key, len(skim_df))

    lept1_pt = skim_df["lept1_pt"]
    fill_hist_1d(h_lept1_pt[key], lept1_pt, total_weight, overflow_in_last_bin=True)

    #lept2_pt = skim_df["lept2_pt"]
    #fill_hist_1d(h_lept2_pt[key], lept2_pt, total_weight)

    lept1_eta = skim_df["lept1_eta"]
    fill_hist_1d(h_lept1_eta[key], lept1_eta, total_weight)

    #lept2_eta = skim_df["lept2_eta"]
    #fill_hist_1d(h_lept2_eta[key], lept2_eta, total_weight)

    lept1_phi = skim_df["lept1_phi"]
    fill_hist_1d(h_lept1_phi[key], lept1_phi, total_weight)

    #lept2_phi = skim_df["lept2_phi"]
    #fill_hist_1d(h_lept2_phi[key], lept2_phi, total_weight)

    pf_met_corr = skim_df["pf_met_corr"]
    fill_hist_1d(h_pf_met_corr[key], pf_met_corr, total_weight, overflow_in_last_bin=True)

    pf_met_corr_phi = skim_df["pf_met_corr_phi"]
    fill_hist_1d(h_pf_met_corr_phi[key], pf_met_corr_phi, total_weight)

    fatjet_m = skim_df["fatjet_m"]
    fill_hist_1d(h_fatjet_m[key], fatjet_m, total_weight, overflow_in_last_bin=True)

    fatjet_pt = skim_df["fatjet_pt"]
    fill_hist_1d(h_fatjet_pt[key], fatjet_pt, total_weight, overflow_in_last_bin=True)

    fatjet_eta = skim_df["fatjet_eta"]
    fill_hist_1d(h_fatjet_eta[key], fatjet_eta, total_weight)

    fatjet_phi = skim_df["fatjet_phi"]
    fill_hist_1d(h_fatjet_phi[key], fatjet_phi, total_weight)

    fatjet_n2b1 = df["fatjet_n2b1"]
    fill_hist_1d(h_fatjet_n2b1[key], fatjet_n2b1, total_weight, overflow_in_last_bin=True)

    fatjet_n2b2 = df["fatjet_n2b2"]
    fill_hist_1d(h_fatjet_n2b2[key], fatjet_n2b2, total_weight, overflow_in_last_bin=True)

    fatjet_tau21 = df["fatjet_tau21"]
    fill_hist_1d(h_fatjet_tau21[key], fatjet_tau21, total_weight, overflow_in_last_bin=True)

    w_pt = skim_df["w_pt"]
    fill_hist_1d(h_w_pt[key], w_pt, total_weight, overflow_in_last_bin=True)

    w_eta = skim_df["w_eta"]
    fill_hist_1d(h_w_eta[key], w_eta, total_weight)

    w_mt = skim_df["w_mt"]
    fill_hist_1d(h_w_mt[key], w_mt, total_weight, overflow_in_last_bin=True)

    vbf_j1_pt = skim_df["vbf_j1_pt"]
    fill_hist_1d(h_vbf_j1_pt[key], vbf_j1_pt, total_weight, overflow_in_last_bin=True)

    vbf_j2_pt = skim_df["vbf_j2_pt"]
    fill_hist_1d(h_vbf_j2_pt[key], vbf_j2_pt, total_weight, overflow_in_last_bin=True)

    vbf_j1_eta = skim_df["vbf_j1_eta"]
    fill_hist_1d(h_vbf_j1_eta[key], vbf_j1_eta, total_weight)

    vbf_j2_eta = skim_df["vbf_j2_eta"]
    fill_hist_1d(h_vbf_j2_eta[key], vbf_j2_eta, total_weight)

    vbf_j1_phi = skim_df["vbf_j1_phi"]
    fill_hist_1d(h_vbf_j1_phi[key], vbf_j1_phi, total_weight)

    vbf_j2_phi = skim_df["vbf_j2_phi"]
    fill_hist_1d(h_vbf_j2_phi[key], vbf_j2_phi, total_weight)

    vbf_jj_Deta = skim_df["vbf_jj_Deta"]
    fill_hist_1d(h_vbf_jj_Deta[key], vbf_jj_Deta, total_weight)

    vbf_jj_m = skim_df["vbf_jj_m"]
    fill_hist_1d(h_vbf_jj_m[key], vbf_jj_m, total_weight)

    boson_centrality = skim_df["boson_centrality"]
    fill_hist_1d(h_boson_centrality[key], boson_centrality, total_weight)

    zeppenfeld_w_Deta = skim_df["zeppenfeld_w_Deta"]
    fill_hist_1d(h_zeppenfeld_w_Deta[key], zeppenfeld_w_Deta, total_weight)

    zeppenfeld_v_Deta = skim_df["zeppenfeld_v_Deta"]
    fill_hist_1d(h_zeppenfeld_v_Deta[key], zeppenfeld_v_Deta, total_weight)

    wv_m = skim_df["wv_m"]
    fill_hist_1d(h_wv_m[key], wv_m, total_weight, overflow_in_last_bin=True)
    fill_hist_1d(h_wv_m_8bin[key], wv_m, total_weight, overflow_in_last_bin=True)

    wv_pt = skim_df["wv_pt"]
    fill_hist_1d(h_wv_pt[key], wv_pt, total_weight, overflow_in_last_bin=True)

    wv_eta = skim_df["wv_eta"]
    fill_hist_1d(h_wv_eta[key], wv_eta, total_weight)

    wv_phi = skim_df["wv_phi"]
    fill_hist_1d(h_wv_phi[key], wv_phi, total_weight)

    #mva_score = skim_df["mva_score"]
    #fill_hist_1d(h_mva_score[key], mva_score, total_weight)

    # 2D hists
    fill_hist_2d(h2_n2b1_tau21[key], fatjet_n2b1, fatjet_tau21, total_weight)
    fill_hist_2d(h2_n2b2_tau21[key], fatjet_n2b2, fatjet_tau21, total_weight)

# write hists to root file
# ========================

if args.output == "":
    out_hist_filename = f"{args.region}_{args.lepton}.root"
else:
    out_hist_filename = args.output

out_hist_file = ROOT.TFile(out_hist_filename, "recreate")
out_hist_file.cd()

for k in samples_dict:

    for histogram in hists_1D:
        exec(f"h_{histogram[3]}[k].Write()")

    for histogram in hists_2D:
        exec(f"h2_{histogram[3]}_{histogram[7]}[k].Write()")

total_entries.Write()
ttext.Write()

out_hist_file.Write()
out_hist_file.Close()