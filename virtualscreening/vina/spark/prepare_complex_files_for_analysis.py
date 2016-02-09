from pyspark import SparkContext, SparkConf
from pyspark.sql import SQLContext, Row	
import os
import operator
import ConfigParser as configparser
import ntpath
from vina_utils import get_file_name_sorted_energy, get_directory_pdbqt_analysis, get_files_pdbqt, get_directory_pdb_analysis, get_directory_complex_pdb_analysis, get_files_pdb, loading_pdb_2_list, get_name_receptor_pdb, get_name_model_pdb, get_files_pdb_filter
from summary_statistics import get_summary_statistics, save_txt_summary_statistics
from pdbqt_io import split_pdbqt, pdbqt2pdb
from datetime import datetime
from pdb_io import replace_chain_atom_line

def save_analysis_log(finish_time, start_time):
	log_file_name = 'vs_prepare_files_for_analysis.log'
	current_path = os.getcwd()
	path_file = os.path.join(current_path, log_file_name)
	log_file = open(path_file, 'w')

	diff_time = finish_time - start_time
	msg = 'Starting ' + str(start_time) +'\n'
	log_file.write(msg)
	msg = 'Finishing ' + str(finish_time) +'\n'
	log_file.write(msg)
	msg = 'Time Execution (seconds): ' + str(diff_time.total_seconds()) +'\n'
	log_file.write(msg)


def main():

	sc = SparkContext()

	config = configparser.ConfigParser()
	config.read('config.ini')

	#Broadcast
	#Path that contains all files for analysis
	path_analysis = config.get('DEFAULT', 'path_analysis')
	#Path where all pdbqt files from VS are 
	path_save_structure = config.get('DEFAULT', 'path_save_structure')
	#Path where all pdb receptor are
	path_receptor_pdb = config.get('DEFAULT', 'pdb_path')	
	#Path for saving pdbqt files that are splited from VS
	path_analysis_pdbqt = get_directory_pdbqt_analysis(path_analysis)
	#Path for saving pdb files of models generated by VS
	path_analysis_pdb = get_directory_pdb_analysis(path_analysis)
	#Path for saving complex pdb files of models and receptor
	path_analysis_pdb_complex = get_directory_complex_pdb_analysis(path_analysis)
	path_analysis_pdb_complex_b = sc.broadcast(path_analysis_pdb_complex)
	#Path for drugdesign project
	path_spark_drugdesign = config.get('DRUGDESIGN', 'path_spark_drugdesign')
	#Runing MGLTools for pdbqt to pdb
	pythonsh       = config.get('VINA', 'pythonsh')
	script_pdbqt_to_pdb = config.get('VINA', 'script_pdbqt_to_pdb')	

	#Adding Python Source file
	sc.addPyFile(os.path.join(path_spark_drugdesign,"vina_utils.py"))
	sc.addPyFile(os.path.join(path_spark_drugdesign,"summary_statistics.py"))
	sc.addPyFile(os.path.join(path_spark_drugdesign,"pdbqt_io.py"))
	sc.addPyFile(os.path.join(path_spark_drugdesign,"pdb_io.py"))

	start_time = datetime.now()

	#Creating complex: receptor+pdb_model.pdb

	#Loading all PDB receptor files into memory
	list_all_pdb_receptor_files_path = []
	all_receptor_for_complex = get_files_pdb(path_receptor_pdb)
	for receptor in all_receptor_for_complex:
		list_all_pdb_receptor_files_path.append(loading_pdb_2_list(receptor))

	for pdb_receptor_files in list_all_pdb_receptor_files_path:		
		#Getting receptor name by fully path
		base_file_name_receptor = get_name_receptor_pdb(str(pdb_receptor_files[0]))
		#PDB file loaded into memory is sent by broadcast
		pdb_file_receptor = pdb_receptor_files[1]
		pdb_file_receptor = sc.broadcast(pdb_file_receptor)
		
		#Loading PDB model files based on receptor into memory
		all_model_for_complex = get_files_pdb_filter(path_analysis_pdb,base_file_name_receptor)
		all_model_for_complexRDD = sc.parallelize(all_model_for_complex)
		all_model_filesRDD = all_model_for_complexRDD.map(loading_pdb_2_list).collect()
		all_model_filesRDD	= sc.parallelize(all_model_filesRDD)
# ********** Starting function **********************************************************		
		def build_list_model_for_complex(model):
			full_path_model = model[0]
			model_file = model[1]
			path_pdb_complex = path_analysis_pdb_complex_b.value #Obtained from broadcast
			#Building complex file based on model file name
			base_name_model = get_name_model_pdb(full_path_model)
			complex_name = "compl_"+base_name_model+".pdb"
			full_path_for_save_complex = os.path.join(path_analysis_pdb_complex,complex_name)
			return (model_file, full_path_for_save_complex)
# ********** Finish function **********************************************************					
		all_model_filesRDD = all_model_filesRDD.map(build_list_model_for_complex).collect()

		all_model_filesRDD = sc.parallelize(all_model_filesRDD)
# ********** Starting function **********************************************************
		def save_model_receptor(list_receptor_model_file):
			receptor_file = pdb_file_receptor.value #Obtained from broadcast
			model_file = list_receptor_model_file[0]			
			full_path_for_save_complex = list_receptor_model_file[1]
			#Open file for writting the complex
			f_compl = open(full_path_for_save_complex, "w")
			#Insert lines of receptor
			for item in  receptor_file:
				f_compl.write(item)
			#Insert lines of model and insert Z chain
			for item in model_file:
				item = replace_chain_atom_line(item,"d","z")
				f_compl.write(item)
			f_compl.close()
# ********** Finish function **********************************************************
		all_model_filesRDD.foreach(save_model_receptor)
	
	finish_time = datetime.now()

	save_analysis_log(finish_time, start_time)

main()