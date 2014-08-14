#!/usr/bin/python2
from __future__ import print_function
import numpy as np
import numpad as ad
import time

from mesh import Mesh
from field import Field, FaceField
from ops import interpolate, div, ddt, implicit, laplacian, forget

case = 'cyclic/'
mesh = Mesh(case)

t = 0.1
dt = 0.005
DT = 0.01

#initialize
T = Field.zeros('T', mesh, 1)
mid = np.array([0.5, 0.5, 0.5])
T.setInternalField(np.exp(-10*np.linalg.norm(mid-mesh.cellCentres[:mesh.nInternalCells], axis=1)).reshape(-1,1))
#T = Field.read('T', mesh, t)
U = 1.*ad.ones((mesh.nFaces, 3))*np.array([1., 0., 0])
U = FaceField('U', mesh, U)

for i in range(0, 300):
    if i % 20 == 0:
        T.write(t)

    print('Simulation Time:', t, 'Time step:', dt)
    equation = lambda TC: [ddt(TC, T, dt) + div(interpolate(TC), U) - laplacian(TC, DT)]
    boundary = lambda TI: T.setInternalField(TI)
    
    implicit(equation, boundary, [T])
    forget([T])
    t += dt
    t = round(t, 6)
    print()
    
