# Copyright (c) The University of Edinburgh 2014
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import types
from dispel4py.core import GenericPE
from processor import GenericWrapper, SimpleProcessingPE
import processor


def simpleLogger(self, msg):
    print("%s: %s" % (self.id, msg))

def process_and_return(workflow, inputs, resultmappings=None):
    numnodes = 0
    for node in workflow.graph.nodes():
        numnodes += 1
        node.getContainedObject().numprocesses = 1
    processes, inputmappings, outputmappings = processor.assign_and_connect(workflow, numnodes)
    # print 'Processes: %s' % processes
    # print inputmappings
    # print outputmappings
    proc_to_pe = {}
    for node in workflow.graph.nodes():
        pe = node.getContainedObject()
        proc_to_pe[processes[pe.id][0]] = pe
    
    simple = SimpleProcessingPE(inputmappings, outputmappings, proc_to_pe)
    simple.id = 'SimplePE'
    simple.result_mappings = resultmappings
    wrapper = SimpleProcessingWrapper(simple, [inputs])
    wrapper.targets = {}
    wrapper.sources = {}
    wrapper.process()
    
    # now collect output data into a single list for each PE
    outputs = {}
    for (pe_id, output_name), data in wrapper.outputs.iteritems():
        if pe_id not in outputs:
            outputs[pe_id] = {}
        try:
            outputs[pe_id][output_name] += data 
        except KeyError:
            outputs[pe_id][output_name] = data
    return outputs
    
def process(workflow, inputs, args=None, resultmappings=None):
    try:
        print 'Inputs: %s' % { pe.id: data for pe, data in inputs.iteritems() }
    except:
        print 'Inputs: %s' % { pe: data for pe, data in inputs.iteritems() }
    results = process_and_return(workflow, inputs, resultmappings)
    print 'Outputs: %s' % results
    
class SimpleProcessingWrapper(GenericWrapper):
    
    def __init__(self, pe, provided_inputs=None):
        GenericWrapper.__init__(self, pe)
        self.pe.log = types.MethodType(simpleLogger, pe)
        self.provided_inputs = provided_inputs
        self.outputs = {}

    def _read(self):
        result = super(SimpleProcessingWrapper, self)._read()
        if result is not None:
            return result
        else:
            return None, processor.STATUS_TERMINATED

    def _write(self, name, data):
        # self.pe.log('Writing %s to %s' % (data, name))
        try:
            self.outputs[name].extend(data)
        except KeyError:
            self.outputs[name] = data
