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

from mpi4py import MPI
        
comm=MPI.COMM_WORLD
rank=comm.Get_rank()
size=comm.Get_size()

from processor import GenericWrapper, simpleLogger, STATUS_TERMINATED, STATUS_ACTIVE    
import processor
import types
import traceback

def process(workflow, inputs, args):
    processes={}
    inputmappings = {}
    outputmappings = {}
    success=True
    nodes = [ node.getContainedObject() for node in workflow.graph.nodes() ]
    if rank == 0 and not args.simple:
        try:
            processes, inputmappings, outputmappings = processor.assign_and_connect(workflow, size)
        except:
            success=False
    success=comm.bcast(success,root=0)

    if args.simple or not success:
        ubergraph = processor.create_partitioned(workflow)
        nodes = [ node.getContainedObject() for node in ubergraph.graph.nodes() ]
        if rank == 0:
            print 'Partitions: %s' % ', '.join(('[%s]' % ', '.join((pe.id for pe in part)) for part in workflow.partitions))
            for node in ubergraph.graph.nodes():
                wrapperPE = node.getContainedObject()
                print('%s contains %s' % (wrapperPE.id, [n.getContainedObject().id for n in wrapperPE.workflow.graph.nodes()]))
            try:
                processes, inputmappings, outputmappings = processor.assign_and_connect(ubergraph, size)
                inputs = processor.map_inputs_to_partitions(ubergraph, inputs)
                success = True
            except:
                # print traceback.format_exc()
                print 'dispel4py.mpi_process: Not enough processes for execution of graph'
                success = False

    success=comm.bcast(success,root=0)

    if not success:
        return

    try:
        inputs = { pe.id : v for pe, v in inputs.iteritems() }
    except AttributeError:
        pass
    processes=comm.bcast(processes,root=0)
    inputmappings=comm.bcast(inputmappings,root=0)
    outputmappings=comm.bcast(outputmappings,root=0)
    inputs=comm.bcast(inputs,root=0)
    
    if rank == 0:
        print 'Processes: %s' % processes
        # print 'Inputs: %s' % inputs

    for pe in nodes:
        if rank in processes[pe.id]:
            provided_inputs = processor.get_inputs(pe, inputs)
            wrapper = MPIWrapper(pe, provided_inputs)
            wrapper.targets = outputmappings[rank]
            wrapper.sources = inputmappings[rank]
            wrapper.process()

class MPIWrapper(GenericWrapper):
    
    def __init__(self, pe, provided_inputs=None):
        GenericWrapper.__init__(self, pe)
        self.pe.log = types.MethodType(simpleLogger, pe)
        self.pe.rank = rank
        self.provided_inputs = provided_inputs
        self.terminated = 0

    def _read(self):
        result = super(MPIWrapper, self)._read()
        if result is not None:
            return result
            
        status = MPI.Status()
        msg=comm.recv(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG, status=status)
        tag = status.Get_tag()
        while tag == STATUS_TERMINATED:
            self.terminated += 1
            if self.terminated >= self._num_sources:
                break
            else:
               msg=comm.recv(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG, status=status)
               tag = status.Get_tag()
        return msg, tag

    def _write(self, name, data):
        try:
            targets = self.targets[name]
        except KeyError:
            # no targets
            # self.pe.log('Produced output: %s' % {name: data})
            return
        for (inputName, communication) in targets:
            output = { inputName : data }
            dest = communication.getDestination(output)
            for i in dest:
                # self.pe.log('Sending %s to %s' % (output, i))
                request=comm.isend(output, tag=STATUS_ACTIVE, dest=i)
                status = MPI.Status()
                request.Wait(status)
                
    def _terminate(self):
        for output, targets in self.targets.iteritems():
            for (inputName, communication) in targets:
                for i in communication.destinations:
                    # self.pe.log('Terminating consumer %s' % i)
                    request=comm.isend(None, tag=STATUS_TERMINATED, dest=i)
