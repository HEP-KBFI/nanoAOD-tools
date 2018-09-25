#!/usr/bin/env python
import os, sys
import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True
from importlib import import_module
from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import PostProcessor

def find_modules(names):
  split = names.split(',')
  has_args = lambda name: name.find('(') != -1 and name.endswith(')') and name.count('(') == 1 and name.count(')') == 1
  modules = {}
  for name in split:
      if has_args(name):
          module_name = name[:name.find('(')]
          module_args = tuple(name[ name.find('(') + 1 : name.find(')') ].split(';'))
          modules[module_name] = module_args
      else:
          modules[name] = None
  return modules

if __name__ == "__main__":
    from optparse import OptionParser
    parser = OptionParser(usage="%prog [options] outputDir inputFiles")
    parser.add_option("-s", "--postfix",dest="postfix", type="string", default=None, help="Postfix which will be appended to the file name (default: _Friend for friends, _Skim for skims)")
    parser.add_option("-J", "--json",  dest="json", type="string", default=None, help="Select events using this JSON file")
    parser.add_option("-c", "--cut",  dest="cut", type="string", default=None, help="Cut string")
    parser.add_option("-b", "--branch-selection",  dest="branchsel", type="string", default=None, help="Branch selection")
    parser.add_option("--bi", "--branch-selection-input",  dest="branchsel_in", type="string", default=None, help="Branch selection input")
    parser.add_option("--bo", "--branch-selection-output",  dest="branchsel_out", type="string", default=None, help="Branch selection output")
    parser.add_option("--friend",  dest="friend", action="store_true", default=False, help="Produce friend trees in output (current default is to produce full trees)")
    parser.add_option("--full",  dest="friend", action="store_false",  default=False, help="Produce full trees in output (this is the current default)")
    parser.add_option("--noout",  dest="noOut", action="store_true",  default=False, help="Do not produce output, just run modules")
    parser.add_option("--justcount",   dest="justcount", default=False, action="store_true",  help="Just report the number of selected events")
    parser.add_option("-I", "--import", dest="imports",  type="string", default=[], action="append", nargs=2, help="Import modules (python package, comma-separated list of ");
    parser.add_option("-z", "--compression",  dest="compression", type="string", default=("LZMA:9"), help="Compression: none, or (algo):(level) ")

    (options, args) = parser.parse_args()

    if options.friend:
        if options.cut or options.json: raise RuntimeError("Can't apply JSON or cut selection when producing friends")

    if len(args) < 2 :
	 parser.print_help()
         sys.exit(1)
    outdir = args[0]; args = args[1:]

    modules = []
    for mod, names in options.imports:
        import_module(mod)
        obj = sys.modules[mod]
        selnames = find_modules(names)
        for name in dir(obj):
            if name[0] == "_": continue

            if name in selnames:
                print "Loading %s from %s%s" % (name, mod, (' with arguments: %s' % ', '.join(selnames[name]) if selnames[name] else ''))
                imported_func = getattr(obj,name)
                if selnames[name]:
                    bound_func = lambda: imported_func(*selnames[name])
                    modules.append(bound_func())
                else:
                    modules.append(imported_func())
    if options.noOut:
        if len(modules) == 0:
            raise RuntimeError("Running with --noout and no modules does nothing!")
    if options.branchsel!=None:
        options.branchsel_in = options.branchsel
        options.branchsel_out = options.branchsel
    p=PostProcessor(outdir,args,options.cut,options.branchsel_in,modules,options.compression,options.friend,options.postfix,options.json,options.noOut,options.justcount,outputbranchsel= options.branchsel_out)
    p.run()

