#!/bin/bash

work_dir="hists_output"
output_tag="2021-05-12_binfix"
tar_file=${output_tag}.tar.gz

base_dir="root://cmseos.fnal.gov//store/user/singhr/wv_vbs_ntuples"
rel_dir="mva_2021_Apr_27"

run_on_years=("2016")
#run_on_years=("2016" "2017" "2018")

run_on_channels=("zv" "zjj")

run_on_main_regions=("sr")
#run_on_main_regions=("sr" "cr_vjets")

mkdir -p ${work_dir}
pushd ${work_dir}

# make sandbox
check_tar=false
if [[ -f ${tar_file} ]]
then
  echo "${tar_file} already exists."
  read -r -p "Do you want to overwrite ${tar_file}? [y/N] " response
  response=${response,,}
  if [[ "$response" =~ ^(yes|y)$ ]]
  then
    check_tar=true
  else
    echo "=> Exiting"
    exit
  fi
else
  check_tar=true
fi

$check_tar && $ANALYSIS_BASE/tools/make_tar.sh ${tar_file}

regions=(\
  "X_l.X_m.X_e" \
  "X_e_pdfUp" \
  "X_m_pdfUp" \
  "X_l_pdfUp" \
  "X_e_pdfDown" \
  "X_m_pdfDown" \
  "X_l_pdfDown" \
  "X_e_qcdUp" \
  "X_m_qcdUp" \
  "X_l_qcdUp" \
  "X_e_qcdDown" \
  "X_m_qcdDown" \
  "X_l_qcdDown" \
  "X_l_jesFlavorQCDUp.X_m_jesFlavorQCDUp.X_e_jesFlavorQCDUp" \
  "X_l_jesFlavorQCDDown.X_m_jesFlavorQCDDown.X_e_jesFlavorQCDDown" \
  "X_l_jesRelativeBalUp.X_m_jesRelativeBalUp.X_e_jesRelativeBalUp" \
  "X_l_jesRelativeBalDown.X_m_jesRelativeBalDown.X_e_jesRelativeBalDown" \
  "X_l_jesHFUp.X_m_jesHFUp.X_e_jesHFUp" \
  "X_l_jesHFDown.X_m_jesHFDown.X_e_jesHFDown" \
  "X_l_jesBBEC1Up.X_m_jesBBEC1Up.X_e_jesBBEC1Up" \
  "X_l_jesBBEC1Down.X_m_jesBBEC1Down.X_e_jesBBEC1Down" \
  "X_l_jesEC2Up.X_m_jesEC2Up.X_e_jesEC2Up" \
  "X_l_jesEC2Down.X_m_jesEC2Down.X_e_jesEC2Down" \
  "X_l_jesAbsoluteUp.X_m_jesAbsoluteUp.X_e_jesAbsoluteUp" \
  "X_l_jesAbsoluteDown.X_m_jesAbsoluteDown.X_e_jesAbsoluteDown" \
  "X_l_jesBBEC1_YearUp.X_m_jesBBEC1_YearUp.X_e_jesBBEC1_YearUp" \
  "X_l_jesBBEC1_YearDown.X_m_jesBBEC1_YearDown.X_e_jesBBEC1_YearDown" \
  "X_l_jesEC2_YearUp.X_m_jesEC2_YearUp.X_e_jesEC2_YearUp" \
  "X_l_jesEC2_YearDown.X_m_jesEC2_YearDown.X_e_jesEC2_YearDown" \
  "X_l_jesAbsolute_YearUp.X_m_jesAbsolute_YearUp.X_e_jesAbsolute_YearUp" \
  "X_l_jesAbsolute_YearDown.X_m_jesAbsolute_YearDown.X_e_jesAbsolute_YearDown" \
  "X_l_jesHF_YearUp.X_m_jesHF_YearUp.X_e_jesHF_YearUp" \
  "X_l_jesHF_YearDown.X_m_jesHF_YearDown.X_e_jesHF_YearDown" \
  "X_l_jesRelativeSample_YearUp.X_m_jesRelativeSample_YearUp.X_e_jesRelativeSample_YearUp" \
  "X_l_jesRelativeSample_YearDown.X_m_jesRelativeSample_YearDown.X_e_jesRelativeSample_YearDown" \
  "X_l_jesTotalUp.X_m_jesTotalUp.X_e_jesTotalUp" \
  "X_l_jesTotalDown.X_m_jesTotalDown.X_e_jesTotalDown" \
  "X_l_scaleUp" \
  "X_l_scaleDown" \
  "X_l_puUp" \
  "X_l_puDown" \
  "X_l_L1PFUp" \
  "X_l_L1PFDown" \
  "X_l_jetPUIDUp" \
  "X_l_jetPUIDDown"
)

for channel in ${run_on_channels[*]}
do
  for year in ${run_on_years[*]}
  do
  outTag=${output_tag}_${year}
  in_dir=${rel_dir}/${year}

    for main_region in ${run_on_main_regions[*]}
    do
      to_replace=${main_region}_${channel}
      region_list="("
      for region_ in ${regions[*]}; do region_list="${region_list}${region_//X/${to_replace}}, "; done
      region_list=${region_list::-2}")"
    done

    condor_submit \
      universe=vanilla \
      executable=../run_make_hists.sh \
      transfer_input=True \
      transfer_output=True \
      stream_error=True \
      stream_output=True \
      log_filename="../condor_logs/\$(hist_file)" \
      log="/dev/null" \
      output="\$(log_filename).out" \
      error="\$(log_filename).err" \
      transfer_input_files="../run_make_hists.sh, ${tar_file}" \
      transfer_output_files="\$(hist_file).root" \
      -append "arguments = ${tar_file} \$(reg) ${year} ${base_dir} ${in_dir} 8 \$(hist_file).root" \
      -append "hist_file = hists_${outTag}_\$(reg)" \
      -append "queue 1 reg in ${region_list}" \
      /dev/null
  done
done

popd
echo "DONE!"
#exit
