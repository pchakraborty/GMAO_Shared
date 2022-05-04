#!/usr/bin/env python3
#
import os
import sys
import subprocess
import shutil
import glob
import ruamel.yaml
import shlex

class catchment(object):
  def __init__(self, params_file):
     yaml = ruamel.yaml.YAML()
     stream ='' 
     with  open(params_file, 'r') as f:
        stream = f.read()
     self.config = yaml.load(stream)

  def regrid(self):
     print("\nRegridding catchment.....\n")
     config = self.config
     model = ''
     in_rstfile =''
     if (config['input']['surface']['catchment']['regrid']):
        model = 'catch'
        in_rstfile = config['input']['surface']['catchment']['rst_file']
     elif (config['input']['surface']['catchcnclm40']['regrid']):
        model = 'catchcnclm40'
        in_rstfile = config['input']['surface']['catchcnclm40']['rst_file']
     elif (config['input']['surface']['catchcnclm45']['regrid']):
        model = 'catchcnclm45'
        in_rstfile = config['input']['surface']['catchcnclm45']['rst_file']
     if model == '':
        return
             

     bindir  = os.getcwd()

     in_bcsdir  = config['input']['shared']['bcs_dir']
     out_bcsdir = config['output']['shared']['bcs_dir']
     out_dir    = config['output']['shared']['out_dir']
     expid      = config['output']['shared']['expid']
     in_wemin   = config['input']['surface']['wemin']
     out_wemin  = config['output']['surface']['wemin']
     surflay    = config['output']['surface']['surflay']
     in_tilefile = config['input']['surface']['tile_file']
     out_tilefile = config['output']['surface']['tile_file']
     account    = config['slurm']['account']
     yyyymmddhh_= str(config['input']['shared']['yyyymmddhh'])
     suffix     = yyyymmddhh_[0:8]+'_'+yyyymmddhh_[8:10]+'z.nc4'

     if (expid) :
        expid = expid + '.'
     else:
        expid = ''
     suffix = '_rst.' + suffix
     out_rstfile = expid + os.path.basename(in_rstfile).split('_rst')[0].split('.')[-1]+suffix

     if not os.path.exists(out_dir) : os.makedirs(out_dir)
     print( "cd " + out_dir)
     os.chdir(out_dir)

     InData_dir = out_dir+'/InData/'
     print ("mkdir -p" + InData_dir)
     os.makedirs(InData_dir, exist_ok = True)
    
     f = os.path.basename(in_rstfile)
     dest = InData_dir+'/'+f
     # file got copy because the computing node cannot access archive
     print('\nCopy ' + rst + ' to ' +dest)
     shutil.copyfile(rst,dest)
     in_rstfile = dest
 
     mk_catch_j_template = """#!/bin/csh -f
#SBATCH --account={account}
#SBATCH --ntasks=56
#SBATCH --time=1:00:00
#SBATCH --job-name=mk_catch
#SBATCH --qos=debug
#SBATCH --output={out_dir}/{mk_catch_log}
#

source {Bin}/g5_modules
set echo

limit stacksize unlimited

set esma_mpirun_X = ( {Bin}/esma_mpirun -np 56 )
set mk_CatchmentRestarts_X   = ( {Bin}/mk_CatchmentRestarts.x )

set params = ( -model {model}  -time {time} -in_tilefile {in_tilefile} )
set params = ( $params -out_bcs {out_bcs} -out_tilefile {out_tilefile} -out_dir {out_dir} )
set params = ( $params -surflay {surflay} -in_wemin {in_wemin} -out_wemin {out_wemin} ) 
set params = ( $params -in_rst {in_rstfile} -out_rst {out_rstfile} ) 
$esma_mpirun_X $mk_CatchmentRestarts_X $params

"""
     catch1script =  mk_catch_j_template.format(Bin = bindir, account = account, out_bcs = out_bcsdir, \
                  model = model, out_dir = out_dir, mk_catch_log = 'mk_catch_log', surflay = surflay,  \
                  in_wemin   = in_wemin, out_wemin = out_wemin, out_tilefile = out_tilefile, in_tilefile = in_tilefile, \
                  in_rstfile = in_rstfile, out_rstfile = out_rstfile, time = yyyymmddhh_ )

     catch_scrpt = open('mk_catchment.j','wt')
     catch_scrpt.write(catch1script)
     catch_scrpt.close()
     print("sbatch -W mk_catchment.j")
     subprocess.call(['sbatch','-W', 'mk_catchment.j'])

     os.chdir(bindir)

if __name__ == '__main__' :
   catch = catchment('regrid_params.yaml')
   catch.regrid()
