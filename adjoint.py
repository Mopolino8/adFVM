#!/usr/bin/python2
from __future__ import print_function


import config, parallel
from config import ad
from parallel import pprint
from field import IOField, Field
from op import laplacian, curl
from interp import central
from problem import primal, nSteps, writeInterval, objectiveGradient, perturb, writeResult
from compat import printMemUsage

import numpy as np
import time
import sys

primal.adjoint = True
mesh = primal.mesh
statusFile = primal.statusFile
try:
    with open(statusFile, 'r') as status:
        firstCheckpoint, result = status.readlines()
    pprint('Read status file, checkpoint =', firstCheckpoint)
    firstCheckpoint = int(firstCheckpoint)
    result = float(result)
except:
    firstCheckpoint = 0
    result = 0.
if parallel.rank == 0:
    timeSteps = np.loadtxt(primal.timeStepFile, ndmin=2)
    timeSteps = np.concatenate((timeSteps, np.array([[np.sum(timeSteps[-1]).round(9), 0]])))
else:
    timeSteps = np.zeros((nSteps + 1, 2))
parallel.mpi.Bcast(timeSteps, root=0)

# provision for restaring adjoint
adjointNames = ['{0}a'.format(name) for name in primal.names]
if firstCheckpoint == 0:
    adjointFields = [IOField(name, np.zeros((mesh.origMesh.nInternalCells, dimensions[0]), config.precision), dimensions, mesh.calculatedBoundary) for name, dimensions in zip(adjointNames, primal.dimensions)]
else:
    adjointFields = [IOField.read(name, mesh, timeSteps[nSteps - firstCheckpoint*writeInterval][0]) for name in adjointNames]
adjointInternalFields = [phi.complete() for phi in adjointFields]
adjointNewFields = [phi.phi.field for phi in adjointFields]
# UGLY HACK
oldFunc = primal.getBCFields
primal.getBCFields = lambda: adjointFields
adjointInitFunc = primal.function(adjointInternalFields, adjointNewFields, 'adjoint_init')
primal.getBCFields = oldFunc
newFields = adjointInitFunc(*[phi.field for phi in adjointFields])
for phi, field in zip(adjointFields, newFields):
    phi.field = field

# local adjoint fields
stackedAdjointFields = primal.stackFields(adjointFields, np)
pprint('\nSTARTING ADJOINT')
pprint('Number of steps:', nSteps)
pprint('Write interval:', writeInterval)
pprint()

def writeAdjointFields(stackedAdjointFields, writeTime):
    fields = primal.unstackFields(stackedAdjointFields, IOField, names=adjointNames, boundary=mesh.calculatedBoundary)
    start = time.time()
    for phi in fields:
    # TODO: fix unstacking F_CONTIGUOUS
        phi.field = np.ascontiguousarray(phi.field)
        phi.write(writeTime)
    parallel.mpi.Barrier()
    end = time.time()
    pprint('Time for writing fields: {0}'.format(end-start))
    pprint()

def viscosity(solution):
    rho = solution[:,0].reshape((-1, 1))
    rhoU = solution[:,1:4]
    U = Field('U', rhoU/rho, (3,))
    vorticity = curl(central(U, mesh.origMesh))
    return 1e-9*vorticity.magSqr()

# adjont field smoothing,
adjointField = Field('a', ad.matrix(), (5,))
weight = Field('w', ad.bcmatrix(), (1,))
smoother = laplacian(adjointField, weight)
smooth = primal.function([adjointField.field, weight.field], smoother.field, 'smoother', BCs=False)

totalCheckpoints = nSteps/writeInterval
for checkpoint in range(firstCheckpoint, totalCheckpoints):
    pprint('PRIMAL FORWARD RUN {0}/{1}: {2} Steps\n'.format(checkpoint, totalCheckpoints, writeInterval))
    primalIndex = nSteps - (checkpoint + 1)*writeInterval
    t, dt = timeSteps[primalIndex]
    solutions = primal.run(startTime=t, dt=dt, nSteps=writeInterval, mode='forward')

    pprint('ADJOINT BACKWARD RUN {0}/{1}: {2} Steps\n'.format(checkpoint, totalCheckpoints, writeInterval))
    # if starting from 0, create the adjointField
    pprint('Time marching for', ' '.join(adjointNames))

    if checkpoint == 0:
        t, dt = timeSteps[-1]
        lastSolution = solutions[-1]
        stackedAdjointFields  = np.ascontiguousarray(objectiveGradient(lastSolution)/(nSteps + 1))
        writeAdjointFields(stackedAdjointFields, t)

    for step in range(0, writeInterval):
        printMemUsage()
        start = time.time()
        fields = primal.unstackFields(stackedAdjointFields, IOField, names=adjointNames, boundary=mesh.calculatedBoundary)
        for phi in fields:
            phi.info()

        adjointIndex = writeInterval-1 - step
        t, dt = timeSteps[primalIndex + adjointIndex]
        if primal.dynamicMesh
            previousMesh, previousSolution = solutions[adjointIndex]
            # new mesh boundary
            primal.mesh.origMesh.boundary = previousMesh.boundary
        else:
            previousSolution = solutions[adjointIndex]
        #paddedPreviousSolution = parallel.getRemoteCells(previousSolution, mesh)
        ## adjoint time stepping
        #paddedJacobian = np.ascontiguousarray(primal.gradient(paddedPreviousSolution, stackedAdjointFields))
        #jacobian = parallel.getAdjointRemoteCells(paddedJacobian, mesh)
        gradients = primal.gradient(previousSolution, stackedAdjointFields, dt)
        gradient = gradients[0]
        sourceGradient = gradients[1:]

        stackedAdjointFields = np.ascontiguousarray(gradient) + np.ascontiguousarray(objectiveGradient(previousSolution)/(nSteps + 1))
        # define function maybe
        #pprint('Smoothing adjoint field')
        #weight = viscosity(previousSolution).field
        #stackedAdjointFields[:mesh.origMesh.nInternalCells] += smooth(stackedAdjointFields, weight)

        # compute sensitivity using adjoint solution
        perturbations = perturb(mesh.origMesh)
        for derivative, delphi in zip(sourceGradient, perturbations):
            result += np.sum(np.ascontiguousarray(derivative) * delphi)

        parallel.mpi.Barrier()
        end = time.time()
        pprint('Time for adjoint iteration: {0}'.format(end-start))
        pprint('Time since beginning:', end-config.runtime)
        pprint('Simulation Time and step: {0}, {1}\n'.format(*timeSteps[primalIndex + adjointIndex + 1]))

    writeAdjointFields(stackedAdjointFields, t)
    with open(statusFile, 'w') as status:
        status.write('{0}\n{1}\n'.format(checkpoint + 1, result))

writeResult('adjoint', result)
